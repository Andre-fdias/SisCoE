from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import UpdateView, CreateView, DeleteView
from django.utils import timezone
from datetime import timedelta

from .models import Lembrete, Tarefa
from .forms import LembreteForm, TarefaForm


# --- Mixins ---

class JsonFormMixin:
    """Mixin para retornar respostas JSON para forms."""
    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse({
            "success": True,
            "message": "Operação realizada com sucesso!",
            "id": self.object.id
        })

    def form_invalid(self, form):
        errors = {field: error[0] for field, error in form.errors.items()}
        return JsonResponse(
            {"success": False, "message": "Erro de validação.", "errors": errors},
            status=400
        )

# --- Views ---

@login_required
def calendario(request):
    user = request.user
    lembretes = Lembrete.objects.select_related('user').filter(user=user)
    tarefas = Tarefa.objects.select_related('user').filter(user=user)
    lembrete_form = LembreteForm()
    tarefa_form = TarefaForm()
    return render(
        request,
        "calendario.html",
        {
            "lembretes": lembretes,
            "tarefas": tarefas,
            "lembrete_form": lembrete_form,
            "tarefa_form": tarefa_form,
        },
    )


class LembreteCreateView(LoginRequiredMixin, JsonFormMixin, CreateView):
    model = Lembrete
    form_class = LembreteForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TarefaCreateView(LoginRequiredMixin, JsonFormMixin, CreateView):
    model = Tarefa
    form_class = TarefaForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class LembreteUpdateView(LoginRequiredMixin, UpdateView):
    model = Lembrete
    form_class = LembreteForm
    template_name = "lembrete_form.html"
    success_url = reverse_lazy("agenda:calendario")

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Lembrete atualizado com sucesso!")
        return super().form_valid(form)


class TarefaUpdateView(LoginRequiredMixin, UpdateView):
    model = Tarefa
    form_class = TarefaForm
    template_name = "eventos/tarefa_form.html"
    success_url = reverse_lazy("agenda:calendario")

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Tarefa atualizada com sucesso!")
        return super().form_valid(form)


class LembreteDeleteView(LoginRequiredMixin, DeleteView):
    model = Lembrete
    http_method_names = ['post']

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({"success": True, "message": "Lembrete excluído com sucesso!"})


class TarefaDeleteView(LoginRequiredMixin, DeleteView):
    model = Tarefa
    http_method_names = ['post']

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({"success": True, "message": "Tarefa excluída com sucesso!"})


@login_required
def eventos_proximos(request):
    user = request.user
    agora = timezone.now()
    limite = agora + timedelta(days=2)
    lembretes_proximos = Lembrete.objects.filter(user=user, data__range=(agora, limite))
    tarefas_proximas = Tarefa.objects.filter(user=user, data_fim__range=(agora, limite))
    eventos_proximos = list(lembretes_proximos) + list(tarefas_proximas)
    return JsonResponse(
        {
            "eventos": [
                {
                    "titulo": evento.titulo,
                    "data": (
                        evento.data.strftime("%Y-%m-%d %H:%M:%S")
                        if hasattr(evento, "data")
                        else evento.data_fim.strftime("%Y-%m-%d %H:%M:%S")
                    ),
                    "tipo": "Lembrete" if hasattr(evento, "data") else "Tarefa",
                }
                for evento in eventos_proximos
            ]
        }
    )