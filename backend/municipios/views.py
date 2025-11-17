from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Posto, Contato, Pessoal, Cidade
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pandas as pd
import csv

# Importe a função de importação (se estiver em import_utils.py)
from .import_utils import importar_dados

# Importe a nova função de exportação PDF
from .export_utils import export_efetivo_pdf_report  # Importe a nova função


@login_required
def posto_list(request):
    postos = Posto.objects.all().prefetch_related("pessoal", "cidades")
    cidades = Cidade.objects.all().select_related("posto")

    # Obter as choices diretamente do modelo
    municipio_choices = Cidade._meta.get_field("municipio").choices

    return render(
        request,
        "posto_list.html",
        {
            "postos": postos,
            "cidades": cidades,
            "municipio_choices": municipio_choices,  # Adicionar ao contexto principal
        },
    )


from django.contrib.auth.decorators import login_required
from backend.efetivo.models import DetalhesSituacao, Promocao


@login_required
def posto_detail(request, pk):
    posto = get_object_or_404(Posto, pk=pk)

    # Definimos os grupos exatamente como estão no modelo
    GRUPOS = {
        "Tc": "Ten Cel",
        "Maj": "Maj",
        "Cap": "Cap",
        "Ten": "Ten QO",
        "Ten QAOPM": "Ten QA",
        "St/Sgt": "St/Sgt",
        "Cb/Sd": "Cb/Sd",
    }

    # Primeiro: Obter todos os cadastros com situação "Efetivo" no posto
    efetivos = DetalhesSituacao.objects.filter(
        situacao="Efetivo", posto_secao=posto.posto_secao
    ).select_related("cadastro")

    # Segundo: Para cada efetivo, pegar sua última promoção
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

    # Preparamos os dados para o template
    efetivo_grupos = {
        "Tc": contagem.get("Tc", 0),
        "Maj": contagem.get("Maj", 0),
        "Cap": contagem.get("Cap", 0),
        "Ten": contagem.get("Ten", 0),
        "Ten_QAOPM": contagem.get("Ten QAOPM", 0),  # Usamos underscore para o template
        "St_Sgt": contagem.get("St/Sgt", 0),  # Usamos underscore para o template
        "Cb_Sd": contagem.get("Cb/Sd", 0),  # Usamos underscore para o template
    }

    # Calcula o total
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


@login_required
def municipio_detail(request, pk):
    cidade = get_object_or_404(Cidade, pk=pk)
    posto = cidade.posto  # Obtenha o posto relacionado à cidade
    return render(request, "municipio_detail.html", {"cidade": cidade, "posto": posto})


@login_required
def posto_secao_detail(request, pk):
    posto = get_object_or_404(Posto, pk=pk)
    return render(request, "posto_secao_detail.html", {"posto": posto})


