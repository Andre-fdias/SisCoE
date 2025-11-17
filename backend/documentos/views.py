from django.shortcuts import render, get_object_or_404, redirect
from backend.documentos.models import Documento, Arquivo
from django.http import HttpResponse
from datetime import datetime
from backend.documentos.forms import DocumentoForm
import logging
from django.contrib import messages
from django.contrib.messages import constants
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch


logger = logging.getLogger(__name__)


def listar_documentos(request):
    """
    Lista todos os documentos, permitindo filtrar por data de publicação e tipo.
    """
    documentos = Documento.objects.all()
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    tipo_selecionado = request.GET.get("tipo")

    if data_inicio:
        try:
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            documentos = documentos.filter(data_documento__gte=data_inicio)
        except ValueError:
            messages.add_message(
                request,
                constants.ERROR,
                "Data de início inválida.",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )

    if data_fim:
        try:
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
            documentos = documentos.filter(data_documento__lte=data_fim)
        except ValueError:
            messages.add_message(
                request,
                constants.ERROR,
                "Data de fim inválida.",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )

    if tipo_selecionado:
        documentos = documentos.filter(tipo=tipo_selecionado)

    tipos = Documento.TIPO_CHOICES

    context = {
        "documentos": documentos,
        "data_inicio": data_inicio.strftime("%Y-%m-%d") if data_inicio else None,
        "data_fim": data_fim.strftime("%Y-%m-%d") if data_fim else None,
        "tipo_selecionado": tipo_selecionado,
        "tipos": tipos,
    }

    return render(request, "listar_documentos.html", context)


def detalhe_documento(request, pk):
    """
    Exibe os detalhes de um documento específico, incluindo seus arquivos anexos.
    A descrição do documento é processada para suportar Markdown.
    """
    documento = get_object_or_404(Documento.objects.prefetch_related("arquivos"), pk=pk)

    # Processar descrição Markdown
    import markdown

    descricao_html = markdown.markdown(documento.descricao)

    return render(
        request,
        "detalhe_documento.html",
        {
            "documento": documento,
            "arquivos": documento.arquivos.all(),
            "descricao_html": descricao_html,
        },
    )


@login_required
def criar_documento(request):
    """
    Cria um novo documento e associa múltiplos arquivos a ele.
    """
    if request.method == "POST":
        form = DocumentoForm(request.POST)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.usuario = request.user
            documento.save()

            arquivos = request.FILES.getlist("arquivos[]")
            tipos_arquivos = request.POST.getlist("tipo[]")

            if arquivos:
                # Lógica para tratar o tipo de arquivo quando múltiplos são selecionados em um único input
                tipos_arquivos_para_uso = []
                if len(tipos_arquivos) == 1 and len(arquivos) > 1:
                    # Se apenas um tipo foi selecionado (para um input 'multiple'), aplique-o a todos os arquivos
                    selected_type = tipos_arquivos[0]
                    tipos_arquivos_para_uso = [selected_type] * len(arquivos)
                elif len(tipos_arquivos) == len(arquivos):
                    # Se há um tipo para cada arquivo (campos de upload individuais)
                    tipos_arquivos_para_uso = tipos_arquivos
                else:
                    # Fallback para 'OUTRO' se a contagem não corresponder por algum motivo inesperado
                    tipos_arquivos_para_uso = ["OUTRO"] * len(arquivos)

                for i, arquivo in enumerate(arquivos):
                    tipo_arquivo = tipos_arquivos_para_uso[i]
                    Arquivo.objects.create(
                        documento=documento, arquivo=arquivo, tipo=tipo_arquivo
                    )

            messages.add_message(
                request,
                constants.SUCCESS,
                "Documento e arquivos criados com sucesso!",
                extra_tags="bg-green-500 text-white p-4 rounded",
            )
            return redirect("documentos:listar_documentos")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.add_message(
                        request,
                        constants.ERROR,
                        f'Erro no campo "{field}": {error}',
                        extra_tags="bg-red-500 text-white p-4 rounded",
                    )
    else:
        form = DocumentoForm()

    context = {
        "form": form,
        "tipos": Documento.TIPO_CHOICES,
    }
    return render(request, "criar_documento.html", context)


