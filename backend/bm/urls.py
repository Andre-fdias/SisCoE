# backend/bm/urls.py
from django.urls import path
from . import views

app_name = 'bm'

urlpatterns = [
    path('', views.listar_bm, name='listar_bm'),
    path('cadastrar/', views.cadastrar_bm, name='cadastrar_bm'),
    path('ver/<int:pk>/', views.ver_bm, name='ver_bm'),  # Padrão correto
    path('editar/<int:pk>/', views.editar_bm, name='editar_bm'),
    path('atualizar-foto/<int:pk>/', views.atualizar_foto, name='atualizar_foto'),
    path('excluir/<int:pk>/', views.excluir_bm, name='excluir_bm'),
    path('importar/', views.importar_bm, name='importar_bm'),
    path('exportar/', views.exportar_bm, name='exportar_bm'),
]