@login_required
def posto_create(request):
    sgb_choices = Posto.sgb_choices
    posto_secao_choices = Posto.posto_secao_choices
    posto_atendimento_choices = Posto.posto_atendimento_choices
    cidade_posto_choices = Posto.cidade_posto_choices
    municipio_choices = Cidade.municipio_choices
    tipo_choices = Posto.tipo_choices
    op_adm_choices = Posto.op_adm_choices

    if request.method == "POST":
        # Dados do Posto
        posto_data = {
            "sgb": request.POST.get("sgb"),
            "posto_secao": request.POST.get("posto_secao"),
            "posto_atendimento": request.POST.get("posto_atendimento"),
            "cidade_posto": request.POST.get("cidade_posto"),
            "tipo_cidade": request.POST.get("tipo_cidade"),
            "op_adm": request.POST.get("op_adm"),
            "usuario": request.user,
        }

        # Processa a imagem do quartel
        if "quartel" in request.FILES:
            posto_data["quartel"] = request.FILES["quartel"]

        # Cria o Posto
        posto = Posto.objects.create(**posto_data)

        # Dados do Contato
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

        # Dados do Pessoal
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

        # Dados das Cidades (múltiplas entradas)
        municipios = request.POST.getlist("municipios[]")
        latitudes = request.POST.getlist("latitudes[]")
        longitudes = request.POST.getlist("longitudes[]")
        bandeiras = request.FILES.getlist("bandeiras[]")
        descricoes = request.POST.getlist("descricoes[]")

        for i in range(len(municipios)):
            cidade_data = {
                "posto": posto,
                "municipio": municipios[i],
                "descricao": descricoes[i],
                "latitude": latitudes[i],
                "longitude": longitudes[i],
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


from django.contrib.auth.decorators import login_required


@login_required
def posto_update(request, pk):
    posto = get_object_or_404(Posto, pk=pk)
    contato = get_object_or_404(Contato, posto=posto)

    # Verifica se é uma requisição AJAX para atualizar cidade
    if (
        request.method == "POST"
        and request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ):
        cidade_id = request.POST.get("cidade_id")

        if cidade_id:
            try:
                cidade = get_object_or_404(Cidade, id=cidade_id, posto=posto)

                # Atualiza os dados da cidade
                cidade.municipio = request.POST.get("municipio", cidade.municipio)

                # Valida e converte coordenadas
                try:
                    cidade.latitude = float(
                        request.POST.get("latitude", cidade.latitude)
                    )
                    cidade.longitude = float(
                        request.POST.get("longitude", cidade.longitude)
                    )
                except (TypeError, ValueError):
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Coordenadas inválidas. Use números decimais.",
                        }
                    )

                cidade.descricao = request.POST.get("descricao", cidade.descricao)

                # Trata o upload da bandeira
                if "bandeira" in request.FILES:
                    # Remove a imagem antiga se existir
                    if cidade.bandeira:
                        cidade.bandeira.delete(save=False)
                    cidade.bandeira = request.FILES["bandeira"]
                elif request.POST.get("bandeira-clear") == "on":
                    if cidade.bandeira:
                        cidade.bandeira.delete(save=False)
                    cidade.bandeira = None

                cidade.save()

                return JsonResponse(
                    {
                        "success": True,
                        "message": "Município atualizado com sucesso!",
                        "data": {
                            "municipio": cidade.municipio,
                            "latitude": cidade.latitude,
                            "longitude": cidade.longitude,
                            "bandeira_url": (
                                cidade.bandeira.url if cidade.bandeira else ""
                            ),
                        },
                    }
                )

            except Exception as e:
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"Erro ao atualizar município: {str(e)}",
                    }
                )

    # Processamento normal do POST (não-AJAX)
    elif request.method == "POST":
        # Atualizando os dados do Posto
        posto.sgb = request.POST.get("sgb", posto.sgb)
        posto.posto_secao = request.POST.get("posto_secao", posto.posto_secao)
        posto.posto_atendimento = request.POST.get(
            "posto_atendimento", posto.posto_atendimento
        )
        posto.cidade_posto = request.POST.get("cidade_posto", posto.cidade_posto)
        posto.tipo_cidade = request.POST.get("tipo_cidade", posto.tipo_cidade)
        posto.op_adm = request.POST.get("op_adm", posto.op_adm)

        if "quartel" in request.FILES:
            # Remove a imagem antiga se existir
            if posto.quartel:
                posto.quartel.delete(save=False)
            posto.quartel = request.FILES["quartel"]

        posto.save()

        # Atualizando Contato
        contato.telefone = request.POST.get("telefone", contato.telefone)
        contato.rua = request.POST.get("rua", contato.rua)
        contato.numero = request.POST.get("numero", contato.numero)
        contato.complemento = request.POST.get("complemento", contato.complemento)
        contato.bairro = request.POST.get("bairro", contato.bairro)
        contato.cidade = request.POST.get("cidade", contato.cidade)
        contato.cep = request.POST.get("cep", contato.cep)
        contato.email = request.POST.get("email", contato.email)

        # Validação das coordenadas
        try:
            contato.latitude = float(
                request.POST.get("latitude", contato.latitude or 0)
            )
            contato.longitude = float(
                request.POST.get("longitude", contato.longitude or 0)
            )
        except ValueError:
            # Pode adicionar uma mensagem de erro se necessário
            pass

        contato.save()

        # Redireciona para a página de detalhes do posto
        return redirect("municipios:posto_detail", pk=posto.pk)

    # Se for GET e AJAX (para pré-carregar dados no modal)
    elif request.headers.get("X-Requested-With") == "XMLHttpRequest":
        cidade_id = request.GET.get("cidade_id")
        if cidade_id:
            cidade = get_object_or_404(Cidade, id=cidade_id, posto=posto)
            return JsonResponse(
                {
                    "municipio": cidade.municipio,
                    "latitude": cidade.latitude,
                    "longitude": cidade.longitude,
                    "descricao": cidade.descricao,
                    "bandeira_url": cidade.bandeira.url if cidade.bandeira else "",
                }
            )

    # Contexto para renderização normal (não-AJAX)
    context = {
        "posto": posto,
        "contato": contato,
        "sgb_choices": Posto._meta.get_field("sgb").choices,
        "posto_secao_choices": Posto._meta.get_field("posto_secao").choices,
        "posto_atendimento_choices": Posto._meta.get_field("posto_atendimento").choices,
        "cidade_posto_choices": Posto._meta.get_field("cidade_posto").choices,
        "tipo_choices": Posto._meta.get_field("op_adm").choices,
        "op_adm_choices": Posto._meta.get_field("tipo_cidade").choices,
    }

    return render(request, "posto_detail.html", context)


