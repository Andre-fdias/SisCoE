import pandas as pd
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import DatabaseError, IntegrityError
from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from .export_utils import export_bm_data
from .models import Cadastro_bm, Imagem_bm
from django.contrib.messages import constants

from backend.core.utils import filter_by_user_sgb


@login_required
def listar_bm(request):
    cadastros = Cadastro_bm.objects.all()
    cadastros = filter_by_user_sgb(cadastros, request.user)
    return render(request, "listar_bm.html", {"cadastros": cadastros})


def ver_bm(request, pk):
    cadastro = get_object_or_404(Cadastro_bm, pk=pk)
    imagens = cadastro.imagens.all()
    context = {
        "cadastro": cadastro,
        "genero": Cadastro_bm.genero_choices,
        "ovb": Cadastro_bm.ovb_choices,
        "esb": Cadastro_bm.esb_choices,
        "sgb": Cadastro_bm.sgb_choices,
        "posto_secao": Cadastro_bm.posto_secao_choices,
        "funcao": Cadastro_bm.funcao_choices,
        "situacao": Cadastro_bm.situacao_choices,
        "alteracao": Cadastro_bm.alteracao_choices,
        "imagens": imagens,
        "cat_cnh": Cadastro_bm.cat_cnh_choices,
    }
    return render(request, "ver_bm.html", context)


@login_required
def cadastrar_bm(request):
    if request.method == "GET":
        context = {
            "genero": Cadastro_bm.genero_choices,
            "ovb": Cadastro_bm.ovb_choices,
            "esb": Cadastro_bm.esb_choices,
            "sgb": Cadastro_bm.sgb_choices,
            "posto_secao": Cadastro_bm.posto_secao_choices,
            "funcao": Cadastro_bm.funcao_choices,
            "situacao": Cadastro_bm.situacao_choices,
            "alteracao": Cadastro_bm.alteracao_choices,
            "cat_cnh": Cadastro_bm.cat_cnh_choices,
        }
        return render(request, "cadastro_bm.html", context)

    elif request.method == "POST":
        try:
            # Recupera todos os dados do POST
            nome = request.POST.get("nome")
            nome_de_guerra = request.POST.get("nome_de_guerra")
            situacao = request.POST.get("situacao")
            sgb = request.POST.get("sgb")
            posto_secao = request.POST.get("posto_secao")
            cpf = request.POST.get("cpf")
            rg = request.POST.get("rg")
            cnh = request.POST.get("cnh")  # Adicionado
            cat_cnh = request.POST.get("cat_cnh")  # Adicionado
            esb = request.POST.get("esb")
            ovb = request.POST.get("ovb")
            admissao = request.POST.get("admissao")
            nasc = request.POST.get("nasc")
            email = request.POST.get("email")
            telefone = request.POST.get("telefone")
            apresentacao_na_unidade = request.POST.get("apresentacao_na_unidade")
            saida_da_unidade = request.POST.get("saida_da_unidade")
            funcao = request.POST.get("funcao")
            genero = request.POST.get("genero")

            # Cria o objeto Cadastro_bm
            cadastro = Cadastro_bm(
                nome=nome,
                nome_de_guerra=nome_de_guerra,
                situacao=situacao,
                sgb=sgb,
                posto_secao=posto_secao,
                cpf=cpf,
                rg=rg,
                cnh=cnh,  # Adicionado
                cat_cnh=cat_cnh,  # Adicionado
                esb=esb,
                ovb=ovb,
                admissao=admissao,
                nasc=nasc,
                email=email,
                telefone=telefone,
                apresentacao_na_unidade=apresentacao_na_unidade,
                saida_da_unidade=saida_da_unidade,
                funcao=funcao,
                genero=genero,
                user=request.user,
            )
            cadastro.save()

            # Upload da imagem se existir
            if "image" in request.FILES:
                Imagem_bm.objects.create(
                    cadastro=cadastro, image=request.FILES["image"], user=request.user
                )

            messages.success(request, "Cadastro realizado com sucesso!")
            return redirect("bm:ver_bm", pk=cadastro.id)

        except Exception as e:
            messages.error(request, f"Erro ao cadastrar: {str(e)}")
            return redirect("bm:cadastrar_bm")


