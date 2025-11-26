from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Posto, Contato, Pessoal, Cidade
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pandas as pd
import csv
from django.db.models import Sum
import requests
import os
import json
from django.views.decorators.http import require_POST
from geopy.distance import geodesic

from .import_utils import importar_dados
from .export_utils import export_efetivo_pdf_report
from backend.accounts.decorators import permissao_necessaria


@permissao_necessaria('sgb')
def municipios_home(request):
    """
    Renderiza a página de seleção principal para o app de municípios
    e calcula as estatísticas para a visão geral.
    """
    posto_count = Posto.objects.count()
    municipio_count = Cidade.objects.count()
    
    efetivo_agregado = Pessoal.objects.aggregate(
        total_cel=Sum('cel'),
        total_ten_cel=Sum('ten_cel'),
        total_maj=Sum('maj'),
        total_cap=Sum('cap'),
        total_tenqo=Sum('tenqo'),
        total_tenqa=Sum('tenqa'),
        total_asp=Sum('asp'),
        total_st_sgt=Sum('st_sgt'),
        total_cb_sd=Sum('cb_sd')
    )

    efetivo_count = sum(value for value in efetivo_agregado.values() if value is not None)

    context = {
        'posto_count': posto_count,
        'municipio_count': municipio_count,
        'efetivo_count': efetivo_count,
    }
    return render(request, "municipios_home.html", context)


@permissao_necessaria('sgb')
def posto_list(request):
    """
    Lista todos os Postos (QPO).
    """
    postos = Posto.objects.all().prefetch_related("pessoal", "cidades")
    return render(request, "posto_list.html", {"postos": postos})


@permissao_necessaria('sgb')
def municipio_list(request):
    """
    Lista todos os Municípios.
    """
    cidades = Cidade.objects.all().select_related("posto")
    return render(request, "municipio_list.html", {"cidades": cidades})


from backend.efetivo.models import DetalhesSituacao, Promocao


@permissao_necessaria('sgb')
def posto_detail(request, pk):
    posto = get_object_or_404(Posto, pk=pk)

    GRUPOS = {
        "Tc": "Ten Cel",
        "Maj": "Maj",
        "Cap": "Cap",
        "Ten": "Ten QO",
        "Ten QAOPM": "Ten QA",
        "St/Sgt": "St/Sgt",
        "Cb/Sd": "Cb/Sd",
    }

    efetivos = DetalhesSituacao.objects.filter(
        situacao="Efetivo", posto_secao=posto.posto_secao
    ).select_related("cadastro")

    contagem = {grupo: 0 for grupo in GRUPOS.keys()}

    for efetivo in efetivos:
        ultima_promocao = (
            Promocao.objects.filter(cadastro=efetivo.cadastro)
            .order_by("-ultima_promocao")
            .first()
        )

        if ultima_promocao and ultima_promocao.grupo.strip() in GRUPOS:
            grupo = ultima_promocao.grupo.strip()
            contagem[grupo] += 1

    efetivo_grupos = {
        "Tc": contagem.get("Tc", 0),
        "Maj": contagem.get("Maj", 0),
        "Cap": contagem.get("Cap", 0),
        "Ten": contagem.get("Ten", 0),
        "Ten_QAOPM": contagem.get("Ten QAOPM", 0),
        "St_Sgt": contagem.get("St/Sgt", 0),
        "Cb_Sd": contagem.get("Cb/Sd", 0),
    }

    total_efetivo = sum(contagem.values())

    try:
        pessoal = Pessoal.objects.get(posto=posto)
    except Pessoal.DoesNotExist:
        pessoal = None

    context = {
        "posto": posto,
        "efetivo_grupos": efetivo_grupos,
        "total_efetivo": total_efetivo,
        "pessoal": pessoal,
    }

    return render(request, "posto_detail.html", context)


@permissao_necessaria('sgb')
def municipio_detail(request, pk):
    cidade = get_object_or_404(Cidade, pk=pk)
    posto = cidade.posto
    return render(request, "municipio_detail.html", {"cidade": cidade, "posto": posto})


@permissao_necessaria('sgb')
def posto_secao_detail(request, pk):
    posto = get_object_or_404(Posto, pk=pk)
    return render(request, "posto_secao_detail.html", {"posto": posto})


