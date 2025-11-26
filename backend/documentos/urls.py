from django.urls import path
from . import views

app_name = "documentos"  # Adicione o app_name para namespaces

urlpatterns = [
    path("", views.listar_documentos, name="listar_documentos"),
    path("documento/<int:pk>/", views.detalhe_documento, name="detalhe_documento"),
    path("documento/criar/", views.criar_documento, name="criar_documento"),
    path("documento/<int:pk>/editar/", views.editar_documento, name="editar_documento"),
    path(
        "documento/excluir/<int:pk>/", views.excluir_documento, name="excluir_documento"
    ),
    path("noticias/carrossel/", views.carrossel_noticias, name="carrossel_noticias"),
    path(
        "arquivo/<int:pk>/conteudo/",
        views.carregar_conteudo_arquivo,
        name="carregar_conteudo_arquivo",
    ),
    path(
        "gerenciar-arquivos/<int:pk>/",
        views.gerenciar_arquivos,
        name="gerenciar_arquivos",
    ),
    path("arquivo/excluir/<int:arquivo_id>/", views.remover_arquivo, name="excluir_arquivo"),
    path("galeria/", views.galeria_documentos, name="galeria_documentos"),
]
