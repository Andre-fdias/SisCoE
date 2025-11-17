from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from datetime import datetime, date, timedelta
from .models import Cadastro_adicional, HistoricoCadastro
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
import logging

from backend.core.utils import filter_by_user_sgb


logger = logging.getLogger(__name__)


def alert_response(type, title, message, status=200):
    """
    Helper function to return a JSON response with alert data for AJAX requests.
    The 'modal_alerts.html' JavaScript listens for this structure.
    """
    return JsonResponse(
        {"alert": {"type": type, "title": title, "message": message}}, status=status
    )


@login_required
def cadastrar_adicional(request):
    """
    View para cadastrar Adicional para um militar.
    """
    if request.method == "GET":
        return render(request, "adicional/cadastrar_adicional.html")

    elif request.method == "POST":
        # Obtenção dos dados do formulário
        n_bloco_adicional = request.POST.get("n_bloco_adicional")
        cadastro_id = request.POST.get("cadastro_id")
        data_ultimo_adicional_str = request.POST.get("data_ultimo_adicional")
        situacao_adicional = request.POST.get("situacao_adicional")
        dias_desconto_adicional = int(
            request.POST.get("dias_desconto_adicional", 0) or 0
        )
        sexta_parte = (
            request.POST.get("sexta_parte_hidden", "False") == "True"
        )  # Campo oculto
        user = request.user

        # Determine if it's an AJAX request
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        # Validações básicas
        if not cadastro_id:
            error_msg = "Cadastro do militar não localizado."
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=400
                )
            messages.error(request, error_msg)
            return redirect("adicional:cadastrar_adicional")

        cadastro = get_object_or_404(Cadastro, id=cadastro_id)

        if not data_ultimo_adicional_str:
            error_msg = "Favor inserir a data de concessão do último Adicional"
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=400
                )
            messages.error(request, error_msg)
            return redirect("adicional:cadastrar_adicional")

        try:
            # Conversão de datas
            data_ultimo_adicional = datetime.strptime(
                data_ultimo_adicional_str, "%Y-%m-%d"
            ).date()

            # Validação dos números de bloco
            if not n_bloco_adicional or not n_bloco_adicional.isdigit():
                error_msg = "Número do Bloco Adicional inválido."
                if is_ajax:
                    return alert_response(
                        type="error", title="Erro!", message=error_msg, status=400
                    )
                messages.error(request, error_msg)
                return redirect("adicional:cadastrar_adicional")

            numero_adicional = int(n_bloco_adicional)
            numero_prox_adicional = numero_adicional + 1
            proximo_adicional = (
                data_ultimo_adicional
                + timezone.timedelta(days=365 * 5)
                - timezone.timedelta(days=dias_desconto_adicional)
            )
            mes_proximo_adicional = proximo_adicional.month
            ano_proximo_adicional = proximo_adicional.year

            with transaction.atomic():
                # Criação do Adicional
                adicional = Cadastro_adicional.objects.create(
                    cadastro=cadastro,
                    user_created=user,
                    numero_adicional=numero_adicional,
                    data_ultimo_adicional=data_ultimo_adicional,
                    numero_prox_adicional=numero_prox_adicional,
                    proximo_adicional=proximo_adicional,
                    mes_proximo_adicional=mes_proximo_adicional,
                    ano_proximo_adicional=ano_proximo_adicional,
                    dias_desconto_adicional=dias_desconto_adicional,
                    situacao_adicional=situacao_adicional,
                    sexta_parte=sexta_parte,
                )

                # Registrar no histórico do Adicional
                HistoricoCadastro.objects.create(
                    cadastro=cadastro,
                    cadastro_adicional=adicional,
                    numero_adicional=adicional.numero_adicional,
                    data_ultimo_adicional=adicional.data_ultimo_adicional,
                    situacao_adicional=situacao_adicional,
                    usuario_alteracao=user,
                    numero_prox_adicional=numero_prox_adicional,
                    proximo_adicional=proximo_adicional,
                    mes_proximo_adicional=mes_proximo_adicional,
                    ano_proximo_adicional=ano_proximo_adicional,
                    dias_desconto_adicional=dias_desconto_adicional,
                    status_adicional=adicional.status_adicional,
                )

            success_msg = "Adicional cadastrado com sucesso!"
            if is_ajax:
                return alert_response(
                    type="success", title="Sucesso!", message=success_msg
                )
            messages.success(request, success_msg)
            return redirect("adicional:listar_adicional")

        except ValueError as e:
            error_msg = (
                f"Formato de data inválido. Use o formato AAAA-MM-DD. Erro: {str(e)}"
            )
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=400
                )
            messages.error(request, error_msg)
            return redirect("adicional:cadastrar_adicional")
        except Exception as e:
            error_msg = f"Ocorreu um erro ao cadastrar: {str(e)}"
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=500
                )
            messages.error(request, error_msg)
            return redirect("adicional:cadastrar_adicional")