@permissao_necessaria('sgb')
def posto_create(request):
    sgb_choices = Posto.sgb_choices
    posto_secao_choices = Posto.posto_secao_choices
    posto_atendimento_choices = Posto.posto_atendimento_choices
    cidade_posto_choices = Posto.cidade_posto_choices
    municipio_choices = Cidade.municipio_choices
    tipo_choices = Posto.tipo_choices
    op_adm_choices = Posto.op_adm_choices

    if request.method == "POST":
        sgb = request.POST.get("sgb")
        posto_secao = request.POST.get("posto_secao")

        if not sgb or not posto_secao:
            from django.contrib import messages
            messages.error(request, "Os campos 'SGB' e 'Posto/Seção' são obrigatórios. Selecione um SGB para habilitar o Posto/Seção.")
            return redirect('municipios:posto_create')

        posto_data = {
            "sgb": sgb,
            "posto_secao": posto_secao,
            "posto_atendimento": request.POST.get("posto_atendimento"),
            "cidade_posto": request.POST.get("cidade_posto"),
            "tipo_cidade": request.POST.get("tipo_cidade"),
            "op_adm": request.POST.get("op_adm"),
            "usuario": request.user,
        }

        if "quartel" in request.FILES:
            posto_data["quartel"] = request.FILES["quartel"]

        posto = Posto.objects.create(**posto_data)

        contato_data = {
            "posto": posto,
            "telefone": request.POST.get("telefone"),
            "rua": request.POST.get("rua"),
            "numero": request.POST.get("numero"),
            "complemento": request.POST.get("complemento"),
            "bairro": request.POST.get("bairro"),
            "cidade": request.POST.get("cidade"),
            "cep": request.POST.get("cep"),
            "email": request.POST.get("email_funcional"),
            "latitude": request.POST.get("latitude_contato"),
            "longitude": request.POST.get("longitude_contato"),
        }
        Contato.objects.create(**contato_data)

        pessoal_data = {
            "posto": posto,
            "cel": int(request.POST.get("cel", 0)),
            "ten_cel": int(request.POST.get("ten_cel", 0)),
            "maj": int(request.POST.get("maj", 0)),
            "cap": int(request.POST.get("cap", 0)),
            "tenqo": int(request.POST.get("ten", 0)),
            "tenqa": int(request.POST.get("tenqa", 0)),
            "asp": int(request.POST.get("asp", 0)),
            "st_sgt": int(request.POST.get("st_sgt", 0)),
            "cb_sd": int(request.POST.get("cb_sd", 0)),
        }
        Pessoal.objects.create(**pessoal_data)

        municipios = request.POST.getlist("municipios[]")
        latitudes = request.POST.getlist("latitudes[]")
        longitudes = request.POST.getlist("longitudes[]")
        bandeiras = request.FILES.getlist("bandeiras[]")
        descricoes = request.POST.getlist("descricoes[]")

        for i in range(len(municipios)):
            lat = latitudes[i] if latitudes[i] and latitudes[i] != 'Buscando...' and latitudes[i] != 'Não encontrado' else None
            lon = longitudes[i] if longitudes[i] and longitudes[i] != 'Buscando...' and longitudes[i] != 'Não encontrado' else None

            cidade_data = {
                "posto": posto,
                "municipio": municipios[i],
                "descricao": descricoes[i],
                "latitude": lat,
                "longitude": lon,
            }

            if i < len(bandeiras) and bandeiras[i]:
                cidade_data["bandeira"] = bandeiras[i]

            Cidade.objects.create(**cidade_data)

        return redirect("municipios:posto_list")

    return render(
        request,
        "posto_form.html",
        {
            "sgb_choices": sgb_choices,
            "posto_secao_choices": posto_secao_choices,
            "posto_atendimento_choices": posto_atendimento_choices,
            "cidade_posto_choices": cidade_posto_choices,
            "municipio_choices": municipio_choices,
            "tipo_choices": tipo_choices,
            "op_adm_choices": op_adm_choices,
        },
    )