@login_required
def editar_bm(request, pk):
    cadastro = get_object_or_404(Cadastro_bm, pk=pk)

    if request.method == "POST":
        try:
            cadastro.nome = request.POST.get("nome")
            cadastro.nome_de_guerra = request.POST.get("nome_de_guerra")
            cadastro.situacao = request.POST.get("situacao") or request.POST.get(
                "status"
            )
            cadastro.sgb = request.POST.get("sgb")
            cadastro.posto_secao = request.POST.get("posto_secao")
            cadastro.cpf = request.POST.get("cpf")
            cadastro.rg = request.POST.get("rg")
            cadastro.esb = request.POST.get("esb")
            cadastro.ovb = request.POST.get("ovb")
            cadastro.admissao = datetime.strptime(
                request.POST.get("admissao"), "%Y-%m-%d"
            ).date()
            cadastro.nasc = datetime.strptime(
                request.POST.get("nasc"), "%Y-%m-%d"
            ).date()
            cadastro.email = request.POST.get("email")
            cadastro.telefone = request.POST.get("telefone")
            cadastro.apresentacao_na_unidade = datetime.strptime(
                request.POST.get("apresentacao_na_unidade"), "%Y-%m-%d"
            ).date()
            saida_da_unidade_str = request.POST.get("saida_da_unidade")
            if saida_da_unidade_str:
                cadastro.saida_da_unidade = datetime.strptime(
                    saida_da_unidade_str, "%Y-%m-%d"
                ).date()
            else:
                cadastro.saida_da_unidade = None
            cadastro.funcao = request.POST.get("funcao")
            cadastro.genero = request.POST.get("genero")
            cadastro.save()

            messages.add_message(
                request, constants.SUCCESS, "Cadastro atualizado com sucesso!"
            )
            return redirect("bm:ver_bm", pk=cadastro.id)

        except Exception as e:
            messages.add_message(
                request, constants.ERROR, f"Erro ao atualizar: {str(e)}"
            )

            context = {
                "cadastro": cadastro,
                "genero": Cadastro_bm.genero_choices,
                "ovb": Cadastro_bm.ovb_choices,
                "esb": Cadastro_bm.esb_choices,
                "sgb": Cadastro_bm.sgb_choices,
                "posto_secao": Cadastro_bm.posto_secao_choices,
                "funcao": Cadastro_bm.funcao_choices,
                "situacao": Cadastro_bm.situacao_choices,
                "alteracao": Cadastro_bm.alteracao_choices,
            }
            return render(request, "ver_bm.html", context)

    context = {
        "cadastro": cadastro,
        "genero": Cadastro_bm.genero_choices,
        "ovb": Cadastro_bm.ovb_choices,
        "esb": Cadastro_bm.esb_choices,
        "sgb": Cadastro_bm.sgb_choices,
        "posto_secao": Cadastro_bm.posto_secao_choices,
        "funcao": Cadastro_bm.funcao_choices,
        "situacao": Cadastro_bm.situacao_choices,
        "alteracao": Cadastro_bm.alteracao_choices,
    }
    return render(request, "ver_bm.html", context)


@login_required
def atualizar_foto(request, pk):
    cadastro = get_object_or_404(Cadastro_bm, pk=pk)

    if request.method == "POST" and "image" in request.FILES:
        try:
            # Remove imagens antigas
            cadastro.imagens.all().delete()

            # Cria nova imagem
            Imagem_bm.objects.create(
                cadastro=cadastro, image=request.FILES["image"], user=request.user
            )
            messages.add_message(
                request, constants.SUCCESS, "Foto atualizada com sucesso!"
            )
        except Exception as e:
            messages.add_message(
                request, constants.ERROR, f"Erro ao atualizar foto: {str(e)}"
            )

    return redirect("bm:ver_bm", pk=cadastro.id)


