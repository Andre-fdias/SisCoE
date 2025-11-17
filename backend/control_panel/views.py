# control_panel/views.py (completo)
import psutil
import docker
import redis
import subprocess
import json
import logging
import os
import re
from urllib.parse import urlparse
from datetime import datetime
from django.db import connection
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib import messages

from .models import UsefulLink

logger = logging.getLogger(__name__)


def is_staff_or_superuser(user):
    return user.is_superuser


# Funções auxiliares movidas para o topo para melhor organização
def _calculate_cpu_percent(stats):
    """Calcula uso de CPU a partir das stats do Docker"""
    try:
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        system_delta = (
            stats["cpu_stats"]["system_cpu_usage"]
            - stats["precpu_stats"]["system_cpu_usage"]
        )

        if system_delta > 0 and cpu_delta > 0:
            return round(
                (cpu_delta / system_delta)
                * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"])
                * 100,
                2,
            )
        return 0
    except (KeyError, ZeroDivisionError):
        return 0


def _calculate_memory_usage(stats):
    """Calcula uso de memória a partir das stats do Docker em MB"""
    try:
        return round(stats["memory_stats"]["usage"] / (1024 * 1024), 2)
    except KeyError:
        return 0


def _check_port_status(host, port):
    """Verifica se uma porta está respondendo"""
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return "active" if result == 0 else "down"
    except (socket.gaierror, socket.error):
        return "down"


# Views Principais
@login_required
@user_passes_test(is_staff_or_superuser)
def dashboard(request):
    # O contexto é carregado dinamicamente via API, não é necessário aqui.
    return render(request, "control_panel/dashboard.html")


@login_required
@user_passes_test(is_staff_or_superuser)
def services_view(request):
    context = {
        "service_status": get_detailed_service_status(),
        "container_status": get_container_status(),
    }
    return render(request, "control_panel/services.html", context)


@login_required
@user_passes_test(is_staff_or_superuser)
def logs_view(request):
    log_level = request.GET.get("level", "ERROR")
    context = {
        "recent_logs": get_recent_logs(level=log_level),
        "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        "selected_level": log_level,
    }
    return render(request, "control_panel/logs.html", context)


@login_required
@user_passes_test(is_staff_or_superuser)
def performance_view(request):
    context = {
        "performance_metrics": get_performance_metrics(),
        "database_metrics": get_database_metrics(),
    }
    return render(request, "control_panel/performance.html", context)


@login_required
@user_passes_test(is_staff_or_superuser)
def containers_view(request):
    context = {
        "containers": get_detailed_container_info(),
        "images": get_docker_images(),
        "system_info": get_docker_system_info(),
    }
    return render(request, "control_panel/containers.html", context)


@login_required
@user_passes_test(is_staff_or_superuser)
def settings_view(request):
    if request.method == "POST":
        # Processar configurações
        messages.success(request, "Configurações atualizadas com sucesso!")

    context = {
        "settings": get_system_settings(),
    }
    return render(request, "control_panel/settings.html", context)


# Funções de Coleta de Dados
def get_system_metrics():
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time

        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": memory.percent,
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "disk_usage": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_display": str(uptime).split(".")[0],
            "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
            "network_io": psutil.net_io_counters()._asdict(),
        }
    except Exception as e:
        logger.error(f"Erro ao coletar métricas do sistema: {e}")
        return {"error": str(e)}