@permissao_necessaria('sgb')
def posto_update(request, pk):
    posto = get_object_or_404(Posto, pk=pk)
    contato = get_object_or_404(Contato, posto=posto)

    if (
        request.method == "POST"
        and request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ):
        cidade_id = request.POST.get("cidade_id")

        if cidade_id:
            try:
                cidade = get_object_or_404(Cidade, id=cidade_id, posto=posto)
                cidade.municipio = request.POST.get("municipio", cidade.municipio)
                cidade.latitude = float(request.POST.get("latitude", cidade.latitude))
                cidade.longitude = float(request.POST.get("longitude", cidade.longitude))
                cidade.descricao = request.POST.get("descricao", cidade.descricao)

                if "bandeira" in request.FILES:
                    if cidade.bandeira:
                        cidade.bandeira.delete(save=False)
                    cidade.bandeira = request.FILES["bandeira"]
                elif request.POST.get("bandeira-clear") == "on":
                    if cidade.bandeira:
                        cidade.bandeira.delete(save=False)
                    cidade.bandeira = None

                cidade.save()

                return JsonResponse({"success": True, "message": "Município atualizado com sucesso!", "data": {"municipio": cidade.municipio, "latitude": cidade.latitude, "longitude": cidade.longitude, "bandeira_url": (cidade.bandeira.url if cidade.bandeira else "")}})
            except (TypeError, ValueError):
                return JsonResponse({"success": False, "message": "Coordenadas inválidas. Use números decimais."})
            except Exception as e:
                return JsonResponse({"success": False, "message": f"Erro ao atualizar município: {str(e)}"})

    elif request.method == "POST":
        posto.sgb = request.POST.get("sgb", posto.sgb)
        posto.posto_secao = request.POST.get("posto_secao", posto.posto_secao)
        posto.posto_atendimento = request.POST.get("posto_atendimento", posto.posto_atendimento)
        posto.cidade_posto = request.POST.get("cidade_posto", posto.cidade_posto)
        posto.tipo_cidade = request.POST.get("tipo_cidade", posto.tipo_cidade)
        posto.op_adm = request.POST.get("op_adm", posto.op_adm)

        if "quartel" in request.FILES:
            if posto.quartel:
                posto.quartel.delete(save=False)
            posto.quartel = request.FILES["quartel"]

        posto.save()

        contato.telefone = request.POST.get("telefone", contato.telefone)
        contato.rua = request.POST.get("rua", contato.rua)
        contato.numero = request.POST.get("numero", contato.numero)
        contato.complemento = request.POST.get("complemento", contato.complemento)
        contato.bairro = request.POST.get("bairro", contato.bairro)
        contato.cidade = request.POST.get("cidade", contato.cidade)
        contato.cep = request.POST.get("cep", contato.cep)
        contato.email = request.POST.get("email", contato.email)

        try:
            contato.latitude = float(request.POST.get("latitude", contato.latitude or 0))
            contato.longitude = float(request.POST.get("longitude", contato.longitude or 0))
        except ValueError:
            pass

        contato.save()
        return redirect("municipios:posto_detail", pk=posto.pk)

    elif request.headers.get("X-Requested-With") == "XMLHttpRequest":
        cidade_id = request.GET.get("cidade_id")
        if cidade_id:
            cidade = get_object_or_404(Cidade, id=cidade_id, posto=posto)
            return JsonResponse({"municipio": cidade.municipio, "latitude": cidade.latitude, "longitude": cidade.longitude, "descricao": cidade.descricao, "bandeira_url": cidade.bandeira.url if cidade.bandeira else ""})

    context = {
        "posto": posto, "contato": contato, "sgb_choices": Posto._meta.get_field("sgb").choices,
        "posto_secao_choices": Posto._meta.get_field("posto_secao").choices, "posto_atendimento_choices": Posto._meta.get_field("posto_atendimento").choices,
        "cidade_posto_choices": Posto._meta.get_field("cidade_posto").choices, "tipo_choices": Posto._meta.get_field("op_adm").choices,
        "op_adm_choices": Posto._meta.get_field("tipo_cidade").choices,
    }
    return render(request, "posto_detail.html", context)

from django.contrib.auth.hashers import check_password

@permissao_necessaria('sgb')
def excluir_posto(request, id):
    if request.method == "POST":
        try:
            cadastro = get_object_or_404(Posto, id=id)
            current_user = request.user
            password = request.POST.get("password", "")

            if not check_password(password, current_user.password):
                return JsonResponse({"success": False, "message": "Senha incorreta! Operação cancelada."})

            cadastro.delete()
            return JsonResponse({"success": True, "message": "Posto excluído com sucesso."})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Erro ao excluir: {str(e)}"})

    return JsonResponse({"success": False, "message": "Método inválido."})



