# Bibliotecas padrão
import json
import logging
import sys
from datetime import datetime  # Importar date também
import random
from faker import Faker
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError, transaction
from django.db.models import OuterRef, Prefetch, Q, Subquery
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from django.utils.decorators import method_decorator  # IMPORTAÇÃO ADICIONADA AQUI
from django.views import View  # IMPORTAÇÃO ADICIONADA AQUI

# Django authentication
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model  # Importar o modelo de usuário
from backend.accounts.decorators import (
    permissao_necessaria,
    apply_model_permissions_filter,
)

# Staticfiles finder
from django.contrib.staticfiles import finders
from django.contrib.messages import (
    constants,
)  # <--- ADICIONADO: Importa as constantes de mensagens


# Modelos locais
from .models import (
    Cadastro,
    CatEfetivo,
    DetalhesSituacao,
    HistoricoCatEfetivo,
    HistoricoDetalhesSituacao,
    HistoricoPromocao,
    Imagem,
    Promocao,
)

# Modelos de outros apps

from backend.cursos.models import Curso, Medalha
from backend.municipios.models import Posto
from backend.rpt.models import Cadastro_rpt
from backend.lp.models import LP, LP_fruicao

# ReportLab para PDF
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    Frame,
    PageTemplate,
)

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus.doctemplate import PageTemplate

import os
from backend.core.utils import filter_by_user_sgb
from backend.core.monitoring_decorators import track_function_latency


# Configuração de logging
logger = logging.getLogger(__name__)

User = get_user_model()  # Obtém o modelo de usuário ativo

# Adicionado para gerar imagens fake
from PIL import Image as PILImage, ImageDraw, ImageFont
from io import BytesIO

def generate_fake_image(text="Sample Text", width=150, height=150):
    """Gera uma imagem falsa com texto para fins de teste."""
    img = PILImage.new('RGB', (width, height), color = (128, 128, 128))
    d = ImageDraw.Draw(img)
    
    # Tenta usar uma fonte padrão, se não, usa a fonte default do Pillow
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font = ImageFont.load_default()
        
    d.text((10,10), text, fill=(255,255,0), font=font)
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@login_required
@permissao_necessaria(
    level="gestor", redirect_url="accounts:acesso_negado"
)  # Garante o nível de acesso à view
def cadastrar_militar(request):
    if request.method == "GET":
        context = {
            "posto_grad": Promocao.posto_grad_choices,
            "quadro": Promocao.quadro_choices,
            "grupo": Promocao.grupo_choices,
            "sgb": DetalhesSituacao.sgb_choices,
            "posto_secao": DetalhesSituacao.posto_secao_choices,
            "esta_adido": DetalhesSituacao.esta_adido_choices,
            "funcao": DetalhesSituacao.funcao_choices,
            "op_adm": DetalhesSituacao.op_adm_choices,
            "prontidao": DetalhesSituacao.prontidao_choices,
            "genero": Cadastro.genero_choices,
            "situacao": DetalhesSituacao.situacao_choices,
            "alteracao": Cadastro.alteracao_choices,
        }
        return render(request, "cadastrar_militar.html", context)

    elif request.method == "POST":
        cpf = request.POST.get("cpf")
        if Cadastro.objects.filter(cpf=cpf).exists():
            messages.error(
                request,
                "Erro: CPF já cadastrado.",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )
            return redirect("/efetivo/cadastrar_militar")

        try:
            with transaction.atomic():
                # Criar cadastro básico
                cadastro = Cadastro(
                    re=request.POST.get("re"),
                    dig=request.POST.get("dig"),
                    nome=request.POST.get("nome"),
                    nome_de_guerra=request.POST.get("nome_de_guerra"),
                    genero=request.POST.get("genero"),
                    nasc=request.POST.get("nasc"),
                    matricula=request.POST.get("matricula"),
                    admissao=request.POST.get("admissao"),
                    previsao_de_inatividade=request.POST.get("previsao_de_inatividade"),
                    cpf=cpf,
                    rg=request.POST.get("rg"),
                    tempo_para_averbar_inss=request.POST.get("tempo_para_averbar_inss"),
                    tempo_para_averbar_militar=request.POST.get(
                        "tempo_para_averbar_militar"
                    ),
                    email=request.POST.get("email"),
                    telefone=request.POST.get("telefone"),
                    alteracao=request.POST.get("alteracao"),
                    user=request.user,
                )
                cadastro.save()
                print(f"Cadastro básico salvo com sucesso - ID: {cadastro.id}")

                # Salvar imagem se existir
                if request.FILES.get("image"):
                    imagem = Imagem.objects.create(
                        cadastro=cadastro,
                        image=request.FILES.get("image"),
                        user=request.user,
                    )
                    print(f"Imagem salva com sucesso - ID: {imagem.id}")

                # Criar situação funcional
                apresentacao_na_unidade = request.POST.get("apresentacao_na_unidade")
                detalhes = DetalhesSituacao(
                    cadastro=cadastro,
                    situacao=request.POST.get("situacao", "Efetivo"),
                    sgb=request.POST.get("sgb"),
                    posto_secao=request.POST.get("posto_secao"),
                    esta_adido=request.POST.get("esta_adido"),
                    funcao=request.POST.get("funcao"),
                    op_adm=request.POST.get("op_adm"),
                    prontidao=request.POST.get("prontidao"),
                    apresentacao_na_unidade=apresentacao_na_unidade,
                    saida_da_unidade=request.POST.get("saida_da_unidade"),
                    usuario_alteracao=request.user,
                )
                detalhes.save()
                print(f"DetalhesSituacao salvo com sucesso - ID: {detalhes.id}")

                # Criar promoção
                promocao = Promocao(
                    cadastro=cadastro,
                    posto_grad=request.POST.get("posto_grad"),
                    quadro=request.POST.get("quadro"),
                    grupo=request.POST.get("grupo"),
                    ultima_promocao=request.POST.get("ultima_promocao"),
                    usuario_alteracao=request.user,
                )
                promocao.save()
                print(f"Promoção salva com sucesso - ID: {promocao.id}")

                # Criar categoria de efetivo
                cat_efetivo = CatEfetivo.objects.create(
                    cadastro=cadastro,
                    tipo="ATIVO",  # Sempre ATIVO no cadastro inicial
                    data_inicio=apresentacao_na_unidade,
                    usuario_cadastro=request.user,
                    ativo=True,
                )
                print(f"CatEfetivo salvo com sucesso - ID: {cat_efetivo.id}")

                messages.success(
                    request,
                    "Militar cadastrado com sucesso",
                    extra_tags="bg-green-500 text-white p-4 rounded",
                )
                return redirect("/efetivo/cadastrar_militar")

        except IntegrityError as e:
            print(f"Erro de integridade: {str(e)}", file=sys.stderr)
            messages.error(
                request,
                f"Erro: Dados inválidos ou duplicados. Detalhes: {str(e)}",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )
        except Exception as e:
            print(f"Erro geral: {str(e)}", file=sys.stderr)
            messages.error(
                request,
                f"Erro ao cadastrar militar: {str(e)}",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )

        return redirect("/efetivo/cadastrar_militar")


def gerar_cadastros_fake(request):
    logger.info("Requisição para gerar cadastros fake recebida.")

    if not request.user.is_superuser:
        logger.warning(f"Tentativa de acesso negado para gerar cadastros fake por: {str(request.user)}")
        return JsonResponse(
            {"status": "error", "message": "Acesso negado. Apenas superusuários podem gerar cadastros fake."},
            status=403,
        )

    try:
        data = json.loads(request.body)
        quantidade = int(data.get('quantidade', 1))
        if not 1 <= quantidade <= 500:
            raise ValueError("A quantidade deve estar entre 1 e 500.")
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error(f"Erro ao processar a quantidade de cadastros: {e}")
        return JsonResponse(
            {"status": "error", "message": f"Quantidade inválida. Forneça um número entre 1 e 500. Erro: {e}"},
            status=400,
        )

    fake = Faker("pt_BR")
    fake.unique.clear()  # Limpa o cache de valores únicos no início
    cadastros_criados = 0
    erros = 0

    for i in range(quantidade):
        try:
            # Cada militar é criado em sua própria transação para isolar falhas
            with transaction.atomic():
                # 1. Criar Cadastro
                sexo_fake = random.choice([choice[0] for choice in Cadastro.genero_choices if choice[0]])
                data_nascimento_fake = fake.date_of_birth(minimum_age=18, maximum_age=60)
                data_ingresso_fake = fake.date_between(start_date="-20y", end_date="-5y")
                # Corrigido: A matrícula deve ser uma data, não um objeto datetime
                matricula_fake = fake.date_between(start_date=data_ingresso_fake, end_date="today")
                previsao_inatividade_fake = fake.date_between(start_date="today", end_date="+30y")

                cadastro = Cadastro.objects.create(
                    re=str(fake.unique.random_number(digits=6)),
                    dig=str(random.randint(0, 9)),
                    nome=fake.name(),
                    nome_de_guerra=fake.first_name(),
                    genero=sexo_fake,
                    nasc=data_nascimento_fake,
                    matricula=matricula_fake,
                    admissao=data_ingresso_fake,
                    previsao_de_inatividade=previsao_inatividade_fake,
                    cpf=fake.cpf(),
                    rg=str(fake.unique.random_number(digits=9)),
                    tempo_para_averbar_inss=random.randint(0, 100),
                    tempo_para_averbar_militar=random.randint(0, 100),
                    email=fake.unique.email(),
                    telefone=fake.phone_number(),
                    alteracao=random.choice([choice[0] for choice in Cadastro.alteracao_choices if choice[0]]),
                    user=request.user,
                )

                # 2. Criar Promocao
                posto_grad_fake = random.choice([choice[0] for choice in Promocao.posto_grad_choices if choice[0]])
                quadro_fake = random.choice([choice[0] for choice in Promocao.quadro_choices if choice[0]])
                grupo_fake = random.choice([choice[0] for choice in Promocao.grupo_choices if choice[0]])
                data_promocao_fake = fake.date_between(start_date=cadastro.admissao, end_date="today")

                Promocao.objects.create(
                    cadastro=cadastro,
                    posto_grad=posto_grad_fake,
                    quadro=quadro_fake,
                    grupo=grupo_fake,
                    ultima_promocao=data_promocao_fake,
                    usuario_alteracao=request.user,
                )

                # 3. Criar DetalhesSituacao
                sgb_fake = random.choice([choice[0] for choice in DetalhesSituacao.sgb_choices if choice[0]])
                posto_secao_fake = random.choice([choice[0] for choice in DetalhesSituacao.posto_secao_choices if choice[0]])
                esta_adido_fake = random.choice([choice[0] for choice in DetalhesSituacao.esta_adido_choices if choice[0]])
                funcao_fake = random.choice([choice[0] for choice in DetalhesSituacao.funcao_choices if choice[0]])
                op_adm_fake = random.choice([choice[0] for choice in DetalhesSituacao.op_adm_choices if choice[0]])
                prontidao_fake = random.choice([choice[0] for choice in DetalhesSituacao.prontidao_choices if choice[0]])
                apresentacao_unidade_fake = fake.date_between(start_date="-5y", end_date="today")
                saida_unidade_fake = fake.date_between(start_date=apresentacao_unidade_fake, end_date="+1y") if random.choice([True, False]) else None

                DetalhesSituacao.objects.create(
                    cadastro=cadastro,
                    situacao="Efetivo",
                    sgb=sgb_fake,
                    posto_secao=posto_secao_fake,
                    esta_adido=esta_adido_fake,
                    funcao=funcao_fake,
                    op_adm=op_adm_fake,
                    prontidao=prontidao_fake,
                    apresentacao_na_unidade=apresentacao_unidade_fake,
                    saida_da_unidade=saida_unidade_fake,
                    usuario_alteracao=request.user,
                )

                # 4. Criar CatEfetivo
                data_inicio_cat_fake = fake.date_between(start_date="-2y", end_date="today")
                data_termino_cat_fake = fake.date_between(start_date="today", end_date="+1y") if random.choice([True, False]) else None

                CatEfetivo.objects.create(
                    cadastro=cadastro,
                    tipo="ATIVO",
                    data_inicio=data_inicio_cat_fake,
                    data_termino=data_termino_cat_fake,
                    usuario_cadastro=request.user,
                    ativo=True,
                    observacao=fake.sentence(),
                )

                # 5. Gerar e Salvar Imagem
                fake_image_data = generate_fake_image(text=f"{cadastro.nome_de_guerra}\nRE: {cadastro.re}")
                image_name = f"fake_militar_{cadastro.re}.png"
                img_obj = Imagem(cadastro=cadastro, user=request.user)
                img_obj.image.save(image_name, ContentFile(fake_image_data), save=True)

            # Se a transação foi bem-sucedida, incrementa o contador
            cadastros_criados += 1
            logger.debug(f"Sucesso na criação do cadastro {i+1}/{quantidade} para o militar: {cadastro.nome}")

        except IntegrityError as e:
            logger.warning(f"Erro de integridade na tentativa {i+1}/{quantidade}: {e}. Pulando.")
            erros += 1
            fake.unique.clear()  # Limpa o cache de unicidade para a próxima iteração
            continue
        except Exception as e:
            logger.error(f"Erro inesperado na tentativa {i+1}/{quantidade}: {e}", exc_info=True)
            erros += 1
            continue

    message = f"{cadastros_criados} de {quantidade} cadastros fakes gerados com sucesso."
    if erros > 0:
        message += f" {erros} tentativas falharam devido a erros."

    logger.info(message)
    return JsonResponse({"status": "success", "message": message})