@login_required
def buscar_militar_adicional(request):
    """
    Busca um militar pelo RE para pré-preencher o formulário de cadastro de Adicional.
    """
    template_name = "adicional/cadastrar_adicional.html"
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        re = request.POST.get("re", "").strip()
        if not re:
            # Removed extra_tags as modal_alerts.html handles styling
            if is_ajax:
                return alert_response(
                    type="error",
                    title="Atenção!",
                    message="Por favor, informe o RE para buscar.",
                    status=400,
                )
            messages.warning(request, "Por favor, informe o RE para buscar.")
            return render(request, template_name)

        try:
            # Busca o cadastro principal
            cadastro = Cadastro.objects.get(re=re)

            # Busca os dados relacionados
            detalhes = (
                DetalhesSituacao.objects.filter(cadastro=cadastro)
                .order_by("-id")
                .first()
            )
            imagem = Imagem.objects.filter(cadastro=cadastro).order_by("-id").first()
            promocao = (
                Promocao.objects.filter(cadastro=cadastro).order_by("-id").first()
            )

            # Verifica dados obrigatórios
            if not detalhes:
                if is_ajax:
                    return alert_response(
                        type="error",
                        title="Erro!",
                        message="Detalhamento não encontrado",
                        status=400,
                    )
                messages.error(request, "Detalhamento não encontrado")
                return render(request, template_name)
            if not promocao:
                if is_ajax:
                    return alert_response(
                        type="error",
                        title="Erro!",
                        message="Dados de Posto e graduação não localizados",
                        status=400,
                    )
                messages.error(request, "Dados de Posto e graduação não localizados")
                return render(request, template_name)

            # Prepara o contexto
            context = {
                "cadastro": cadastro,
                "detalhes": detalhes,
                "imagem": imagem,
                "promocao": promocao,
                "found_re": re,
            }
            # For AJAX, you might want to return HTML snippet or JSON data for dynamic update
            if is_ajax:
                # Example: render a partial template or just return a success signal
                html_form = render_to_string(
                    "adicional/_militar_details_partial.html", context, request=request
                )
                return JsonResponse(
                    {
                        "success": True,
                        "html_form": html_form,
                        "alert": {
                            "type": "success",
                            "title": "Militar Encontrado!",
                            "message": f"Dados do militar {cadastro.nome_completo} carregados.",
                        },
                    }
                )
            return render(request, template_name, context)

        except Cadastro.DoesNotExist:
            error_msg = f'Militar com RE "{re}" não cadastrado no sistema'
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=404
                )
            messages.error(request, error_msg)
            return render(request, template_name, {"searched_re": re})

        except Exception as e:
            error_msg = f"Ocorreu um erro ao buscar o militar: {str(e)}"
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=500
                )
            messages.error(request, error_msg)
            return render(request, template_name)

    return render(request, template_name)


