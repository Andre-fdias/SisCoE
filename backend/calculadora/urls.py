from django.urls import path
from . import views as v


app_name = "calculadora"


urlpatterns = [
    path("", v.calcular_tempo_servico, name="calcular_tempo_servico"),
]