@login_required
@permissao_necessaria(level="sgb", redirect_url="accounts:acesso_negado")
@apply_model_permissions_filter(Cadastro)
def listar_militar(request):
    if request.method == "GET":
        latest_detalhe_situacao = DetalhesSituacao.objects.filter(
            cadastro=OuterRef("pk")
        ).order_by("-data_alteracao", "-id")

        cadastros = Cadastro.objects.annotate(
            latest_status=Subquery(latest_detalhe_situacao.values("situacao")[:1]),
            latest_sgb=Subquery(latest_detalhe_situacao.values("sgb")[:1]),
            latest_posto_secao=Subquery(
                latest_detalhe_situacao.values("posto_secao")[:1]
            ),
            latest_prontidao=Subquery(latest_detalhe_situacao.values("prontidao")[:1]),
            latest_saida_da_unidade=Subquery(
                latest_detalhe_situacao.values("saida_da_unidade")[:1]
            ),
        ).filter(latest_status="Efetivo")

        cadastros = filter_by_user_sgb(cadastros, request.user)

        cadastros = (
            cadastros.prefetch_related(
                Prefetch(
                    "categorias_efetivo",
                    queryset=CatEfetivo.objects.filter(ativo=True),
                    to_attr="categorias_ativas",
                ),
                "imagens",
                "promocoes",
            )
            .annotate(
                latest_posto_grad=Subquery(
                    Promocao.objects.filter(cadastro=OuterRef("pk"))
                    .order_by("-ultima_promocao")
                    .values("posto_grad")[:1]
                )
            )
            .order_by("latest_posto_grad", "nome_de_guerra")
        )

        context = {"cadastros": cadastros, "current_date": timezone.now().date()}
        return render(request, "listar_militar.html", context)


@login_required
def listar_outros_status_militar(request):
    if request.method == "GET":
        latest_detalhe_situacao = DetalhesSituacao.objects.filter(
            cadastro=OuterRef("pk")
        ).order_by("-data_alteracao", "-id")

        cadastros = (
            Cadastro.objects.annotate(
                latest_status=Subquery(latest_detalhe_situacao.values("situacao")[:1]),
                latest_sgb=Subquery(latest_detalhe_situacao.values("sgb")[:1]),
                latest_posto_secao=Subquery(
                    latest_detalhe_situacao.values("posto_secao")[:1]
                ),
                latest_prontidao=Subquery(
                    latest_detalhe_situacao.values("prontidao")[:1]
                ),
                latest_saida_da_unidade=Subquery(
                    latest_detalhe_situacao.values("saida_da_unidade")[:1]
                ),
            )
            .exclude(latest_status="Efetivo")
            .filter(latest_status__isnull=False)
        )

        cadastros = filter_by_user_sgb(cadastros, request.user)

        cadastros = (
            cadastros.prefetch_related(
                Prefetch(
                    "categorias_efetivo",
                    queryset=CatEfetivo.objects.filter(ativo=True),
                    to_attr="categorias_ativas",
                ),
                "imagens",
                "promocoes",
            )
            .annotate(
                latest_posto_grad=Subquery(
                    Promocao.objects.filter(cadastro=OuterRef("pk"))
                    .order_by("-ultima_promocao")
                    .values("posto_grad")[:1]
                )
            )
            .order_by("latest_posto_grad", "nome_de_guerra")
        )

        context = {"cadastros": cadastros, "current_date": timezone.now().date()}
        return render(request, "listar_outros_status.html", context)


# --- View para controlar afastamentos" ---
class RestricaoHelper:
    @staticmethod
    def get_regra_principal(sigla):
        regras_map = {
            # Grupo 5.2.1
            "BS": "5.2.1",
            "CI": "5.2.1",
            "DV": "5.2.1",
            "EF": "5.2.1",
            "FO": "5.2.1",
            "IS": "5.2.1",
            "LP": "5.2.1",
            "MA": "5.2.1",
            "MC": "5.2.1",
            "MG": "5.2.1",
            "OU": "5.2.1",
            "PO": "5.2.1",
            "PQ": "5.2.1",
            "SA": "5.2.1",
            "SE": "5.2.1",
            "SH": "5.2.1",
            "SM": "5.2.1",
            "SP": "5.2.1",
            # Grupo 5.2.2
            "AU": "5.2.2",
            "EP": "5.2.2",
            "ES": "5.2.2",
            "LR": "5.2.2",
            "PT": "5.2.2",
            "VP": "5.2.2",
            # Demais grupos
            "SN": "5.2.3",
            "SG": "5.2.4",
            "UA": "5.2.5",
            "UU": "5.2.6",
            "CC": "5.2.6",
            "CB": "5.2.6",
            "UB": "5.2.7",
            "UC": "5.2.7",
            "US": "5.2.7",
            "DG": "5.2.8",
            "EM": "5.2.8",
            "LS": "5.2.8",
            "MP": "5.2.8",
            "SB": "5.2.8",
            "SI": "5.2.8",
            "ST": "5.2.8",
        }
        return regras_map.get(sigla, "")


# --- View para Detalhar militares" ---
@login_required
@permissao_necessaria(level="sgb")
def ver_militar(request, id):
    try:
        if not id:
            messages.error(
                request, "ID inválido", extra_tags="bg-red-500 text-white p-4 rounded"
            )
            return redirect("efetivo:listar_militar")

        # Obter o cadastro principal com related objects
        cadastro = (
            Cadastro.objects.select_related("user")
            .prefetch_related(
                "imagens",
                "promocoes",
                "detalhes_situacao",
                "categorias_efetivo",
                "cadastro_rpt",
                "lp_set",  # Adicionado para otimizar consulta de LPs
            )
            .get(id=id)
        )

        today = timezone.now().date()
        detalhes = cadastro.detalhes_situacao.order_by("-data_alteracao", "-id").first()
        promocao = cadastro.promocoes.last()
        categoria_atual = cadastro.categorias_efetivo.filter(ativo=True).first()

        # Buscar LPs concluídas do militar
        lps_concluidas = cadastro.lp_set.filter(
            status_lp=LP.StatusLP.CONCLUIDO
        ).order_by("numero_lp")

        # Para cada LP, tentar obter a fruição associada
        for lp in lps_concluidas:
            try:
                lp.previsao_associada = LP_fruicao.objects.get(lp_concluida=lp)
            except LP_fruicao.DoesNotExist:
                lp.previsao_associada = None

        # Verificar se existe alguma restrição ativa para o militar
        tem_restricao_ativa = cadastro.categorias_efetivo.filter(tipo='RESTRICAO', ativo=True).exists()

        # Processar Restrições
        MENSAGENS_RESTRICOES = {
            "BS": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "CI": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "DV": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "EF": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio. As OPM estabelecerão plano de exercícios físicos compatíveis.",
            "FO": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "IS": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "LP": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "MA": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "MC": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "MG": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "OU": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "PO": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "PQ": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "SA": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "SE": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "SH": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "SM": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "SP": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "AU": "Deverá ser empregado somente em atividades administrativas.",
            "EP": "Deverá ser empregado somente em atividades administrativas.",
            "ES": "Deverá ser empregado somente em atividades administrativas.",
            "LR": "Deverá ser empregado somente em atividades administrativas.",
            "PT": "Deverá ser empregado somente em atividades administrativas.",
            "VP": "Deverá ser empregado somente em atividades administrativas.",
            "SN": "Deverá ser escalado para trabalhar durante o dia em qualquer atividade.",
            "SG": "Deverá ser empregado, preferencialmente, na atividade de policiamento ostensivo, ou, caso não seja possível, em atividades administrativas e de apoio.",
            "UA": "Deverá ser desarmado e empregado em atividades administrativas. Pode requerer processo administrativo para verificar condições de permanência no serviço ativo.",
            "UU": "Deverá ser escalado em atividades administrativas ou de apoio, com uniforme de treinamento físico (B-5.1), sem atendimento ao público.",
            "CC": "Deverá ser escalado em atividades administrativas ou de apoio, com uniforme de treinamento físico (B-5.1), sem atendimento ao público. Cabelos penteados com gel/rede obrigatoriamente.",
            "CB": "Deverá ser escalado em atividades administrativas ou de apoio, com uniforme de treinamento físico (B-5.1), sem atendimento ao público.",
            "UB": "Deverá calçar sandálias de borracha na cor preta, sem estampas, e ser escalado em atividades administrativas ou de apoio.",
            "UC": "Deverá calçar sandálias de borracha na cor preta, sem estampas, e ser escalado em atividades administrativas ou de apoio.",
            "US": "Deverá calçar sandálias de borracha na cor preta, sem estampas, e ser escalado em atividades administrativas ou de apoio.",
            "DG": "Deverá ser empregado no policiamento ostensivo.",
            "EM": "Deverá ser empregado no policiamento ostensivo.",
            "LS": "Deverá ser empregado no policiamento ostensivo.",
            "MP": "Deverá ser empregado no policiamento ostensivo.",
            "SB": "Deverá ser empregado no policiamento ostensivo.",
            "SI": "Deverá ser empregado no policiamento ostensivo.",
            "ST": "Deverá ser empregado no policiamento ostensivo.",
        }

        restricoes_aplicaveis = []
        restricoes_siglas = set() # Para armazenar siglas únicas e verificar 'UA'
        for categoria_restricao in cadastro.categorias_efetivo.filter(tipo='RESTRICAO', ativo=True):
            for field in CatEfetivo._meta.get_fields():
                if field.name.startswith("restricao_") and getattr(
                    categoria_restricao, field.name
                ):
                    sigla = field.name.split("_")[-1].upper()
                    if sigla in MENSAGENS_RESTRICOES:
                        restricoes_aplicaveis.append(
                            {
                                "sigla": sigla,
                                "nome": field.verbose_name,
                                "mensagem": MENSAGENS_RESTRICOES[sigla],
                                "regra": RestricaoHelper.get_regra_principal(sigla),
                            }
                        )
                        restricoes_siglas.add(sigla) # Adicionar a sigla ao conjunto


        # Status da Categoria
        categoria_status = {}
        if categoria_atual:
            if (
                categoria_atual.tipo != "ATIVO"
                and categoria_atual.data_termino
                and categoria_atual.data_termino < today
            ):
                categoria_status = {
                    "texto": f"{categoria_atual.get_tipo_display()} (Expirado)",
                    "classe": "bg-red-100 text-red-800",
                    "icone": "fa-exclamation-triangle",
                }
            elif categoria_atual.tipo != "ATIVO":
                categoria_status = {
                    "texto": f"{categoria_atual.get_tipo_display()} (Até {categoria_atual.data_termino.strftime('%d/%m/%Y') if categoria_atual.data_termino else 'Indefinido'})",
                    "classe": "bg-yellow-100 text-yellow-800",
                    "icone": "fa-info-circle",
                }
            else:
                categoria_status = {
                    "texto": categoria_atual.get_tipo_display(),
                    "classe": "bg-green-100 text-green-800",
                    "icone": "fa-check-circle",
                }
            categoria_atual.status_display = categoria_status

        # Lógica para cursos especiais
        cursos_especiais = []
        if detalhes and detalhes.op_adm:
            tag_desejada = (
                "Administrativo"
                if detalhes.op_adm == "Administrativo"
                else "Operacional"
            )

            # Filtra os cursos usando o mapeamento de tags
            cursos_filtrados = []
            for curso in Curso.objects.filter(cadastro=cadastro):
                if Curso.CURSOS_TAGS.get(curso.curso) == tag_desejada:
                    cursos_filtrados.append(curso.get_curso_display())

            # Remove duplicatas mantendo a ordem
            cursos_especiais = list(dict.fromkeys(cursos_filtrados))

        # Dados relacionados
        medalhas_do_militar = Medalha.objects.filter(cadastro=cadastro).order_by(
            "-data_publicacao_lp"
        )
        cursos_do_militar = Curso.objects.filter(cadastro=cadastro).order_by(
            "-data_publicacao"
        )

        # Dados RPT
        cadastro_rpt = cadastro.cadastro_rpt.first()
        count_in_section = (
            Cadastro_rpt.objects.filter(
                posto_secao_destino=cadastro_rpt.posto_secao_destino,
                status="Aguardando",
            ).count()
            if cadastro_rpt
            else 0
        )

        context = {
            "cadastro": cadastro,
            "detalhes": detalhes,
            "promocao": promocao,
            "today": today,
            "categoria_atual": categoria_atual,
            "restricoes_aplicaveis": restricoes_aplicaveis,
            "restricoes_siglas": list(restricoes_siglas),
            "tem_restricao_ativa": tem_restricao_ativa,
            "medalhas_do_militar": medalhas_do_militar,
            "cursos_do_militar": cursos_do_militar,
            "cadastro_rpt": cadastro_rpt,
            "count_in_section": count_in_section,
            "cursos_especiais": cursos_especiais,
            "lps_concluidas": lps_concluidas,  # Novo item no contexto
            # Choices
            "situacao_choices": DetalhesSituacao.situacao_choices,
            "sgb_choices": DetalhesSituacao.sgb_choices,
            "posto_secao_choices": DetalhesSituacao.posto_secao_choices,
            "esta_adido_choices": DetalhesSituacao.esta_adido_choices,
            "funcao_choices": DetalhesSituacao.funcao_choices,
            "op_adm_choices": DetalhesSituacao.op_adm_choices,
            "prontidao_choices": DetalhesSituacao.prontidao_choices,
            "posto_grad_choices": Promocao.posto_grad_choices,
            "quadro_choices": Promocao.quadro_choices,
            "grupo_choices": Promocao.grupo_choices,
            "genero_choices": Cadastro.genero_choices,
            "alteracao_choices": Cadastro.alteracao_choices,
            "categoria_choices": CatEfetivo.TIPO_CHOICES,
        }

        return render(request, "ver_militar.html", context)

    except Cadastro.DoesNotExist:
        messages.error(
            request,
            "Militar não encontrado",
            extra_tags="bg-red-500 text-white p-4 rounded",
        )
        return redirect("efetivo:listar_militar")

    except Exception as e:
        logger.error(f"Erro ao acessar militar ID {id}: {str(e)}")
        messages.error(
            request,
            "Erro interno ao carregar os dados",
            extra_tags="bg-red-500 text-white p-4 rounded",
        )
        return redirect("efetivo:listar_militar")