# views.py do app municipio
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required


@login_required
def excluir_municipio(request, id):
    if request.method == "POST":
        try:
            cadastro = get_object_or_404(Posto, id=id)
            current_user = request.user
            password = request.POST.get("password", "")

            if not check_password(password, current_user.password):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Senha incorreta! Operação cancelada.",
                    }
                )

            cadastro.delete()
            return JsonResponse(
                {"success": True, "message": "Município excluído com sucesso."}
            )

        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Erro ao excluir: {str(e)}"}
            )

    return JsonResponse({"success": False, "message": "Método inválido."})


def calcular_rota(request):
    cidades = Cidade.objects.all().select_related("posto")
    return render(request, "calcular_rota.html", {"cidades": cidades})


from django.contrib.auth.decorators import login_required


@login_required
def editar_pessoal(request, pk):
    """
    View para editar os dados de pessoal de um posto específico.
    """
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
        # Redirecione para a página de detalhes do posto ou outra página desejada
        return redirect("municipios:posto_detail", pk=posto.pk)
    else:
        # Se a requisição não for POST, você pode renderizar um formulário
        # preenchido com os dados do pessoal (se necessário em outro cenário)
        # No seu caso, o modal já está preenchido via template.
        return render(
            request, "posto_detail.html", {"posto": posto, "pessoal": pessoal}
        )


from django.contrib.auth.decorators import login_required


@login_required
def editar_contato(request, pk):
    """
    View para editar os dados de contato de um posto específico.
    """
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
            # Handle the case where latitude cannot be converted to a float
            # You might want to add an error message to the user
            pass  # Or add error handling

        try:
            if longitude_str:
                contato.longitude = float(longitude_str.replace(",", "."))
            else:
                contato.longitude = None
        except ValueError:
            # Handle the case where longitude cannot be converted to a float
            # You might want to add an error message to the user
            pass  # Or add error handling

        contato.save()
        # Redirecione para a página de detalhes do posto
        return redirect("municipios:posto_detail", pk=posto.pk)
    else:
        # Se a requisição não for POST, renderize a página de detalhes do posto
        # O modal já está preenchido via template.
        return render(
            request, "posto_detail.html", {"posto": posto, "contato": contato}
        )


def posto_print(request, pk):
    # Obtém o objeto posto ou retorna 404 se não existir
    posto = get_object_or_404(Posto, pk=pk)

    # Renderiza um template específico para impressão
    return render(
        request,
        "posto_print.html",
        {
            "posto": posto,
        },
    )


# views.py
import json
from django.views.decorators.http import require_POST
from geopy.distance import geodesic


