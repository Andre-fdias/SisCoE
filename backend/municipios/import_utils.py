from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
import pandas as pd

from .models import Posto, Contato, Pessoal, Cidade

# Mapeamento para garantir consistência dos cabeçalhos (lowercase e sem espaços)
# Assegure que os nomes das colunas no seu arquivo CSV/Excel correspondam a estas chaves.
COLUMN_MAPPING = {
    "sgb": "sgb",
    "posto_secao": "posto_secao",
    "posto_atendimento": "posto_atendimento",
    "cidade_posto": "cidade_posto",
    "tipo_cidade": "tipo_cidade",
    "op_adm": "op_adm",
    "quartel": "quartel",  # Para ImagemField, o valor aqui seria o caminho do arquivo, o que geralmente não é feito via importação simples
    "data_criacao": "data_criacao",
    "usuario_id": "usuario_id",  # Usar _id para ForeignKeys
    "telefone": "telefone",
    "rua": "rua",
    "numero": "numero",
    "complemento": "complemento",
    "bairro": "bairro",
    "cidade_contato": "cidade_contato",  # Coluna no CSV para o campo cidade do Contato
    "cep": "cep",
    "email": "email",
    "longitude_contato": "longitude_contato",
    "latitude_contato": "latitude_contato",
    "cel": "cel",
    "ten_cel": "ten_cel",
    "maj": "maj",
    "cap": "cap",
    "tenqo": "tenqo",
    "tenqa": "tenqa",
    "asp": "asp",
    "st_sgt": "st_sgt",
    "cb_sd": "cb_sd",
    "descricao_cidade": "descricao_cidade",  # Coluna no CSV para a descrição da Cidade
    "municipio": "municipio",  # Coluna no CSV para o nome do Município
    "longitude_cidade": "longitude_cidade",
    "latitude_cidade": "latitude_cidade",
    "bandeira": "bandeira",  # Para ImageField
}


