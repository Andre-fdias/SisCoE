from django.urls import path
from . import views

app_name = "agenda"

urlpatterns = [
    path("calendario/", views.calendario, name="calendario"),
    path("lembrete/novo/", views.lembrete_novo, name="lembrete_novo"),
    path("tarefa/nova/", views.tarefa_nova, name="tarefa_nova"),
    path("lembrete/editar/<int:pk>/", views.lembrete_editar, name="lembrete_editar"),
    path("tarefa/editar/<int:pk>/", views.tarefa_editar, name="tarefa_editar"),
    path("lembrete/excluir/<int:pk>/", views.excluir_lembrete, name="excluir_lembrete"),
    path("tarefa/excluir/<int:pk>/", views.excluir_tarefa, name="excluir_tarefa"),
    path("calendario/", views.calendario, name="calendario"),
    path("eventos-proximos/", views.eventos_proximos, name="eventos_proximos"),
]