@login_required
def excluir_bm(request, pk):
    cadastro = get_object_or_404(Cadastro_bm, pk=pk)
    User = get_user_model()  # Obter o modelo de usuário personalizado

    if request.method == "POST":
        password = request.POST.get("password")
        username_field = (
            User.USERNAME_FIELD
        )  # Get the username field from the user model.
        username = getattr(request.user, username_field)  # get username value.
        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                cadastro.delete()
                messages.add_message(
                    request, constants.SUCCESS, "Cadastro excluído com sucesso!"
                )
                return redirect("bm:listar_bm")
            except DatabaseError as e:
                messages.add_message(
                    request,
                    constants.ERROR,
                    f"Erro no banco de dados ao excluir cadastro: {e}",
                )
                return redirect("bm:detalhes_bm", pk=pk)
            except IntegrityError as e:
                messages.add_message(
                    request,
                    constants.ERROR,
                    f"Erro de integridade ao excluir cadastro: {e}",
                )
                return redirect("bm:detalhes_bm", pk=pk)
            except Exception as e:
                messages.add_message(
                    request,
                    constants.ERROR,
                    f"Erro inesperado ao excluir cadastro: {e}",
                )
                return redirect("bm:detalhes_bm", pk=pk)
        else:
            messages.add_message(request, constants.ERROR, "Senha incorreta")
            return render(request, "confirmar_exclusao.html", {"cadastro": cadastro})

    return render(request, "confirmar_exclusao.html", {"cadastro": cadastro})


from django.contrib.auth.decorators import login_required


