from django.shortcuts import render
from datetime import date, timedelta
from .forms import CalculoMilitarForm


def calcular_tempo_servico(request):
    form = CalculoMilitarForm(request.POST or None)
    resultados = None

    if form.is_valid():
        calculo = form.save()
        data_admissao = calculo.data_admissao
        tempo_ffaa_pm_cbm = calculo.tempo_ffaa_pm_cbm
        tempo_inss_outros = min(calculo.tempo_inss_outros, 1825)
        afastamentos = calculo.afastamentos

        data_01jan21 = date(2021, 1, 1)
        tempo_01jan21 = (data_01jan21 - data_admissao).days

        total_dias = (
            tempo_01jan21 + tempo_ffaa_pm_cbm + tempo_inss_outros - afastamentos
        )

        data_30anos = data_admissao + timedelta(days=30 * 365)
        dif_30anos = (data_30anos - data_01jan21).days

        pedagio_17 = round(dif_30anos * 0.17)
        data_30anos_pedagio = data_30anos + timedelta(days=pedagio_17)

        data_25anos = data_admissao + timedelta(days=25 * 365)

        data_base = date(2022, 1, 1)
        acrescimo_4meses = min((data_30anos - data_base).days // 365 * 120, 5 * 120)

        data_tempo_militar = data_25anos + timedelta(days=acrescimo_4meses)

        resultados = {
            "calculo": calculo,
            "tempo_01jan21": tempo_01jan21,
            "total_dias": total_dias,
            "data_30anos": data_30anos,
            "dif_30anos": dif_30anos,
            "pedagio_17": pedagio_17,
            "data_30anos_pedagio": data_30anos_pedagio,
            "data_25anos": data_25anos,
            "data_base": data_base,
            "acrescimo_4meses": acrescimo_4meses,
            "data_tempo_militar": data_tempo_militar,
        }

    return render(
        request, "calculadora/calculo.html", {"form": form, "resultados": resultados}
    )