def get_service_status():
    services = {}

    # PostgreSQL
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
            )
            table_count = cursor.fetchone()[0]
            cursor.execute("SELECT pg_database_size(current_database());")
            db_size = cursor.fetchone()[0]

        services["postgresql"] = {
            "status": "healthy",
            "message": f"{table_count} tabelas, {round(db_size/1024/1024, 2)} MB",
            "version": version.split(",")[0],
            "details": {
                "tables": table_count,
                "size_mb": round(db_size / 1024 / 1024, 2),
            },
        }
    except Exception as e:
        services["postgresql"] = {
            "status": "down",
            "message": "Connection failed",
            "version": "N/A",
            "details": {"error": str(e)},
        }

    # Redis
    try:
        r = redis.Redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2)
        r.ping()
        info = r.info()
        services["redis"] = {
            "status": "healthy",
            "message": f"Memória: {info['used_memory_human']}",
            "version": info["redis_version"],
            "details": {
                "used_memory": info["used_memory_human"],
                "connected_clients": info["connected_clients"],
                "keyspace_hits": info["keyspace_hits"],
            },
        }
    except Exception as e:
        services["redis"] = {
            "status": "down",
            "message": "Connection failed",
            "version": "N/A",
            "details": {"error": str(e)},
        }

    # Django App
    services["django"] = {
        "status": "healthy",
        "message": "Aplicação rodando normalmente",
        "version": settings.VERSION,
        "details": {
            "debug": settings.DEBUG,
            "allowed_hosts": len(settings.ALLOWED_HOSTS),
        },
    }

    # Celery
    try:
        from celery import current_app

        insp = current_app.control.inspect(timeout=1)
        active_workers = insp.active() or {}
        services["celery"] = {
            "status": "healthy" if active_workers else "warning",
            "message": (
                f"{len(active_workers)} workers ativos"
                if active_workers
                else "Nenhum worker ativo"
            ),
            "version": "5.3+",
            "details": {
                "workers": len(active_workers),
                "active_tasks": sum(len(tasks) for tasks in active_workers.values()),
            },
        }
    except Exception as e:
        services["celery"] = {
            "status": "down",
            "message": "Failed to connect",
            "version": "N/A",
            "details": {"error": str(e)},
        }

    return services


