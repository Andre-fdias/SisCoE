# backend/cursos/urls.py
from django.urls import path
from . import views

app_name = 'cursos'

urlpatterns = [
    # URLs para Medalhas (gerais, se existirem)
    path('medalhas/', views.medalha_list, name='medalha_list'),
    path('medalhas/cadastrar/', views.medalha_create, name='medalha_create'),
    path('medalhas/<int:pk>/editar/', views.medalha_edit, name='medalha_edit'),
    path('medalhas/<int:pk>/excluir/', views.medalha_delete, name='medalha_delete'),
    path('medalhas/buscar-militar/', views.buscar_militar_medalha, name='buscar_militar_medalha'),

    # Novas URLs para importação/exportação de Medalhas (se existirem)
    path('medalhas/export/csv/', views.export_medalhas_csv, name='export_medalhas_csv'),
    path('medalhas/import/csv/', views.import_medalhas_csv, name='import_medalhas_csv'),
    path('medalhas/importar/', views.importar_medalhas_view, name='importar_medalhas_view'),

    # URLs para Cursos (gerais)
    path('cursos/', views.curso_list, name='curso_list'),
    path('cursos/cadastrar/', views.curso_create, name='curso_create'),
    path('cursos/buscar-militar/', views.buscar_militar_curso, name='buscar_militar_curso'),
    path('cursos/<int:pk>/edit/', views.curso_edit, name='curso_edit'),
    path('cursos/<int:pk>/excluir/', views.curso_delete, name='curso_delete'),
    
    # Novas URLs para importação/exportação de Cursos (se existirem)
    path('cursos/export/csv/', views.export_cursos_csv, name='export_cursos_csv'),
    path('cursos/import/csv/', views.import_cursos_csv, name='import_cursos_csv'),
    path('cursos/importar/', views.importar_cursos_view, name='importar_cursos_view'),

   # URLs para cursos do usuário (já estão corretas no seu urls.py)
    # URLs para cursos do usuário
    path('meus-cursos/', views.user_curso_list, name='user_curso_list'),
    path('meus-cursos/novo/', views.user_curso_create, name='user_curso_create'),  # NOME CORRIGIDO
    path('meus-cursos/<int:pk>/editar/', views.user_curso_edit, name='user_curso_edit'),
    path('meus-cursos/<int:pk>/excluir/', views.user_curso_delete, name='user_curso_delete'),

    
    # NOVAS URLs para medalhas do usuário (adicione ou verifique estas linhas)
    path('meus-medalhas/', views.user_medalha_list, name='user_medalha_list'),
    path('meus-medalhas/novo/', views.user_medalha_create, name='user_medalha_create'), # Linha corrigida
    path('meus-medalhas/editar/<int:pk>/', views.user_medalha_edit, name='user_medalha_edit'),
    path('meus-medalhas/excluir/<int:pk>/', views.user_medalha_delete, name='user_medalha_delete'),
]
