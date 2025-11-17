from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from functools import wraps


def permissao_necessaria(level, redirect_url="acesso_negado"):
    """
    Decorador que redireciona para URL específica quando não tem permissão,
    com tratamento especial para visitantes.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(
                    request, "Por favor, faça login para acessar esta página."
                )
                return redirect(reverse("accounts:login"))

            # Se for visitante, verifica se a view está na lista de permissões
            if request.user.permissoes == "visitantes":
                allowed_views_for_visitantes = [
                    "listar_militar",
                    "listar_outros_status_militar",
                    "ver_militar",
                    "listar_rpt",
                    "ver_rpt",
                    "posto_list",
                    "posto_detail",
                    "municipio_detail",
                    "posto_secao_detail",
                    "medalha_list",
                    "curso_list",
                    "listar_bm",
                    "ver_bm",
                    "index",
                ]

                view_name = request.resolver_match.url_name
                if view_name not in allowed_views_for_visitantes:
                    messages.error(
                        request,
                        "Visitantes não têm permissão para acessar esta página.",
                    )
                    return redirect(reverse(redirect_url))

            # Verificação normal de permissão hierárquica
            if not request.user.has_permission_level(level):
                messages.error(
                    request,
                    f"Você precisa ter permissão de {level} para acessar esta página.",
                )
                return redirect(reverse(redirect_url))

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def apply_model_permissions_filter(model_class, redirect_url="acesso_negado"):
    """
    Decorador que aplica filtro e redireciona se não tiver permissão
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(
                    request, "Por favor, faça login para acessar esta página."
                )
                return redirect(reverse("accounts:login"))

            # Aplica o filtro de permissões
            queryset = request.user.filter_by_permissions(model_class.objects.all())

            # Se o queryset estiver vazio devido a restrições de permissão
            if queryset.count() == 0 and not (
                request.user.is_superuser or request.user.has_permission_level("gestor")
            ):
                messages.error(request, "Seu acesso está restrito a dados do seu SGB.")
                return redirect(reverse(redirect_url))

            request.filtered_queryset = queryset
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def permission_required(perm, redirect_url="acesso_negado"):
    """
    Decorador que verifica permissão específica e redireciona
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(
                    request, "Por favor, faça login para acessar esta página."
                )
                return redirect(reverse("accounts:login"))

            if not (request.user.is_superuser or request.user.has_perm(perm)):
                messages.error(
                    request, f"Você não tem a permissão '{perm}' necessária."
                )
                return redirect(reverse(redirect_url))

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def group_required(*group_names, redirect_url="acesso_negado"):
    """
    Decorador que verifica grupo e redireciona
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(
                    request, "Por favor, faça login para acessar esta página."
                )
                return redirect(reverse("accounts:login"))

            if not (
                request.user.is_superuser
                or request.user.groups.filter(name__in=group_names).exists()
            ):
                groups = ", ".join(group_names)
                messages.error(
                    request, f"Você precisa pertencer ao grupo {groups} para acessar."
                )
                return redirect(reverse(redirect_url))

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
