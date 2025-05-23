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
    
    # URLs para Cursos
    path('cursos/', views.curso_list, name='curso_list'),
    path('cursos/cadastrar/', views.curso_create, name='curso_create'),
    path('cursos/<int:pk>/editar/', views.curso_update, name='curso_update'),
    path('cursos/<int:pk>/excluir/', views.curso_delete, name='curso_delete'),
    path('cursos/buscar-militar/', views.buscar_militar_curso, name='buscar_militar_curso'),
]