from django.urls import path
from . import views as v

app_name = 'municipios'

urlpatterns = [
    path('', v.posto_list, name='posto_list'),
    path('<int:pk>/', v.posto_detail, name='posto_detail'),
    path('municipio/<int:pk>/', v.municipio_detail, name='municipio_detail'),
    path('novo/', v.posto_create, name='posto_create'),
    path('<int:pk>/editar/', v.posto_update, name='posto_update'),
    path('<int:pk>/editar_pessoal/', v.editar_pessoal, name='editar_pessoal'),
    path('<int:pk>/editar_contato/', v.editar_contato, name='editar_contato'), # Nova URL para salvar o modal de edição de contato
    path('<int:pk>/deletar/', v.excluir_municipio, name='excluir_municipio'),
    path('calcular_rota/', v.calcular_rota, name='calcular_rota'),   # Nova URL
    path('posto/<int:pk>/print/', v.posto_print, name='posto_print'),
]