def editar_documento(request, pk):
    """
    Permite a edição de um documento existente.
    Atualiza os campos do documento com os dados do formulário submetido.
    Verifica se o usuário está autenticado antes de salvar.
    """
    documento = get_object_or_404(Documento, pk=pk)

    if request.method == "POST":
        try:
            # Atualização manual dos campos
            documento.data_publicacao = request.POST.get("data_publicacao")
            documento.data_documento = request.POST.get("data_documento")
            documento.numero_documento = request.POST.get("numero_documento")
            documento.assunto = request.POST.get("assunto")
            documento.assinada_por = request.POST.get("assinada_por")
            documento.tipo = request.POST.get("tipo")
            documento.descricao = request.POST.get("descricao")

            if request.user.is_authenticated:
                documento.usuario = request.user
            else:
                messages.add_message(
                    request,
                    constants.ERROR,
                    "Usuário não autenticado.",
                    extra_tags="bg-red-500 text-white p-4 rounded",
                )
                return redirect("login")

            documento.save()
            messages.add_message(
                request,
                constants.SUCCESS,
                "Documento atualizado com sucesso!",
                extra_tags="bg-green-500 text-white p-4 rounded",
            )
            return redirect("documentos:detalhe_documento", pk=pk)

        except Exception as e:
            logger.error(f"Erro ao salvar documento: {e}")
            messages.add_message(
                request,
                constants.ERROR,
                f"Erro ao salvar documento: {e}",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )

    tipos = Documento.TIPO_CHOICES

    return render(
        request,
        "editar_documento.html",
        {
            "documento": documento,
            "tipos": tipos,
        },
    )


@login_required
@require_POST
def editar_documento_arquivos(request, pk):
    """
    Via requisição AJAX, permite adicionar novos arquivos a um documento existente.
    Verifica permissões do usuário e valida o número de arquivos e tipos fornecidos.
    Retorna uma resposta JSON com o resultado da operação e mensagens de feedback.
    """
    # Verifica se é uma requisição AJAX
    if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
        messages.add_message(
            request,
            constants.ERROR,
            "Requisição inválida.",
            extra_tags="bg-red-500 text-white p-4 rounded",
        )
        return JsonResponse(
            {"success": False, "error": "Requisição inválida"}, status=400
        )

    try:
        documento = get_object_or_404(Documento, pk=pk)

        # Verifica permissões
        if not request.user.has_perm("documentos.change_documento", documento):
            messages.add_message(
                request,
                constants.ERROR,
                "Permissão negada.",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )
            return JsonResponse(
                {"success": False, "error": "Permissão negada"}, status=403
            )

        # Processa apenas se houver arquivos
        novos_arquivos = request.FILES.getlist("novos_arquivos[]", [])
        novos_tipos = request.POST.getlist("novos_tipos[]", [])

        if len(novos_arquivos) != len(novos_tipos):
            messages.add_message(
                request,
                constants.ERROR,
                "Número de arquivos e tipos não corresponde.",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": "Número de arquivos e tipos não corresponde",
                },
                status=400,
            )

        # Se não há arquivos para adicionar
        if not novos_arquivos:
            return JsonResponse(
                {"success": True, "message": "Nenhum arquivo para adicionar"}
            )

        # Processa os arquivos
        arquivos_salvos = []
        for arquivo, tipo in zip(novos_arquivos, novos_tipos):
            if not tipo:  # Ignora se não tiver tipo
                continue

            # Valida o tipo
            if tipo not in dict(Arquivo.TIPO_CHOICES).keys():
                messages.add_message(
                    request,
                    constants.ERROR,
                    f"Tipo de arquivo inválido: {tipo}.",
                    extra_tags="bg-red-500 text-white p-4 rounded",
                )
                return JsonResponse(
                    {"success": False, "error": f"Tipo de arquivo inválido: {tipo}"},
                    status=400,
                )

            # Cria o arquivo
            novo_arquivo = Arquivo.objects.create(
                documento=documento, arquivo=arquivo, tipo=tipo
            )
            arquivos_salvos.append(
                {
                    "id": novo_arquivo.id,
                    "nome": novo_arquivo.arquivo.name,
                    "tipo": novo_arquivo.get_tipo_display(),
                }
            )

        messages.add_message(
            request,
            constants.SUCCESS,
            f"{len(arquivos_salvos)} arquivo(s) adicionado(s) com sucesso.",
            extra_tags="bg-green-500 text-white p-4 rounded",
        )
        return JsonResponse(
            {
                "success": True,
                "message": f"{len(arquivos_salvos)} arquivo(s) adicionado(s) com sucesso",
                "arquivos": arquivos_salvos,
            }
        )

    except Documento.DoesNotExist:
        messages.add_message(
            request,
            constants.ERROR,
            "Documento não encontrado.",
            extra_tags="bg-red-500 text-white p-4 rounded",
        )
        return JsonResponse(
            {"success": False, "error": "Documento não encontrado"}, status=404
        )
    except Exception as e:
        messages.add_message(
            request,
            constants.ERROR,
            f"Erro ao adicionar arquivos: {str(e)}.",
            extra_tags="bg-red-500 text-white p-4 rounded",
        )
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def remover_arquivo(request, arquivo_id):
    """
    Remove um arquivo específico associado a um documento via requisição POST.
    Retorna uma resposta JSON indicando o sucesso ou falha da operação.
    """
    if request.method == "POST":
        try:
            arquivo = get_object_or_404(Arquivo, pk=arquivo_id)
            arquivo.delete()
            return JsonResponse({"success": True})
        except Arquivo.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Arquivo não encontrado"}, status=404
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    else:
        return JsonResponse(
            {"success": False, "error": "Método não permitido"}, status=405
        )


