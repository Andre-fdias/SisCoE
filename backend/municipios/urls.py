# municipios/urls.py
from django.urls import path
from . import views as v

app_name = "municipios"

urlpatterns = [
    path("", v.municipios_home, name="municipios_home"),
    path("postos/", v.posto_list, name="posto_list"),
    path("municipios/", v.municipio_list, name="municipio_list"),
    path("<int:pk>/", v.posto_detail, name="posto_detail"),
    path("municipio/<int:pk>/", v.municipio_detail, name="municipio_detail"),
    path("novo/", v.posto_create, name="posto_create"),
    path("<int:pk>/editar/", v.posto_update, name="posto_update"),
    path("<int:pk>/editar_pessoal/", v.editar_pessoal, name="editar_pessoal"),
    path("<int:pk>/editar_contato/", v.editar_contato, name="editar_contato"),
    path("<int:pk>/deletar/", v.excluir_posto, name="excluir_posto"),
    path("roteirizador/", v.rota_calculator_page, name="rota_calculator_page"),
    path("posto/<int:pk>/print/", v.posto_print, name="posto_print"),
    path("modal-rota/", v.modal_rota, name="modal_rota"),
    path("importar/", v.importar_municipios, name="importar_municipios"),
    path("exportar-postos-csv/", v.exportar_postos_csv, name="exportar_postos_csv"),
    # API Endpoints
    path('api/cep-info/', v.api_cep_info, name='api_cep_info'),
    path('api/municipio-info/', v.api_municipio_info, name='api_municipio_info'),
    path("api/calculate-route/", v.calculate_route_api, name="calculate_route_api"),
    path('api/geocode/autocomplete/', v.api_geocode_autocomplete, name='api_geocode_autocomplete'),
    # Nova URL para exportação do relatório PDF de efetivo
    path(
        "exportar-relatorio-efetivo-pdf/",
        v.exportar_relatorio_efetivo_pdf,
        name="exportar_relatorio_efetivo_pdf",
    ),
]