# --- View para excluir militares" ---
@login_required
def excluir_militar(request, id):
    if request.method == "POST":
        try:
            # Obter objetos relevantes
            cadastro = Cadastro.objects.get(id=id)
            current_user = request.user

            # Verificar senha
            password = request.POST.get("password", "")
            if not check_password(password, current_user.password):
                messages.add_message(
                    request,
                    constants.ERROR,
                    "Senha incorreta! Operação cancelada.",
                    extra_tags="bg-red-500 text-white p-4 rounded delete_error",
                )  # Adicione 'delete_error'
                return redirect("efetivo:ver_militar", id=id)

            # Realizar exclusão
            cadastro.delete()
            messages.add_message(
                request,
                constants.SUCCESS,
                "Cadastro excluído com sucesso.",
                extra_tags="bg-green-500 text-white p-4 rounded",
            )
            return redirect("efetivo:listar_militar")

        except Cadastro.DoesNotExist:
            messages.add_message(
                request,
                constants.ERROR,
                "Militar não encontrado!.",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )
            return redirect("efetivo:listar_militar")
        except Exception as e:
            messages.add_message(
                request,
                constants.ERROR,
                f"Erro ao excluir: {str(e)}",
                extra_tags="bg-red-500 text-white p-4 rounded delete_error",
            )  # Adicione 'delete_error'
            return redirect("efetivo:ver_militar", id=id)

    return redirect("efetivo:listar_militar")


# responsável pela edição da model promoções
@login_required
def editar_posto_graduacao(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)
    promocao_atual = cadastro.promocoes.last()

    if request.method == "GET":
        return render(
            request,
            "editar_posto_graduacao.html",
            {
                "cadastro": cadastro,
                "promocao": promocao_atual,
                "posto_grad": Promocao.posto_grad_choices,
                "quadro": Promocao.quadro_choices,
                "grupo": Promocao.grupo_choices,
            },
        )

    elif request.method == "POST":
        ultima_promocao = request.POST.get("ultima_promocao")
        posto_grad = request.POST.get("posto_grad")
        quadro = request.POST.get("quadro")
        grupo = request.POST.get("grupo")

        if not ultima_promocao:
            return redirect("editar_posto_graduacao", id=cadastro.id)

        if promocao_atual:
            HistoricoPromocao.objects.create(
                cadastro=cadastro,
                posto_grad=promocao_atual.posto_grad,
                quadro=promocao_atual.quadro,
                grupo=promocao_atual.grupo,
                ultima_promocao=promocao_atual.ultima_promocao,
                usuario_alteracao=request.user,
                data_alteracao=timezone.now(),
            )

        nova_promocao = Promocao(
            cadastro=cadastro,
            posto_grad=posto_grad,
            quadro=quadro,
            grupo=grupo,
            ultima_promocao=ultima_promocao,
            usuario_alteracao=request.user,
        )
    nova_promocao.save()
    messages.add_message(
        request,
        constants.SUCCESS,
        "Dados de Posto e Graduação atualizados com sucesso.",
        extra_tags="bg-green-500 text-white p-4 rounded",
    )
    return redirect("efetivo:ver_militar", id=cadastro.id)


# responsável pela edição da model  cadastro
@login_required
def editar_dados_pessoais_contatos(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)

    if request.method == "POST":
        try:
            # Atualizar os campos do cadastro com os dados do formulário
            cadastro.nome = request.POST.get("nome")
            cadastro.nome_de_guerra = request.POST.get("nome_de_guerra")
            cadastro.re = request.POST.get("re")
            cadastro.dig = request.POST.get("dig")
            cadastro.genero = request.POST.get("genero")
            cadastro.nasc = request.POST.get("nasc")
            cadastro.matricula = request.POST.get("matricula")
            cadastro.admissao = request.POST.get("admissao")
            cadastro.previsao_de_inatividade = request.POST.get(
                "previsao_de_inatividade"
            )
            cadastro.cpf = request.POST.get("cpf")
            cadastro.rg = request.POST.get("rg")
            cadastro.telefone = request.POST.get("telefone")
            cadastro.email = request.POST.get("email")  # Atualiza o email do cadastro
            cadastro.tempo_para_averbar_militar = request.POST.get(
                "tempo_para_averbar_militar", 0
            )
            cadastro.tempo_para_averbar_inss = request.POST.get(
                "tempo_para_averbar_inss", 0
            )
            cadastro.alteracao = request.POST.get("alteracao")

            # Validar e salvar
            cadastro.full_clean()  # Validação do modelo
            cadastro.save()

            # Atualizar o User associado, se existir e o email ou nomes mudaram
            try:
                user_militar = User.objects.get(email=cadastro.email)
                if user_militar.first_name != cadastro.nome:
                    user_militar.first_name = cadastro.nome
                if user_militar.last_name != cadastro.nome_de_guerra:
                    user_militar.last_name = cadastro.nome_de_guerra
                # Se o email do militar mudou, o email do usuário também deve mudar
                if user_militar.email != cadastro.email:
                    # Isso pode causar um IntegrityError se o novo email já existir em outro usuário
                    user_militar.email = cadastro.email
                user_militar.save()
                logger.info(f"Usuário associado ao militar {cadastro.re} atualizado.")
            except User.DoesNotExist:
                logger.warning(
                    f"Nenhum usuário encontrado para o e-mail {cadastro.email} ao editar dados pessoais."
                )
            except IntegrityError:
                # Se o novo email já existe para outro usuário, reverte a alteração no cadastro
                transaction.set_rollback(True)
                raise ValidationError(
                    {"email": "Este e-mail já está em uso por outro usuário."}
                )
            except Exception as user_update_e:
                logger.error(
                    f"Erro ao atualizar usuário associado ao militar {cadastro.re}: {user_update_e}",
                    exc_info=True,
                )
                transaction.set_rollback(True)
                raise ValidationError(
                    {"geral": "Erro ao atualizar dados do usuário associado."}
                )

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": True, "message": "Dados atualizados com sucesso!"}
                )

            messages.success(request, "Dados atualizados com sucesso!")
            return redirect("efetivo:ver_militar", id=cadastro.id)

        except ValidationError as e:
            error_message = "; ".join(
                [f"{k}: {', '.join(v)}" for k, v in e.message_dict.items()]
            )
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "message": error_message}, status=400
                )

            messages.error(request, f"Erro de validação: {error_message}")
        except Exception as e:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": str(e)}, status=400)

            messages.error(request, f"Erro ao atualizar dados: {str(e)}")

    context = {
        "cadastro": cadastro,
    }
    return render(request, "modals/editar_dados_pessoais.html", context)


# responsável pela edição da model  cadastro pag de user
# views.py
@login_required
def editar_averbacao_militar(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)

    if request.method == "POST":
        try:
            cadastro.tempo_para_averbar_militar = int(
                request.POST.get("tempo_para_averbar_militar", 0)
            )
            cadastro.save()
            messages.success(
                request,
                "Averbação militar atualizada com sucesso!",
                extra_tags="bg-green-500 text-white p-4 rounded",
            )
        except Exception as e:
            messages.error(
                request,
                f"Erro ao atualizar: {e}",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )

    return redirect("efetivo:visualizar_militar_publico", id=id)


@login_required
def editar_averbacao_inss(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)

    if request.method == "POST":
        try:
            cadastro.tempo_para_averbar_inss = int(
                request.POST.get("tempo_para_averbar_inss", 0)
            )
            cadastro.save()
            messages.success(
                request,
                "Averbação INSS atualizada com sucesso!",
                extra_tags="bg-green-500 text-white p-4 rounded",
            )
        except Exception as e:
            messages.error(
                request,
                f"Erro ao atualizar: {e}",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )

    return redirect("efetivo:visualizar_militar_publico", id=id)


@login_required
def editar_telefone(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)

    if request.method == "POST":
        try:
            cadastro.telefone = request.POST.get("telefone", "")
            cadastro.save()
            messages.success(
                request,
                "Telefone atualizado com sucesso!",
                extra_tags="bg-green-500 text-white p-4 rounded",
            )
        except Exception as e:
            messages.error(
                request,
                f"Erro ao atualizar: {e}",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )

    return redirect("efetivo:visualizar_militar_publico", id=id)


@login_required
def editar_email(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)

    if request.method == "POST":
        try:
            # Validação do domínio do e-mail no backend
            email_novo = request.POST.get("email", "")
            if not email_novo.endswith("@policiamilitar.sp.gov.br"):
                # Mensagem de erro se o domínio não for o esperado
                messages.error(
                    request,
                    "O e-mail deve ter o domínio @policiamilitar.sp.gov.br.",
                    extra_tags="bg-red-500 text-white p-4 rounded",
                )
                # Retorna para a página anterior, ou JsonResponse se for uma requisição AJAX
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "O e-mail deve ter o domínio @policiamilitar.sp.gov.br.",
                        },
                        status=400,
                    )
                return redirect("efetivo:visualizar_militar_publico", id=id)

            # Atualiza o campo de e-mail do cadastro
            cadastro.email = email_novo
            cadastro.save()

            messages.success(
                request,
                "E-mail atualizado com sucesso!",
                extra_tags="bg-green-500 text-white p-4 rounded",
            )

            # Se a requisição for AJAX, retorna JsonResponse
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "message": "E-mail atualizado com sucesso!",
                        "updated_email": cadastro.email,
                    }
                )

        except Exception as e:
            messages.error(
                request,
                f"Erro ao atualizar o e-mail: {e}",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "message": f"Erro ao atualizar o e-mail: {e}"},
                    status=500,
                )

    return redirect("efetivo:visualizar_militar_publico", id=id)


# responsável pela edição da model imagens
@login_required
def editar_imagem(request, id):

    cadastro = get_object_or_404(Cadastro, id=id)

    if request.method == "POST":
        if request.FILES.get("image"):
            try:
                with transaction.atomic():
                    # Deleta todas as imagens anteriores associadas a este cadastro
                    # antes de salvar a nova. Isso garante que sempre haverá apenas uma
                    # imagem de perfil "ativa" para o militar se for o comportamento desejado.
                    # Se você deseja manter um histórico de imagens, essa lógica precisará ser ajustada.
                    Imagem.objects.filter(cadastro=cadastro).delete()

                    nova_imagem = Imagem(
                        cadastro=cadastro,
                        image=request.FILES.get("image"),
                        user=request.user,
                    )
                    nova_imagem.save()
                    messages.add_message(
                        request,
                        constants.SUCCESS,
                        "Imagem atualizada com sucesso",
                        extra_tags="bg-green-500 text-white p-4 rounded",
                    )
            except Exception as e:
                messages.add_message(
                    request,
                    constants.ERROR,
                    f"Erro ao salvar a imagem: {str(e)}",
                    extra_tags="bg-red-500 text-white p-4 rounded",
                )
        else:
            messages.add_message(
                request,
                constants.ERROR,
                "Por favor, envie uma imagem válida.",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )

        return redirect("efetivo:ver_militar", id=cadastro.id)

    return render(
        request,
        "editar_imagem.html",
        {
            "cadastro": cadastro,
            "imagem": cadastro.imagens.last(),  # Continua pegando a última, que agora será a única se a deleção funcionar
        },
    )