def excluir_documento(request, pk):
    """
    Exclui um documento específico via requisição POST.
    Redireciona para a listagem de documentos após a exclusão.
    Na requisição GET, renderiza a página de confirmação de exclusão (atualmente a mesma listagem).
    """
    documento = get_object_or_404(Documento, pk=pk)
    if request.method == "POST":
        documento.delete()
        messages.add_message(
            request,
            constants.SUCCESS,
            "Documento excluído com sucesso.",
            extra_tags="bg-green-500 text-white p-4 rounded",
        )
        return redirect("documentos:listar_documentos")
    return render(request, "listar_documentos.html", {"documento": documento})


def carrossel_noticias(request):
    """
    Exibe as 5 últimas notícias (documentos) ordenadas por data de criação.
    Utilizado para um carrossel na página inicial ou seção de notícias.
    """
    ultimas_noticias = Documento.objects.order_by("-data_criacao")[:5]
    return render(
        request, "carrossel_noticias.html", {"ultimas_noticias": ultimas_noticias}
    )


def carregar_conteudo_arquivo(request, pk):
    """
    Carrega e exibe o conteúdo de um arquivo, dependendo do seu tipo (TEXT, DOC, PDF).
    Para arquivos de texto e DOC, lê o conteúdo e retorna como texto plano.
    Para arquivos PDF, retorna o arquivo com o content type apropriado para visualização no navegador.
    Arquivos de outros tipos retornam um erro.
    """
    arquivo = get_object_or_404(Arquivo, pk=pk)
    if arquivo.tipo == "TEXT" or arquivo.tipo == "DOC":
        try:
            with arquivo.arquivo.open("r") as f:
                conteudo = f.read()
            return HttpResponse(conteudo, content_type="text/plain")
        except Exception as e:
            return HttpResponse(f"Erro ao ler arquivo: {str(e)}", status=500)
    elif arquivo.tipo == "PDF":  # adicionado para pdf
        return HttpResponse(arquivo.arquivo, content_type="application/pdf")
    else:
        return HttpResponse(
            "Tipo de arquivo não suportado para visualização de conteúdo.", status=400
        )


@login_required
@require_POST
def excluir_arquivo(request, pk):
    """
    Exclui um arquivo específico via requisição POST e AJAX.
    Verifica as permissões do usuário antes de excluir o arquivo.
    Retorna uma resposta JSON indicando o sucesso ou falha da exclusão.
    """
    try:
        arquivo = Arquivo.objects.get(pk=pk)

        # Verifica se o usuário tem permissão para excluir
        if not request.user.has_perm("documentos.delete_arquivo", arquivo):
            return JsonResponse(
                {"success": False, "error": "Permissão negada"}, status=403
            )

        arquivo.delete()

        return JsonResponse(
            {"success": True, "message": "Arquivo excluído com sucesso"}
        )

    except Arquivo.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Arquivo não encontrado"}, status=404
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def gerenciar_arquivos(request, pk):
    documento = get_object_or_404(Documento, pk=pk)
    tipos = Arquivo.TIPO_CHOICES

    if request.method == "POST":
        try:
            # Processar arquivos existentes
            for key, value in request.POST.items():
                if key.startswith("tipo_"):
                    arquivo_id = key.split("_")[1]
                    arquivo = Arquivo.objects.get(id=arquivo_id)
                    arquivo.tipo = value
                    arquivo.save()

            # Processar novos arquivos
            novos_arquivos = request.FILES.getlist("novos_arquivos")
            novos_tipos = request.POST.getlist("novos_tipos")

            for arquivo, tipo in zip(novos_arquivos, novos_tipos):
                Arquivo.objects.create(documento=documento, arquivo=arquivo, tipo=tipo)

            messages.success(request, "Alterações salvas com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro ao salvar alterações: {str(e)}")

        return redirect("documentos:detalhe_documento", pk=pk)

    return redirect("documentos:listar_documentos")


from .models import Documento, Arquivo


