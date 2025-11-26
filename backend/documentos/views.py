from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from datetime import datetime
from django.contrib import messages
from django.contrib.messages import constants
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
import logging
import markdown

from .models import Documento, Arquivo
from .forms import DocumentoForm

logger = logging.getLogger(__name__)

# Helper para verificar permissão
def user_can_access_document(user, documento):
    """Verifica se o usuário pode acessar um documento."""
    return user.permissoes in ['admin', 'gestor'] or documento.usuario == user

@login_required
def listar_documentos(request):
    """
    Lista documentos com base na permissão do usuário.
    Gestores/Admins veem todos; outros usuários veem apenas os seus.
    """
    user = request.user
    if user.permissoes in ['admin', 'gestor']:
        documentos = Documento.objects.select_related('usuario').prefetch_related('arquivos').all()
    else:
        documentos = Documento.objects.select_related('usuario').prefetch_related('arquivos').filter(usuario=user)

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    tipo_selecionado = request.GET.get("tipo")

    if data_inicio:
        try:
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            documentos = documentos.filter(data_documento__gte=data_inicio)
        except ValueError:
            messages.error(request, "Data de início inválida.")

    if data_fim:
        try:
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
            documentos = documentos.filter(data_documento__lte=data_fim)
        except ValueError:
            messages.error(request, "Data de fim inválida.")

    if tipo_selecionado:
        documentos = documentos.filter(tipo=tipo_selecionado)

    context = {
        "documentos": documentos.order_by("-data_documento"),
        "data_inicio": data_inicio.strftime("%Y-%m-%d") if data_inicio else None,
        "data_fim": data_fim.strftime("%Y-%m-%d") if data_fim else None,
        "tipo_selecionado": tipo_selecionado,
        "tipos": Documento.TIPO_CHOICES,
    }
    return render(request, "listar_documentos.html", context)

@login_required
def detalhe_documento(request, pk):
    """ Exibe os detalhes de um documento se o usuário tiver permissão. """
    documento = get_object_or_404(Documento.objects.prefetch_related("arquivos"), pk=pk)
    if not user_can_access_document(request.user, documento):
        raise Http404

    descricao_html = markdown.markdown(documento.descricao)
    context = {
        "documento": documento,
        "arquivos": documento.arquivos.all(),
        "descricao_html": descricao_html,
    }
    return render(request, "detalhe_documento.html", context)

@login_required
def criar_documento(request):
    """ Cria um novo documento, associando-o ao usuário logado. """
    if request.method == "POST":
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.usuario = request.user
            documento.save()

            arquivos = request.FILES.getlist("arquivos[]")
            tipos_arquivos = request.POST.getlist("tipo[]")

            if arquivos:
                tipos_arquivos_para_uso = []
                if len(tipos_arquivos) == 1 and len(arquivos) > 1:
                    selected_type = tipos_arquivos[0]
                    tipos_arquivos_para_uso = [selected_type] * len(arquivos)
                elif len(tipos_arquivos) == len(arquivos):
                    tipos_arquivos_para_uso = tipos_arquivos
                else:
                    tipos_arquivos_para_uso = ["OUTRO"] * len(arquivos)

                for i, arquivo in enumerate(arquivos):
                    tipo_arquivo = tipos_arquivos_para_uso[i]
                    Arquivo.objects.create(
                        documento=documento, arquivo=arquivo, tipo=tipo_arquivo
                    )
            
            messages.success(request, "Documento e arquivos criados com sucesso!")
            return redirect("documentos:listar_documentos")
        else:
            messages.error(request, "Erro ao validar o formulário.")
    else:
        form = DocumentoForm()

    context = {"form": form, "tipos": Documento.TIPO_CHOICES}
    return render(request, "criar_documento.html", context)

@login_required
def editar_documento(request, pk):
    """ Permite a edição de um documento se o usuário tiver permissão. """
    documento = get_object_or_404(Documento, pk=pk)
    if not user_can_access_document(request.user, documento):
        raise Http404

    if request.method == "POST":
        form = DocumentoForm(request.POST, instance=documento)
        if form.is_valid():
            # A linha que permitia troca de dono foi removida.
            # O form.save() já atualiza a instância existente.
            form.save()
            messages.success(request, "Documento atualizado com sucesso!")
            return redirect("documentos:detalhe_documento", pk=pk)
        else:
            messages.error(request, "Erro ao validar os dados do formulário.")
    else:
        form = DocumentoForm(instance=documento)

    context = {"form": form, "documento": documento, "tipos": Documento.TIPO_CHOICES}
    return render(request, "editar_documento.html", context)