@require_POST
def calcular_rota(request):
    try:
        data = json.loads(request.body)
        origem_posto_secao_value = data.get(
            "origem_posto_secao"
        )  # This is the value from the choice tuple
        destino_posto_secao_value = data.get(
            "destino_posto_secao"
        )  # This is the value from the choice tuple

        if not origem_posto_secao_value or not destino_posto_secao_value:
            return JsonResponse(
                {"success": False, "error": "Origem e destino são obrigatórios"},
                status=400,
            )

        # Retrieve lat/lng for origin Posto based on the posto_secao value
        try:
            # Find the Posto instance where posto_secao matches the value
            origem_posto_instance = Posto.objects.get(
                posto_secao=origem_posto_secao_value
            )
            origem_contato = Contato.objects.get(posto=origem_posto_instance)
            origem_lat = origem_contato.latitude
            origem_lng = origem_contato.longitude

            # Use the display name from the choices for response, or just the value
            origem_nome = dict(Posto.posto_secao_choices).get(
                origem_posto_secao_value, origem_posto_secao_value
            )

        except (Posto.DoesNotExist, Contato.DoesNotExist):
            return JsonResponse(
                {
                    "success": False,
                    "error": f'Coordenadas de origem para "{origem_posto_secao_value}" não encontradas. Certifique-se de que o Posto existe e tem um Contato associado.',
                },
                status=400,
            )

        # Retrieve lat/lng for destination Posto based on the posto_secao value
        try:
            destino_posto_instance = Posto.objects.get(
                posto_secao=destino_posto_secao_value
            )
            destino_contato = Contato.objects.get(posto=destino_posto_instance)
            destino_lat = destino_contato.latitude
            destino_lng = destino_contato.longitude

            destino_nome = dict(Posto.posto_secao_choices).get(
                destino_posto_secao_value, destino_posto_secao_value
            )

        except (Posto.DoesNotExist, Contato.DoesNotExist):
            return JsonResponse(
                {
                    "success": False,
                    "error": f'Coordenadas de destino para "{destino_posto_secao_value}" não encontradas. Certifique-se de que o Posto existe e tem um Contato associado.',
                },
                status=400,
            )

        # Cálculo da distância usando geopy
        distancia = geodesic((origem_lat, origem_lng), (destino_lat, destino_lng)).km

        # Cálculo do tempo estimado (70km/h)
        tempo = round((distancia / 70) * 60)  # Em minutos

        return JsonResponse(
            {
                "success": True,
                "distancia": round(distancia, 1),
                "tempo": tempo,
                "origem": origem_nome,
                "destino": destino_nome,
                "origem_lat": origem_lat,  # Return these for map visualization if needed
                "origem_lng": origem_lng,
                "destino_lat": destino_lat,
                "destino_lng": destino_lng,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def modal_rota(request):
    """
    View para renderizar o modal de cálculo de rota, carregando apenas os Postos
    que possuem informações de contato (latitude/longitude) salvas no sistema.
    """
    # Get only the Posto objects that have an associated Contato and whose posto_secao is not empty
    # We use select_related to optimize the query by fetching Contato data in the same query
    valid_postos = (
        Posto.objects.filter(contato__isnull=False)
        .exclude(posto_secao="")
        .select_related("contato")
        .order_by("posto_secao")
    )

    # Prepare the options for the select dropdowns, mapping posto_secao values to labels
    # We'll use the label from posto_secao_choices for display
    posto_secao_value_to_label_map = dict(Posto.posto_secao_choices)

    posto_options_for_template = []
    posto_coordinates_map = {}

    for posto in valid_postos:
        # Get the human-readable label from the choices, fallback to value if not found
        display_label = posto_secao_value_to_label_map.get(
            posto.posto_secao, posto.posto_secao
        )

        posto_options_for_template.append(
            {"value": posto.posto_secao, "label": display_label}
        )
        posto_coordinates_map[posto.posto_secao] = {
            "lat": posto.contato.latitude,
            "lon": posto.contato.longitude,
        }

    return render(
        request,
        "modals/modal_rota.html",
        {
            "posto_options": posto_options_for_template,  # Now contains only valid, saved posts
            "posto_coordinates_map_json": json.dumps(posto_coordinates_map),
        },
    )


from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required
@permission_required("municipios.add_posto")  # Ajuste a permissão conforme necessário
def importar_municipios(request):
    """
    View para importar dados de municípios a partir de um arquivo CSV ou Excel.
    """
    template_name = "importar_municipios.html"
    redirect_url = "municipios:posto_list"  # Use o nome correto da sua URL

    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")

        # Validações iniciais
        if not arquivo:
            messages.error(
                request,
                "Nenhum arquivo selecionado para importação.",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )
            return redirect(reverse(redirect_url))

        extensao = arquivo.name.split(".")[-1].lower()
        if extensao not in ["csv", "xls", "xlsx"]:
            messages.error(
                request,
                f'Formato de arquivo "{extensao}" não suportado. Use CSV ou Excel.',
                extra_tags="bg-red-500 text-white p-4 rounded",
            )
            return redirect(reverse(redirect_url))

        if arquivo.size > 10 * 1024 * 1024:  # Limite de 10MB
            messages.error(
                request,
                "Arquivo excede o limite de tamanho (máximo 10MB).",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )
            return redirect(reverse(redirect_url))

        try:
            # Ler o arquivo com Pandas
            df = None
            if extensao == "csv":
                try:
                    df = pd.read_csv(
                        arquivo,
                        sep=";",
                        encoding="utf-8-sig",
                        dtype=str,
                        keep_default_na=False,
                        na_filter=False,
                    )
                except UnicodeDecodeError:
                    arquivo.seek(0)
                    df = pd.read_csv(
                        arquivo,
                        sep=";",
                        encoding="latin-1",
                        dtype=str,
                        keep_default_na=False,
                        na_filter=False,
                    )
            elif extensao in ["xls", "xlsx"]:
                df = pd.read_excel(
                    arquivo, dtype=str, keep_default_na=False, na_values=[]
                )

            # Converter o DataFrame para um arquivo CSV virtual
            csv_data = df.to_csv(sep=";", index=False, encoding="utf-8")
            # Criar um arquivo na memória
            csv_file = ContentFile(csv_data.encode("utf-8"))

            # Salvar o arquivo temporário
            file_path = default_storage.save("temp_import.csv", csv_file)
            # Obter o caminho completo do arquivo
            full_file_path = default_storage.path(file_path)
            # Chamar a função de importação
            registros_processados, erros_processamento = importar_dados(
                full_file_path, request.user
            )  # Passar o usuário
            # Excluir o arquivo temporário
            default_storage.delete(file_path)

            # Feedback da importação
            if registros_processados > 0:
                messages.success(
                    request,
                    f"✅ {registros_processados} registro(s) importado(s) com sucesso!",
                    extra_tags="bg-green-500 text-white p-4 rounded",
                )

            if erros_processamento:
                total_erros = len(erros_processamento)
                erros_preview = "; ".join(erros_processamento[:5])
                erros_msg = f"⚠️ {total_erros} erro(s) ocorreram durante a importação. "
                if total_erros <= 5:
                    erros_msg += f"Erros: {erros_preview}"
                else:
                    erros_msg += f"Primeiros {5} erros: {erros_preview} (...e mais {total_erros - 5})"
                messages.warning(
                    request,
                    erros_msg,
                    extra_tags="bg-yellow-500 text-white p-4 rounded",
                )

        except Exception as e:
            messages.error(
                request,
                f"Erro ao processar o arquivo: {e}",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )

        return redirect(reverse(redirect_url))

    return render(request, template_name)


from django.contrib.auth.decorators import login_required, permission_required

# Importe a função de importação (se estiver em import_utils.py)


@login_required
@permission_required("municipios.view_posto")  # Permissão para visualizar Posto
def exportar_postos_csv(request):
    """
    Exporta todos os dados de Postos, Contatos e Pessoal relacionados em um único arquivo CSV.
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="postos_e_dados_relacionados.csv"'
    )

    # Adicionar quoting=csv.QUOTE_NONNUMERIC para garantir que campos com vírgulas (decimais) sejam citados
    writer = csv.writer(response, delimiter=";", quoting=csv.QUOTE_NONNUMERIC)

    # Cabeçalhos do CSV
    headers = [
        "ID_Posto",
        "SGB",
        "Posto_Secao",
        "Posto_Atendimento",
        "Cidade_Posto",
        "Tipo_Cidade",
        "Op_Adm",
        "Data_Criacao",
        "Usuario",
        "Contato_Telefone",
        "Contato_Rua",
        "Contato_Numero",
        "Contato_Complemento",
        "Contato_Bairro",
        "Contato_Cidade",
        "Contato_CEP",
        "Contato_Email",
        "Contato_Longitude",
        "Contato_Latitude",
        "Pessoal_Cel",
        "Pessoal_Ten_Cel",
        "Pessoal_Maj",
        "Pessoal_Cap",
        "Pessoal_TenQO",
        "Pessoal_TenQA",
        "Pessoal_Asp",
        "Pessoal_St_Sgt",
        "Pessoal_Cb_Sd",
        "Pessoal_Total_Efetivo",
    ]
    writer.writerow(headers)

    # Obter todos os Postos, pré-carregando Contato e Pessoal para evitar N+1 queries
    # Adicionando 'usuario' ao select_related para que o objeto User seja carregado
    postos = (
        Posto.objects.select_related("contato", "usuario")
        .prefetch_related("pessoal")
        .all()
    )

    for posto in postos:
        # Dados do Posto
        row_data = [
            posto.id,
            posto.sgb,
            posto.posto_secao,
            posto.posto_atendimento,
            posto.cidade_posto,
            posto.tipo_cidade,
            posto.op_adm,
            (
                posto.data_criacao.strftime("%Y-%m-%d %H:%M:%S")
                if posto.data_criacao
                else ""
            ),
            # Use posto.usuario.email se o seu User model usa email como USERNAME_FIELD
            # Caso contrário, use posto.usuario.get_username() ou posto.usuario.username
            (
                posto.usuario.email
                if posto.usuario and hasattr(posto.usuario, "email")
                else (posto.usuario.get_username() if posto.usuario else "")
            ),
        ]

        # Dados do Contato (se existir)
        contato = getattr(posto, "contato", None)
        if contato:
            row_data.extend(
                [
                    contato.telefone,
                    contato.rua,
                    contato.numero,
                    contato.complemento,
                    contato.bairro,
                    contato.cidade,
                    contato.cep,
                    contato.email,
                    # Garante que a longitude e latitude são formatadas como string com vírgula e citadas
                    (
                        str(contato.longitude).replace(".", ",")
                        if contato.longitude is not None
                        else ""
                    ),
                    (
                        str(contato.latitude).replace(".", ",")
                        if contato.latitude is not None
                        else ""
                    ),
                ]
            )
        else:
            row_data.extend([""] * 10)

        # Dados do Pessoal (pega o primeiro, se houver, ou agrega se a lógica for diferente)
        pessoal = posto.pessoal.first()
        if pessoal:
            row_data.extend(
                [
                    pessoal.cel,
                    pessoal.ten_cel,
                    pessoal.maj,
                    pessoal.cap,
                    pessoal.tenqo,
                    pessoal.tenqa,
                    pessoal.asp,
                    pessoal.st_sgt,
                    pessoal.cb_sd,
                    pessoal.total,
                ]
            )
        else:
            row_data.extend([""] * 10)

        writer.writerow(row_data)

    return response


@login_required
@permission_required("municipios.view_posto")  # Permissão para visualizar Posto
def exportar_relatorio_efetivo_pdf(request):
    """
    Gera um relatório PDF do efetivo, agrupado por SGB e Posto/Seção.
    Filtros: sgb (opcional), posto_secao (opcional).
    """
    # Obter filtros da requisição (GET)
    sgb_filter = request.GET.get("sgb")
    posto_secao_filter = request.GET.get("posto_secao")

    # Filtrar os Postos com base nos parâmetros
    # Pré-carrega 'pessoal' para evitar N+1 queries
    queryset = Posto.objects.all().prefetch_related("pessoal")

    if sgb_filter:
        queryset = queryset.filter(sgb=sgb_filter)
    if posto_secao_filter:
        queryset = queryset.filter(posto_secao=posto_secao_filter)

    # Agrupar os dados para o relatório
    # Vamos agrupar por SGB e depois por Posto_Seção
    # O ReportLab precisa dos dados já organizados.

    # Para calcular o efetivo_grupos e total_efetivo para cada Posto
    # e também o pessoal.total (efetivo planejado)
    # Precisamos iterar sobre o queryset e calcular esses valores.

    report_data = []
    for posto in queryset:
        # Lógica para calcular efetivo_grupos e total_efetivo (do seu posto_detail)
        # ASSUMO que 'backend.efetivo.models.DetalhesSituacao' e 'Promocao'
        # são acessíveis ou que você tem uma forma de calcular o efetivo existente.
        # Se não, os valores de 'efetivo_grupos' e 'total_efetivo' serão 0.

        # Simulação dos dados de efetivo_grupos (se não houver integração real)
        # Se você tiver a integração real com 'backend.efetivo', use-a aqui.
        efetivo_grupos = {
            "Tc": 0,
            "Maj": 0,
            "Cap": 0,
            "Ten": 0,
            "Ten_QAOPM": 0,
            "St_Sgt": 0,
            "Cb_Sd": 0,
        }
        total_efetivo_existente = 0

        # Se você tiver a lógica real de contagem do efetivo existente, coloque-a aqui.
        # Exemplo (comentado, pois depende de 'backend.efetivo'):
        # from backend.efetivo.models import DetalhesSituacao, Promocao
        # efetivos_existentes = DetalhesSituacao.objects.filter(
        #     situacao='Efetivo',
        #     posto_secao=posto.posto_secao
        # ).select_related('cadastro')
        # for ef_existente in efetivos_existentes:
        #     ultima_promocao = Promocao.objects.filter(
        #         cadastro=ef_existente.cadastro
        #     ).order_by('-ultima_promocao').first()
        #     if ultima_promocao and ultima_promocao.grupo.strip() in GRUPOS:
        #         grupo_key = ultima_promocao.grupo.strip().replace('/', '_') # Ex: St/Sgt -> St_Sgt
        #         efetivo_grupos[grupo_key] += 1
        # total_efetivo_existente = sum(efetivo_grupos.values())

        # Dados do Pessoal (efetivo planejado/QPO)
        pessoal = posto.pessoal.first()  # Pega o primeiro registro de Pessoal

        pessoal_data = {
            "cel": pessoal.cel if pessoal else 0,
            "ten_cel": pessoal.ten_cel if pessoal else 0,
            "maj": pessoal.maj if pessoal else 0,
            "cap": pessoal.cap if pessoal else 0,
            "tenqo": pessoal.tenqo if pessoal else 0,
            "tenqa": pessoal.tenqa if pessoal else 0,
            "asp": pessoal.asp if pessoal else 0,
            "st_sgt": pessoal.st_sgt if pessoal else 0,
            "cb_sd": pessoal.cb_sd if pessoal else 0,
            "total_planejado": (
                pessoal.total if pessoal else 0
            ),  # Propriedade total do modelo Pessoal
        }

        report_data.append(
            {
                "posto_obj": posto,  # O objeto Posto completo
                "efetivo_existente_grupos": efetivo_grupos,  # Efetivo real (calculado)
                "total_efetivo_existente": total_efetivo_existente,
                "pessoal_planejado": pessoal_data,  # Efetivo planejado (do modelo Pessoal)
            }
        )

    # Chamar a função de exportação PDF do export_utils.py
    pdf_buffer, filename = export_efetivo_pdf_report(
        request, report_data, sgb_filter, posto_secao_filter
    )

    response = HttpResponse(pdf_buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