@login_required
def editar_imagem_user(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)

    # Verifica permissão
    if not request.user.is_superuser and request.user.cadastro != cadastro:
        return JsonResponse({"error": "Sem permissão"}, status=403)

    if request.method == "POST":
        if request.FILES.get("image"):
            try:
                with transaction.atomic():
                    # Deleta todas as imagens anteriores associadas a este cadastro
                    Imagem.objects.filter(cadastro=cadastro).delete()

                    # Cria uma nova imagem
                    nova_imagem = Imagem(
                        cadastro=cadastro,
                        image=request.FILES.get("image"),
                        user=request.user,
                    )
                    nova_imagem.save()

                    return JsonResponse(
                        {
                            "success": True,
                            "message": "Imagem atualizada com sucesso!",  # Adicionado mensagem de sucesso para o JsonResponse
                            "image_url": nova_imagem.image.url,
                        }
                    )
            except Exception as e:
                logger.error(
                    f"Erro ao atualizar imagem via AJAX para militar ID {id}: {e}",
                    exc_info=True,
                )
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"Erro ao salvar a imagem: {str(e)}",  # Mensagem de erro para o JsonResponse
                    },
                    status=500,
                )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Nenhuma imagem enviada ou formato inválido.",
                },
                status=400,
            )  # Mensagem mais descritiva

    return JsonResponse(
        {"success": False, "message": "Método não permitido."}, status=405
    )  # Mensagem mais descritiva


# responsável por checar a existencia do RPT
@login_required
def check_rpt(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)
    exists = Cadastro_rpt.objects.filter(cadastro=cadastro).exists()
    return JsonResponse({"exists": exists})


# responsável pela visualização em grade do efetivo existente
@login_required
def detalhar_efetivo(request, posto_id):
    posto = get_object_or_404(Posto, pk=posto_id)

    # Ordem hierárquica dos postos/grads
    ORDEM_POSTOS = [
        "Cel PM",
        "Ten Cel PM",
        "Maj PM",
        "CAP PM",
        "1º Ten PM",
        "1º Ten QAPM",
        "2º Ten PM",
        "2º Ten QAPM",
        "Asp OF PM",
        "Subten PM",
        "1º Sgt PM",
        "2º Sgt PM",
        "3º Sgt PM",
        "Cb PM",
        "Sd PM",
        "Sd PM 2ºCL",
    ]

    # Obtém o prefixo do posto_secao (7 primeiros dígitos)
    posto_secao_prefixo = posto.posto_secao[:7]

    # Otimizando as consultas
    militares_queryset = (
        Cadastro.objects.filter(
            Q(detalhes_situacao__posto_secao=posto.posto_secao)
            | Q(
                detalhes_situacao__funcao="CMT_PB",
                detalhes_situacao__posto_secao__startswith=posto_secao_prefixo,
            )
        )
        .select_related("user")
        .prefetch_related(
            Prefetch("imagens", queryset=Imagem.objects.all().order_by("-create_at")),
            Prefetch(
                "promocoes",
                queryset=Promocao.objects.all().order_by("-ultima_promocao"),
            ),
            Prefetch(
                "detalhes_situacao",
                queryset=DetalhesSituacao.objects.all().order_by("-data_alteracao"),
            ),
            Prefetch(
                "categorias_efetivo", queryset=CatEfetivo.objects.filter(ativo=True)
            ),
        )
        .distinct()
    )

    # Converter QuerySet para lista para poder ordenar
    militares = list(militares_queryset)

    # Função para ordenação
    def get_ordenacao(militar):
        ultima_promocao = militar.promocoes.first()
        if ultima_promocao:
            posto_grad = ultima_promocao.posto_grad
            try:
                ordem_posto = ORDEM_POSTOS.index(posto_grad)
            except ValueError:
                ordem_posto = len(ORDEM_POSTOS)
            data_promocao = ultima_promocao.ultima_promocao or datetime.min.date()
        else:
            ordem_posto = len(ORDEM_POSTOS)
            data_promocao = datetime.min.date()

        return (ordem_posto, -data_promocao.toordinal())

    # Ordenar os militares
    militares.sort(key=get_ordenacao)

    # Obtém o comandante separadamente
    comandante = next(
        (
            m
            for m in militares
            if any(
                d.funcao == "CMT_PB" and d.posto_secao.startswith(posto_secao_prefixo)
                for d in m.detalhes_situacao.all()
            )
        ),
        None,
    )

    # Remover o comandante da lista de militares (se existir)
    if comandante:
        militares = [m for m in militares if m.id != comandante.id]

    # Adicionar categoria atual a cada militar
    for militar in militares:
        militar.categoria_atual = next(
            (c for c in militar.categorias_efetivo.all() if c.ativo), None
        )

    if comandante:
        comandante.categoria_atual = next(
            (c for c in comandante.categorias_efetivo.all() if c.ativo), None
        )

    context = {
        "posto": posto,
        "militares": militares,
        "comandante": comandante,
        "unidade_nome": posto.posto_secao,
        "posto_secao_prefixo": posto_secao_prefixo,
        "categoria_choices": CatEfetivo.TIPO_CHOICES,
    }
    return render(request, "detalhes_efetivo.html", context)


# responsável pelo historico de afastamentos
def historico_categorias(request, militar_id):
    militar = get_object_or_404(Cadastro, id=militar_id)
    historicos = (
        HistoricoCatEfetivo.objects.filter(cat_efetivo__cadastro=militar)
        .select_related("cat_efetivo", "usuario_alteracao")
        .order_by("-data_registro")
    )

    return render(
        request,
        "historico_categorias.html",
        {
            "militar": militar,
            "historicos": historicos,
            "today": timezone.now().date(),
        },
    )


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None


def criar_historico(categoria, usuario):
    historico_data = {
        "cat_efetivo": categoria,
        "tipo": categoria.tipo,
        "data_inicio": categoria.data_inicio,
        "data_termino": categoria.data_termino,
        "observacao": categoria.observacao,
        "boletim_concessao_lsv": categoria.boletim_concessao_lsv,
        "data_boletim_lsv": categoria.data_boletim_lsv,
        "usuario_alteracao": usuario,
        "ativo": categoria.ativo,
    }

    if categoria.tipo == "RESTRICAO":
        campos_restricao = [
            f.name for f in CatEfetivo._meta.fields if f.name.startswith("restricao_")
        ]
        historico_data.update(
            {campo: getattr(categoria, campo) for campo in campos_restricao}
        )

    HistoricoCatEfetivo.objects.create(**historico_data)


@login_required
def adicionar_categoria_efetivo(request, militar_id):
    militar = get_object_or_404(Cadastro, id=militar_id)
    today = timezone.now().date()

    if request.method == "POST":
        form_data = request.POST.copy()
        tipo = form_data.get("tipo")

        if not tipo:
            messages.error(request, "Tipo de categoria é obrigatório!")
            return redirect("efetivo:ver_militar", id=militar_id)

        try:
            with transaction.atomic():
                # Converter strings para date quando necessário
                data_inicio_str = form_data.get("data_inicio")
                data_termino_str = form_data.get("data_termino")
                data_boletim_lsv_str = form_data.get("data_boletim_lsv")

                data_inicio = (
                    datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
                    if data_inicio_str
                    else None
                )
                data_termino = (
                    datetime.strptime(data_termino_str, "%Y-%m-%d").date()
                    if data_termino_str
                    else None
                )
                data_boletim_lsv = (
                    datetime.strptime(data_boletim_lsv_str, "%Y-%m-%d").date()
                    if data_boletim_lsv_str
                    else None
                )

                # Verificar se a data de término é anterior à data atual
                if data_termino and data_termino < today:
                    messages.warning(
                        request,
                        "Data de término já expirada. Categoria será marcada como inativa.",
                    )
                    ativo = False
                else:
                    ativo = True

                # Criar nova categoria
                nova_categoria = CatEfetivo(
                    cadastro=militar,
                    tipo=tipo,
                    data_inicio=data_inicio,
                    data_termino=data_termino,
                    usuario_cadastro=request.user,
                    ativo=ativo,
                    observacao=form_data.get("observacao", ""),
                )

                # Campos específicos para LSV
                if tipo == "LSV":
                    nova_categoria.boletim_concessao_lsv = form_data.get(
                        "boletim_concessao_lsv", ""
                    )
                    nova_categoria.data_boletim_lsv = data_boletim_lsv

                # Campos de restrição (só aplica se for RESTRICAO)
                if tipo == "RESTRICAO":
                    campos_restricao = [
                        field.name
                        for field in CatEfetivo._meta.get_fields()
                        if field.name.startswith("restricao_")
                    ]
                    for campo in campos_restricao:
                        setattr(nova_categoria, campo, campo in form_data)

                nova_categoria.save()

                # Criar registro no histórico
                historico_data = {
                    "cat_efetivo": nova_categoria,
                    "tipo": nova_categoria.tipo,
                    "data_inicio": nova_categoria.data_inicio,
                    "data_termino": nova_categoria.data_termino,
                    "observacao": nova_categoria.observacao,
                    "boletim_concessao_lsv": nova_categoria.boletim_concessao_lsv,
                    "data_boletim_lsv": nova_categoria.data_boletim_lsv,
                    "usuario_alteracao": request.user,
                    "ativo": nova_categoria.ativo,
                }

                # Adiciona campos de restrição ao histórico se for do tipo RESTRICAO
                if tipo == "RESTRICAO":
                    historico_data.update(
                        {
                            campo: getattr(nova_categoria, campo)
                            for campo in campos_restricao
                        }
                    )

                HistoricoCatEfetivo.objects.create(**historico_data)

                messages.success(request, "Categoria adicionada com sucesso!")
                return redirect("efetivo:ver_militar", id=militar_id)

        except Exception as e:
            messages.error(request, f"Erro ao adicionar categoria: {str(e)}")
            return redirect("efetivo:ver_militar", id=militar_id)

    # Se não for POST, redireciona para a página do militar
    return redirect("efetivo:ver_militar", id=militar_id)


# views.py