def gravar_historico(instance, usuario_alteracao):
    """
    Grava um snapshot completo do Cadastro_adicional no histórico
    """
    HistoricoCadastro.objects.create(
        cadastro_adicional=instance,
        usuario_alteracao=usuario_alteracao,
        cadastro=instance.cadastro,
        user_created=instance.user_created,
        user_updated=instance.user_updated,
        usuario_conclusao=instance.usuario_conclusao,
        created_at=instance.created_at,
        updated_at=instance.updated_at,
        data_conclusao=instance.data_conclusao,
        numero_adicional=instance.numero_adicional,
        data_ultimo_adicional=instance.data_ultimo_adicional,
        numero_prox_adicional=instance.numero_prox_adicional,
        proximo_adicional=instance.proximo_adicional,
        mes_proximo_adicional=instance.mes_proximo_adicional,
        ano_proximo_adicional=instance.ano_proximo_adicional,
        dias_desconto_adicional=instance.dias_desconto_adicional,
        situacao_adicional=instance.situacao_adicional,
        sexta_parte=instance.sexta_parte,
        confirmacao_6parte=instance.confirmacao_6parte,
        data_concessao_adicional=instance.data_concessao_adicional,
        bol_g_pm_adicional=instance.bol_g_pm_adicional,
        data_publicacao_adicional=instance.data_publicacao_adicional,
        status_adicional=instance.status_adicional,
    )


@login_required
def listar_adicional(request):
    registros_adicional = Cadastro_adicional.objects.all()
    registros_adicional = filter_by_user_sgb(registros_adicional, request.user)

    current_year = datetime.now().year
    anos = list(range(2018, current_year + 2))

    context = {
        "registros_adicional": registros_adicional,
        "anos": anos,
    }
    return render(request, "adicional/listar_adicional.html", context)


@login_required
@require_http_methods(["GET"])
def historico_adicional(request, id):
    """
    View para exibir o histórico completo de um adicional
    """
    adicional = get_object_or_404(
        Cadastro_adicional.objects.select_related("cadastro"), id=id
    )

    historicos = (
        HistoricoCadastro.objects.filter(cadastro_adicional=adicional)
        .select_related("usuario_alteracao")
        .order_by("-data_alteracao")
    )

    context = {
        "adicional": adicional,
        "historicos_encerrados": historicos,
        "campos_historicos": [
            ("data_alteracao", "Data Alteração"),
            ("usuario_alteracao", "Responsável"),
            ("numero_adicional", "Bloco"),
            ("situacao_adicional", "Situação"),
            ("status_adicional", "Status"),
            ("data_publicacao_adicional", "Data Publicação"),
            ("bol_g_pm_adicional", "BOL GPm"),
        ],
    }

    return render(request, "adicional/historico_adicional.html", context)


@login_required
def ver_adicional(request, id):
    """
    View para exibir os detalhes de um registro de Adicional
    """
    adicional = get_object_or_404(
        Cadastro_adicional.objects.select_related(
            "cadastro", "user_created", "user_updated"
        ),
        id=id,
    )

    # Histórico de alterações do adicional específico
    historico_alteracoes = HistoricoCadastro.objects.filter(
        cadastro_adicional=adicional
    ).order_by("-data_alteracao")

    # Histórico de todos adicionais encerrados do militar
    historico_encerrados = (
        Cadastro_adicional.objects.filter(
            cadastro=adicional.cadastro,
            status_adicional=Cadastro_adicional.StatusAdicional.ENCERRADO,
        )
        .exclude(id=id)
        .order_by("numero_adicional")
    )

    context = {
        "cadastro_adicional": adicional,
        "historico_alteracoes": historico_alteracoes,
        "historico_encerrados": historico_encerrados,
        "current_year": datetime.now().year,
    }
    return render(request, "adicional/detalhar_adicional.html", context)


