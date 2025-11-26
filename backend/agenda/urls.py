from django.urls import path
from . import views

app_name = "agenda"

urlpatterns = [
    path("calendario/", views.calendario, name="calendario"),
    path("lembrete/novo/", views.LembreteCreateView.as_view(), name="lembrete_novo"),
    path("tarefa/nova/", views.TarefaCreateView.as_view(), name="tarefa_nova"),
    path("lembrete/editar/<int:pk>/", views.LembreteUpdateView.as_view(), name="lembrete_editar"),
    path("tarefa/editar/<int:pk>/", views.TarefaUpdateView.as_view(), name="tarefa_editar"),
    path("lembrete/excluir/<int:pk>/", views.LembreteDeleteView.as_view(), name="excluir_lembrete"),
    path("tarefa/excluir/<int:pk>/", views.TarefaDeleteView.as_view(), name="excluir_tarefa"),
    path("eventos-proximos/", views.eventos_proximos, name="eventos_proximos"),
]