@permissao_necessaria('sgb')
def editar_pessoal(request, pk):
    posto = get_object_or_404(Posto, pk=pk)
    pessoal = get_object_or_404(Pessoal, posto=posto)

    if request.method == "POST":
        pessoal.cel = request.POST.get("cel", 0)
        pessoal.ten_cel = request.POST.get("ten_cel", 0)
        pessoal.maj = request.POST.get("maj", 0)
        pessoal.cap = request.POST.get("cap", 0)
        pessoal.tenqo = request.POST.get("tenqo", 0)
        pessoal.tenqa = request.POST.get("tenqa", 0)
        pessoal.asp = request.POST.get("asp", 0)
        pessoal.st_sgt = request.POST.get("st_sgt", 0)
        pessoal.cb_sd = request.POST.get("cb_sd", 0)
        pessoal.save()
        return redirect("municipios:posto_detail", pk=posto.pk)
    else:
        return render(request, "posto_detail.html", {"posto": posto, "pessoal": pessoal})


@permissao_necessaria('sgb')
def editar_contato(request, pk):
    posto = get_object_or_404(Posto, pk=pk)
    contato = get_object_or_404(Contato, posto=posto)

    if request.method == "POST":
        contato.telefone = request.POST.get("telefone", "")
        contato.rua = request.POST.get("rua", "")
        contato.numero = request.POST.get("numero", "")
        contato.complemento = request.POST.get("complemento", "")
        contato.bairro = request.POST.get("bairro", "")
        contato.cidade = request.POST.get("cidade", "")
        contato.cep = request.POST.get("cep", "")
        contato.email = request.POST.get("email", "")

        latitude_str = request.POST.get("latitude", None)
        longitude_str = request.POST.get("longitude", None)

        try:
            if latitude_str:
                contato.latitude = float(latitude_str.replace(",", "."))
            else:
                contato.latitude = None
        except ValueError:
            pass

        try:
            if longitude_str:
                contato.longitude = float(longitude_str.replace(",", "."))
            else:
                contato.longitude = None
        except ValueError:
            pass

        contato.save()
        return redirect("municipios:posto_detail", pk=posto.pk)
    else:
        return render(request, "posto_detail.html", {"posto": posto, "contato": contato})


@permissao_necessaria('sgb')
def posto_print(request, pk):
    posto = get_object_or_404(Posto, pk=pk)
    return render(request, "posto_print.html", {"posto": posto})


