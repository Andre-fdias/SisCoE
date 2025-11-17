# municipios/urls.py
from django.urls import path
from . import views as v

app_name = "municipios"

urlpatterns = [
    path("", v.posto_list, name="posto_list"),
    path("<int:pk>/", v.posto_detail, name="posto_detail"),
    path("municipio/<int:pk>/", v.municipio_detail, name="municipio_detail"),
    path("novo/", v.posto_create, name="posto_create"),
    path("<int:pk>/editar/", v.posto_update, name="posto_update"),
    path("<int:pk>/editar_pessoal/", v.editar_pessoal, name="editar_pessoal"),
    path("<int:pk>/editar_contato/", v.editar_contato, name="editar_contato"),
    path("<int:pk>/deletar/", v.excluir_municipio, name="excluir_municipio"),
    path("calcular_rota/", v.calcular_rota, name="calcular_rota"),
    path("posto/<int:pk>/print/", v.posto_print, name="posto_print"),
    path("modal-rota/", v.modal_rota, name="modal_rota"),
    path("calcular-rota/", v.calcular_rota, name="calcular_rota"),
    path("importar/", v.importar_municipios, name="importar_municipios"),
    path("exportar-postos-csv/", v.exportar_postos_csv, name="exportar_postos_csv"),
    # Nova URL para exportação do relatório PDF de efetivo
    path(
        "exportar-relatorio-efetivo-pdf/",
        v.exportar_relatorio_efetivo_pdf,
        name="exportar_relatorio_efetivo_pdf",
    ),
]