@method_decorator(csrf_exempt, name="dispatch")
class SalvarEdicaoCategoriaView(View):
    def post(self, request, categoria_id, *args, **kwargs):
        categoria = get_object_or_404(CatEfetivo, id=categoria_id)

        try:
            # Assuming data is sent as JSON via fetch API
            data = json.loads(request.body)
            novo_tipo = data.get("tipo")
            novo_periodo = data.get("periodo")
            novas_restricoes = data.get("restricoes")

            # Update the category fields
            categoria.tipo = novo_tipo
            categoria.periodo = novo_periodo
            categoria.restricoes = novas_restricoes
            categoria.save()

            return JsonResponse(
                {"success": True, "message": "Categoria atualizada com sucesso!"}
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


@require_http_methods(["POST"])
def salvar_edicao_categoria(request, categoria_id):
    try:
        categoria = CategoriaEfetivo.objects.get(id=categoria_id)

        # Verifica se a categoria está ativa (pode ser editada)
        if not categoria.ativo:
            return JsonResponse(
                {"error": "Esta categoria não está ativa e não pode ser editada"},
                status=400,
            )

        data = request.POST

        # Atualiza os campos básicos
        if "data_inicio" in data:
            categoria.data_inicio = data["data_inicio"] or None
        if "data_termino" in data:
            categoria.data_termino = data["data_termino"] or None
        if "observacao" in data:
            categoria.observacao = data["observacao"]

        # Atualiza restrições se for do tipo RESTRICAO
        if categoria.tipo == "RESTRICAO":
            restricoes = Restricao.objects.all()
            for restricao in restricoes:
                field_name = f"restricao_{restricao.id}"
                setattr(categoria, field_name, field_name in data)

        categoria.save()

        return JsonResponse({"success": True})

    except CategoriaEfetivo.DoesNotExist:
        return JsonResponse({"error": "Categoria não encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
def excluir_categoria_efetivo(request, categoria_id):
    categoria = get_object_or_404(CatEfetivo, id=categoria_id)
    militar_id = categoria.cadastro.id

    if request.method == "POST":
        try:
            with transaction.atomic():
                # Remove categoria e histórico relacionado
                HistoricoCatEfetivo.objects.filter(cat_efetivo=categoria).delete()
                categoria.delete()
                messages.success(
                    request, "Registro e histórico excluídos permanentemente!"
                )
        except Exception as e:
            messages.error(request, f"Erro na exclusão: {str(e)}")

    return redirect("efetivo:historico_categorias", militar_id=militar_id)


@login_required
def excluir_historico_categoria(request, historico_id):
    historico = get_object_or_404(HistoricoCatEfetivo, id=historico_id)
    militar_id = historico.cat_efetivo.cadastro.id

    if request.method == "POST":
        historico.delete()
        messages.success(request, "Histórico excluído permanentemente.")

    return redirect("efetivo:historico_categorias", militar_id=militar_id)


# resposnsavel pelos filtros da visualização de detalhes de efetivo
class ListaMilitaresView(ListView):
    model = Cadastro
    template_name = "lista_militares.html"
    context_object_name = "militares"

    # Define your subgrupos_estrutura as a class attribute
    subgrupos_estrutura = {
        "EM": [
            {"codigo": "703150000", "nome": "CMT", "filhos": []},
            {"codigo": "703159000", "nome": "SUB CMT", "filhos": []},
            {"codigo": "703159100", "nome": "SEC ADM", "filhos": []},
            {
                "codigo": "703159110",
                "nome": "B/1 E B/5",
                "filhos": [{"codigo": "703159110-1", "nome": "B/5", "filhos": []}],
            },
            {"codigo": "703159120", "nome": "AA", "filhos": []},
            {
                "codigo": "703159130",
                "nome": "B/3 E MOTOMEC",
                "filhos": [{"codigo": "703159130-1", "nome": "MOTOMEC", "filhos": []}],
            },
            {"codigo": "703159131", "nome": "COBOM", "filhos": []},
            {"codigo": "703159140", "nome": "B/4", "filhos": []},
            {"codigo": "703159150", "nome": "ST UGE", "filhos": []},
            {"codigo": "703159160", "nome": "ST PJMD", "filhos": []},
            {"codigo": "703159200", "nome": "SEC ATIV TEC", "filhos": []},
        ],
        "1ºSGB": [
            {"codigo": "703151000", "nome": "CMT 1º SGB", "filhos": []},
            {"codigo": "703151100", "nome": "ADM PB CERRADO", "filhos": []},
            {"codigo": "703151101", "nome": "EB CERRADO", "filhos": []},
            {"codigo": "703151102", "nome": "EB ZONA NORTE", "filhos": []},
            {"codigo": "703151200", "nome": "ADM PB SANTA ROSÁLIA", "filhos": []},
            {"codigo": "703151201", "nome": "EB SANTA ROSÁLIA", "filhos": []},
            {"codigo": "703151202", "nome": "EB ÉDEM", "filhos": []},
            {"codigo": "703151300", "nome": "ADM PB VOTORANTIM", "filhos": []},
            {"codigo": "703151301", "nome": "EB VOTORANTIM", "filhos": []},
            {"codigo": "703151302", "nome": "EB PIEDADE", "filhos": []},
            {"codigo": "703151800", "nome": "ADM 1º SGB", "filhos": []},
        ],
        "2ºSGB": [
            {"codigo": "703152000", "nome": "CMT 2º SGB", "filhos": []},
            {"codigo": "703152100", "nome": "ADM PB ITU", "filhos": []},
            {"codigo": "703152101", "nome": "EB ITU", "filhos": []},
            {"codigo": "703152102", "nome": "EB PORTO FELIZ", "filhos": []},
            {"codigo": "703152200", "nome": "ADM PB SALTO", "filhos": []},
            {"codigo": "703152201", "nome": "EB SALTO", "filhos": []},
            {"codigo": "703152300", "nome": "ADM PB SÃO ROQUE", "filhos": []},
            {"codigo": "703152301", "nome": "EB SÃO ROQUE", "filhos": []},
            {"codigo": "703152302", "nome": "EB IBIÚNA", "filhos": []},
            {"codigo": "703152800", "nome": "ADM 2º SGB", "filhos": []},
            {"codigo": "703152900", "nome": "NUCL ATIV TEC 2º SGB", "filhos": []},
        ],
        "3ºSGB": [
            {"codigo": "703153000", "nome": "CMT 3º SGB", "filhos": []},
            {"codigo": "703153100", "nome": "ADM PB ITAPEVA", "filhos": []},
            {"codigo": "703153101", "nome": "EB ITAPEVA", "filhos": []},
            {"codigo": "703153102", "nome": "EB APIAÍ", "filhos": []},
            {"codigo": "703153103", "nome": "EB ITARARÉ", "filhos": []},
            {"codigo": "703153104", "nome": "EB CAPÃO BONITO", "filhos": []},
            {"codigo": "703153800", "nome": "ADM 3º SGB", "filhos": []},
            {"codigo": "703153900", "nome": "NUCL ATIV TEC 3º SGB", "filhos": []},
        ],
        "4ºSGB": [
            {"codigo": "703154000", "nome": "CMT 4º SGB", "filhos": []},
            {"codigo": "703154100", "nome": "ADM PB ITAPETININGA", "filhos": []},
            {"codigo": "703154101", "nome": "EB ITAPETININGA", "filhos": []},
            {"codigo": "703154102", "nome": "EB BOITUVA", "filhos": []},
            {"codigo": "703154103", "nome": "EB ANGATUBA", "filhos": []},
            {"codigo": "703154200", "nome": "ADM PB TATUÍ", "filhos": []},
            {"codigo": "703154201", "nome": "EB TATUÍ", "filhos": []},
            {"codigo": "703154202", "nome": "EB TIETÊ", "filhos": []},
            {"codigo": "703154203", "nome": "EB LARANJAL PAULISTA", "filhos": []},
            {"codigo": "703154800", "nome": "ADM 4º SGB", "filhos": []},
            {"codigo": "703154900", "nome": "NUCL ATIV TEC 4º SGB", "filhos": []},
        ],
        "5ºSGB": [
            {"codigo": "703155000", "nome": "CMT 5º SGB", "filhos": []},
            {"codigo": "703155100", "nome": "ADM PB BOTUCATU", "filhos": []},
            {"codigo": "703155101", "nome": "EB BOTUCATU", "filhos": []},
            {"codigo": "703155102", "nome": "EB ITATINGA", "filhos": []},
            {"codigo": "703155200", "nome": "ADM PB AVARÉ", "filhos": []},
            {"codigo": "703155201", "nome": "EB AVARÉ", "filhos": []},
            {"codigo": "703155202", "nome": "EB PIRAJU", "filhos": []},
            {"codigo": "703155203", "nome": "EB ITAÍ", "filhos": []},
            {"codigo": "703155800", "nome": "ADM 5º SGB", "filhos": []},
            {"codigo": "703155900", "nome": "NUCL ATIV TEC 5º SGB", "filhos": []},
        ],
    }

    def get_base_queryset(self):
        """
        Retorna o queryset base com apenas militares de situação 'Efetivo'.
        """
        latest_detalhe_situacao = DetalhesSituacao.objects.filter(
            cadastro=OuterRef("pk")
        ).order_by("-data_alteracao", "-id")

        return Cadastro.objects.annotate(
            latest_status=Subquery(latest_detalhe_situacao.values("situacao")[:1])
        ).filter(latest_status="Efetivo")

    def get_queryset(self):
        queryset = self.get_base_queryset()
        grupo_ativo = self.request.GET.get("grupo")
        subgrupo_ativo = self.request.GET.get("subgrupo")

        if subgrupo_ativo:
            queryset = queryset.filter(
                detalhes_situacao__posto_secao__startswith=subgrupo_ativo
            )
        elif grupo_ativo:
            queryset = queryset.filter(detalhes_situacao__sgb=grupo_ativo)

        queryset = (
            queryset.distinct()
            .prefetch_related(
                "detalhes_situacao", "imagens", "promocoes", "categorias_efetivo"
            )
            .order_by("re")
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grupos = [
            ("EM", "Estado Maior"),
            ("1ºSGB", "1º Subgrupamento"),
            ("2ºSGB", "2º Subgrupamento"),
            ("3ºSGB", "3º Subgrupamento"),
            ("4ºSGB", "4º Subgrupamento"),
            ("5ºSGB", "5º Subgrupamento"),
        ]
        grupo_ativo = self.request.GET.get("grupo")
        subgrupo_ativo = self.request.GET.get("subgrupo")

        base_queryset = self.get_base_queryset()

        # Calcula a contagem para cada subgrupo e filho
        subgrupo_counts = {}
        for grupo_key, _ in grupos:
            estrutura = self.subgrupos_estrutura.get(grupo_key, [])
            subgrupo_counts.update(self.calcular_contagens(estrutura, base_queryset))

        # Calcula a contagem total para cada grupo principal
        agrupamento_counts = {}
        for grupo_key, _ in grupos:
            agrupamento_counts[grupo_key] = (
                base_queryset.filter(detalhes_situacao__sgb=grupo_key)
                .distinct()
                .count()
            )
        
        # Agrupamento para a visualização em grade
        prontidao_verde = []
        prontidao_amarela = []
        prontidao_azul = []
        administrativo = []
        afastados = []

        # O queryset do contexto já está filtrado, vamos usá-lo
        militares_filtrados = context['militares']

        for militar in militares_filtrados:
            categoria_atual = militar.categorias_efetivo.filter(ativo=True).first()
            detalhe_atual = militar.detalhes_situacao.order_by("-data_alteracao", "-id").first()

            if categoria_atual and categoria_atual.tipo != 'ATIVO':
                afastados.append(militar)
            elif detalhe_atual and detalhe_atual.op_adm == 'Administrativo':
                administrativo.append(militar)
            elif detalhe_atual:
                if detalhe_atual.prontidao == 'VERDE':
                    prontidao_verde.append(militar)
                elif detalhe_atual.prontidao == 'AMARELA':
                    prontidao_amarela.append(militar)
                elif detalhe_atual.prontidao == 'AZUL':
                    prontidao_azul.append(militar)

        context.update(
            {
                "subgrupo_counts": subgrupo_counts,
                "agrupamento_counts": agrupamento_counts,
                "grupos": grupos,
                "grupo_ativo": grupo_ativo,
                "subgrupo_ativo": subgrupo_ativo,
                "grupo_ativo_nome": dict(grupos).get(grupo_ativo, ""),
                "subgrupo_ativo_nome": self.get_subgrupo_nome(
                    grupo_ativo, subgrupo_ativo
                ),
                "subgrupos_estrutura": self.subgrupos_estrutura,
                "current_date": timezone.now().date(),
                # Listas para a grade
                "prontidao_verde": prontidao_verde,
                "prontidao_amarela": prontidao_amarela,
                "prontidao_azul": prontidao_azul,
                "administrativo": administrativo,
                "afastados": afastados,
                "afastamento_types": [choice[0] for choice in CatEfetivo.TIPO_CHOICES],
            }
        )
        return context

    def calcular_contagens(self, estrutura, base_queryset):
        contagens = {}
        for item in estrutura:
            # Conta usando o queryset base já filtrado por 'Efetivo'
            count = (
                base_queryset.filter(detalhes_situacao__posto_secao__startswith=item["codigo"])
                .distinct()
                .count()
            )
            contagens[item["codigo"]] = count

            if item.get("filhos"):
                contagens.update(self.calcular_contagens(item["filhos"], base_queryset))
        return contagens

    def get_subgrupo_nome(self, grupo_key, subgrupo_codigo):
        if not grupo_key or not subgrupo_codigo:
            return ""
        
        estrutura = self.subgrupos_estrutura.get(grupo_key, [])
        
        for item in estrutura:
            if item['codigo'] == subgrupo_codigo:
                return item['nome']
            if item.get('filhos'):
                for filho in item['filhos']:
                    if filho['codigo'] == subgrupo_codigo:
                        return filho['nome']
        return ""


# resposnsavel pelos gerção de etiquetas
def get_image_path(file):
    path = finders.find(f"img/{file}")
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo estático img/{file} não encontrado!")
    return path


def pagina_buscar_militar(request):

    return render(request, "buscar_militar.html")


@track_function_latency
def gerar_etiqueta_pdf(request):
    if request.method == "GET":
        return render(request, "buscar_militar.html")

    re_param = request.POST.get("re", "").strip()
    context = {"re_value": re_param}

    if not re_param:
        context["error_message"] = "Por favor, digite o RE do militar."
        return render(request, "buscar_militar.html", context, status=400)

    try:
        cadastro = get_object_or_404(Cadastro, re=re_param)
    except Exception:
        context["error_message"] = f"Militar com RE {re_param} não encontrado."
        return render(request, "buscar_militar.html", context, status=404)

    try:
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="etiqueta_militar_{re_param}.pdf"'
        )

        # --- Dimensões da Etiqueta ---
        ETIQUETA_WIDTH = 130 * mm
        ETIQUETA_HEIGHT = 60 * mm
        page_width, page_height = A4

        # Margens
        margin_page = 10 * mm
        x_pos = margin_page
        y_pos = page_height - margin_page - ETIQUETA_HEIGHT

        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            rightMargin=0,
            leftMargin=0,
            topMargin=0,
            bottomMargin=0,
        )

        styles = getSampleStyleSheet()

        # --- Estilos Personalizados ---
        styles.add(
            ParagraphStyle(
                name="HeaderText",
                fontSize=11,
                leading=12,
                textColor=colors.HexColor("#1a365d"),
                alignment=1,
                fontName="Helvetica-Bold",
                spaceAfter=6 * mm,
            )
        )

        styles.add(
            ParagraphStyle(
                name="MilitaryName",
                fontSize=14,
                leading=15,
                textColor=colors.black,
                alignment=1,
                fontName="Helvetica-Bold",
            )
        )

        styles.add(
            ParagraphStyle(
                name="MilitaryRankWarName",
                fontSize=11,
                leading=12,
                textColor=colors.HexColor("#1a365d"),
                alignment=1,
                fontName="Helvetica-Bold",
            )
        )

        styles.add(
            ParagraphStyle(
                name="MilitaryRE",
                fontSize=13,
                leading=11,
                textColor=colors.HexColor("#9c4221"),
                alignment=1,
                fontName="Helvetica-Bold",
            )
        )

        styles.add(
            ParagraphStyle(
                name="MilitaryDetail",
                fontSize=9,
                leading=10,
                textColor=colors.black,
                alignment=1,
                spaceAfter=0.5 * mm,
            )
        )

        # --- Carregar imagens ---
        try:
            # Logo como marca d'água central (3x4 ocupando toda altura)
            logo_img = Image(
                get_image_path("logo.png"),
                width=(3 / 4) * ETIQUETA_HEIGHT,
                height=ETIQUETA_HEIGHT,
            )

            # Brasão no canto superior esquerdo (15x15mm)
            brasao_img = Image(
                get_image_path("brasao.png"), width=15 * mm, height=15 * mm
            )

            # Brasão PM no canto superior direito (15x15mm)
            brasao_pm_img = Image(
                get_image_path("brasaopm.png"), width=15 * mm, height=15 * mm
            )

        except Exception as e:
            context["error_message"] = f"Erro ao carregar imagens: {str(e)}"
            return render(request, "buscar_militar.html", context, status=500)

        # ===== Obter imagem do militar =====
        user_image = None
        if cadastro.imagens.exists():
            try:
                ultima_imagem = cadastro.imagens.last()
                # Usar caminho absoluto da imagem
                image_path = ultima_imagem.image.path
                user_image = Image(image_path, width=25 * mm, height=30 * mm)
            except Exception as img_error:
                print(f"Erro ao carregar imagem do militar: {str(img_error)}")
        # ===== FIM DA SEÇÃO DE IMAGEM DO MILITAR =====

        # --- Elementos da etiqueta ---
        elements = []

        # Cabeçalho com brasões e texto
        header_data = [
            [
                brasao_img,
                Paragraph("15º GRUPAMENTO DE BOMBEIROS", styles["HeaderText"]),
                brasao_pm_img,
            ]
        ]

        header_table = Table(
            header_data,
            colWidths=[20 * mm, ETIQUETA_WIDTH - 40 * mm, 20 * mm],
            rowHeights=[15 * mm],
        )

        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                    ("LEFTPADDING", (1, 0), (1, 0), 0),
                    ("RIGHTPADDING", (1, 0), (1, 0), 0),
                ]
            )
        )

        elements.append(header_table)

        # ===== Conteúdo Principal com Foto =====
        content_data = []

        # Coluna de texto (esquerda)
        text_content = [
            Paragraph(
                cadastro.nome.upper() if cadastro.nome else "", styles["MilitaryName"]
            ),
            Spacer(1, 1 * mm),
        ]

        last_promotion = cadastro.promocoes.order_by("-data_alteracao").first()
        if last_promotion and last_promotion.posto_grad:
            rank_war_name = f"{last_promotion.posto_grad.upper()} {cadastro.nome_de_guerra.upper() if cadastro.nome_de_guerra else ''}"
        else:
            rank_war_name = (
                cadastro.nome_de_guerra.upper() if cadastro.nome_de_guerra else ""
            )

        text_content.append(
            Paragraph(rank_war_name.strip(), styles["MilitaryRankWarName"])
        )
        text_content.append(Spacer(1, 1 * mm))

        re_text = (
            f"{cadastro.re or ''}-{cadastro.dig or ''}"
            if cadastro.dig
            else f"{cadastro.re or ''}"
        )
        text_content.append(Paragraph(re_text, styles["MilitaryRE"]))
        text_content.append(Spacer(1, 3 * mm))

        last_situacao = cadastro.detalhes_situacao.order_by("-data_alteracao").first()
        if last_situacao:
            if last_situacao.funcao:
                text_content.append(
                    Paragraph(last_situacao.funcao.upper(), styles["MilitaryDetail"])
                )
            if last_situacao.sgb:
                text_content.append(
                    Paragraph(last_situacao.sgb.upper(), styles["MilitaryDetail"])
                )
            if last_situacao.posto_secao:
                text_content.append(
                    Paragraph(
                        last_situacao.posto_secao.upper(), styles["MilitaryDetail"]
                    )
                )

        # Coluna de imagem (esquerda) - INVERTIDA A POSIÇÃO AQUI
        image_content = []
        if user_image:
            # Definir cores de borda por patente
            border_color = colors.HexColor("#1a365d")  # Azul padrão

            # Listas de patentes
            officer_ranks = [
                "Cel PM",
                "Ten Cel PM",
                "Maj PM",
                "CAP PM",
                "1º Ten PM",
                "1º Ten QAPM",
                "2º Ten PM",
                "2º Ten QAPM",
                "Asp OF PM",
            ]

            nco_ranks = ["Subten PM", "1º Sgt PM", "2º Sgt PM", "3º Sgt PM"]

            if last_promotion and last_promotion.posto_grad in officer_ranks:
                border_color = colors.HexColor("#d4af37")  # Dourado para oficiais
            elif last_promotion and last_promotion.posto_grad in nco_ranks:
                border_color = colors.HexColor("#c0c0c0")  # Prata para sargentos

            # Criar tabela para a imagem com borda
            img_table = Table([[user_image]], colWidths=[25 * mm], rowHeights=[30 * mm])

            img_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("LINEABOVE", (0, 0), (-1, -1), 1, border_color),
                        ("LINEBELOW", (0, 0), (-1, -1), 1, border_color),
                        ("LINEBEFORE", (0, 0), (-1, -1), 1, border_color),
                        ("LINEAFTER", (0, 0), (-1, -1), 1, border_color),
                        ("BOX", (0, 0), (-1, -1), 1, border_color),
                    ]
                )
            )

            image_content.append(img_table)
        else:
            # Placeholder para quando não há imagem
            no_image_text = Paragraph("SEM IMAGEM", styles["MilitaryDetail"])
            no_image_table = Table(
                [[no_image_text]], colWidths=[25 * mm], rowHeights=[30 * mm]
            )
            no_image_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.lightgrey),
                    ]
                )
            )
            image_content.append(no_image_table)

        # Coluna de texto (direita) - INVERTIDA A POSIÇÃO AQUI
        text_content = [
            Paragraph(
                cadastro.nome.upper() if cadastro.nome else "", styles["MilitaryName"]
            ),
            Spacer(1, 1 * mm),
        ]

        last_promotion = cadastro.promocoes.order_by("-data_alteracao").first()
        if last_promotion and last_promotion.posto_grad:
            rank_war_name = f"{last_promotion.posto_grad.upper()} {cadastro.nome_de_guerra.upper() if cadastro.nome_de_guerra else ''}"
        else:
            rank_war_name = (
                cadastro.nome_de_guerra.upper() if cadastro.nome_de_guerra else ""
            )

        text_content.append(
            Paragraph(rank_war_name.strip(), styles["MilitaryRankWarName"])
        )
        text_content.append(Spacer(1, 1 * mm))

        re_text = (
            f"{cadastro.re or ''}-{cadastro.dig or ''}"
            if cadastro.dig
            else f"{cadastro.re or ''}"
        )
        text_content.append(Paragraph(re_text, styles["MilitaryRE"]))
        text_content.append(Spacer(1, 3 * mm))

        last_situacao = cadastro.detalhes_situacao.order_by("-data_alteracao").first()
        if last_situacao:
            if last_situacao.funcao:
                text_content.append(
                    Paragraph(last_situacao.funcao.upper(), styles["MilitaryDetail"])
                )
            if last_situacao.sgb:
                text_content.append(
                    Paragraph(last_situacao.sgb.upper(), styles["MilitaryDetail"])
                )
            if last_situacao.posto_secao:
                text_content.append(
                    Paragraph(
                        last_situacao.posto_secao.upper(), styles["MilitaryDetail"]
                    )
                )

        # Juntar conteúdo em uma tabela de 2 colunas - ORDEM INVERTIDA AQUI
        content_data.append(
            [
                image_content,  # Imagem agora na primeira coluna (esquerda)
                text_content,  # Texto agora na segunda coluna (direita)
            ]
        )

        content_table = Table(
            content_data, colWidths=[10 * mm, ETIQUETA_WIDTH - 30 * mm]
        )  # Larguras ajustadas

        content_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    (
                        "ALIGN",
                        (0, 0),
                        (0, 0),
                        "CENTER",
                    ),  # Alinha a imagem ao centro da sua coluna
                    (
                        "ALIGN",
                        (1, 0),
                        (1, 0),
                        "LEFT",
                    ),  # Alinha o texto à esquerda da sua coluna
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (0, 0),
                        15 * mm,
                    ),  # Ajusta padding da imagem
                    ("RIGHTPADDING", (0, 0), (0, 0), 1 * mm),  # Ajusta padding do texto
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        elements.append(content_table)
        # ===== FIM DO CONTEÚDO PRINCIPAL =====

        # --- Função para desenhar o layout completo ---
        def draw_page(canvas, doc):
            # Marca d'água
            canvas.saveState()
            canvas.setFillAlpha(0.1)
            logo_img.drawOn(
                canvas,
                x_pos + (ETIQUETA_WIDTH - logo_img.drawWidth) / 2,
                y_pos + (ETIQUETA_HEIGHT - logo_img.drawHeight) / 2,
            )
            canvas.restoreState()

            # Bordas estilizadas
            canvas.saveState()

            AZUL_ESCURO = colors.HexColor("#1a365d")
            DOURADO = colors.HexColor("#d4af37")

            # Borda externa
            canvas.setStrokeColor(AZUL_ESCURO)
            canvas.setLineWidth(1.2 * mm)
            canvas.rect(
                x_pos - 0.6 * mm,
                y_pos - 0.6 * mm,
                ETIQUETA_WIDTH + 1.2 * mm,
                ETIQUETA_HEIGHT + 1.2 * mm,
            )

            # Filete dourado
            canvas.setStrokeColor(DOURADO)
            canvas.setLineWidth(0.6 * mm)
            canvas.rect(
                x_pos + 2 * mm,
                y_pos + 2 * mm,
                ETIQUETA_WIDTH - 4 * mm,
                ETIQUETA_HEIGHT - 4 * mm,
            )

            # Linha intermediária
            canvas.setStrokeColor(AZUL_ESCURO)
            canvas.setLineWidth(0.3 * mm)
            canvas.rect(
                x_pos + 1 * mm,
                y_pos + 1 * mm,
                ETIQUETA_WIDTH - 2 * mm,
                ETIQUETA_HEIGHT - 2 * mm,
            )

            # Cantos decorados
            TAMANHO_CANTO = 5 * mm

            # Canto superior esquerdo
            canvas.setStrokeColor(AZUL_ESCURO)
            canvas.setLineWidth(0.5 * mm)
            canvas.line(
                x_pos - 0.6 * mm,
                y_pos + ETIQUETA_HEIGHT + 0.6 * mm - TAMANHO_CANTO,
                x_pos - 0.6 * mm,
                y_pos + ETIQUETA_HEIGHT + 0.6 * mm,
            )
            canvas.line(
                x_pos - 0.6 * mm,
                y_pos + ETIQUETA_HEIGHT + 0.6 * mm,
                x_pos - 0.6 * mm + TAMANHO_CANTO,
                y_pos + ETIQUETA_HEIGHT + 0.6 * mm,
            )

            # Canto superior direito
            canvas.line(
                x_pos + ETIQUETA_WIDTH + 0.6 * mm - TAMANHO_CANTO,
                y_pos + ETIQUETA_HEIGHT + 0.6 * mm,
                x_pos + ETIQUETA_WIDTH + 0.6 * mm,
                y_pos + ETIQUETA_HEIGHT + 0.6 * mm,
            )
            canvas.line(
                x_pos + ETIQUETA_WIDTH + 0.6 * mm,
                y_pos + ETIQUETA_HEIGHT + 0.6 * mm,
                x_pos + ETIQUETA_WIDTH + 0.6 * mm,
                y_pos + ETIQUETA_HEIGHT + 0.6 * mm - TAMANHO_CANTO,
            )

            # Canto inferior esquerdo
            canvas.line(
                x_pos - 0.6 * mm,
                y_pos - 0.6 * mm,
                x_pos - 0.6 * mm,
                y_pos - 0.6 * mm + TAMANHO_CANTO,
            )
            canvas.line(
                x_pos - 0.6 * mm,
                y_pos - 0.6 * mm,
                x_pos - 0.6 * mm + TAMANHO_CANTO,
                y_pos - 0.6 * mm,
            )

            # Canto inferior direito
            canvas.line(
                x_pos + ETIQUETA_WIDTH + 0.6 * mm - TAMANHO_CANTO,
                y_pos - 0.6 * mm,
                x_pos + ETIQUETA_WIDTH + 0.6 * mm,
                y_pos - 0.6 * mm,
            )
            canvas.line(
                x_pos + ETIQUETA_WIDTH + 0.6 * mm,
                y_pos - 0.6 * mm,
                x_pos + ETIQUETA_WIDTH + 0.6 * mm,
                y_pos - 0.6 * mm + TAMANHO_CANTO,
            )

            canvas.restoreState()

        # Frame e construção do PDF
        frame = Frame(
            x_pos,
            y_pos,
            ETIQUETA_WIDTH,
            ETIQUETA_HEIGHT,
            leftPadding=5 * mm,
            bottomPadding=5 * mm,
            rightPadding=5 * mm,
            topPadding=5 * mm,
            showBoundary=0,
        )

        doc.addPageTemplates(
            [PageTemplate(id="EtiquetaPage", frames=frame, onPage=draw_page)]
        )
        doc.build(elements)

        return response

    except Exception as e:
        import traceback

        traceback.print_exc()
        context["error_message"] = f"Erro ao gerar etiqueta: {str(e)}"
        return render(request, "buscar_militar.html", context, status=500)