@login_required
@user_passes_test(lambda u: u.is_superuser)
def importar_bm(request):
    if request.method == "POST" and request.FILES.get("arquivo"):
        arquivo = request.FILES["arquivo"]
        extensao = arquivo.name.split(".")[-1].lower()

        try:
            # ========= VALIDAÇÃO INICIAL =========
            # Verificar tamanho do arquivo (5MB máximo)
            if arquivo.size > 5 * 1024 * 1024:
                messages.error(request, "Arquivo muito grande (máximo 5MB).")
                return redirect("bm:importar_bm")

            # ========= LEITURA DO ARQUIVO =========
            # Ler CSV/Excel sem converter "N/A" para NaN
            if extensao == "csv":
                df = pd.read_csv(
                    arquivo,
                    sep=";",
                    encoding="utf-8-sig",
                    dtype=str,
                    keep_default_na=False,
                    na_filter=False,
                )
            elif extensao in ["xls", "xlsx"]:
                df = pd.read_excel(
                    arquivo, dtype=str, keep_default_na=False, na_values=[]
                )
            else:
                messages.error(request, "Formato inválido (use CSV ou Excel).")
                return redirect("bm:importar_bm")

            # ========= COLUNAS OBRIGATÓRIAS =========
            colunas_obrigatorias = {
                "nome",
                "nome_de_guerra",
                "cpf",
                "rg",
                "admissao",
                "nasc",
                "apresentacao_na_unidade",
                "posto_secao",
                "sgb",
            }

            # Verificar se todas as colunas obrigatórias existem
            if missing := colunas_obrigatorias - set(df.columns):
                messages.error(request, f'Colunas faltando: {", ".join(missing)}')
                return redirect("bm:importar_bm")

            # ========= PRÉ-VALIDAÇÃO POR LINHA =========
            erros_pre_validacao = []
            for index, row in df.iterrows():
                try:
                    # Ignorar linhas totalmente vazias
                    if all(str(v).strip() in ["", "nan", "N/A"] for v in row):
                        continue

                    # Validar campos obrigatórios brutos (sem substituir N/A)
                    for campo in colunas_obrigatorias:
                        valor = str(row.get(campo, "")).strip()
                        if valor in ["", "nan", "N/A"]:
                            raise ValueError(
                                f'Campo "{campo}" está vazio ou é inválido'
                            )

                except Exception as e:
                    erros_pre_validacao.append(f"Linha {index + 2}: {str(e)}")

            if erros_pre_validacao:
                erros_msg = f'Erros críticos: {", ".join(erros_pre_validacao[:3])}... (total: {len(erros_pre_validacao)})'
                messages.error(request, erros_msg)
                return redirect("bm:importar_bm")

            # ========= TRATAMENTO DE VALORES VAZIOS =========
            # Substituir vazios por N/A apenas em campos NÃO obrigatórios
            campos_nao_obrigatorios = list(set(df.columns) - colunas_obrigatorias)
            df[campos_nao_obrigatorios] = df[campos_nao_obrigatorios].replace(
                ["", None, "nan"], "N/A"
            )

            # ========= PROCESSAMENTO DAS LINHAS =========
            registros_processados = 0
            registros_ignorados = 0
            erros_processamento = []

            def converter_data(valor, field_name):
                valor = str(valor).strip()
                if valor == "N/A":
                    raise ValueError(f'Campo "{field_name}" não pode ser N/A')

                # Converter datas do Excel (timestamp)
                if valor.replace(".", "").isdigit():
                    try:
                        return (
                            datetime(1899, 12, 30) + timedelta(days=float(valor))
                        ).date()
                    except:
                        pass

                # Converter strings
                formatos = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
                for fmt in formatos:
                    try:
                        return datetime.strptime(valor, fmt).date()
                    except:
                        continue
                raise ValueError(f'Formato de data inválido: "{valor}"')

            for index, row in df.iterrows():
                try:
                    # Ignorar linhas totalmente inválidas
                    if all(str(v) == "N/A" for v in row):
                        continue

                    # Validar CPF
                    cpf = str(row["cpf"]).strip().zfill(11)
                    if len(cpf) != 11 or not cpf.isdigit():
                        raise ValueError(f"CPF inválido: {cpf}")

                    # Verificar duplicidade
                    if Cadastro_bm.objects.filter(cpf=cpf).exists():
                        registros_ignorados += 1
                        continue

                    # Converter datas obrigatórias
                    admissao = converter_data(row["admissao"], "admissao")
                    nasc = converter_data(row["nasc"], "nasc")
                    apresentacao = converter_data(
                        row["apresentacao_na_unidade"], "apresentacao_na_unidade"
                    )

                    # Tratar data de saída (opcional)
                    saida = None
                    if str(row.get("saida_da_unidade", "N/A")) != "N/A":
                        saida = converter_data(
                            row["saida_da_unidade"], "saida_da_unidade"
                        )

                    # Criar registro no banco de dados
                    Cadastro_bm.objects.create(
                        nome=row["nome"].strip(),
                        nome_de_guerra=row["nome_de_guerra"].strip(),
                        situacao=row.get("situacao", "Efetivo").strip(),
                        sgb=row["sgb"].strip(),
                        posto_secao=row["posto_secao"].strip(),
                        cpf=cpf,
                        rg=row["rg"].strip(),
                        cnh=row.get("cnh", "N/A").strip(),
                        cat_cnh=row.get("cat_cnh", "N/A").strip(),
                        esb=row.get("esb", "NÃO").strip(),
                        ovb=row.get("ovb", "NÃO POSSUI").strip(),
                        admissao=admissao,
                        nasc=nasc,
                        email=row.get("email", "N/A").strip(),
                        telefone=row.get("telefone", "N/A").strip(),
                        apresentacao_na_unidade=apresentacao,
                        saida_da_unidade=saida,
                        funcao=row.get("funcao", "N/A").strip(),
                        genero=row.get("genero", "Masculino").strip(),
                        user=request.user,
                    )
                    registros_processados += 1

                except Exception as e:
                    erros_processamento.append(f"Linha {index + 2}: {str(e)}")
                    continue

            # ========= FEEDBACK FINAL =========
            if registros_processados > 0:
                msg = f"✅ {registros_processados} registros importados com sucesso!"
                if registros_ignorados > 0:
                    msg += f" ⚠️ {registros_ignorados} CPFs duplicados ignorados."
                messages.success(request, msg)

            if erros_processamento:
                erros_msg = f"⚠️ {len(erros_processamento)} erro(s): " + ", ".join(
                    erros_processamento[:3]
                )
                if len(erros_processamento) > 3:
                    erros_msg += f" (...mais {len(erros_processamento)-3})"
                messages.warning(request, erros_msg)

            return redirect("bm:listar_bm")

        except Exception as e:
            messages.error(request, f"❌ Falha na importação: {str(e)}")
            return redirect("bm:importar_bm")

    return render(request, "importar_bm.html")


def exportar_bm(request):
    if request.method == "POST":
        format_type = request.POST.get("export_format")
        if not format_type:
            return HttpResponseBadRequest("Formato de exportação não especificado")

        queryset = Cadastro_bm.objects.all()
        return export_bm_data(request, queryset, format_type)

    return HttpResponseBadRequest("Método não permitido")