@require_POST
@permissao_necessaria('sgb')
def calculate_route_api(request):
    try:
        data = json.loads(request.body)
        origin = data.get('origin')
        destination = data.get('destination')
        waypoints = data.get('waypoints', [])
        
        km_per_l = float(data.get('vehicle', {}).get('km_per_l', 0))
        fuel_price = float(data.get('fuel_price', 0))

        if not origin or not destination:
            return JsonResponse({'error': 'Origem e destino são obrigatórios.'}, status=400)

        coords = [f"{origin['lng']},{origin['lat']}"]
        for wp in waypoints:
            coords.append(f"{wp['lng']},{wp['lat']}")
        coords.append(f"{destination['lng']},{destination['lat']}")
        
        coordinates_str = ";".join(coords)
        
        osrm_url = f"http://router.project-osrm.org/route/v1/driving/{coordinates_str}"
        params = {'overview': 'full', 'geometries': 'geojson'}
        
        response = requests.get(osrm_url, params=params)
        response.raise_for_status()
        route_data = response.json()

        if route_data.get('code') != 'Ok':
            return JsonResponse({'error': 'Não foi possível encontrar uma rota.', 'details': route_data.get('message')}, status=400)

        main_route = route_data['routes'][0]
        distance_meters = main_route.get('distance', 0)
        duration_seconds = main_route.get('duration', 0)
        polyline = main_route.get('geometry')

        distance_km = distance_meters / 1000

        estimated_liters = (distance_km / km_per_l) if km_per_l > 0 else 0
        estimated_cost = estimated_liters * fuel_price

        return JsonResponse({
            'status': 'ok', 'distance_km': round(distance_km, 2), 'duration_seconds': round(duration_seconds),
            'polyline': polyline, 'estimated_liters': round(estimated_liters, 2), 'estimated_cost': round(estimated_cost, 2),
            'steps': [{'instruction': step['maneuver']['instruction'], 'distance_m': step['distance'], 'duration_s': step['duration']} for step in main_route['legs'][0]['steps']]
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Payload JSON inválido.'}, status=400)
    except (requests.exceptions.RequestException, KeyError, IndexError) as e:
        return JsonResponse({'error': f'Erro ao processar a rota: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Um erro inesperado ocorreu: {str(e)}'}, status=500)


from django.contrib import messages

@permissao_necessaria('sgb')
def importar_municipios(request):
    template_name = "importar_municipios.html"
    redirect_url = "municipios:posto_list"

    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")

        if not arquivo:
            messages.error(request, "Nenhum arquivo selecionado para importação.", extra_tags="bg-red-500 text-white p-4 rounded")
            return redirect(reverse(redirect_url))

        extensao = arquivo.name.split(".")[-1].lower()
        if extensao not in ["csv", "xls", "xlsx"]:
            messages.error(request, f'Formato de arquivo "{extensao}" não suportado. Use CSV ou Excel.', extra_tags="bg-red-500 text-white p-4 rounded")
            return redirect(reverse(redirect_url))

        if arquivo.size > 10 * 1024 * 1024:
            messages.error(request, "Arquivo excede o limite de tamanho (máximo 10MB).", extra_tags="bg-red-500 text-white p-4 rounded")
            return redirect(reverse(redirect_url))

        try:
            df = None
            if extensao == "csv":
                try:
                    df = pd.read_csv(arquivo, sep=";", encoding="utf-8-sig", dtype=str, keep_default_na=False, na_filter=False)
                except UnicodeDecodeError:
                    arquivo.seek(0)
                    df = pd.read_csv(arquivo, sep=";", encoding="latin-1", dtype=str, keep_default_na=False, na_filter=False)
            elif extensao in ["xls", "xlsx"]:
                df = pd.read_excel(arquivo, dtype=str, keep_default_na=False, na_values=[])

            csv_data = df.to_csv(sep=";", index=False, encoding="utf-8")
            csv_file = ContentFile(csv_data.encode("utf-8"))
            file_path = default_storage.save("temp_import.csv", csv_file)
            full_file_path = default_storage.path(file_path)
            registros_processados, erros_processamento = importar_dados(full_file_path, request.user)
            default_storage.delete(file_path)

            if registros_processados > 0:
                messages.success(request, f"✅ {registros_processados} registro(s) importado(s) com sucesso!", extra_tags="bg-green-500 text-white p-4 rounded")
            if erros_processamento:
                total_erros = len(erros_processamento)
                erros_preview = "; ".join(erros_processamento[:5])
                erros_msg = f"⚠️ {total_erros} erro(s) ocorreram durante a importação. "
                if total_erros <= 5:
                    erros_msg += f"Erros: {erros_preview}"
                else:
                    erros_msg += f"Primeiros {5} erros: {erros_preview} (...e mais {total_erros - 5})"
                messages.warning(request, erros_msg, extra_tags="bg-yellow-500 text-white p-4 rounded")
        except Exception as e:
            messages.error(request, f"Erro ao processar o arquivo: {e}", extra_tags="bg-red-500 text-white p-4 rounded")
        return redirect(reverse(redirect_url))
    return render(request, template_name)


@permissao_necessaria('sgb')
def exportar_postos_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="postos_e_dados_relacionados.csv"'
    writer = csv.writer(response, delimiter=";", quoting=csv.QUOTE_NONNUMERIC)
    headers = [
        "ID_Posto", "SGB", "Posto_Secao", "Posto_Atendimento", "Cidade_Posto", "Tipo_Cidade", "Op_Adm", "Data_Criacao", "Usuario",
        "Contato_Telefone", "Contato_Rua", "Contato_Numero", "Contato_Complemento", "Contato_Bairro", "Contato_Cidade", "Contato_CEP", "Contato_Email", "Contato_Longitude", "Contato_Latitude",
        "Pessoal_Cel", "Pessoal_Ten_Cel", "Pessoal_Maj", "Pessoal_Cap", "Pessoal_TenQO", "Pessoal_TenQA", "Pessoal_Asp", "Pessoal_St_Sgt", "Pessoal_Cb_Sd", "Pessoal_Total_Efetivo",
    ]
    writer.writerow(headers)
    postos = Posto.objects.select_related("contato", "usuario").prefetch_related("pessoal").all()
    for posto in postos:
        row_data = [
            posto.id, posto.sgb, posto.posto_secao, posto.posto_atendimento, posto.cidade_posto, posto.tipo_cidade, posto.op_adm,
            (posto.data_criacao.strftime("%Y-%m-%d %H:%M:%S") if posto.data_criacao else ""),
            (posto.usuario.email if posto.usuario and hasattr(posto.usuario, "email") else (posto.usuario.get_username() if posto.usuario else "")),
        ]
        contato = getattr(posto, "contato", None)
        if contato:
            row_data.extend([contato.telefone, contato.rua, contato.numero, contato.complemento, contato.bairro, contato.cidade, contato.cep, contato.email, (str(contato.longitude).replace(".", ",") if contato.longitude is not None else ""), (str(contato.latitude).replace(".", ",") if contato.latitude is not None else "")])
        else:
            row_data.extend([""] * 10)
        pessoal = posto.pessoal.first()
        if pessoal:
            row_data.extend([pessoal.cel, pessoal.ten_cel, pessoal.maj, pessoal.cap, pessoal.tenqo, pessoal.tenqa, pessoal.asp, pessoal.st_sgt, pessoal.cb_sd, pessoal.total])
        else:
            row_data.extend([""] * 10)
        writer.writerow(row_data)
    return response


@permissao_necessaria('sgb')
def exportar_relatorio_efetivo_pdf(request):
    sgb_filter = request.GET.get("sgb")
    posto_secao_filter = request.GET.get("posto_secao")
    queryset = Posto.objects.all().prefetch_related("pessoal")
    if sgb_filter:
        queryset = queryset.filter(sgb=sgb_filter)
    if posto_secao_filter:
        queryset = queryset.filter(posto_secao=posto_secao_filter)
    report_data = []
    for posto in queryset:
        efetivo_grupos = {"Tc": 0, "Maj": 0, "Cap": 0, "Ten": 0, "Ten_QAOPM": 0, "St_Sgt": 0, "Cb_Sd": 0}
        total_efetivo_existente = 0
        pessoal = posto.pessoal.first()
        pessoal_data = {"cel": pessoal.cel if pessoal else 0, "ten_cel": pessoal.ten_cel if pessoal else 0, "maj": pessoal.maj if pessoal else 0, "cap": pessoal.cap if pessoal else 0, "tenqo": pessoal.tenqo if pessoal else 0, "tenqa": pessoal.tenqa if pessoal else 0, "asp": pessoal.asp if pessoal else 0, "st_sgt": pessoal.st_sgt if pessoal else 0, "cb_sd": pessoal.cb_sd if pessoal else 0, "total_planejado": (pessoal.total if pessoal else 0)}
        report_data.append({"posto_obj": posto, "efetivo_existente_grupos": efetivo_grupos, "total_efetivo_existente": total_efetivo_existente, "pessoal_planejado": pessoal_data})
    pdf_buffer, filename = export_efetivo_pdf_report(request, report_data, sgb_filter, posto_secao_filter)
    response = HttpResponse(pdf_buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

@permissao_necessaria('sgb')
def api_cep_info(request):
    cep = request.GET.get('cep', '').replace('-', '').replace('.', '')
    if not cep or not cep.isdigit() or len(cep) != 8:
        return JsonResponse({'error': 'CEP inválido.'}, status=400)
    try:
        viacep_response = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
        viacep_response.raise_for_status()
        viacep_data = viacep_response.json()
        if viacep_data.get('erro'):
            return JsonResponse({'error': 'CEP não encontrado.'}, status=404)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Erro ao contatar a API de CEP: {e}'}, status=503)
    try:
        address_string = f"{viacep_data.get('logradouro', '')}, {viacep_data.get('bairro', '')}, {viacep_data.get('localidade', '')}, {viacep_data.get('uf', '')}, Brazil"
        nominatim_response = requests.get('https://nominatim.openstreetmap.org/search', params={'q': address_string, 'format': 'json', 'limit': 1}, headers={'User-Agent': 'SisCoE/1.0'})
        nominatim_response.raise_for_status()
        nominatim_data = nominatim_response.json()
        if not nominatim_data:
            fallback_address = f"{viacep_data.get('localidade', '')}, {viacep_data.get('uf', '')}, Brazil"
            nominatim_response = requests.get('https://nominatim.openstreetmap.org/search', params={'q': fallback_address, 'format': 'json', 'limit': 1}, headers={'User-Agent': 'SisCoE/1.0'})
            nominatim_response.raise_for_status()
            nominatim_data = nominatim_response.json()
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Erro ao contatar a API de geocodificação: {e}'}, status=503)
    final_data = {'rua': viacep_data.get('logradouro', ''), 'bairro': viacep_data.get('bairro', ''), 'cidade': viacep_data.get('localidade', ''), 'complemento': viacep_data.get('complemento', ''), 'latitude': None, 'longitude': None}
    if nominatim_data:
        final_data['latitude'] = nominatim_data[0].get('lat')
        final_data['longitude'] = nominatim_data[0].get('lon')
    return JsonResponse(final_data)

from .services import fetch_wikipedia_data

@permissao_necessaria('sgb')
def api_municipio_info(request):
    municipio_nome = request.GET.get('municipio', None)
    uf = request.GET.get('uf', 'SP')
    if not municipio_nome:
        return JsonResponse({'error': 'Nome do município não fornecido.'}, status=400)
    cidade_obj, created = Cidade.objects.get_or_create(municipio=municipio_nome, defaults={'posto': None})
    if not cidade_obj.descricao or not cidade_obj.bandeira:
        wiki_data = fetch_wikipedia_data(cidade_obj.municipio, uf)
        if wiki_data:
            if not cidade_obj.descricao and wiki_data.get('descricao'):
                cidade_obj.descricao = wiki_data['descricao']
            if not cidade_obj.bandeira and wiki_data.get('url_bandeira'):
                url = wiki_data['url_bandeira']
                try:
                    result = urllib.request.urlretrieve(url)
                    cidade_obj.bandeira.save(os.path.basename(url), ContentFile(open(result[0], 'rb').read()))
                except (urllib.error.URLError, FileNotFoundError, ValueError) as e:
                    print(f"Erro ao baixar ou salvar a imagem da bandeira de {url}: {e}")
            cidade_obj.save()
    if not cidade_obj.latitude or not cidade_obj.longitude:
        try:
            address_string = f"{cidade_obj.municipio}, {uf}, Brazil"
            nominatim_response = requests.get('https://nominatim.openstreetmap.org/search', params={'q': address_string, 'format': 'json', 'limit': 1}, headers={'User-Agent': 'SisCoE/1.0'})
            nominatim_response.raise_for_status()
            nominatim_data = nominatim_response.json()
            if nominatim_data:
                cidade_obj.latitude = nominatim_data[0].get('lat')
                cidade_obj.longitude = nominatim_data[0].get('lon')
                cidade_obj.save()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar coordenadas para {cidade_obj.municipio}: {e}")
    return JsonResponse({'latitude': cidade_obj.latitude, 'longitude': cidade_obj.longitude, 'descricao': cidade_obj.descricao, 'bandeira_url': cidade_obj.bandeira.url if cidade_obj.bandeira else None})

@permissao_necessaria('sgb')
def api_geocode_autocomplete(request):
    query = request.GET.get('q', '')
    if not query or len(query) < 3:
        return JsonResponse([], safe=False)
    params = {'q': query, 'format': 'json', 'addressdetails': 1, 'limit': 7, 'countrycodes': 'br', 'accept-language': 'pt-BR'}
    try:
        response = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers={'User-Agent': 'SisCoE/1.0'})
        response.raise_for_status()
        results = response.json()
        suggestions = []
        for r in results:
            address = r.get('address', {})
            city = address.get('city') or address.get('town') or address.get('village')
            state = address.get('state')
            road = address.get('road')
            display_parts = []
            if r.get('osm_type') == 'relation' and city:
                display_parts.extend([part for part in [city, state] if part])
            else:
                display_parts.extend([part for part in [road, city, state] if part])
            short_address = ", ".join(display_parts)
            if not short_address or any(s['short_address'] == short_address for s in suggestions):
                continue
            suggestions.append({'short_address': short_address, 'lat': r.get('lat'), 'lon': r.get('lon')})
        return JsonResponse(suggestions, safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)