@login_required
def editar_adicional(request, id):
    """
    View para editar um registro de Adicional existente
    """
    adicional = get_object_or_404(Cadastro_adicional, id=id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        try:
            data_ultimo_adicional_str = request.POST.get("data_ultimo_adicional")

            if not data_ultimo_adicional_str:
                error_msg = "Data do último adicional é obrigatória"
                if is_ajax:
                    return alert_response(
                        type="error", title="Erro!", message=error_msg, status=400
                    )
                messages.error(request, error_msg)
                return redirect(reverse("adicional:editar_adicional", args=[id]))

            data_ultimo_adicional = datetime.strptime(
                data_ultimo_adicional_str, "%Y-%m-%d"
            ).date()

            # Atualiza os campos
            adicional.numero_adicional = int(request.POST.get("numero_adicional"))
            adicional.data_ultimo_adicional = data_ultimo_adicional
            adicional.dias_desconto_adicional = int(
                request.POST.get("dias_desconto_adicional", 0)
            )
            adicional.situacao_adicional = request.POST.get("situacao_adicional")

            if "sexta_parte" in request.POST:
                adicional.sexta_parte = True
            else:
                adicional.sexta_parte = False

            adicional.save()

            success_msg = "Adicional atualizado com sucesso"
            if is_ajax:
                return alert_response(
                    type="success", title="Sucesso!", message=success_msg
                )
            messages.success(request, success_msg)
            return redirect(reverse("adicional:ver_adicional", args=[id]))

        except ValueError as e:
            error_msg = f"Erro ao processar os dados: {str(e)}"
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=400
                )
            messages.error(request, error_msg)
            return redirect(reverse("adicional:editar_adicional", args=[id]))
        except Exception as e:
            error_msg = f"Ocorreu um erro inesperado ao editar: {str(e)}"
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=500
                )
            messages.error(request, error_msg)
            return redirect(reverse("adicional:editar_adicional", args=[id]))

    context = {
        "adicional": adicional,
    }
    return render(request, "editar_adicional.html", context)


@login_required
def excluir_adicional(request, id):
    """
    View para excluir um registro de Adicional
    """
    adicional = get_object_or_404(Cadastro_adicional, id=id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        try:
            password = request.POST.get("password")

            if not request.user.check_password(password):
                error_msg = "Autenticação falhou - senha incorreta"
                if is_ajax:
                    return alert_response(
                        type="error",
                        title="Erro de Autenticação!",
                        message=error_msg,
                        status=403,
                    )
                messages.error(request, error_msg)
                return redirect(reverse("adicional:ver_adicional", args=[id]))

            adicional.delete()
            success_msg = "Adicional excluído com sucesso"
            if is_ajax:
                return alert_response(
                    type="success", title="Sucesso!", message=success_msg, status=200
                )
            messages.success(request, success_msg)
            return redirect("adicional:listar_adicional")

        except Exception as e:
            error_msg = f"Erro ao excluir: {str(e)}"
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=500
                )
            messages.error(request, error_msg)
            return redirect(reverse("adicional:ver_adicional", args=[id]))

    return redirect(reverse("adicional:ver_adicional", args=[id]))


def editar_dias_desconto(request, pk):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if request.method == "POST":
        adicional = get_object_or_404(Cadastro_adicional, pk=pk)
        try:
            dias_desconto = int(request.POST.get("dias_desconto", 0))
            if dias_desconto < 0:
                raise ValueError("Dias de desconto não podem ser negativos")

            adicional.dias_desconto_adicional = dias_desconto
            adicional.save()
            success_msg = "Dias de desconto atualizados com sucesso!"
            if is_ajax:
                return alert_response(
                    type="success", title="Sucesso!", message=success_msg
                )
            messages.success(request, success_msg)
        except ValueError as e:
            error_msg = str(e)
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=400
                )
            messages.error(request, error_msg)  # Removed extra_tags
        except Exception as e:
            error_msg = f"Ocorreu um erro inesperado: {str(e)}"
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=500
                )
            messages.error(request, error_msg)

        return redirect("adicional:ver_adicional", id=pk)

    return redirect("adicional:ver_adicional", id=pk)


