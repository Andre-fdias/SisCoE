import pandas as pd
from datetime import datetime

def limpar_cpf(cpf):
    """Remove caracteres não numéricos do CPF"""
    if pd.isna(cpf):
        return ''
    return str(cpf).replace('.', '').replace('-', '').strip()

def converter_data(valor):
    """Converte diversos formatos de data para o padrão YYYY-MM-DD"""
    if pd.isna(valor):
        return None
    
    # Se for número (data do Excel)
    if isinstance(valor, (int, float)):
        try:
            return (datetime(1899, 12, 30) + pd.Timedelta(days=valor)).strftime('%Y-%m-%d')
        except:
            return None
    
    # Se for string
    elif isinstance(valor, str):
        try:
            # Tenta vários formatos de data
            for fmt in ('%Y-%m-%d %H:%M:%S', '%d/%m/%Y', '%Y-%m-%d'):
                try:
                    return datetime.strptime(valor.split()[0], fmt).strftime('%Y-%m-%d')
                except:
                    continue
            return None
        except:
            return None
    
    # Se já for datetime
    elif hasattr(valor, 'strftime'):
        return valor.strftime('%Y-%m-%d')
    
    return None

def transformar_arquivo(input_path, output_path):
    # Ler o arquivo Excel
    try:
        df = pd.read_excel(input_path, sheet_name='Bombeiro_Municipal', dtype={'CNH': str, 'RG': str})
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return False
    
    # Mapear colunas do arquivo para o modelo do sistema
    mapeamento_colunas = {
        'NOME': 'nome',
        'CPF': 'cpf',
        'RG': 'rg',
        'CNH': 'cnh',
        'POSSUI CURSO ESB DE BOMBEIRO': 'esb',
        'CATEGORIA': 'cat_cnh',
        'OVB': 'ovb',
        'ADMISSÃO': 'admissao',
        'NASC': 'nasc',
        'E-MAIL PARTICULAR': 'email',
        'SGB': 'sgb',
        'Cod_Posto': 'posto_secao',
        'SITUAÇÃO': 'situacao',
        'ADMISSAO NO GB': 'apresentacao_na_unidade',
        'SAIDA DO GB': 'saida_da_unidade'
    }
    
    # Renomear colunas
    df = df.rename(columns=mapeamento_colunas)
    
    # Criar colunas que não existem no arquivo original
    df['nome_de_guerra'] = df['nome'].str.split().str[0]  # Primeiro nome como nome de guerra
    df['funcao'] = ''  # Campo vazio pois não existe no original
    df['genero'] = 'Masculino'  # Valor padrão
    df['telefone'] = ''  # Campo não presente no original
    
    # Tratamento de dados
    df['cpf'] = df['cpf'].apply(limpar_cpf)
    df['esb'] = df['esb'].apply(lambda x: 'SIM' if x == 'SIM' else 'NÃO')
    
    # Converter datas
    for col in ['admissao', 'nasc', 'apresentacao_na_unidade', 'saida_da_unidade']:
        df[col] = df[col].apply(converter_data)
    
    # Selecionar e ordenar colunas conforme o modelo
    colunas_finais = [
        'nome', 'nome_de_guerra', 'situacao', 'sgb', 'posto_secao', 'cpf', 'rg', 'cnh', 'cat_cnh',
        'esb', 'ovb', 'admissao', 'nasc', 'email', 'telefone', 'apresentacao_na_unidade',
        'saida_da_unidade', 'funcao', 'genero'
    ]
    
    df_final = df[colunas_finais]
    
    # Salvar arquivo tratado
    try:
        df_final.to_csv(output_path, index=False, encoding='utf-8-sig', sep=';')
        print(f"✅ Arquivo transformado salvo com sucesso em: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar o arquivo: {e}")
        return False

if __name__ == "__main__":
    print("=== Transformador de Arquivo de Bombeiros ===")
    input_file = input("Digite o nome do arquivo Excel de entrada (ex: Bombeiro Municipal.xlsx): ")
    output_file = input("Digite o nome do arquivo CSV de saída (ex: bombeiros_formatado.csv): ")
    
    if transformar_arquivo(input_file, output_file):
        print("\nPronto! O arquivo está formatado para importação.")
        print("Agora você pode usar este arquivo CSV no sistema Django.")
    else:
        print("\nOcorreu um erro durante o processamento.")