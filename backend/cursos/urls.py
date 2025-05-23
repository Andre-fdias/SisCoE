# backend/cursos/urls.py
from django.urls import path
from . import views

app_name = 'cursos'

urlpatterns = [
    # URLs para Medalhas
    path('medalhas/', views.medalha_list, name='medalha_list'),
    path('medalhas/cadastrar/', views.medalha_create, name='medalha_create'),
    path('medalhas/<int:pk>/editar/', views.medalha_edit, name='medalha_edit'),
    path('medalhas/<int:pk>/excluir/', views.medalha_delete, name='medalha_delete'),
    path('medalhas/buscar-militar/', views.buscar_militar_medalha, name='buscar_militar_medalha'),

    # Novas URLs para importação/exportação de Medalhas
    path('medalhas/export/csv/', views.export_medalhas_csv, name='export_medalhas_csv'),
    path('medalhas/import/csv/', views.import_medalhas_csv, name='import_medalhas_csv'),
    path('medalhas/importar/', views.importar_medalhas_view, name='importar_medalhas_view'),

    # URLs para Cursos
    path('cursos/', views.curso_list, name='curso_list'),
    path('cursos/cadastrar/', views.curso_create, name='curso_create'),
    path('cursos/buscar-militar/', views.buscar_militar_curso, name='buscar_militar_curso'),
    path('cursos/<int:pk>/edit/', views.curso_edit, name='curso_edit'), # This is the crucial line
    path('cursos/<int:pk>/excluir/', views.curso_delete, name='curso_delete'),
    
    # Novas URLs para importação/exportação de Cursos (Adicione estas linhas)
    path('cursos/export/csv/', views.export_cursos_csv, name='export_cursos_csv'),
    path('cursos/import/csv/', views.import_cursos_csv, name='import_cursos_csv'),
    path('cursos/importar/', views.importar_cursos_view, name='importar_cursos_view'),
]