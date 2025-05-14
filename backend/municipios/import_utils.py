import csv
import os
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Posto, Contato, Pessoal, Cidade

def parse_date(date_str):
    """Tenta converter uma string de data em objeto datetime"""
    if not date_str or str(date_str).lower() == 'nan':
        return None
    
    date_formats = [
        '%Y-%m-%d %H:%M:%S',
        '%d/%m/%Y %H:%M:%S',
        '%Y-%m-%d',
        '%d/%m/%Y'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            continue
    return None

def safe_int(value, default=0):
    """Converte para inteiro com valor padrão se falhar"""
    try:
        return int(float(value)) if value else default
    except (ValueError, TypeError):
        return default

def safe_float(value, default=None):
    """Converte para float com valor padrão se falhar"""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def importar_dados(arquivo_csv, usuario):
    """
    Importa dados de um arquivo CSV para os modelos Posto, Contato, Pessoal e Cidade.
    
    Args:
        arquivo_csv (str): Caminho completo para o arquivo CSV
        usuario (User): Usuário responsável pela importação
        
    Returns:
        tuple: (registros_processados, erros_processamento)
    """
    registros_processados = 0
    erros_processamento = []
    required_fields = [
        'sgb', 'posto_secao', 'posto_atendimento', 'cidade_posto',
        'tipo_cidade', 'op_adm', 'telefone', 'rua', 'numero',
        'bairro', 'cidade_contato', 'cep', 'email', 'municipio'
    ]

    try:
        with open(arquivo_csv, 'r', encoding='utf-8') as arquivo:
            # Verifica se o arquivo está vazio
            if arquivo.read(1) == '':
                erros_processamento.append("Arquivo CSV vazio")
                return 0, erros_processamento
            arquivo.seek(0)
            
            leitor_csv = csv.DictReader(arquivo, delimiter=';')
            
            # Verifica campos obrigatórios
            missing_fields = [field for field in required_fields if field not in leitor_csv.fieldnames]
            if missing_fields:
                erros_processamento.append(
                    f"Campos obrigatórios faltantes: {', '.join(missing_fields)}"
                )
                return 0, erros_processamento

            for linha_num, linha in enumerate(leitor_csv, 1):
                try:
                    # Processamento dos dados
                    dados = {
                        'sgb': linha['sgb'].strip(),
                        'posto_secao': linha['posto_secao'].strip(),
                        'posto_atendimento': linha['posto_atendimento'].strip(),
                        'cidade_posto': linha['cidade_posto'].strip(),
                        'tipo_cidade': linha['tipo_cidade'].strip(),
                        'op_adm': linha['op_adm'].strip(),
                        'quartel': linha.get('quartel', '').strip() or None,
                        'data_criacao': parse_date(linha.get('data_criacao')),
                        'usuario_id': safe_int(linha.get('usuario_id', usuario.id)),
                    }

                    # Criar Posto
                    posto = Posto.objects.create(
                        **dados,
                        usuario=usuario if 'usuario_id' not in linha else User.objects.get(id=dados['usuario_id'])
                    )

                    # Criar Contato
                    Contato.objects.create(
                        posto=posto,
                        telefone=linha['telefone'].strip(),
                        rua=linha['rua'].strip(),
                        numero=linha['numero'].strip(),
                        complemento=linha.get('complemento', '').strip(),
                        bairro=linha['bairro'].strip(),
                        cidade=linha['cidade_contato'].strip(),
                        cep=linha['cep'].strip(),
                        email=linha['email'].strip(),
                        longitude=safe_float(linha.get('longitude_contato')),
                        latitude=safe_float(linha.get('latitude_contato')),
                    )

                    # Criar Pessoal
                    Pessoal.objects.create(
                        posto=posto,
                        cel=safe_int(linha.get('cel')),
                        ten_cel=safe_int(linha.get('ten_cel')),
                        maj=safe_int(linha.get('maj')),
                        cap=safe_int(linha.get('cap')),
                        tenqo=safe_int(linha.get('tenqo')),
                        tenqa=safe_int(linha.get('tenqa')),
                        asp=safe_int(linha.get('asp')),
                        st_sgt=safe_int(linha.get('st_sgt')),
                        cb_sd=safe_int(linha.get('cb_sd')),
                    )

                    # Criar Cidade
                    Cidade.objects.create(
                        posto=posto,
                        descricao=linha.get('descricao_cidade', '').strip(),
                        municipio=linha['municipio'].strip(),
                        longitude=safe_float(linha.get('longitude_cidade')),
                        latitude=safe_float(linha.get('latitude_cidade')),
                        bandeira=linha.get('bandeira', '').strip() or None,
                    )

                    registros_processados += 1

                except ObjectDoesNotExist as e:
                    erros_processamento.append(
                        f"Linha {linha_num}: Usuário com ID {linha.get('usuario_id')} não encontrado"
                    )
                except Exception as e:
                    erros_processamento.append(
                        f"Linha {linha_num}: Erro ao processar - {str(e)}"
                    )

    except UnicodeDecodeError:
        try:
            with open(arquivo_csv, 'r', encoding='latin-1') as arquivo:
                leitor_csv = csv.DictReader(arquivo, delimiter=';')
                # Repetir o processamento para latin-1
        except Exception as e:
            erros_processamento.append(f"Erro ao ler arquivo: {str(e)}")
            return 0, erros_processamento
    except Exception as e:
        erros_processamento.append(f"Erro ao processar arquivo: {str(e)}")
        return 0, erros_processamento

    return registros_processados, erros_processamento