@login_required
def editar_concessao(request, pk):
    adicional = get_object_or_404(Cadastro_adicional, id=pk)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        try:
            if not request.user.is_authenticated:
                error_msg = "Usuário não autenticado"
                if is_ajax:
                    return alert_response(
                        type="error",
                        title="Erro de Autenticação!",
                        message=error_msg,
                        status=403,
                    )
                messages.error(request, error_msg)  # Removed extra_tags
                return redirect("adicional:ver_adicional", id=pk)

            data_concessao = request.POST.get("data_concessao")
            if data_concessao:
                adicional.data_concessao_adicional = data_concessao
                adicional.status_adicional = (
                    Cadastro_adicional.StatusAdicional.PUBLICADO
                )

            adicional.bol_g_pm_adicional = request.POST.get("bol_g_pm", "")

            data_publicacao = request.POST.get("data_publicacao")
            if data_publicacao:
                adicional.data_publicacao_adicional = data_publicacao

            adicional.user_updated = request.user
            adicional.save()

            HistoricoCadastro.objects.create(
                cadastro_adicional=adicional,
                situacao_adicional=adicional.situacao_adicional,
                usuario_alteracao=request.user,
                numero_prox_adicional=adicional.numero_prox_adicional,
                proximo_adicional=adicional.proximo_adicional,
                mes_proximo_adicional=adicional.mes_proximo_adicional,
                ano_proximo_adicional=adicional.ano_proximo_adicional,
                dias_desconto_adicional=adicional.dias_desconto_adicional,
                cadastro=adicional.cadastro,
            )

            success_msg = "Detalhes atualizados!"
            if is_ajax:
                return alert_response(
                    type="success", title="Sucesso!", message=success_msg
                )
            messages.success(request, success_msg)
            return redirect("adicional:ver_adicional", id=adicional.id)

        except ValueError as e:
            error_msg = f"Erro: {str(e)}"
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=400
                )
            messages.error(request, error_msg)
            return redirect("adicional:ver_adicional", id=adicional.id)

        except Exception as e:
            error_msg = f"Erro: {str(e)}"
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=500
                )
            messages.error(request, error_msg)
            return redirect("adicional:ver_adicional", id=adicional.id)

    return redirect("adicional:ver_adicional", id=adicional.id)


@require_POST
@csrf_exempt  # Consider if you need to exempt CSRF here, generally not recommended for POST
def confirmar_6parte(request, pk):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    try:
        adicional = Cadastro_adicional.objects.get(pk=pk)
        adicional.confirmacao_6parte = True
        adicional.save()
        if is_ajax:
            return alert_response(
                type="success",
                title="Sucesso!",
                message="Confirmação da 6ª Parte registrada com sucesso!",
            )
        return JsonResponse(
            {"success": True}
        )  # Fallback for non-modal AJAX, though modal is preferred
    except Cadastro_adicional.DoesNotExist:
        error_msg = "Adicional não encontrado"
        if is_ajax:
            return alert_response(
                type="error", title="Erro!", message=error_msg, status=404
            )
        return JsonResponse({"success": False, "message": error_msg}, status=404)
    except Exception as e:
        error_msg = str(e)
        if is_ajax:
            return alert_response(
                type="error", title="Erro!", message=error_msg, status=500
            )
        return JsonResponse({"success": False, "message": error_msg}, status=500)


@login_required
def confirmar_sipa(request, pk):
    adicional = get_object_or_404(Cadastro_adicional, pk=pk)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        try:
            if not request.user.is_authenticated:
                error_msg = "Usuário não autenticado"
                if is_ajax:
                    return alert_response(
                        type="error",
                        title="Erro de Autenticação!",
                        message=error_msg,
                        status=403,
                    )
                messages.error(request, error_msg)
                return redirect("adicional:ver_adicional", id=pk)

            password = request.POST.get("password")
            if not password:
                error_msg = "Senha não fornecida"
                if is_ajax:
                    return alert_response(
                        type="error", title="Erro!", message=error_msg, status=400
                    )
                messages.error(request, error_msg)
                return redirect("adicional:ver_adicional", id=pk)

            user = authenticate(
                request, username=request.user.get_username(), password=password
            )
            if not user or user != request.user:
                error_msg = "Senha incorreta"
                if is_ajax:
                    return alert_response(
                        type="error", title="Erro!", message=error_msg, status=403
                    )
                messages.error(request, error_msg)
                return redirect("adicional:ver_adicional", id=pk)

            adicional.dias_desconto_adicional = int(
                request.POST.get("dias_desconto", 0)
            )
            adicional.status_adicional = Cadastro_adicional.StatusAdicional.LANCADO_SIPA
            adicional.numero_prox_adicional = int(
                request.POST.get("numero_prox_adicional", 1)
            )

            proximo_adicional = request.POST.get("proximo_adicional")
            if proximo_adicional:
                adicional.proximo_adicional = datetime.strptime(
                    proximo_adicional, "%Y-%m-%d"
                ).date()
            else:
                adicional.proximo_adicional = None

            if (
                adicional.numero_prox_adicional == 4
            ):  # Assuming 4th additional grants sexta_parte
                adicional.sexta_parte = request.POST.get("sexta_parte") == "on"
            else:
                adicional.sexta_parte = False

            adicional.user_updated = request.user
            adicional.save()

            HistoricoCadastro.objects.create(
                cadastro_adicional=adicional,
                situacao_adicional=adicional.situacao_adicional,
                usuario_alteracao=request.user,
                numero_prox_adicional=adicional.numero_prox_adicional,
                proximo_adicional=adicional.proximo_adicional,
                mes_proximo_adicional=adicional.mes_proximo_adicional,
                ano_proximo_adicional=adicional.ano_proximo_adicional,
                dias_desconto_adicional=adicional.dias_desconto_adicional,
            )

            success_msg = "Lançamento no SIPA confirmado com sucesso!"
            if is_ajax:
                return alert_response(
                    type="success", title="Sucesso!", message=success_msg
                )
            messages.success(request, success_msg)
            return redirect("adicional:ver_adicional", id=pk)

        except ValueError as e:
            error_msg = f"Erro nos dados fornecidos: {str(e)}"
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=400
                )
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)}"
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=500
                )
            messages.error(request, error_msg)

    return redirect("adicional:ver_adicional", id=pk)