# backend/efetivo/views.py (ou onde suas views estão)
# views.py


@login_required
@require_http_methods(["POST"])
def editar_situacao_funcional(request, id):
    logger.info(f"Iniciando editar_situacao_funcional para militar ID: {id}")
    try:
        cadastro = get_object_or_404(Cadastro, id=id)
        detalhe_situacao = cadastro.detalhes_situacao.order_by(
            "-data_alteracao"
        ).first()

        if not detalhe_situacao:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Situação funcional não encontrada para o militar especificado.",
                },
                status=404,
            )

        # Criar histórico APENAS com os dados ANTES da atualização
        HistoricoDetalhesSituacao.objects.create(
            cadastro=cadastro,
            situacao=detalhe_situacao.situacao,
            sgb=detalhe_situacao.sgb,
            posto_secao=detalhe_situacao.posto_secao,
            esta_adido=detalhe_situacao.esta_adido,
            funcao=detalhe_situacao.funcao,
            op_adm=detalhe_situacao.op_adm,
            cat_efetivo=detalhe_situacao.cat_efetivo,
            prontidao=detalhe_situacao.prontidao,
            apresentacao_na_unidade=detalhe_situacao.apresentacao_na_unidade,
            saida_da_unidade=detalhe_situacao.saida_da_unidade,
            usuario_alteracao=request.user,
        )

        # Atualizar APENAS o modelo DetalhesSituacao
        detalhe_situacao.situacao = request.POST.get("situacao")

        saida_str = request.POST.get("saida_da_unidade")
        if saida_str:
            try:
                detalhe_situacao.saida_da_unidade = datetime.strptime(
                    saida_str, "%Y-%m-%d"
                ).date()
            except ValueError:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Formato de data de saída da unidade inválido. Use AAAA-MM-DD.",
                    },
                    status=400,
                )
        else:
            detalhe_situacao.saida_da_unidade = None

        detalhe_situacao.data_alteracao = timezone.now()
        detalhe_situacao.usuario_alteracao = request.user
        detalhe_situacao.save()

        logger.info(f"Situação funcional atualizada para militar ID: {id}.")
        return JsonResponse(
            {
                "success": True,
                "message": "Situação funcional atualizada com sucesso!",
                "show_choice_modal": True,
            }
        )

    except Exception as e:
        logger.error(
            f"Erro inesperado ao editar situação funcional para militar ID {id}: {e}",
            exc_info=True,
        )
        return JsonResponse(
            {"success": False, "message": f"Erro interno do servidor: {str(e)}"},
            status=500,
        )