def galeria_documentos(request):
    # Obter todos os documentos com seus arquivos relacionados otimizados
    documentos = Documento.objects.prefetch_related(
        Prefetch("arquivos", queryset=Arquivo.objects.all())
    ).all()

    # Aplicar filtros
    assunto = request.GET.get("assunto")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if assunto:
        documentos = documentos.filter(assunto__icontains=assunto)

    if data_inicio:
        try:
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            documentos = documentos.filter(data_documento__gte=data_inicio)
        except ValueError:
            pass

    if data_fim:
        try:
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
            documentos = documentos.filter(data_documento__lte=data_fim)
        except ValueError:
            pass

    # Preparar dados para o template - AGORA INCLUINDO numero_documento
    documentos_com_arquivos = []
    for doc in documentos.order_by("-data_documento"):
        if doc.arquivos.exists():  # Só inclui documentos com arquivos
            documentos_com_arquivos.append(
                {
                    "id": doc.id,
                    "assunto": doc.assunto,
                    "numero_documento": doc.numero_documento,  # ADICIONADO ESTE CAMPO
                    "data_documento": doc.data_documento,
                    "arquivos": doc.arquivos.all(),
                }
            )

    context = {
        "documentos": documentos_com_arquivos,
        "filtros": {
            "assunto": assunto or "",
            "data_inicio": data_inicio.strftime("%Y-%m-%d") if data_inicio else "",
            "data_fim": data_fim.strftime("%Y-%m-%d") if data_fim else "",
        },
    }

    return render(request, "galeria_documentos.html", context)


def gerenciar_arquivos(request, pk):
    """
    Permite gerenciar os arquivos associados a um documento específico.
    Na requisição POST, atualiza os tipos de arquivos existentes e permite adicionar novos arquivos ao documento.
    Após a conclusão, redireciona para a página de detalhes do documento.
    """
    documento = get_object_or_404(Documento, pk=pk)
    tipos = Arquivo.TIPO_CHOICES

    if request.method == "POST":
        try:
            # Processar a atualização dos tipos de arquivos existentes
            for key, value in request.POST.items():
                if key.startswith("tipo_"):
                    arquivo_id = key.split("_")[1]
                    arquivo = Arquivo.objects.get(id=arquivo_id)
                    arquivo.tipo = value
                    arquivo.save()

            # Processar o upload e a associação de novos arquivos
            novos_arquivos = request.FILES.getlist("novos_arquivos")
            novos_tipos = request.POST.getlist("novos_tipos")

            for arquivo, tipo in zip(novos_arquivos, novos_tipos):
                Arquivo.objects.create(documento=documento, arquivo=arquivo, tipo=tipo)

            messages.add_message(
                request,
                constants.SUCCESS,
                "Alterações salvas com sucesso!",
                extra_tags="bg-green-500 text-white p-4 rounded",
            )

        except Exception as e:
            messages.add_message(
                request,
                constants.ERROR,
                f"Erro ao salvar alterações: {str(e)}",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )

        return redirect("documentos:detalhe_documento", pk=pk)

    # Se a requisição não for POST, redireciona para a listagem de documentos (pode ser ajustado se necessário)
    return redirect("documentos:listar_documentos")


def galeria_documentos(request):
    """
    Exibe uma galeria de documentos, mostrando cada documento com seus arquivos anexos.
    Permite filtrar os documentos por assunto e por um intervalo de datas de documento.
    A listagem é otimizada para carregar os arquivos relacionados eficientemente.
    """
    # Obter todos os documentos com seus arquivos relacionados otimizados
    documentos = Documento.objects.prefetch_related(
        Prefetch("arquivos", queryset=Arquivo.objects.all())
    ).all()

    # Aplicar filtros
    assunto = request.GET.get("assunto")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if assunto:
        documentos = documentos.filter(assunto__icontains=assunto)

    if data_inicio:
        try:
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            documentos = documentos.filter(data_documento__gte=data_inicio)
        except ValueError:
            messages.add_message(
                request,
                constants.ERROR,
                "Data de início inválida.",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )

    if data_fim:
        try:
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
            documentos = documentos.filter(data_documento__lte=data_fim)
        except ValueError:
            messages.add_message(
                request,
                constants.ERROR,
                "Data de fim inválida.",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )

    # Preparar dados para o template - INCLUINDO numero_documento
    documentos_com_arquivos = []
    for doc in documentos.order_by("-data_documento"):
        if doc.arquivos.exists():  # Só inclui documentos com arquivos
            documentos_com_arquivos.append(
                {
                    "id": doc.id,
                    "assunto": doc.assunto,
                    "numero_documento": doc.numero_documento,  # INCLUÍDO ESTE CAMPO
                    "data_documento": doc.data_documento,
                    "arquivos": doc.arquivos.all(),
                }
            )

    context = {
        "documentos": documentos_com_arquivos,
        "filtros": {
            "assunto": assunto or "",
            "data_inicio": data_inicio.strftime("%Y-%m-%d") if data_inicio else "",
            "data_fim": data_fim.strftime("%Y-%m-%d") if data_fim else "",
        },
    }

    return render(request, "galeria_documentos.html", context)
