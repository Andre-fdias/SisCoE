import requests
import logging

logger = logging.getLogger(__name__)

def fetch_wikipedia_data(cidade_nome, uf):
    """
    Busca a descrição e a URL da bandeira de um município na Wikipédia.

    :param cidade_nome: Nome do município.
    :param uf: Sigla da Unidade Federativa.
    :return: Um dicionário contendo 'descricao' and 'url_bandeira'.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "SisCoE/1.0 (https://github.com/seu_usuario/seu_repo; seu_email@example.com)"
    })

    # Termos de busca
    termo_cidade = f"{cidade_nome} ({uf})"
    termo_bandeira = f"Bandeira de {cidade_nome}"

    dados_retorno = {
        "descricao": None,
        "url_bandeira": None
    }

    # --- 1. Buscar Resumo (Extrato da página da cidade) ---
    url_wiki_api = "https://pt.wikipedia.org/w/api.php"
    params_resumo = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "titles": termo_cidade,
        "exintro": True,
        "explaintext": True,
        "redirects": 1,
    }

    try:
        response = session.get(url_wiki_api, params=params_resumo, timeout=5)
        response.raise_for_status()
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id != "-1" and "extract" in page_data:
                # Limita a descrição para evitar textos muito longos
                dados_retorno["descricao"] = page_data["extract"]
                break
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar resumo da Wikipédia para '{termo_cidade}': {e}")
    except (KeyError, IndexError):
        logger.warning(f"Estrutura de resposta inesperada do resumo da Wikipédia para '{termo_cidade}'.")


    # --- 2. Buscar Bandeira (Imagem) ---
    params_imagem = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "titles": termo_bandeira,
        "pithumbsize": 200,  # Tamanho razoável para thumbnail
        "redirects": 1,
    }

    try:
        response_img = session.get(url_wiki_api, params=params_imagem, timeout=5)
        response_img.raise_for_status()
        data_img = response_img.json()
        pages_img = data_img.get("query", {}).get("pages", {})
        for page_id, page_data in pages_img.items():
            if page_id != "-1" and "thumbnail" in page_data:
                dados_retorno["url_bandeira"] = page_data["thumbnail"]["source"]
                break
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar bandeira da Wikipédia para '{termo_bandeira}': {e}")
    except (KeyError, IndexError):
        logger.warning(f"Estrutura de resposta inesperada da imagem da Wikipédia para '{termo_bandeira}'.")

    return dados_retorno