@login_required
@require_http_methods(["POST"])
def nova_situacao_funcional(request, id):
    logger.info(f"Iniciando nova_situacao_funcional para militar ID: {id}")
    try:
        cadastro = get_object_or_404(Cadastro, id=id)

        # Obter situação atual e criar histórico
        situacao_atual = cadastro.detalhes_situacao.order_by("-data_alteracao").first()
        if situacao_atual:
            HistoricoDetalhesSituacao.objects.create(
                cadastro=cadastro,
                situacao=situacao_atual.situacao,
                sgb=situacao_atual.sgb,
                posto_secao=situacao_atual.posto_secao,
                esta_adido=situacao_atual.esta_adido,
                funcao=situacao_atual.funcao,
                op_adm=situacao_atual.op_adm,
                cat_efetivo=situacao_atual.cat_efetivo,
                prontidao=situacao_atual.prontidao,
                apresentacao_na_unidade=situacao_atual.apresentacao_na_unidade,
                saida_da_unidade=situacao_atual.saida_da_unidade,
                usuario_alteracao=request.user,
            )

        # Criar nova situação (substitui a anterior)
        nova_situacao = DetalhesSituacao(
            cadastro=cadastro,
            situacao=request.POST.get("situacao"),
            sgb=request.POST.get("sgb"),
            posto_secao=request.POST.get("posto_secao"),
            esta_adido=request.POST.get("esta_adido") or None,
            funcao=request.POST.get("funcao"),
            op_adm=request.POST.get("op_adm", None),
            cat_efetivo=request.POST.get("cat_efetivo", "ATIVO"),
            prontidao=request.POST.get("prontidao", "VERDE"),
            usuario_alteracao=request.user,
        )

        # Validação de datas
        apresentacao_str = request.POST.get("apresentacao_na_unidade")
        if not apresentacao_str:
            return JsonResponse(
                {"success": False, "message": "Data de apresentação é obrigatória"},
                status=400,
            )

        try:
            nova_situacao.apresentacao_na_unidade = datetime.strptime(
                apresentacao_str, "%Y-%m-%d"
            ).date()
        except ValueError:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Formato de data de apresentação inválido",
                },
                status=400,
            )

        saida_str = request.POST.get("saida_da_unidade")
        if saida_str:
            try:
                nova_situacao.saida_da_unidade = datetime.strptime(
                    saida_str, "%Y-%m-%d"
                ).date()
            except ValueError:
                return JsonResponse(
                    {"success": False, "message": "Formato de data de saída inválido"},
                    status=400,
                )

        nova_situacao.save()
        logger.info(f"Nova situação funcional cadastrada para militar ID: {id}.")
        return JsonResponse(
            {"success": True, "message": "Nova situação cadastrada com sucesso!"}
        )

    except Exception as e:
        logger.error(f"Erro ao cadastrar nova situação: {e}", exc_info=True)
        return JsonResponse(
            {"success": False, "message": f"Erro interno: {str(e)}"}, status=500
        )


@login_required
def historico_movimentacoes(request, id):
    cadastro = get_object_or_404(Cadastro, id=id)
    promocoes = Promocao.objects.filter(cadastro=cadastro).order_by("-data_alteracao")
    historico_detalhes_situacao = HistoricoDetalhesSituacao.objects.filter(
        cadastro=cadastro
    ).order_by("-data_alteracao")

    return render(
        request,
        "historico_movimentacoes.html",
        {
            "cadastro": cadastro,
            "promocoes": promocoes,
            "historico_detalhes_situacao": historico_detalhes_situacao,
        },
    )


@login_required
@require_http_methods(["POST"])
@csrf_exempt  # Considere remover csrf_exempt e usar {% csrf_token %} no seu formulário HTML para segurança
def salvar_situacao_funcional(request, id):
    logger.debug(f"Recebido POST para salvar_situacao_funcional para militar ID: {id}")
    try:
        cadastro = get_object_or_404(Cadastro, id=id)
        detalhe_situacao = get_object_or_404(DetalhesSituacao, cadastro=cadastro)

        # PASSO CRUCIAL: Criar o registro de histórico com os DADOS ATUAIS (ANTES da atualização)
        HistoricoDetalhesSituacao.objects.create(
            cadastro=detalhe_situacao.cadastro,
            situacao=detalhe_situacao.situacao,
            sgb=detalhe_situacao.sgb,
            posto_secao=detalhe_situacao.posto_secao,
            esta_adido=detalhe_situacao.esta_adido,
            funcao=detalhe_situacao.funcao,
            op_adm=detalhe_situacao.op_adm,  # Adicionado: Capturar o valor de op_adm
            prontidao=detalhe_situacao.prontidao,  # Adicionado: Capturar o valor de prontidao
            cat_efetivo=detalhe_situacao.cat_efetivo,  # Adicionado: Capturar o valor de cat_efetivo
            apresentacao_na_unidade=detalhe_situacao.apresentacao_na_unidade,
            saida_da_unidade=detalhe_situacao.saida_da_unidade,
            usuario_alteracao=request.user,  # Quem fez a alteração
            # data_alteracao é auto_now_add=True, então não precisa ser passada aqui
        )

        # Agora, atualize os campos do objeto DetalhesSituacao principal com os novos dados do POST
        detalhe_situacao.situacao = request.POST.get("situacao")
        detalhe_situacao.sgb = request.POST.get("sgb")
        detalhe_situacao.posto_secao = request.POST.get("posto_secao")
        detalhe_situacao.esta_adido = (
            request.POST.get("esta_adido") or None
        )  # Tratar string vazia como None
        detalhe_situacao.funcao = request.POST.get("funcao")
        detalhe_situacao.prontidao = request.POST.get("prontidao")

        # Para campos de data, use datetime.strptime para converter a string para objeto date
        # E trate o caso de campo vazio (None)
        apresentacao_str = request.POST.get("apresentacao_na_unidade")
        detalhe_situacao.apresentacao_na_unidade = (
            datetime.strptime(apresentacao_str, "%Y-%m-%d").date()
            if apresentacao_str
            else None
        )

        saida_str = request.POST.get("saida_da_unidade")
        detalhe_situacao.saida_da_unidade = (
            datetime.strptime(saida_str, "%Y-%m-%d").date() if saida_str else None
        )

        # Estes campos também devem ser atualizados se forem incluídos como hidden inputs no HTML,
        # caso contrário, manterão o valor existente no objeto detalhe_situacao.
        detalhe_situacao.op_adm = (
            request.POST.get("op_adm", detalhe_situacao.op_adm) or None
        )  # Adicionado: Garantir que pode ser None
        detalhe_situacao.cat_efetivo = request.POST.get(
            "cat_efetivo", detalhe_situacao.cat_efetivo
        )  # Adicionado: Pegar do POST

        detalhe_situacao.data_alteracao = (
            timezone.now()
        )  # Atualiza a data de alteração do objeto principal
        detalhe_situacao.usuario_alteracao = request.user
        detalhe_situacao.save()  # Salva as alterações no objeto DetalhesSituacao principal

        return JsonResponse(
            {
                "success": True,
                "message": "Situação funcional atualizada com sucesso!",
                "updated_data": {
                    "situacao": detalhe_situacao.situacao,
                    "saida_da_unidade": (
                        detalhe_situacao.saida_da_unidade.strftime("%d/%m/%Y")
                        if detalhe_situacao.saida_da_unidade
                        else None
                    ),
                },
            }
        )

    except DetalhesSituacao.DoesNotExist:
        logger.warning(f"DetalhesSituacao não encontrado para o cadastro ID: {id}")
        return JsonResponse(
            {"success": False, "message": "Detalhes de situação não encontrados."},
            status=404,
        )
    except Exception as e:
        logger.error(
            f"Erro inesperado ao salvar a situação funcional para o militar ID {id}: {e}"
        )
        return JsonResponse(
            {"success": False, "message": f"Erro interno do servidor: {e}"}, status=500
        )


@login_required
@require_http_methods(["POST"])
def excluir_historico_promocao(request, promocao_id):
    cadastro_id = None  # Initialize cadastro_id to None for safe fallback
    try:
        # Use HistoricoPromocao model for get_object_or_404
        promocao = get_object_or_404(HistoricoPromocao, id=promocao_id)
        cadastro_id = promocao.cadastro.id  # Get cadastro_id before deletion
        promocao.delete()
        # Removed redundant extra_tags as styling is handled by message.tags in the template
        messages.success(request, "Registro de promoção excluído com sucesso!")
    except Exception as e:
        # Removed redundant extra_tags
        messages.error(request, f"Erro ao excluir registro de promoção: {str(e)}")

    # Always attempt to redirect, prioritizing the specific militar's history
    if cadastro_id:
        return redirect("efetivo:historico_movimentacoes", id=cadastro_id)
    else:
        # Fallback if cadastro_id could not be determined (e.g., object not found initially)
        return redirect("efetivo:listar_militar")