def parse_date(date_str):
    """Tenta converter uma string de data em objeto datetime"""
    if not date_str or str(date_str).lower() == "nan":
        return None

    date_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",  # Adicionado formato comum americano
        "%Y/%m/%d",
    ]

    for fmt in date_formats:
        try:
            # Tenta converter para float primeiro para pegar datas em formato numérico de Excel
            if isinstance(date_str, (int, float)):
                # Converte o número de série do Excel para datetime
                return datetime.fromtimestamp(
                    (date_str - 25569) * 86400
                )  # Baseado em 1970-01-01
            return datetime.strptime(str(date_str).strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def safe_int(value, default=0):
    """Converte para inteiro com valor padrão se falhar. Lida com NaN/empty strings."""
    try:
        if (
            pd.isna(value) or value == ""
        ):  # Usar pandas.isna para NaN e verificar string vazia
            return default
        return int(
            float(value)
        )  # Converte para float primeiro para lidar com decimais ou strings como "10.0"
    except (ValueError, TypeError):
        return default


def safe_float(value, default=None):
    """Converte para float com valor padrão se falhar. Lida com NaN/empty strings."""
    try:
        if pd.isna(value) or value == "":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def clean_header(header):
    """Limpa o cabeçalho para corresponder ao mapeamento."""
    return header.strip().lower().replace(" ", "_").replace("-", "_")


def importar_dados(arquivo_path, usuario):
    registros_processados = 0
    erros_processamento = []
    User = get_user_model()  # Obter o modelo de usuário

    try:
        # Tenta ler com pandas, que é mais robusto para CSV/Excel
        df = pd.read_csv(arquivo_path, sep=None, engine="python", encoding="utf-8")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(
                arquivo_path, sep=None, engine="python", encoding="latin-1"
            )
        except Exception as e:
            erros_processamento.append(
                f"Erro ao ler arquivo (decodificação/formato): {str(e)}"
            )
            return 0, erros_processamento
    except Exception as e:
        # Se não for CSV, tenta Excel
        try:
            df = pd.read_excel(arquivo_path)
        except Exception as e_excel:
            erros_processamento.append(
                f"Erro ao ler arquivo (CSV ou Excel): {str(e)} / {str(e_excel)}"
            )
            return 0, erros_processamento

    # Normalizar os nomes das colunas no DataFrame
    df.columns = [clean_header(col) for col in df.columns]

    # Verificar se todos os cabeçalhos necessários existem no DataFrame
    missing_headers = [col for col in COLUMN_MAPPING.keys() if col not in df.columns]
    if missing_headers:
        erros_processamento.append(
            f"Cabeçalhos obrigatórios ausentes no arquivo: {', '.join(missing_headers)}. Verifique as instruções de importação."
        )
        return 0, erros_processamento

    # Iterar sobre as linhas do DataFrame
    for linha_num, row_series in df.iterrows():
        linha_dict = row_series.to_dict()
        current_line_errors = []

        try:
            with transaction.atomic():  # Garante que todas as operações para uma linha são atômicas
                # --- Processar Posto ---
                posto_atendimento = linha_dict.get(
                    COLUMN_MAPPING["posto_atendimento"], ""
                ).strip()
                if not posto_atendimento:
                    current_line_errors.append(
                        "campo 'posto_atendimento' é obrigatório para Posto."
                    )
                    raise ValueError(
                        "Posto Atendimento é obrigatório."
                    )  # Levanta erro para pular esta linha

                posto_data = {
                    "sgb": linha_dict.get(COLUMN_MAPPING["sgb"], "").strip(),
                    "posto_secao": linha_dict.get(
                        COLUMN_MAPPING["posto_secao"], ""
                    ).strip(),
                    "posto_atendimento": posto_atendimento,
                    "cidade_posto": linha_dict.get(
                        COLUMN_MAPPING["cidade_posto"], ""
                    ).strip(),
                    "tipo_cidade": linha_dict.get(
                        COLUMN_MAPPING["tipo_cidade"], ""
                    ).strip(),
                    "op_adm": linha_dict.get(COLUMN_MAPPING["op_adm"], "").strip(),
                    # 'quartel': linha_dict.get(COLUMN_MAPPING['quartel'], '').strip() or None, # ImageField não pode ser importado assim
                    "data_criacao": parse_date(
                        linha_dict.get(COLUMN_MAPPING["data_criacao"])
                    ),
                }

                # Validar choices para Posto
                if posto_data["sgb"] not in [c[0] for c in Posto.sgb_choices if c[0]]:
                    posto_data["sgb"] = ""  # Default para vazio se for inválido
                if posto_data["op_adm"] not in [
                    c[0] for c in Posto.op_adm_choices if c[0]
                ]:
                    posto_data["op_adm"] = ""  # Default para vazio se for inválido
                if posto_data["posto_secao"] not in [
                    c[0] for c in Posto.posto_secao_choices if c[0]
                ]:
                    posto_data["posto_secao"] = ""  # Default para vazio se for inválido

                # Tentar encontrar o usuário
                usuario_id = safe_int(linha_dict.get(COLUMN_MAPPING["usuario_id"]))
                if usuario_id is None:
                    # Se usuario_id não for fornecido, usar o usuário da requisição
                    posto_data["usuario"] = usuario
                else:
                    try:
                        posto_data["usuario"] = User.objects.get(id=usuario_id)
                    except ObjectDoesNotExist:
                        current_line_errors.append(
                            f"Usuário com ID {usuario_id} não encontrado."
                        )
                        posto_data["usuario"] = (
                            usuario  # Fallback para o usuário logado
                        )
                    except Exception as e:
                        current_line_errors.append(
                            f"Erro ao buscar usuário {usuario_id}: {str(e)}"
                        )
                        posto_data["usuario"] = (
                            usuario  # Fallback para o usuário logado
                        )

                # Tenta obter o posto existente, se não existir, cria um novo
                posto, created = Posto.objects.get_or_create(
                    posto_atendimento=posto_atendimento,  # Campo único para get_or_create
                    defaults=posto_data,
                )
                if not created:
                    # Se o posto já existe, atualiza os campos (exceto o que já foi usado para get_or_create)
                    for key, value in posto_data.items():
                        setattr(posto, key, value)
                    posto.save()

                # --- Processar Contato ---
                contato_data = {
                    "posto": posto,
                    "telefone": (
                        str(
                            safe_int(
                                linha_dict.get(COLUMN_MAPPING["telefone"]), default=""
                            )
                        )
                        if linha_dict.get(COLUMN_MAPPING["telefone"])
                        else ""
                    ),  # Garante string vazia se None
                    "rua": linha_dict.get(COLUMN_MAPPING["rua"], "").strip(),
                    "numero": linha_dict.get(COLUMN_MAPPING["numero"], "").strip(),
                    "complemento": linha_dict.get(
                        COLUMN_MAPPING["complemento"], ""
                    ).strip()
                    or None,
                    "bairro": linha_dict.get(COLUMN_MAPPING["bairro"], "").strip(),
                    "cidade": linha_dict.get(
                        COLUMN_MAPPING["cidade_contato"], ""
                    ).strip(),  # Usar 'cidade_contato' do CSV
                    "cep": (
                        str(safe_int(linha_dict.get(COLUMN_MAPPING["cep"]), default=""))
                        if linha_dict.get(COLUMN_MAPPING["cep"])
                        else ""
                    ),  # Garante string vazia se None
                    "email": linha_dict.get(COLUMN_MAPPING["email"], "").strip()
                    or None,
                    "longitude": safe_float(
                        linha_dict.get(COLUMN_MAPPING["longitude_contato"])
                    ),
                    "latitude": safe_float(
                        linha_dict.get(COLUMN_MAPPING["latitude_contato"])
                    ),
                }
                # Tenta obter o contato existente para este posto, ou cria um novo
                contato, created_contato = Contato.objects.get_or_create(
                    posto=posto, defaults=contato_data
                )
                if not created_contato:
                    for key, value in contato_data.items():
                        setattr(contato, key, value)
                    contato.save()

                # --- Processar Pessoal ---
                pessoal_data = {
                    "posto": posto,
                    "cel": safe_int(linha_dict.get(COLUMN_MAPPING["cel"])),
                    "ten_cel": safe_int(linha_dict.get(COLUMN_MAPPING["ten_cel"])),
                    "maj": safe_int(linha_dict.get(COLUMN_MAPPING["maj"])),
                    "cap": safe_int(linha_dict.get(COLUMN_MAPPING["cap"])),
                    "tenqo": safe_int(linha_dict.get(COLUMN_MAPPING["tenqo"])),
                    "tenqa": safe_int(linha_dict.get(COLUMN_MAPPING["tenqa"])),
                    "asp": safe_int(linha_dict.get(COLUMN_MAPPING["asp"])),
                    "st_sgt": safe_int(linha_dict.get(COLUMN_MAPPING["st_sgt"])),
                    "cb_sd": safe_int(linha_dict.get(COLUMN_MAPPING["cb_sd"])),
                }
                # Tenta obter o pessoal existente para este posto, ou cria um novo
                pessoal, created_pessoal = Pessoal.objects.get_or_create(
                    posto=posto, defaults=pessoal_data
                )
                if not created_pessoal:
                    for key, value in pessoal_data.items():
                        setattr(pessoal, key, value)
                    pessoal.save()

                # --- Processar Cidade ---
                municipio_nome = linha_dict.get(COLUMN_MAPPING["municipio"], "").strip()
                if not municipio_nome:
                    current_line_errors.append(
                        "campo 'municipio' é obrigatório para Cidade."
                    )
                    raise ValueError(
                        "Nome do município é obrigatório."
                    )  # Levanta erro para pular esta linha

                cidade_data = {
                    "posto": posto,
                    "descricao": linha_dict.get(
                        COLUMN_MAPPING["descricao_cidade"], ""
                    ).strip()
                    or None,
                    "municipio": municipio_nome,
                    "longitude": safe_float(
                        linha_dict.get(COLUMN_MAPPING["longitude_cidade"])
                    ),
                    "latitude": safe_float(
                        linha_dict.get(COLUMN_MAPPING["latitude_cidade"])
                    ),
                    # 'bandeira': linha_dict.get(COLUMN_MAPPING['bandeira'], '').strip() or None, # ImageField não pode ser importado assim
                }
                # Tenta obter a cidade existente para este posto e este município, ou cria uma nova
                cidade, created_cidade = Cidade.objects.get_or_create(
                    posto=posto,
                    municipio=municipio_nome,  # Adicionar municipio para get_or_create para evitar duplicação para o mesmo posto
                    defaults=cidade_data,
                )
                if not created_cidade:
                    for key, value in cidade_data.items():
                        setattr(cidade, key, value)
                    cidade.save()

                if not current_line_errors:
                    registros_processados += 1

        except ValueError as e:
            erros_processamento.append(
                f"Linha {linha_num + 2}: Erro de valor - {str(e)}. Dados: {linha_dict}"
            )
        except ObjectDoesNotExist as e:
            erros_processamento.append(
                f"Linha {linha_num + 2}: Objeto relacionado não encontrado - {str(e)}. Dados: {linha_dict}"
            )
        except IntegrityError as e:
            erros_processamento.append(
                f"Linha {linha_num + 2}: Erro de integridade (duplicidade ou FK inválida) - {str(e)}. Dados: {linha_dict}"
            )
        except ValidationError as e:
            erros_processamento.append(
                f"Linha {linha_num + 2}: Erro de validação do modelo - {e.messages}. Dados: {linha_dict}"
            )
        except Exception as e:
            # Captura qualquer outra exceção inesperada
            erros_processamento.append(
                f"Linha {linha_num + 2}: Erro inesperado - {str(e)}. Dados: {linha_dict}"
            )

        if current_line_errors:
            erros_processamento.extend(
                [f"Linha {linha_num + 2}: {err}" for err in current_line_errors]
            )

    return registros_processados, erros_processamento