@login_required
def carregar_dados_sipa(request, pk):
    adicional = get_object_or_404(Cadastro_adicional, pk=pk)

    data = {
        "numero_prox_adicional": adicional.numero_prox_adicional,
        "proximo_adicional": (
            adicional.proximo_adicional.strftime("%Y-%m-%d")
            if adicional.proximo_adicional
            else ""
        ),
        "dias_desconto_adicional": adicional.dias_desconto_adicional,
        "sexta_parte": adicional.sexta_parte,
        "n_choices": [
            {"value": c[0], "label": c[1]}
            for c in Cadastro_adicional.StatusAdicional.choices
        ],
    }
    # This view is purely for AJAX data loading, so JsonResponse is appropriate.
    return JsonResponse(data)


@login_required
@permission_required("adicional.can_concluir_adicional", raise_exception=True)
def concluir_adicional(request, id):
    logger.info(f"Usuário acessando a view: {request.user.email}")
    logger.info(f"Usuário está autenticado: {request.user.is_authenticated}")

    adicional = get_object_or_404(Cadastro_adicional, id=id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method != "POST":
        if is_ajax:
            return alert_response(
                type="error", title="Erro!", message="Método não permitido", status=405
            )
        return redirect(reverse("adicional:ver_adicional", args=[id]))

    # Using alert_response directly for AJAX and messages for non-AJAX for consistency
    try:
        if adicional.situacao_adicional == "Concluído":
            raise ValidationError("Este adicional já foi concluído.")

        password = request.POST.get("password")
        if not password:
            raise ValidationError("Senha não fornecida.")

        # Autenticação usando email como identificador (ensure your User model supports email authentication this way)
        user = authenticate(request, email=request.user.email, password=password)

        if not user or user != request.user:
            raise ValidationError("Autenticação falhou - senha incorreta.")

        data_concessao_str = request.POST.get("data_concessao")
        if not data_concessao_str:
            raise ValidationError("A data de concessão é obrigatória.")

        try:
            data_concessao = date.fromisoformat(data_concessao_str)
        except ValueError:
            raise ValidationError("Formato de data inválido. Use AAAA-MM-DD.")

        if data_concessao > date.today():
            raise ValidationError("A data de concessão não pode ser no futuro.")

        # Check for sexta_parte only if numero_prox_adicional is 4
        if adicional.numero_prox_adicional == 4:
            sexta_parte = request.POST.get("sexta_parte") == "on"
            if not sexta_parte:
                raise ValidationError(
                    "Confirmação da 6ª Parte é obrigatória para o 4º Adicional."
                )
            adicional.confirmacao_6parte = True
        else:
            adicional.confirmacao_6parte = (
                False  # Ensure it's false if not 4th additional
            )

        # Atualiza o adicional atual para concluído
        adicional.situacao_adicional = "Concluído"
        adicional.status_adicional = "encerrado"
        adicional.data_concessao_adicional = data_concessao
        adicional.usuario_conclusao = request.user
        adicional.data_conclusao = timezone.now()
        adicional.sexta_parte = (
            adicional.numero_prox_adicional == 4
        )  # Recalculate based on the current state

        with transaction.atomic():
            adicional.save()
            # If you have a gravar_historico, ensure it's called with relevant data
            # gravar_historico(adicional, request.user) # If you want a full snapshot on conclusion

        success_message = "Adicional concluído com sucesso!"
        if is_ajax:
            return alert_response(
                type="success", title="Concluído!", message=success_message
            )
        messages.success(request, success_message)
        return redirect(reverse("adicional:ver_adicional", args=[id]))

    except ValidationError as e:
        error_message = str(e)
        logger.warning(f"Erro de validação: {error_message}")
        if is_ajax:
            return alert_response(
                type="error",
                title="Erro de Validação",
                message=error_message,
                status=400,
            )
        messages.error(request, error_message)
        return redirect(reverse("adicional:ver_adicional", args=[id]))
    except Exception as e:
        error_message = f"Ocorreu um erro inesperado: {str(e)}"
        logger.exception(f"Erro inesperado: {error_message}")
        if is_ajax:
            return alert_response(
                type="error", title="Erro Interno", message=error_message, status=500
            )
        messages.error(request, error_message)
        return redirect(reverse("adicional:ver_adicional", args=[id]))


@login_required
@require_POST
def novo_adicional(request):
    # Verificação dupla de AJAX
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if not is_ajax:
        # If not AJAX, return a bad request response with a message the modal will still catch
        messages.error(request, "Requisição inválida: Esta operação requer AJAX.")
        return redirect(
            "some_fallback_url"
        )  # Redirect to a relevant page or previous page
        # return JsonResponse({
        #     'success': False,
        #     'alert': {
        #         'type': 'error',
        #         'title': 'Erro!',
        #         'message': 'Requisição inválida'
        #     }
        # }, status=400) # This won't work for non-AJAX if no client-side JS handles it.

    try:
        data = request.POST
        cadastro_id = data.get("cadastro_id")
        n_bloco_adicional = data.get("n_bloco_adicional")
        data_ultimo_adicional_str = data.get("data_ultimo_adicional")
        situacao_adicional = data.get("situacao_adicional")

        # Validações básicas
        if not all([cadastro_id, n_bloco_adicional, data_ultimo_adicional_str]):
            return alert_response(
                type="error",
                title="Erro!",
                message="Dados obrigatórios faltando",
                status=400,
            )

        # Obter o objeto Cadastro
        cadastro_militar = get_object_or_404(Cadastro, id=cadastro_id)

        # Converter dados
        try:
            numero_adicional = int(n_bloco_adicional)
            data_ultimo_adicional = datetime.strptime(
                data_ultimo_adicional_str, "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError) as e:
            return alert_response(
                type="error",
                title="Erro!",
                message=f"Dados inválidos: {str(e)}",
                status=400,
            )

        # Calcular campos derivados
        proximo_adicional = data_ultimo_adicional + timedelta(days=1825)  # 5 anos
        mes_proximo_adicional = proximo_adicional.month
        ano_proximo_adicional = proximo_adicional.year
        numero_prox_adicional = numero_adicional + 1

        # Criar novo adicional
        novo_adicional_obj = Cadastro_adicional(
            cadastro=cadastro_militar,
            numero_adicional=numero_adicional,
            data_ultimo_adicional=data_ultimo_adicional,
            situacao_adicional=situacao_adicional or "Aguardando",
            dias_desconto_adicional=0,
            proximo_adicional=proximo_adicional,
            mes_proximo_adicional=mes_proximo_adicional,
            ano_proximo_adicional=ano_proximo_adicional,
            numero_prox_adicional=numero_prox_adicional,
            user_created=request.user,
            status_adicional="aguardando_requisitos",
        )

        novo_adicional_obj.full_clean()
        novo_adicional_obj.save()

        # No need for redirect_url if the modal handles the feedback.
        # If you still need a redirect after modal, the client-side JS would handle it.
        return alert_response(
            type="success",
            title="Sucesso!",
            message="Novo adicional criado com sucesso!",
        )

    except ValidationError as e:
        return alert_response(
            type="error",
            title="Erro de Validação",
            message=f'Erro de validação: {", ".join(e.messages)}',
            status=400,
        )
    except Exception as e:
        logger.error(f"Erro ao criar novo adicional: {str(e)}", exc_info=True)
        return alert_response(
            type="error",
            title="Erro Interno",
            message=f"Erro ao criar adicional: {str(e)}",
            status=500,
        )


@login_required
def editar_cadastro_adicional(request, id):
    adicional = get_object_or_404(Cadastro_adicional, id=id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    try:
        n_choices = Cadastro_adicional._meta.get_field("numero_adicional").choices
        situacao_choices = Cadastro_adicional._meta.get_field(
            "situacao_adicional"
        ).choices
        status_choices = Cadastro_adicional._meta.get_field("status_adicional").choices
    except Exception:
        error_msg = "Erro ao carregar opções do formulário"
        if is_ajax:
            return alert_response(
                type="error", title="Erro!", message=error_msg, status=500
            )
        messages.error(request, error_msg)
        return redirect("adicional:ver_adicional", id=id)

    if request.method == "POST":
        try:
            with transaction.atomic():
                fields_to_update = [
                    "numero_adicional",
                    "numero_prox_adicional",
                    "situacao_adicional",
                    "status_adicional",
                    "dias_desconto_adicional",
                    "bol_g_pm_adicional",
                ]

                for field in fields_to_update:
                    if field in request.POST:
                        setattr(adicional, field, request.POST.get(field))

                numeric_fields = {
                    "mes_proximo_adicional": int,
                    "ano_proximo_adicional": int,
                }

                for field, type_func in numeric_fields.items():
                    if request.POST.get(field):
                        setattr(adicional, field, type_func(request.POST.get(field)))

                date_fields = [
                    "data_ultimo_adicional",
                    "proximo_adicional",
                    "data_concessao_adicional",
                    "data_publicacao_adicional",
                ]

                for field in date_fields:
                    if request.POST.get(field):
                        setattr(
                            adicional,
                            field,
                            datetime.strptime(
                                request.POST.get(field), "%Y-%m-%d"
                            ).date(),
                        )

                adicional.sexta_parte = "sexta_parte" in request.POST
                adicional.confirmacao_6parte = "confirmacao_6parte" in request.POST

                adicional.user_updated = request.user
                adicional.updated_at = timezone.now()

                adicional.full_clean()
                adicional.save()

                # This HistoricoCadastro creation seems to be generic logging for any edit.
                # Ensure 'usuario' and 'acao' fields exist in HistoricoCadastro model if uncommenting.
                # try:
                #     if hasattr(adicional, 'historicos'): # This check might not be robust
                #         HistoricoCadastro.objects.create(
                #             cadastro_adicional=adicional,
                #             usuario=request.user,
                #             acao="EDIÇÃO",
                #             detalhes=f"Editado por {request.user.username}"
                #         )
                # except Exception:
                #     pass

                success_msg = "Cadastro atualizado com sucesso!"
                if is_ajax:
                    return alert_response(
                        type="success", title="Sucesso!", message=success_msg
                    )
                messages.success(request, success_msg)
                return redirect("adicional:ver_adicional", id=adicional.id)

        except ValueError as e:
            error_msg = f"Erro nos valores informados: {str(e)}"
            if is_ajax:
                return alert_response(
                    type="error", title="Erro!", message=error_msg, status=400
                )
            messages.error(request, error_msg)
        except ValidationError as e:
            error_msg = f'Erro de validação: {", ".join(e.messages)}'
            if is_ajax:
                return alert_response(
                    type="error",
                    title="Erro de Validação!",
                    message=error_msg,
                    status=400,
                )
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = "Ocorreu um erro inesperado. Administrador foi notificado."
            logger.exception(f"Erro inesperado em editar_cadastro_adicional: {str(e)}")
            if is_ajax:
                return alert_response(
                    type="error", title="Erro Interno!", message=error_msg, status=500
                )
            messages.error(request, error_msg)

    context = {
        "adicional": adicional,
        "n_choices": n_choices,
        "situacao_choices": situacao_choices,
        "status_choices": status_choices,
    }

    return render(request, "editar_geral.html", context)
