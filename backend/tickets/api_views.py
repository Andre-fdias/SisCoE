import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem

logger = logging.getLogger(__name__)


@csrf_exempt
def buscar_dados_cpf(request):
    """API para buscar dados do militar por CPF"""
    logger.info("=== INÍCIO buscar_dados_cpf ===")

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            cpf = data.get("cpf", "")
            logger.info(f"CPF recebido: {cpf}")

            if not cpf or len(cpf) != 14:
                logger.error(f"CPF inválido: {cpf}")
                return JsonResponse(
                    {"error": "CPF inválido ou fora do formato XXX.XXX.XXX-XX"},
                    status=400,
                )

            # Limpa o CPF
            cpf_limpo = cpf.replace(".", "").replace("-", "")
            logger.info(f"CPF limpo para busca: {cpf_limpo}")

            # Busca o cadastro pelo CPF - TENTA COM E SEM FORMATAÇÃO
            try:
                # Primeiro tenta com formatação
                cadastro = Cadastro.objects.get(cpf=cpf)
                logger.info(f"Cadastro encontrado COM formatação: {cadastro.nome}")
            except Cadastro.DoesNotExist:
                # Tenta sem formatação
                cadastro = Cadastro.objects.get(cpf=cpf_limpo)
                logger.info(f"Cadastro encontrado SEM formatação: {cadastro.nome}")

            # Busca os dados mais recentes da situação
            situacao = (
                DetalhesSituacao.objects.filter(cadastro=cadastro)
                .order_by("-data_alteracao")
                .first()
            )
            logger.info(f"Situação encontrada: {situacao}")

            # Busca a promoção mais recente
            promocao = (
                Promocao.objects.filter(cadastro=cadastro)
                .order_by("-data_alteracao")
                .first()
            )
            logger.info(f"Promoção encontrada: {promocao}")

            # Busca a foto mais recente
            foto = (
                Imagem.objects.filter(cadastro=cadastro).order_by("-create_at").first()
            )
            logger.info(f"Foto encontrada: {foto}")

            response_data = {
                "nome": cadastro.nome,
                "nome_guerra": cadastro.nome_de_guerra,
                "email": cadastro.email,
                "telefone": cadastro.telefone,
                "re": f"{cadastro.re}-{cadastro.dig}",
                "posto_grad": promocao.posto_grad if promocao else "",
                "sgb": situacao.sgb if situacao else "",
                "posto_secao": situacao.posto_secao if situacao else "",
                "foto_url": foto.image.url if foto else "",
            }

            logger.info(f"Dados retornados: {response_data}")
            return JsonResponse(response_data)

        except Cadastro.DoesNotExist:
            logger.error(
                f"Cadastro não encontrado para CPF (com e sem formatação): {cpf}"
            )
            return JsonResponse({"error": "Militar não encontrado"}, status=404)
        except Exception as e:
            logger.error(f"Erro em buscar_dados_cpf: {str(e)}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método não permitido"}, status=405)