@login_required
@require_http_methods(["POST"])
def excluir_historico_detalhe_situacao(request, detalhe_id):

    cadastro_id = None  # Initialize cadastro_id to None for safe fallback
    try:
        # Use HistoricoDetalhesSituacao model for get_object_or_404
        detalhe_situacao = get_object_or_404(HistoricoDetalhesSituacao, id=detalhe_id)
        cadastro_id = detalhe_situacao.cadastro.id  # Get cadastro_id before deletion
        detalhe_situacao.delete()
        # Removed redundant extra_tags
        messages.success(
            request, "Registro de detalhe de situação excluído com sucesso!"
        )
    except Exception as e:
        # Removed redundant extra_tags
        messages.error(
            request, f"Erro ao excluir registro de detalhe de situação: {str(e)}"
        )

    # Always attempt to redirect, prioritizing the specific militar's history
    if cadastro_id:
        return redirect("efetivo:historico_movimentacoes", id=cadastro_id)
    else:
        # Fallback if cadastro_id could not be determined
        return redirect("efetivo:listar_militar")


# efetivo/views.py
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model  # Importar o modelo User
from backend.efetivo.models import (  # Certifique-se de que todos os modelos necessários estão importados
    Cadastro,
    DetalhesSituacao,
    Promocao,
    Imagem,
    CatEfetivo,
    HistoricoDetalhesSituacao,
    HistoricoCatEfetivo,
)


import logging

logger = logging.getLogger(__name__)

# Obter o modelo de usuário personalizado
User = get_user_model()


@login_required
def visualizar_militar_publico(request, id):
    """
    Exibe o perfil público do militar logado, garantindo que as promoções,
    situação funcional e dados derivados sejam os mais recentes e corretos.
    Inclui todos os dados necessários para o template visualizar_militar_publico.html.
    """
    try:
        logged_in_user = request.user

        # Garantir que o usuário logado tem cadastro vinculado
        if not hasattr(logged_in_user, "cadastro") or not logged_in_user.cadastro:
            messages.error(
                request,
                "Seu perfil de usuário não está vinculado a um cadastro militar.",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )
            return redirect("core:index")

        # Garantir que só pode ver o próprio perfil
        if logged_in_user.cadastro.id != id:
            messages.error(
                request,
                "Acesso não autorizado: você só pode visualizar seu próprio perfil.",
                extra_tags="bg-red-500 text-white p-4 rounded",
            )
            return redirect("core:index")

        # Busca otimizada do cadastro e relações
        cadastro = (
            Cadastro.objects.select_related("user")
            .prefetch_related(
                Prefetch(
                    "imagens", queryset=Imagem.objects.all().order_by("-create_at")
                ),
                Prefetch(
                    "promocoes",
                    queryset=Promocao.objects.all().order_by("-ultima_promocao"),
                ),
                Prefetch(
                    "detalhes_situacao",
                    queryset=DetalhesSituacao.objects.all().order_by("-data_alteracao"),
                ),
                Prefetch(
                    "categorias_efetivo",
                    queryset=CatEfetivo.objects.filter(ativo=True).order_by(
                        "-data_inicio"
                    ),
                ),
                Prefetch("cadastro_rpt"),
                Prefetch(
                    "lp_set",
                    queryset=LP.objects.filter(
                        status_lp=LP.StatusLP.CONCLUIDO
                    ).order_by("numero_lp"),
                ),
            )
            .get(id=id)
        )

        today = timezone.now().date()

        # Pega a situação funcional mais recente
        detalhes = cadastro.detalhes_situacao.order_by(
            "-data_alteracao", "-id"  # Data/hora de edição  # Mais recente de verdade
        ).first()

        # Pega a promoção *atual* pela última data real de promoção
        promocao = cadastro.promocoes.order_by(
            "-ultima_promocao",  # Data real de promoção
            "-data_alteracao",  # Data/hora que foi salva no sistema
            "-id",  # ID mais alto = mais recente de verdade
        ).first()

        # Categoria atual ativa
        categoria_atual = cadastro.categorias_efetivo.first()

        # Todas promoções para o template (ordenadas corretamente)
        promocoes = cadastro.promocoes.order_by("-ultima_promocao")

        # Histórico de detalhes de situação
        historico_detalhes_situacao = HistoricoDetalhesSituacao.objects.filter(
            cadastro=cadastro
        ).order_by("-data_alteracao")

        # Histórico de categorias
        historico_detalhes_cat = HistoricoCatEfetivo.objects.filter(
            cat_efetivo__cadastro=cadastro, deletado=False
        ).order_by("-data_registro")

        # LPs concluídas com fruição associada
        lps_concluidas = list(cadastro.lp_set.all())
        for lp in lps_concluidas:
            try:
                lp.previsao_associada = LP_fruicao.objects.get(lp_concluida=lp)
            except LP_fruicao.DoesNotExist:
                lp.previsao_associada = None

        # MENSAGENS_RESTRICOES e a lógica de restrições permanecem as mesmas
        MENSAGENS_RESTRICOES = {
            "BS": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "CI": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "DV": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "EF": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio. As OPM estabelecerão plano de exercícios físicos compatíveis.",
            "FO": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "IS": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "LP": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "MA": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "MC": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "MG": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "OU": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "PO": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "PQ": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "SA": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "SE": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "SH": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "SM": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "SP": "Deverá ser empregado em atividades operacionais nos locais da Unidade que disponham de condições que atendam às suas restrições, ou em atividades de guarda do quartel, administrativas ou de apoio.",
            "AU": "Deverá ser empregado somente em atividades administrativas.",
            "EP": "Deverá ser empregado somente em atividades administrativas.",
            "ES": "Deverá ser empregado somente em atividades administrativas.",
            "LR": "Deverá ser empregado somente em atividades administrativas.",
            "PT": "Deverá ser empregado somente em atividades administrativas.",
            "VP": "Deverá ser empregado somente em atividades administrativas.",
            "SN": "Deverá ser escalado para trabalhar durante o dia em qualquer atividade.",
            "SG": "Deverá ser empregado, preferencialmente, na atividade de policiamento ostensivo, ou, caso não seja possível, em atividades administrativas e de apoio.",
            "UA": "Deverá ser desarmado e empregado em atividades administrativas. Pode requerer processo administrativo para verificar condições de permanência no serviço ativo.",
            "UU": "Deverá ser escalado em atividades administrativas ou de apoio, com uniforme de treinamento físico (B-5.1), sem atendimento ao público.",
            "CC": "Deverá ser escalado em atividades administrativas ou de apoio, com uniforme de treinamento físico (B-5.1), sem atendimento ao público. Cabelos penteados com gel/rede obrigatoriamente.",
            "CB": "Deverá ser escalado em atividades administrativas ou de apoio, com uniforme de treinamento físico (B-5.1), sem atendimento ao público.",
            "UB": "Deverá calçar sandálias de borracha na cor preta, sem estampas, e ser escalado em atividades administrativas ou de apoio.",
            "UC": "Deverá calçar sandálias de borracha na cor preta, sem estampas, e ser escalado em atividades administrativas ou de apoio.",
            "US": "Deverá calçar sandálias de borracha na cor preta, sem estampas, e ser escalado em atividades administrativas ou de apoio.",
            "DG": "Deverá ser empregado no policiamento ostensivo.",
            "EM": "Deverá ser empregado no policiamento ostensivo.",
            "LS": "Deverá ser empregado no policiamento ostensivo.",
            "MP": "Deverá ser empregado no policiamento ostensivo.",
            "SB": "Deverá ser empregado no policiamento ostensivo.",
            "SI": "Deverá ser empregado no policiamento ostensivo.",
            "ST": "Deverá ser empregado no policiamento ostensivo.",
        }

        restricoes_aplicaveis = []
        if categoria_atual and categoria_atual.tipo == "RESTRICAO":
            campos_restricao = [
                f.name
                for f in CatEfetivo._meta.get_fields()
                if f.name.startswith("restricao_") and hasattr(f, "verbose_name")
            ]
            for campo in campos_restricao:
                valor_campo = getattr(categoria_atual, campo, None)
                if valor_campo:
                    sigla = campo.split("_")[-1].upper()
                    if sigla in MENSAGENS_RESTRICOES:
                        verbose_name = CatEfetivo._meta.get_field(campo).verbose_name
                        restricoes_aplicaveis.append(
                            {
                                "sigla": sigla,
                                "nome": verbose_name,
                                "mensagem": MENSAGENS_RESTRICOES[sigla],
                                "regra": "",
                            }
                        )

        # Status visual da categoria
        if categoria_atual:
            if (
                categoria_atual.tipo != "ATIVO"
                and categoria_atual.data_termino
                and categoria_atual.data_termino < today
            ):
                categoria_atual.status_display = {
                    "texto": f"{categoria_atual.get_tipo_display()} (Expirado)",
                    "classe": "bg-red-100 text-red-800",
                    "icone": "fa-exclamation-triangle",
                }
            elif categoria_atual.tipo != "ATIVO":
                categoria_atual.status_display = {
                    "texto": f"{categoria_atual.get_tipo_display()} (Até {categoria_atual.data_termino.strftime('%d/%m/%Y') if categoria_atual.data_termino else 'Indefinido'})",
                    "classe": "bg-yellow-100 text-yellow-800",
                    "icone": "fa-info-circle",
                }
            else:
                categoria_atual.status_display = {
                    "texto": categoria_atual.get_tipo_display(),
                    "classe": "bg-green-100 text-green-800",
                    "icone": "fa-check-circle",
                }

        # Cursos especiais
        cursos_especiais = []
        if detalhes and detalhes.op_adm:
            tag_desejada = (
                "Administrativo"
                if detalhes.op_adm == "Administrativo"
                else "Operacional"
            )
            cursos_filtrados = []
            if hasattr(Curso, "CURSOS_TAGS"):
                for curso in Curso.objects.filter(cadastro=cadastro):
                    if Curso.CURSOS_TAGS.get(curso.curso) == tag_desejada:
                        cursos_filtrados.append(
                            {
                                "nome": curso.get_curso_display(),
                                "data": curso.data_publicacao,
                            }
                        )
                cursos_especiais = list(
                    {
                        c["nome"]: c
                        for c in sorted(
                            cursos_filtrados, key=lambda x: x["data"], reverse=True
                        )
                    }.values()
                )

        # Medalhas e cursos completos
        medalhas_do_militar = Medalha.objects.filter(cadastro=cadastro).order_by(
            "-data_publicacao_lp"
        )
        cursos_do_militar = Curso.objects.filter(cadastro=cadastro).order_by(
            "-data_publicacao"
        )

        # Cadastro RPT e contagem
        cadastro_rpt = None
        count_in_section = 0
        if hasattr(cadastro, "cadastro_rpt"):
            cadastro_rpt = cadastro.cadastro_rpt
            if cadastro_rpt and hasattr(cadastro_rpt, "posto_secao_destino"):
                count_in_section = Cadastro_rpt.objects.filter(
                    posto_secao_destino=cadastro_rpt.posto_secao_destino,
                    status="Aguardando",
                ).count()

        # Contexto completo para o template
        context = {
            "cadastro": cadastro,
            "detalhes": detalhes,
            "promocao": promocao,
            "today": today,
            "categoria_atual": categoria_atual,
            "restricoes_aplicaveis": restricoes_aplicaveis,
            "medalhas_do_militar": medalhas_do_militar,
            "cursos_do_militar": cursos_do_militar,
            "cadastro_rpt": cadastro_rpt,
            "count_in_section": count_in_section,
            "cursos_especiais": cursos_especiais,
            "lps_concluidas": lps_concluidas,
            "promocoes": promocoes,
            "historico_detalhes_situacao": historico_detalhes_situacao,
            "historico_categorias_militar": historico_detalhes_cat,
            # Choices para selects no front
            "situacao_choices": DetalhesSituacao.situacao_choices,
            "sgb_choices": DetalhesSituacao.sgb_choices,
            "posto_secao_choices": DetalhesSituacao.posto_secao_choices,
            "esta_adido_choices": DetalhesSituacao.esta_adido_choices,
            "funcao_choices": DetalhesSituacao.funcao_choices,
            "op_adm_choices": DetalhesSituacao.op_adm_choices,
            "prontidao_choices": DetalhesSituacao.prontidao_choices,
            "posto_grad_choices": Promocao.posto_grad_choices,
            "quadro_choices": Promocao.quadro_choices,
            "grupo_choices": Promocao.grupo_choices,
            "genero_choices": Cadastro.genero_choices,
            "alteracao_choices": Cadastro.alteracao_choices,
            "categoria_choices": CatEfetivo.TIPO_CHOICES,
        }

        return render(request, "efetivo/visualizar_militar_publico.html", context)

    except User.DoesNotExist:
        messages.error(
            request,
            "Usuário não encontrado.",
            extra_tags="bg-red-500 text-white p-4 rounded",
        )
        return redirect("core:index")
    except Cadastro.DoesNotExist:
        messages.error(
            request,
            "Cadastro militar não encontrado.",
            extra_tags="bg-red-500 text-white p-4 rounded",
        )
        return redirect("core:index")
    except Exception as e:
        logger.error(f"Erro ao acessar perfil público ID {id}: {e}", exc_info=True)
        messages.error(
            request,
            "Erro interno ao carregar os dados.",
            extra_tags="bg-red-500 text-white p-4 rounded",
        )
        return redirect("core:index")