@login_required
@require_POST
def excluir_documento(request, pk):
    """ Exclui um documento se o usuário tiver permissão. """
    documento = get_object_or_404(Documento, pk=pk)
    if not user_can_access_document(request.user, documento):
        raise Http404
        
    documento.delete()
    messages.success(request, "Documento excluído com sucesso.")
    return redirect("documentos:listar_documentos")

@login_required
@require_POST
def remover_arquivo(request, arquivo_id):
    """ Remove um arquivo se o usuário tiver permissão sobre o documento pai. """
    arquivo = get_object_or_404(Arquivo, pk=arquivo_id)
    if not user_can_access_document(request.user, arquivo.documento):
        return JsonResponse({"success": False, "error": "Permissão negada"}, status=403)
        
    arquivo.delete()
    return JsonResponse({"success": True})

@login_required
def carregar_conteudo_arquivo(request, pk):
    """ Serve um arquivo se o usuário tiver permissão. """
    arquivo = get_object_or_404(Arquivo, pk=pk)
    if not user_can_access_document(request.user, arquivo.documento):
        raise Http404

    # Lógica para servir o arquivo
    if arquivo.tipo in ["TEXT", "DOC"]:
        try:
            with arquivo.arquivo.open("r") as f:
                conteudo = f.read()
            return HttpResponse(conteudo, content_type="text/plain")
        except Exception as e:
            return HttpResponse(f"Erro ao ler arquivo: {str(e)}", status=500)
    elif arquivo.tipo == "PDF":
        return HttpResponse(arquivo.arquivo, content_type="application/pdf")
    else:
        return HttpResponse("Tipo de arquivo não suportado para visualização.", status=400)

@login_required
def gerenciar_arquivos(request, pk):
    """ Gerencia arquivos de um documento se o usuário tiver permissão. """
    documento = get_object_or_404(Documento, pk=pk)
    if not user_can_access_document(request.user, documento):
        raise Http404

    if request.method == "POST":
        try:
            # Processar arquivos existentes
            for key, value in request.POST.items():
                if key.startswith("tipo_"):
                    arquivo_id = key.split("_")[1]
                    arquivo = Arquivo.objects.get(id=arquivo_id, documento=documento)
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
    
    # Se GET, ou para contexto da página
    context = {"documento": documento, "tipos": Arquivo.TIPO_CHOICES}
    return render(request, 'gerenciar_arquivos.html', context)


@login_required
def galeria_documentos(request):
    """ Exibe uma galeria de documentos com base na permissão do usuário. """
    user = request.user
    if user.permissoes in ['basico'
    '']:
        documentos_base = Documento.objects.all()
    else:
        documentos_base = Documento.objects.filter(usuario=user)

    documentos = documentos_base.prefetch_related(
        Prefetch("arquivos", queryset=Arquivo.objects.all())
    ).order_by("-data_documento")
    
    # Filtros
    assunto = request.GET.get("assunto")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if assunto:
        documentos = documentos.filter(assunto__icontains=assunto)
    if data_inicio:
        try:
            documentos = documentos.filter(data_documento__gte=datetime.strptime(data_inicio, "%Y-%m-%d").date())
        except ValueError: pass
    if data_fim:
        try:
            documentos = documentos.filter(data_documento__lte=datetime.strptime(data_fim, "%Y-%m-%d").date())
        except ValueError: pass
    
    documentos_com_arquivos = [
        doc for doc in documentos if doc.arquivos.exists()
    ]

    context = {
        "documentos": documentos_com_arquivos,
        "filtros": {
            "assunto": assunto or "",
            "data_inicio": data_inicio or "",
            "data_fim": data_fim or "",
        },
    }
    return render(request, "galeria_documentos.html", context)

# Views obsoletas ou de uso específico
def carrossel_noticias(request):
    ultimas_noticias = Documento.objects.order_by("-data_criacao")[:5]
    return render(request, "carrossel_noticias.html", {"ultimas_noticias": ultimas_noticias})