def get_detailed_service_status():
    basic_status = get_service_status()

    # Adicionar mais detalhes
    for service_name, service in basic_status.items():
        if service_name == "postgresql" and service["status"] == "healthy":
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT schemaname, tablename, tableowner 
                        FROM pg_tables 
                        WHERE schemaname = 'public' 
                        ORDER BY tablename 
                        LIMIT 10
                    """
                    )
                    service["tables"] = cursor.fetchall()
            except Exception as e:
                service["tables_error"] = str(e)

    return basic_status


def get_django_info(request):
    from django.conf import settings
    from django.apps import apps

    return {
        "debug": settings.DEBUG,
        "installed_apps": len(settings.INSTALLED_APPS),
        "models_count": len(apps.get_models()),
        "middleware": len(settings.MIDDLEWARE),
        "database_engine": settings.DATABASES["default"]["ENGINE"],
        "allowed_hosts": settings.ALLOWED_HOSTS,
        "time_zone": settings.TIME_ZONE,
        "static_root": str(settings.STATIC_ROOT),
        "media_root": str(settings.MEDIA_ROOT),
    }


def get_container_status():
    try:
        client = docker.from_env(timeout=5)
        containers = []

        for container in client.containers.list(all=True):
            stats = {}
            if container.status == "running":
                try:
                    # Use one_shot=False for a stream, but for a snapshot, one_shot=True is better.
                    # However, the API docs suggest one_shot=False is deprecated and behavior is now default.
                    stats = container.stats(stream=False)
                except Exception:
                    pass  # Ignora erro se não conseguir pegar stats

            containers.append(
                {
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else "N/A",
                    "ports": container.ports,
                    "created": container.attrs["Created"][:19],
                    "cpu_usage": _calculate_cpu_percent(stats) if stats else 0,
                    "memory_usage": _calculate_memory_usage(stats) if stats else 0,
                }
            )

        return containers
    except docker.errors.DockerException as e:
        logger.error(f"Erro de comunicação com o Docker: {e}")
        return []  # Retorna lista vazia em caso de erro de comunicação
    except Exception as e:
        logger.error(f"Erro inesperado ao obter status dos containers: {e}")
        return []


def get_detailed_container_info():
    try:
        client = docker.from_env(timeout=5)
        containers = []

        for container in client.containers.list(all=True):
            container_info = {
                "id": container.short_id,
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "N/A",
                "command": container.attrs["Config"]["Cmd"],
                "created": container.attrs["Created"],
                "ports": container.ports,
                "volumes": container.attrs["Mounts"],
                "network": container.attrs["NetworkSettings"]["Networks"],
                "labels": container.labels,
            }

            if container.status == "running":
                try:
                    stats = container.stats(stream=False)
                    container_info["stats"] = {
                        "cpu_percent": _calculate_cpu_percent(stats),
                        "memory_usage": _calculate_memory_usage(stats),
                        "memory_limit": stats.get("memory_stats", {}).get("limit", 0),
                        "network_io": stats.get("networks", {}),
                    }
                except Exception as e:
                    container_info["stats_error"] = str(e)

            containers.append(container_info)

        return containers
    except Exception as e:
        logger.error(f"Erro ao obter informações detalhadas dos containers: {e}")
        return []


def get_docker_images():
    try:
        client = docker.from_env(timeout=5)
        return [
            {
                "tags": image.tags,
                "id": image.short_id,
                "created": image.attrs["Created"],
                "size": image.attrs["Size"],
            }
            for image in client.images.list()
        ]
    except Exception as e:
        logger.error(f"Erro ao obter imagens Docker: {e}")
        return []


def get_docker_system_info():
    try:
        client = docker.from_env(timeout=5)
        return client.info()
    except Exception as e:
        logger.error(f"Erro ao obter informações do sistema Docker: {e}")
        return {}


def get_external_tools():
    tools = []
    for link in UsefulLink.objects.filter(is_active=True).order_by("order"):
        parsed_url = urlparse(link.url)
        status = "active"  # Default for relative URLs

        # Check status only for external http/https URLs
        if parsed_url.scheme in ["http", "https"] and parsed_url.hostname:
            port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
            status = _check_port_status(parsed_url.hostname, port)

        tools.append(
            {
                "name": link.name,
                "url": link.url,
                "icon": link.icon,
                "status": status,
                "description": link.description,
            }
        )
    return tools


def get_recent_logs(level="ERROR", limit=50):
    """Obtém logs recentes da aplicação, parseando nível e mensagem."""
    try:
        log_file = (
            getattr(settings, "LOGGING", {})
            .get("handlers", {})
            .get("file", {})
            .get("filename")
        )
        if not log_file or not os.path.exists(log_file):
            return [
                {
                    "level": "ERROR",
                    "message": f"Arquivo de log não configurado ou não encontrado: {log_file}",
                }
            ]

        logs = []
        log_pattern = re.compile(
            r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*[:-]?\s*(.*)", re.IGNORECASE
        )

        with open(log_file, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if len(logs) >= limit:
                    break

                match = log_pattern.match(line.strip())
                if match:
                    log_level = match.group(1).upper()
                    log_message = match.group(2).strip()
                else:
                    log_level = "INFO"
                    log_message = line.strip()

                if log_level == level.upper() or level.upper() == "ALL":
                    logs.append({"level": log_level, "message": log_message})

        return logs
    except Exception as e:
        logger.error(f"Erro ao ler logs: {e}")
        return [{"level": "ERROR", "message": f"Erro ao carregar logs: {e}"}]


def get_performance_metrics():
    """Métricas de performance da aplicação lidas do cache."""
    total_requests = cache.get("total_requests", 0)
    total_request_time = cache.get("total_request_time", 0.0)
    error_count_4xx = cache.get("error_count_4xx", 0)
    error_count_5xx = cache.get("error_count_5xx", 0)

    if total_requests > 0:
        average_response_time_ms = (total_request_time / total_requests) * 1000
        error_rate = ((error_count_4xx + error_count_5xx) / total_requests) * 100
    else:
        average_response_time_ms = 0
        error_rate = 0

    return {
        "requests_per_second": 0,
        "average_response_time_ms": round(average_response_time_ms, 2),
        "error_rate": round(error_rate, 2),
        "total_requests": total_requests,
        "error_count_4xx": error_count_4xx,
        "error_count_5xx": error_count_5xx,
        "active_users": 0,
    }


def get_database_metrics():
    """Métricas do banco de dados"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_connections,
                    COUNT(*) FILTER (WHERE state = 'active') as active_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """
            )
            connections = cursor.fetchone()

            cursor.execute(
                """
                SELECT schemaname, relname, n_live_tup
                FROM pg_stat_user_tables 
                ORDER BY n_live_tup DESC 
                LIMIT 10;
            """
            )
            table_stats = cursor.fetchall()

            return {
                "total_connections": connections[0],
                "active_connections": connections[1],
                "table_stats": table_stats,
            }
    except Exception as e:
        return {"error": str(e)}


def get_system_settings():
    """Configurações do sistema"""
    return {
        "app_name": "SisCoE",
        "version": getattr(settings, "VERSION", "N/A"),
        "environment": "Development" if settings.DEBUG else "Production",
        "debug_mode": settings.DEBUG,
        "time_zone": settings.TIME_ZONE,
        "language_code": settings.LANGUAGE_CODE,
    }


# API Endpoints
@login_required
@user_passes_test(is_staff_or_superuser)
def api_health(request):
    """Endpoint de health check"""
    return JsonResponse(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system_metrics": get_system_metrics(),
            "service_status": get_service_status(),
            "django_info": get_django_info(request),
            "container_status": get_container_status(),
            "external_tools": get_external_tools(),
        }
    )


@login_required
@user_passes_test(is_staff_or_superuser)
def api_metrics(request):
    """Endpoint de métricas"""
    return JsonResponse(
        {
            "system_metrics": get_system_metrics(),
            "performance_metrics": get_performance_metrics(),
            "database_metrics": get_database_metrics(),
            "timestamp": datetime.now().isoformat(),
        }
    )


@login_required
@user_passes_test(is_staff_or_superuser)
def api_services(request):
    """Endpoint de status dos serviços"""
    return JsonResponse(
        {
            "services": get_detailed_service_status(),
            "timestamp": datetime.now().isoformat(),
        }
    )


@login_required
@user_passes_test(is_staff_or_superuser)
def api_containers(request):
    """Endpoint de status dos containers"""
    return JsonResponse(
        {
            "containers": get_detailed_container_info(),
            "timestamp": datetime.now().isoformat(),
        }
    )


# Ações
@login_required
@user_passes_test(is_staff_or_superuser)
@require_http_methods(["POST"])
@csrf_exempt  # Para simplificar, mas em produção use CSRF token
def api_restart_service(request):
    """Reinicia um serviço via docker-compose"""
    service = request.POST.get("service")
    if not service:
        service_data = json.loads(request.body)
        service = service_data.get("service")

    command = ["docker-compose", "restart", service]

    try:
        if service not in ["web", "celery", "celery-beat", "rabbitmq", "redis", "db"]:
            return JsonResponse(
                {"status": "error", "message": "Serviço inválido"}, status=400
            )

        result = subprocess.run(
            command, capture_output=True, text=True, timeout=60, check=False
        )
        if result.returncode == 0:
            return JsonResponse(
                {
                    "status": "success",
                    "message": f"Serviço {service} reiniciado com sucesso.",
                }
            )
        else:
            logger.error(f"Erro ao reiniciar serviço {service}: {result.stderr}")
            return JsonResponse(
                {"status": "error", "message": result.stderr or result.stdout},
                status=500,
            )

    except subprocess.TimeoutExpired:
        return JsonResponse(
            {"status": "error", "message": f"Timeout ao reiniciar o serviço {service}"},
            status=500,
        )
    except Exception as e:
        logger.error(f"Exceção ao reiniciar serviço: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required
@user_passes_test(is_staff_or_superuser)
@require_http_methods(["POST"])
def api_restart_container(request):
    """Reinicia um container específico"""
    container_name = request.POST.get("container_name")
    if not container_name:
        return JsonResponse(
            {"status": "error", "message": "Nome do container não fornecido"},
            status=400,
        )

    try:
        client = docker.from_env(timeout=5)
        container = client.containers.get(container_name)
        container.restart(timeout=30)

        return JsonResponse(
            {"status": "success", "message": f"Container {container_name} reiniciado"}
        )
    except docker.errors.NotFound:
        return JsonResponse(
            {
                "status": "error",
                "message": f"Container {container_name} não encontrado",
            },
            status=404,
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required
@user_passes_test(is_staff_or_superuser)
@require_http_methods(["POST"])
def api_clear_cache(request):
    """Limpa o cache do Django e do Redis."""
    try:
        cache.clear()
        message = "Cache do Django limpo. "

        try:
            r = redis.Redis.from_url(
                settings.CELERY_BROKER_URL, socket_connect_timeout=2
            )
            r.flushdb()
            message += "Cache do Redis (db 0) limpo."
        except Exception as e:
            logger.warning(f"Não foi possível limpar o cache do Redis: {e}")
            message += "Não foi possível limpar o cache do Redis."

        return JsonResponse({"status": "success", "message": message})
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required
@user_passes_test(is_staff_or_superuser)
@require_http_methods(["POST"])
def api_send_test_email(request):
    """Envia email de teste"""
    try:
        send_mail(
            "Teste do Painel de Controle - SisCoE",
            f"Este é um email de teste enviado para {request.user.email} a partir do painel de controle do SisCoE em {datetime.now()}.",
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=False,
        )
        return JsonResponse(
            {
                "status": "success",
                "message": f"Email de teste enviado para {request.user.email}",
            }
        )
    except Exception as e:
        logger.error(f"Erro ao enviar email de teste: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required
@user_passes_test(is_staff_or_superuser)
@require_http_methods(["POST"])  # Mudado para POST para ser consistente
def api_run_health_check(request):
    """Executa verificação completa de saúde"""
    try:
        health_results = {
            "database": get_service_status().get("postgresql", {}).get("status"),
            "redis": get_service_status().get("redis", {}).get("status"),
            "celery": get_service_status().get("celery", {}).get("status"),
            "system": (
                "healthy"
                if get_system_metrics().get("cpu_usage", 100) < 90
                else "warning"
            ),
        }

        all_healthy = all(status == "healthy" for status in health_results.values())

        return JsonResponse(
            {
                "status": "success",
                "results": health_results,
                "message": (
                    "Verificação de saúde concluída. Tudo parece OK."
                    if all_healthy
                    else "Verificação de saúde concluída com avisos."
                ),
            }
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required
@user_passes_test(is_staff_or_superuser)
@require_http_methods(["POST"])
def api_backup_database(request):
    """Executa backup do banco de dados"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(settings.BASE_DIR, "..", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = os.path.join(backup_dir, f"siscoe_backup_{timestamp}.sql")

        db_settings = settings.DATABASES["default"]

        command = [
            "docker-compose",
            "exec",
            "-T",
            "db",
            "pg_dump",
            f"-U{db_settings['USER']}",
            f"-d{db_settings['NAME']}",
        ]

        env = os.environ.copy()
        env["PGPASSWORD"] = db_settings["PASSWORD"]

        result = subprocess.run(
            command, capture_output=True, text=True, timeout=300, env=env, check=False
        )

        if result.returncode == 0:
            with open(backup_file, "w") as f:
                f.write(result.stdout)

            return JsonResponse(
                {
                    "status": "success",
                    "message": f"Backup criado: {os.path.basename(backup_file)}",
                    "file_size": os.path.getsize(backup_file),
                }
            )
        else:
            logger.error(f"Erro no pg_dump: {result.stderr}")
            return JsonResponse(
                {"status": "error", "message": result.stderr}, status=500
            )

    except subprocess.TimeoutExpired:
        return JsonResponse(
            {"status": "error", "message": "Timeout ao criar backup"}, status=500
        )
    except Exception as e:
        logger.error(f"Erro ao criar backup: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# Handlers de erro
def handler404(request, exception):
    return render(request, "control_panel/404.html", status=404)


def handler500(request):
    return render(request, "control_panel/500.html", status=500)
