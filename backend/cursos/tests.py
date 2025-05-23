from django.db import models
from django.conf import settings
from backend.efetivo.models import Cadastro

class TipoMedalha(models.Model):
    TIPO_CHOICES = (
        ('INTERNAS_PMESP', 'Medalhas Internas da PMESP'),
        ('GOVERNAMENTAIS_INTERNACIONAIS', 'Medalhas Governamentais - Internacionais'),
        ('GOVERNAMENTAIS_FEDERAL', 'Medalhas Governamentais - Nível Federal'),
        ('GOVERNAMENTAIS_ESTADUAL', 'Medalhas Governamentais - Nível Estadual'),
        ('GOVERNAMENTAIS_MUNICIPAL', 'Medalhas Governamentais - Nível Municipal'),
        ('NAO_GOVERNAMENTAIS', 'Medalhas Não Governamentais - Entidades Civis'),
    )
    
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100, unique=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    
    def __str__(self):
        return self.nome

class Medalha(models.Model):
    ORDEM_CHOICES = [
        ('I', 'I'), ('II', 'II'), ('III', 'III'), ('IV', 'IV'), ('V', 'V'),
        ('VI', 'VI'), ('VII', 'VII'), ('VIII', 'VIII'), ('IX', 'IX'), ('X', 'X'),
        ('XI', 'XI'), ('XII', 'XII'),
    ]

    # Lista completa de honrarias baseada no PDF
    
        # Medalhas Internas da PMESP
        
    HONRARIA_CHOICES = [
        ("Medalha Solidariedade de Timor-Leste", "Medalha Solidariedade de Timor-Leste"),
        ("Colar Comemorativo do Sesquicentenário da Revolução Liberal de 1842 - CPI-7", "Colar Comemorativo do Sesquicentenário da Revolução Liberal de 1842 - CPI-7"),
        ("Láurea de Mérito Pessoal em 1º Grau", "Láurea de Mérito Pessoal em 1º Grau"),
        ("Láurea de Mérito Pessoal em 2º Grau", "Láurea de Mérito Pessoal em 2º Grau"),
        ("Láurea de Mérito Pessoal em 3º Grau", "Láurea de Mérito Pessoal em 3º Grau"),
        ("Láurea de Mérito Pessoal em 4º Grau", "Láurea de Mérito Pessoal em 4º Grau"),
        ("Láurea de Mérito Pessoal em 5º Grau", "Láurea de Mérito Pessoal em 5º Grau"),
        ("Medalha \"Batalhão de Expedicionários Paulistas\" do Segundo Batalhão de Polícia de Choque", "Medalha \"Batalhão de Expedicionários Paulistas\" do Segundo Batalhão de Polícia de Choque"),
        ("Medalha \"Brigadeiro Tobias\"", "Medalha \"Brigadeiro Tobias\""),
        ("Medalha \"Mérito da Inteligência\" da Policia Militar do Estado de São Paulo – CIPM", "Medalha \"Mérito da Inteligência\" da Policia Militar do Estado de São Paulo – CIPM"),
        ("Medalha \"Mérito da Justiça e Disciplina\" da Policia Militar do Estado de São Paulo", "Medalha \"Mérito da Justiça e Disciplina\" da Policia Militar do Estado de São Paulo"),
        ("Medalha \"Mérito do Comando de Policiamento da Capital", "Medalha \"Mérito do Comando de Policiamento da Capital"),
        ("Medalha \"Nathaniel Prado\" Criador do Gabinete de Munições da Força Pública – CSM/AM", "Medalha \"Nathaniel Prado\" Criador do Gabinete de Munições da Força Pública – CSM/AM"),
        ("Medalha \"Patrono do Comando de Policiamento do Interior Três – Coronel PM Paulo Monte Serrat Filho\"", "Medalha \"Patrono do Comando de Policiamento do Interior Três – Coronel PM Paulo Monte Serrat Filho\""),
        ("Medalha \"Regente Feijó\"", "Medalha \"Regente Feijó\""),
        ("Medalha 1º Centenário do 5º Batalhão de Policia Militar do Interior \"General Júlio Marcondes Salgado\"", "Medalha 1º Centenário do 5º Batalhão de Policia Militar do Interior \"General Júlio Marcondes Salgado\""),
        ("Medalha Batalhão Humaitá - 3º BPChq", "Medalha Batalhão Humaitá - 3º BPChq"),
        ("Medalha Capitão PM Alberto Mendes Júnior da PMESP", "Medalha Capitão PM Alberto Mendes Júnior da PMESP"),
        ("Medalha Centenário da Academia de Polícia Militar do Barro Branco", "Medalha Centenário da Academia de Polícia Militar do Barro Branco"),
        ("Medalha Centenário da Escola de Educação Física", "Medalha Centenário da Escola de Educação Física"),
        ("Medalha Centenário do Centro Odontológico", "Medalha Centenário do Centro Odontológico"),
        ("Medalha Cinquentenário do Centro de Formação de Aperfeiçoamento de Praças", "Medalha Cinquentenário do Centro de Formação de Aperfeiçoamento de Praças"),
        ("Medalha Cinquentenário do Décimo Sexto Batalhão de Policia Militar Metropolitano", "Medalha Cinquentenário do Décimo Sexto Batalhão de Policia Militar Metropolitano"),
        ("Medalha Cinquentenário do Departamento de Suporte Administrativo do Comando Geral – DSA/CG", "Medalha Cinquentenário do Departamento de Suporte Administrativo do Comando Geral – DSA/CG"),
        ("Medalha Comemorativa do 1º Centenário do 3º Grupamento de Incêndio do Corpo de Bombeiros – 3º GB", "Medalha Comemorativa do 1º Centenário do 3º Grupamento de Incêndio do Corpo de Bombeiros – 3º GB"),
        ("Medalha Comemorativa do Centenário do 1º Grupamento de Bombeiros", "Medalha Comemorativa do Centenário do 1º Grupamento de Bombeiros"),
        ("Medalha Comemorativa do Centenário do 6º Grupamento de Incêndio – 6º GI", "Medalha Comemorativa do Centenário do 6º Grupamento de Incêndio – 6º GI"),
        ("Medalha Comemorativa do Centenário do Corpo de Bombeiro da Policia Militar do Estado de São Paulo", "Medalha Comemorativa do Centenário do Corpo de Bombeiro da Policia Militar do Estado de São Paulo"),
        ("Medalha Comemorativa do Cinquentenário de Criação do Décinro Terceiro Batalhão de Policia Militar do Interior", "Medalha Comemorativa do Cinquentenário de Criação do Décinro Terceiro Batalhão de Policia Militar do Interior"),
        ("Medalha Comemorativa do Cinquentenário do Centro de Processamento de Dados", "Medalha Comemorativa do Cinquentenário do Centro de Processamento de Dados"),
        ("Medalha Comemorativa do Cinquentenário do Centro de Seleção, Alistamento e Estudos de Pessoal - CSAEP", "Medalha Comemorativa do Cinquentenário do Centro de Seleção, Alistamento e Estudos de Pessoal - CSAEP"),
        ("Medalha Comemorativa do Sesquicentenário da Polícia Militar do Estado de São Paulo", "Medalha Comemorativa do Sesquicentenário da Polícia Militar do Estado de São Paulo"),
        ("Medalha Coronel Paul Balagny", "Medalha Coronel Paul Balagny"),
        ("Medalha Cruz de Sangue em Bronze", "Medalha Cruz de Sangue em Bronze"),
        ("Medalha Cruz de Sangue em Bronze 2ª Concessão", "Medalha Cruz de Sangue em Bronze 2ª Concessão"),
        ("Medalha Cruz de Sangue em Bronze 3ª Concessão", "Medalha Cruz de Sangue em Bronze 3ª Concessão"),
        ("Medalha Cruz de Sangue em Ouro", "Medalha Cruz de Sangue em Ouro"),
        ("Medalha Cruz de Sangue em Prata", "Medalha Cruz de Sangue em Prata"),
        ("Medalha do 1º Centenário do Centro Médico", "Medalha do 1º Centenário do Centro Médico"),
        ("Medalha do 1º Centenário do Regimento de Polícia Montada \"9 de Julho\"", "Medalha do 1º Centenário do Regimento de Polícia Montada \"9 de Julho\""),
        ("Medalha do Centenário da Aviação da Polícia Militar do Estado de São Paulo – CAvPM", "Medalha do Centenário da Aviação da Polícia Militar do Estado de São Paulo – CAvPM"),
        ("Medalha do Centenário da Corregedoria da Polícia Militar", "Medalha do Centenário da Corregedoria da Polícia Militar"),
        ("Medalha do Centenário de Sétimo Grupamento de Bombeiros – 7º GB", "Medalha do Centenário de Sétimo Grupamento de Bombeiros – 7º GB"),
        ("Medalha do Centenário do 14º Batalhão de Polícia Militar Metropolitano", "Medalha do Centenário do 14º Batalhão de Polícia Militar Metropolitano"),
        ("Medalha do Centenário do 1º Batalhão de Polícia de Choque Tobias de Aguiar", "Medalha do Centenário do 1º Batalhão de Polícia de Choque Tobias de Aguiar"),
        ("Medalha do Centenário do 2º Batalhão de Polícia Militar Metropolitano Coronel Herculano de Carvalho e Silva", "Medalha do Centenário do 2º Batalhão de Polícia Militar Metropolitano Coronel Herculano de Carvalho e Silva"),
        ("Medalha do Centenário do 2º Grupamento de Incêndio do Corpo de Bombeiro – 2º GB", "Medalha do Centenário do 2º Grupamento de Incêndio do Corpo de Bombeiro – 2º GB"),
        ("Medalha do Centenário do 6º Batalhão de Polícia Militar do Interior – \"Ten Cei Pedro Árbues", "Medalha do Centenário do 6º Batalhão de Polícia Militar do Interior – \"Ten Cei Pedro Árbues"),
        ("Medalha do Centenário do Oltavo Batalhão de Polícia Militar do Interior", "Medalha do Centenário do Oltavo Batalhão de Polícia Militar do Interior"),
        ("Medalha do Centenário do Quarto Batalhão de Polícia Militar do Interior", "Medalha do Centenário do Quarto Batalhão de Polícia Militar do Interior"),
        ("Medalha do Cinquentenário da Diretoria de Saúde – DS", "Medalha do Cinquentenário da Diretoria de Saúde – DS"),
        ("Medalha do Cinquentenário do 10º Batalhão de Polícia Militar Metropolitano \"Cei PM Bertholazzi\"", "Medalha do Cinquentenário do 10º Batalhão de Polícia Militar Metropolitano \"Cei PM Bertholazzi\""),
        ("Medalha do Cinquentenário do 12º Batalhão de Polícia Militar Metropolitano", "Medalha do Cinquentenário do 12º Batalhão de Polícia Militar Metropolitano"),
        ("Medalha do Cinquentenário do Canil", "Medalha do Cinquentenário do Canil"),
        ("Medalha do Cinquentenário do Centro de Suprimento e Manutenção de Material de Motomecanização – CMM", "Medalha do Cinquentenário do Centro de Suprimento e Manutenção de Material de Motomecanização – CMM"),
        ("Medalha do Cinquentenário do Décimo Oitavo Batalhão de Polícia Militar do Interior", "Medalha do Cinquentenário do Décimo Oitavo Batalhão de Polícia Militar do Interior"),
        ("Medalha do Cinquentenário do Décimo Sétimo Batalhão de Polícia Militar do Interior", "Medalha do Cinquentenário do Décimo Sétimo Batalhão de Polícia Militar do Interior"),
        ("Medalha do Cinquentenário do Nono Batalhão de Polícia Militar Metropolitano", "Medalha do Cinquentenário do Nono Batalhão de Polícia Militar Metropolitano"),
        ("Medalha do Cinquentenário do Policiamento Florestal e de Mananciais - CPAmb", "Medalha do Cinquentenário do Policiamento Florestal e de Mananciais - CPAmb"),
        ("Medalha do Cinquentenário do Policiamento Rodoviário - CPRv", "Medalha do Cinquentenário do Policiamento Rodoviário - CPRv"),
        ("Medalha do Mérito Comunitário", "Medalha do Mérito Comunitário"),
        ("Medalha do Mérito da Despesa de Pessoal – CIAP", "Medalha do Mérito da Despesa de Pessoal – CIAP"),
        ("Medalha do Sesquicentenário do Corpo Musical – CMUS", "Medalha do Sesquicentenário do Corpo Musical – CMUS"),
        ("Medalha Mérito da Diretoria de Pessoal", "Medalha Mérito da Diretoria de Pessoal"),
        ("Medalha Mérito de Logística da Polícia Militar do Estado de São Paulo – DL", "Medalha Mérito de Logística da Polícia Militar do Estado de São Paulo – DL"),
        ("Medalha Mérito de Telecomunicação – Cel Manoel de Jesus Trindade – DTIC", "Medalha Mérito de Telecomunicação – Cel Manoel de Jesus Trindade – DTIC"),
        ("Medalha Mérito do Estado-maior da Polícia Militar do Estado de São Paulo \"Desembargador Álvaro Lazzarini\"", "Medalha Mérito do Estado-maior da Polícia Militar do Estado de São Paulo \"Desembargador Álvaro Lazzarini\""),
        ("Medalha Mérito do Labor Financeiro - DFP", "Medalha Mérito do Labor Financeiro - DFP"),
        ("Medalha Pedro Dias de Campos em Grau Bronze", "Medalha Pedro Dias de Campos em Grau Bronze"),
        ("Medalha Pedro Dias de Campos em Grau Bronze 2º Concessão", "Medalha Pedro Dias de Campos em Grau Bronze 2º Concessão"),
        ("Medalha Pedro Dias de Campos em Grau Bronze 3ª Concessão", "Medalha Pedro Dias de Campos em Grau Bronze 3ª Concessão"),
        ("Medalha Pedro Dias de Campos em Grau Prata", "Medalha Pedro Dias de Campos em Grau Prata"),
        ("Medalha Pedro Dias de Campos em Grau Prata 2ª Concessão", "Medalha Pedro Dias de Campos em Grau Prata 2ª Concessão"),
        ("Medalha Pedro Dias de Campos em Grau Prata 3ª Concessão", "Medalha Pedro Dias de Campos em Grau Prata 3ª Concessão"),
        ("Título de \"Bombeiro Honorário\"", "Título de \"Bombeiro Honorário\""),
   
        # Medalhas Governamentais - Internacionais
        ('Medalha Solidariedade de Timor-Leste', 'Medalha Solidariedade de Timor-Leste'),
        ('United Nations Medal - Haiti', 'United Nations Medal - Haiti'),
        ('United Nations Medal –Missão Timor-Leste', 'United Nations Medal –Missão Timor-Leste'),
        
        # Medalhas Governamentais - Nível Federal
        ('Medalha Amigo da Marinha', 'Medalha Amigo da Marinha'),
        ('Medalha Comemorativa ao Bicentenário da PMDF', 'Medalha Comemorativa ao Bicentenário da PMDF'),
        ('Medalha Comemorativa do Sexagenário de Criação da Policia do Exército', 'Medalha Comemorativa do Sexagenário de Criação da Policia do Exército'),
        ('Medalha Concurso de Tiro ao Alvo', 'Medalha Concurso de Tiro ao Alvo'),
        ('Medalha da Ordem do Mérito Naval-Grau Grã-Cruz', 'Medalha da Ordem do Mérito Naval-Grau Grã-Cruz'),
        ('Medalha da Ordem do Mérito Naval-Grau Grande Oficial', 'Medalha da Ordem do Mérito Naval-Grau Grande Oficial'),
        ('Medalha da Ordem do Mérito Naval-Grau Cavalheiro', 'Medalha da Ordem do Mérito Naval-Grau Cavalheiro'),
        ('Medalha da Ordem do Mérito Naval-Grau Comendador', 'Medalha da Ordem do Mérito Naval-Grau Comendador'),
        ('Medalha da Ordem do Mérito Naval-Grau Oficial', 'Medalha da Ordem do Mérito Naval-Grau Oficial'),
        ('Medalha do Exército Brasileiro', 'Medalha do Exército Brasileiro'),
        ('Medalha do Mérito Santos Dumont', 'Medalha do Mérito Santos Dumont'),
        ('Medalha do Pacificador', 'Medalha do Pacificador'),
        ('Medalha Embaixador Sérgio Vieira de Mello', 'Medalha Embaixador Sérgio Vieira de Mello'),
        ('Medalha Mérito da Aviação de Segurança Pública Major Ibes Carlos Pacheco', 'Medalha Mérito da Aviação de Segurança Pública Major Ibes Carlos Pacheco'),
        ('Medalha Mérito Tamandaré', 'Medalha Mérito Tamandaré'),
        ('Medalha Ordem do Mérito Militar', 'Medalha Ordem do Mérito Militar'),
        ('Medalha Ordem Mérito Judiciário do STM', 'Medalha Ordem Mérito Judiciário do STM'),
        ('Medalha Praça Mais Distinta', 'Medalha Praça Mais Distinta'),
        ('Medalha do Mérito da Força Nacional Soldado Luis Pedro de Souza Gomes', 'Medalha do Mérito da Força Nacional Soldado Luis Pedro de Souza Gomes'),
        
        # Medalhas Governamentais - Nível Estadual
        ('Medalha 9 de Julho', 'Medalha 9 de Julho'),
        ('Medalha Alferes Joaquim José da Silva Xavier - Tiradentes', 'Medalha Alferes Joaquim José da Silva Xavier - Tiradentes'),
        ('Medalha Alferes Tiradentes', 'Medalha Alferes Tiradentes'),
        ('Medalha Brigadeiro Falcão', 'Medalha Brigadeiro Falcão'),
        ('Medalha Cel Octávio Frota – Grau Grande Mérito', 'Medalha Cel Octávio Frota – Grau Grande Mérito'),
        ('Medalha Cel PM Joaquim Antônio de Sarmento', 'Medalha Cel PM Joaquim Antônio de Sarmento'),
        ('Medalha Comemorativa do Centenário da Caixa Beneficente da Polícia Militar de São Paulo', 'Medalha Comemorativa do Centenário da Caixa Beneficente da Polícia Militar de São Paulo'),
        ('Medalha Comemorativa do Centenário do Corpo de Bombeiro do Estado do Paraná', 'Medalha Comemorativa do Centenário do Corpo de Bombeiro do Estado do Paraná'),
        ('Medalha Comemorativa Jubileu de Brilhante da Casa Militar do Gabinete do Governador', 'Medalha Comemorativa Jubileu de Brilhante da Casa Militar do Gabinete do Governador'),
        ('Medalha Cruz do Mérito Policial', 'Medalha Cruz do Mérito Policial'),
        ('Medalha da Casa Militar do Gabinete do Governador', 'Medalha da Casa Militar do Gabinete do Governador'),
        ('Medalha da Constituição', 'Medalha da Constituição'),
        ('Medalha da Defesa Civil do Estado de São Paulo', 'Medalha da Defesa Civil do Estado de São Paulo'),
        ('Medalha de Honra ao Mérito da Defesa Civil', 'Medalha de Honra ao Mérito da Defesa Civil'),
        ('Medalha de Mérito de Defesa Civil', 'Medalha de Mérito de Defesa Civil'),
        ('Medalha de Serviços Relevantes a Ordem Pública', 'Medalha de Serviços Relevantes a Ordem Pública'),
        ('Medalha do Cinquentenário da Revolução Constitucionalista de 1932', 'Medalha do Cinquentenário da Revolução Constitucionalista de 1932'),
        ('Medalha do Cinquentenário do Corpo de Bombeiros Militar do Estado de Mato Grosso', 'Medalha do Cinquentenário do Corpo de Bombeiros Militar do Estado de Mato Grosso'),
        ('Medalha do Guardião', 'Medalha do Guardião'),
        ('Medalha do Mérito Cel PM Elísio Sobreira', 'Medalha do Mérito Cel PM Elísio Sobreira'),
        ('Medalha do Mérito da Aviação de Segurança Pública Major Ibes Carlos Pacheco', 'Medalha do Mérito da Aviação de Segurança Pública Major Ibes Carlos Pacheco'),
        ('Medalha do Mérito da Casa Militar Cel QOC Fernando Antônio Soares Chaves', 'Medalha do Mérito da Casa Militar Cel QOC Fernando Antônio Soares Chaves'),
        ('Medalha do Mérito de Bombeiros Militar', 'Medalha do Mérito de Bombeiros Militar'),
        ('Medalha do Mérito de Polícia Judiciária Estadual', 'Medalha do Mérito de Polícia Judiciária Estadual'),
        ('Medalha do Mérito Governador Jorge Teixeira de Oliveira', 'Medalha do Mérito Governador Jorge Teixeira de Oliveira'),
        ('Medalha do Mérito Policial Militar', 'Medalha do Mérito Policial Militar'),
        ('Medalha do Mérito Policial Soldado Luiz Gonzaga', 'Medalha do Mérito Policial Soldado Luiz Gonzaga'),
        ('Medalha dos Bandeirantes', 'Medalha dos Bandeirantes'),
        ('Medalha Duque de Caxias – Mérito Intelectual', 'Medalha Duque de Caxias – Mérito Intelectual'),
        ('Medalha Governador Luis Domingues', 'Medalha Governador Luis Domingues'),
        ('Medalha Guardião de Paiaguas', 'Medalha Guardião de Paiaguas'),
        ('Medalha Harpia 25 anos', 'Medalha Harpia 25 anos'),
        ('Medalha Hospital das Clínicas da Faculdade de Medicina da Universidade de São Paulo HCFMUSP', 'Medalha Hospital das Clínicas da Faculdade de Medicina da Universidade de São Paulo HCFMUSP'),
        ('Medalha Imperador D.Pedro II', 'Medalha Imperador D.Pedro II'),
        ('Medalha Imperador Dom Pedro II', 'Medalha Imperador Dom Pedro II'),
        ('Medalha Luiz Gonzaga', 'Medalha Luiz Gonzaga'),
        ('Medalha Mérito Avante Bombeiro', 'Medalha Mérito Avante Bombeiro'),
        ('Medalha Mérito Casa Militar', 'Medalha Mérito Casa Militar'),
        ('Medalha Mérito Forte Príncipe da Beira', 'Medalha Mérito Forte Príncipe da Beira'),
        ('Medalha Mérito Institucional Zumbi dos Palmares', 'Medalha Mérito Institucional Zumbi dos Palmares'),
        ('Medalha Mérito Monte Roraima', 'Medalha Mérito Monte Roraima'),
        ('Medalha Mérito Nestor Gomes', 'Medalha Mérito Nestor Gomes'),
        ('Medalha Mérito Polícia Técnico Científica "Governador Mario Covas"', 'Medalha Mérito Polícia Técnico Científica "Governador Mario Covas"'),
        ('Medalha Ministro Mário Guimarães', 'Medalha Ministro Mário Guimarães'),
        ('Medalha Ordem Honorífica do Mérito Tiradentes – Grau de Grã-Cruz', 'Medalha Ordem Honorífica do Mérito Tiradentes – Grau de Grã-Cruz'),
        ('Medalha Pernambucana do Mérito Musical Capitão Zuzinha', 'Medalha Pernambucana do Mérito Musical Capitão Zuzinha'),
        ('Medalha Pernambucana do Mérito Policial Militar', 'Medalha Pernambucana do Mérito Policial Militar'),
        ('Medalha Presidente Carlos Cavalcanti de Albuquerque', 'Medalha Presidente Carlos Cavalcanti de Albuquerque'),
        ('Medalha Valor Cívico', 'Medalha Valor Cívico'),
        ('Medalha Valor Militar em Bronze', 'Medalha Valor Militar em Bronze'),
        ('Medalha Valor Militar em Ouro', 'Medalha Valor Militar em Ouro'),
        ('Medalha Valor Militar em Prata', 'Medalha Valor Militar em Prata'),
        ('Ordem Honorífica do Mérito Tiradentes – Grau de Comendador', 'Ordem Honorífica do Mérito Tiradentes – Grau de Comendador'),
        ('Título Honorífico de Amigo da Polícia Militar do Estado de Roraima', 'Título Honorífico de Amigo da Polícia Militar do Estado de Roraima'),
        
        # Medalhas Governamentais - Nível Municipal
        ('Barreta com cores do Município de Murutinga do Sul -SP', 'Barreta com cores do Município de Murutinga do Sul -SP'),
        ('Comenda Emília Valsechi Valdanha', 'Comenda Emília Valsechi Valdanha'),
        ('Medalha "Policial Padrão do Ano"', 'Medalha "Policial Padrão do Ano"'),
        ('Medalha Arauto da Paz', 'Medalha Arauto da Paz'),
        ('Medalha Conselheiro Francisco de Paula Mayrink', 'Medalha Conselheiro Francisco de Paula Mayrink'),
        ('Medalha de Mérito Irmãos Takeo e Hirako Okubo', 'Medalha de Mérito Irmãos Takeo e Hirako Okubo'),
        ('Medalha do Mérito do Município de Santo André', 'Medalha do Mérito do Município de Santo André'),
        ('Medalha do Mérito do Pessoal de São Bernardo do Campo', 'Medalha do Mérito do Pessoal de São Bernardo do Campo'),
        ('Medalha do Mérito do Policial de Itaquaquecetuba', 'Medalha do Mérito do Policial de Itaquaquecetuba'),
        ('Medalha Exemplo Digno', 'Medalha Exemplo Digno'),
        ('Medalha Guilherme de Almeida', 'Medalha Guilherme de Almeida'),
        ('Medalha Jânio Quadros', 'Medalha Jânio Quadros'),
        ('Medalha Legislativa de Mérito do Policial Militar de Diadema', 'Medalha Legislativa de Mérito do Policial Militar de Diadema'),
        ('Medalha Legislativo do Mérito Policial Militar de Itapecerica da Serra- 25º BPM/M', 'Medalha Legislativo do Mérito Policial Militar de Itapecerica da Serra- 25º BPM/M'),
        ('Medalha Mérito da Segurança Pública de Praia Grande', 'Medalha Mérito da Segurança Pública de Praia Grande'),
        ('Medalha Mérito do Policial de São Caetano do Sul', 'Medalha Mérito do Policial de São Caetano do Sul'),
        ('Medalha Mérito Policial', 'Medalha Mérito Policial'),
        ('Medalha Ordem do Mérito Cultural Carlos Gomes', 'Medalha Ordem do Mérito Cultural Carlos Gomes'),
        ('Medalha Pérsio de Souza Queiroz Filho', 'Medalha Pérsio de Souza Queiroz Filho'),
        ('Medalha Reconhecimento Comunitário de Segurança', 'Medalha Reconhecimento Comunitário de Segurança'),
        ('Medalha Tiradentes', 'Medalha Tiradentes'),
        ('Mérito Cívico Marilia de Dirceu', 'Mérito Cívico Marilia de Dirceu'),
        ('Medalha Sargento Nilson Mikio Futura Júnior', 'Medalha Sargento Nilson Mikio Futura Júnior'),
        
        # Medalhas Não Governamentais - Entidades Civis
        ('Colar "Tenente Coronel Álvaro Martins"', 'Colar "Tenente Coronel Álvaro Martins"'),
        ('Colar Cadete PM Ruytemberg Rocha – o Cadete Constitucionalista', 'Colar Cadete PM Ruytemberg Rocha – o Cadete Constitucionalista'),
        ('Colar Cadete PM Ruytemberg Rocha – o Cadete PM Herói de 1932', 'Colar Cadete PM Ruytemberg Rocha – o Cadete PM Herói de 1932'),
        ('Colar Cruz da Honra Constitucionalista', 'Colar Cruz da Honra Constitucionalista'),
        ('Colar Cruz do Alvarenga e dos Heróis Anônimos', 'Colar Cruz do Alvarenga e dos Heróis Anônimos'),
        ('Colar da Vitória Evocativo aos 80 anos da Revolução Constitucionalista de 1932', 'Colar da Vitória Evocativo aos 80 anos da Revolução Constitucionalista de 1932'),
        ('Colar Evocativo do Jubileu de Brilhante da Revolução Constitucionalista', 'Colar Evocativo do Jubileu de Brilhante da Revolução Constitucionalista'),
        ('Colar General de Brigada Médico João Severiano da Fonseca – Patrono do Serviço de Saúde do Exército Brasileiro', 'Colar General de Brigada Médico João Severiano da Fonseca – Patrono do Serviço de Saúde do Exército Brasileiro'),
        ('Colar Herói Bento Gonçalves e Silva', 'Colar Herói Bento Gonçalves e Silva'),
        ('Colar Heróis de 32 – O triunfo', 'Colar Heróis de 32 – O triunfo'),
        ('Colar Heróis de 32 – Tributo ao Pantheon', 'Colar Heróis de 32 – Tributo ao Pantheon'),
        ('Colar Heróis de Araraquara', 'Colar Heróis de Araraquara'),
        ('Colar Heróis de fogo', 'Colar Heróis de fogo'),
        ('Colar Heróis do Trem Blindado', 'Colar Heróis do Trem Blindado'),
        ('Colar O Patriarca da Independência – José Bonifácio de Andrade e Silva', 'Colar O Patriarca da Independência – José Bonifácio de Andrade e Silva'),
        ('Colar Ordem de Mérito Cruz do Anhembi', 'Colar Ordem de Mérito Cruz do Anhembi'),
        ('Colar Visconde de Porto Seguro', 'Colar Visconde de Porto Seguro'),
        ('Comenda Ordem de Mérito Cruz do Anhembi', 'Comenda Ordem de Mérito Cruz do Anhembi'),
        ('Cruz de Honra Legionária', 'Cruz de Honra Legionária'),
        ('Grã-Cruz Heróis de 32 - Sempre Viverão', 'Grã-Cruz Heróis de 32 - Sempre Viverão'),
        ('Grã-Cruz Heróis de Fogo', 'Grã-Cruz Heróis de Fogo'),
        ('Grã-Cruz Ordem do Mérito Cruz do Anhembi', 'Grã-Cruz Ordem do Mérito Cruz do Anhembi'),
        ('Grande Colar Heróis de 32 – Tributo aos Constitucionalista', 'Grande Colar Heróis de 32 – Tributo aos Constitucionalista'),
        ('Grão-Colar Ordem do Mérito Cruz do Anhembi', 'Grão-Colar Ordem do Mérito Cruz do Anhembi'),
        ('Medalha Asas da Vitória', 'Medalha Asas da Vitória'),
        ('Medalha Audazes Bombeiros', 'Medalha Audazes Bombeiros'),
        ('Medalha Bicentenário do Nascimento do Marechal Osório', 'Medalha Bicentenário do Nascimento do Marechal Osório'),
        ('Medalha Brigadeiro José Vieira Couto de Magalhães', 'Medalha Brigadeiro José Vieira Couto de Magalhães'),
        ('Medalha Cabo Augusto de Moraes', 'Medalha Cabo Augusto de Moraes'),
        ('Medalha Cabo Bento Martins de Souza', 'Medalha Cabo Bento Martins de Souza'),
        ('Medalha Cadete Constitucionalista', 'Medalha Cadete Constitucionalista'),
        ('Medalha Capitão Franklin – Mérito do Músico Militar', 'Medalha Capitão Franklin – Mérito do Músico Militar'),
        ('Medalha Carmo Turano', 'Medalha Carmo Turano'),
        ('Medalha Caxias – Patrono do Exército Brasileiro', 'Medalha Caxias – Patrono do Exército Brasileiro'),
        ('Medalha Cidadão Policial', 'Medalha Cidadão Policial'),
        ('Medalha Cinquentenário das Forças de Paz do Brasil', 'Medalha Cinquentenário das Forças de Paz do Brasil'),
        ('Medalha Cinquentenário do Batalhão Suez', 'Medalha Cinquentenário do Batalhão Suez'),
        ('Medalha Combatentes de 32', 'Medalha Combatentes de 32'),
        ('Medalha Comemorativa de Vinte e Cinco Anos da Sociedade Veteranos de 32 MMDC', 'Medalha Comemorativa de Vinte e Cinco Anos da Sociedade Veteranos de 32 MMDC'),
        ('Medalha Constitucionalista', 'Medalha Constitucionalista'),
        ('Medalha Coronel PM Delfim Cerqueira Neves', 'Medalha Coronel PM Delfim Cerqueira Neves'),
        ('Medalha Cruz de Paz dos Veteranos da FEB', 'Medalha Cruz de Paz dos Veteranos da FEB'),
        ('Medalha Cruz do Mérito Filosófico e Cultural', 'Medalha Cruz do Mérito Filosófico e Cultural'),
        ('Medalha da Vitória', 'Medalha da Vitória'),
        ('Medalha de Honra ao Mérito Coronel Francisco vieira', 'Medalha de Honra ao Mérito Coronel Francisco vieira'),
        ('Medalha do Bicentenário Dragões da Independência', 'Medalha do Bicentenário Dragões da Independência'),
        ('Medalha do Mérito Ana Terra', 'Medalha do Mérito Ana Terra'),
        ('Medalha do Mérito Cívico Militar', 'Medalha do Mérito Cívico Militar'),
        ('Medalha do Mérito da Academia Brasileira de Medalhistica Militar (ABRAMMIL) – Grau Cavaleiro', 'Medalha do Mérito da Academia Brasileira de Medalhistica Militar (ABRAMMIL) – Grau Cavaleiro'),
        ('Medalha Ordem do Mérito do Batalhão de Suez – Grau Bronze', 'Medalha Ordem do Mérito do Batalhão de Suez – Grau Bronze'),
        ('Medalha Ordem do Mérito do Batalhão de Suez – Grau Ouro', 'Medalha Ordem do Mérito do Batalhão de Suez – Grau Ouro'),
        ('Medalha Ordem do Mérito do Batalhão de Suez – Grau Prata', 'Medalha Ordem do Mérito do Batalhão de Suez – Grau Prata'),
        ('Medalha do Mérito do Tiro de Guerra', 'Medalha do Mérito do Tiro de Guerra'),
        ('Medalha do Mérito Juventude Constitucionalista', 'Medalha do Mérito Juventude Constitucionalista'),
        ('Medalha do Mérito Marechal Castelo Branco', 'Medalha do Mérito Marechal Castelo Branco'),
        ('Medalha do Mérito Marechal Castelo Branco - Bronze', 'Medalha do Mérito Marechal Castelo Branco - Bronze'),
        ('Medalha do Mérito Marechal Castelo Branco - Ouro', 'Medalha do Mérito Marechal Castelo Branco - Ouro'),
        ('Medalha do Mérito Marechal Castelo Branco - Prata', 'Medalha do Mérito Marechal Castelo Branco - Prata'),
        ('Medalha do Mérito Rondon', 'Medalha do Mérito Rondon'),
        ('Medalha do Sesquicentenário do Corpo de Bombeiro Militar do Estado do Rio de Janeiro', 'Medalha do Sesquicentenário do Corpo de Bombeiro Militar do Estado do Rio de Janeiro'),
        ('Medalha dona May de Souza Neves', 'Medalha dona May de Souza Neves'),
        ('Medalha Dr. Synésio de Mello de Oliveira', 'Medalha Dr. Synésio de Mello de Oliveira'),
        ('Medalha Dráusio Marcondes de Souza', 'Medalha Dráusio Marcondes de Souza'),
        ('Medalha Duque de Caxias', 'Medalha Duque de Caxias'),
        ('Medalha Esplendor de São Miguel Paulista', 'Medalha Esplendor de São Miguel Paulista'),
        ('Medalha Garra e Coragem', 'Medalha Garra e Coragem'),
        ('Medalha General Euclydes de Oliveira Figueiredo', 'Medalha General Euclydes de Oliveira Figueiredo'),
        ('Medalha General Francisco Alves do Nascimento Pinto', 'Medalha General Francisco Alves do Nascimento Pinto'),
        ('Medalha General Plínio Pittaluga', 'Medalha General Plínio Pittaluga'),
        ('Medalha Governador Pedro de Toledo', 'Medalha Governador Pedro de Toledo'),
        ('Medalha Heróis Anônimos', 'Medalha Heróis Anônimos'),
        ('Medalha Heróis de 32 - Luta e Constituição', 'Medalha Heróis de 32 - Luta e Constituição'),
        ('Medalha Heróis de Fogo', 'Medalha Heróis de Fogo'),
        ('Medalha Heróis do Brasil', 'Medalha Heróis do Brasil'),
        ('Medalha Heróis do Trem Blindado', 'Medalha Heróis do Trem Blindado'),
        ('Medalha Internacional dos Veteranos das Nações Unidas e Estados Americanos', 'Medalha Internacional dos Veteranos das Nações Unidas e Estados Americanos'),
        ('Medalha Jubileu de Prata', 'Medalha Jubileu de Prata'),
        ('Medalha Lágrima da Terra', 'Medalha Lágrima da Terra'),
        ('Medalha Leão de Judá', 'Medalha Leão de Judá'),
        ('Medalha Liberdade e Democracia', 'Medalha Liberdade e Democracia'),
        ('Medalha Luz da Pátria', 'Medalha Luz da Pátria'),
        ('Medalha Mallet', 'Medalha Mallet'),
        ('Medalha Marechal Cordeiro de Farias (FEB)', 'Medalha Marechal Cordeiro de Farias (FEB)'),
        ('Medalha Marechal Falconiére', 'Medalha Marechal Falconiére'),
        ('Medalha Marechal João Propicio', 'Medalha Marechal João Propicio'),
        ('Medalha Marechal Machado Lopes', 'Medalha Marechal Machado Lopes'),
        ('Medalha Marechal Mascarenhas de Moraes', 'Medalha Marechal Mascarenhas de Moraes'),
        ('Medalha Marechal Teixeira Lott', 'Medalha Marechal Teixeira Lott'),
        ('Medalha Mérito Constitucionalista', 'Medalha Mérito Constitucionalista'),
        ('Medalha Mérito da Força Expedicionária Brasileira', 'Medalha Mérito da Força Expedicionária Brasileira'),
        ('Medalha Mérito do Cooperativismo', 'Medalha Mérito do Cooperativismo'),
        ('Medalha Mérito dos Pacificadores', 'Medalha Mérito dos Pacificadores'),
        ('Medalha Mérito e Dedicação', 'Medalha Mérito e Dedicação'),
        ('Medalha Mérito Marechal Bitencourt', 'Medalha Mérito Marechal Bitencourt'),
        ('Medalha Mérito Marechal Osório', 'Medalha Mérito Marechal Osório'),
        ('Medalha Mérito Maria Quitéria', 'Medalha Mérito Maria Quitéria'),
        ('Medalha Mérito Precursor da Paz', 'Medalha Mérito Precursor da Paz'),
        ('Medalha MMDC', 'Medalha MMDC'),
        ('Medalha Monsenhor Gonçalves', 'Medalha Monsenhor Gonçalves'),
        ('Medalha O Patriarca da Independência – José Bonifácio de Andrade e Silva', 'Medalha O Patriarca da Independência – José Bonifácio de Andrade e Silva'),
        ('Medalha O Solar dos Andradas', 'Medalha O Solar dos Andradas'),
        ('Medalha Ordem do Mérito Cruz do Anhembi', 'Medalha Ordem do Mérito Cruz do Anhembi'),
        ('Medalha Paladinos da Liberdade', 'Medalha Paladinos da Liberdade'),
        ('Medalha Paulo Bonfim – Príncipe dos Poetas', 'Medalha Paulo Bonfim – Príncipe dos Poetas'),
        ('Medalha Presidente Annibal de Freitas', 'Medalha Presidente Annibal de Freitas'),
        ('Medalha Sargento Waldomiro Machado', 'Medalha Sargento Waldomiro Machado'),
        ('Medalha Sentinela da Paz', 'Medalha Sentinela da Paz'),
        ('Medalha Tenente António João', 'Medalha Tenente António João'),
        ('Medalha Tenente Joaquim Nunes Cabral', 'Medalha Tenente Joaquim Nunes Cabral'),
        ('Medalha Tributo a Batalha de Montese', 'Medalha Tributo a Batalha de Montese'),
        ('Medalha Tributo ao FAIBRAS', 'Medalha Tributo ao FAIBRAS'),
        ('Medalha Tributo Naval da Força Expedicionária Brasileira', 'Medalha Tributo Naval da Força Expedicionária Brasileira'),
        ('Ordem do Mérito MMDC – Grau Cavaleiro e ou Dama', 'Ordem do Mérito MMDC – Grau Cavaleiro e ou Dama'),
        ('Ordem do Mérito MMDC – Grau Comendador', 'Ordem do Mérito MMDC – Grau Comendador'),
        ('Ordem do Mérito MMDC – Grau Grã Cruz', 'Ordem do Mérito MMDC – Grau Grã Cruz'),
        ('Ordem do Mérito MMDC – Grau Grande Oficial', 'Ordem do Mérito MMDC – Grau Grande Oficial'),
        ('Ordem do Mérito MMDC – Grau Oficial', 'Ordem do Mérito MMDC – Grau Oficial'),
        ('Colar de Paladino da Paz', 'Colar de Paladino da Paz'),
    ]
    
    id = models.AutoField(primary_key=True)
    honraria = models.CharField(max_length=255, choices=HONRARIA_CHOICES)
    entidade_concedente = models.CharField(max_length=255)
    ordem = models.CharField(max_length=5, choices=ORDEM_CHOICES)
    tipo = models.ForeignKey(TipoMedalha, on_delete=models.CASCADE)
    create = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    observacoes = models.TextField(blank=True, null=True)  # <-- Adicione esta linha
    
    def __str__(self):
        return f"{self.honraria} - {self.entidade_concedente}"

    @classmethod
    def get_honraria_choices(cls):
        return cls.HONRARIA_CHOICES
    
    @classmethod
    def get_medalha_data(cls):
        """Retorna um dicionário com todos os dados das medalhas baseado no documento"""
        return {
            # Medalhas Internas da PMESP
            "Colar Comemorativo do Sesquicentenário da Revolução Liberal de 1842 - CPI-7": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Láurea de Mérito Pessoal em 1º Grau": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Láurea de Mérito Pessoal em 2º Grau": {
                "entidade_concedente": "PMESP",
                "ordem": "V",
                "tipo": "INTERNAS_PMESP"
            },
            "Láurea de Mérito Pessoal em 3º Grau": {
                "entidade_concedente": "PMESP",
                "ordem": "V",
                "tipo": "INTERNAS_PMESP"
            },
            "Láurea de Mérito Pessoal em 4º Grau": {
                "entidade_concedente": "PMESP",
                "ordem": "V",
                "tipo": "INTERNAS_PMESP"
            },
            "Láurea de Mérito Pessoal em 5º Grau": {
                "entidade_concedente": "PMESP",
                "ordem": "V",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha \"Batalhão de Expedicionários Paulistas\" do Segundo Batalhão de Polícia de Choque": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha \"Brigadeiro Tobias\"": {
                "entidade_concedente": "PMESP",
                "ordem": "V",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha \"Mérito da Inteligência\" da Policia Militar do Estado de São Paulo – CIPM": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha \"Mérito da Justiça e Disciplina da Policia Militar do Estado de São Paulo": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha \"Mérito do Comando de Policiamento da Capital": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha \"Nathaniel Prado\" Criador do Gabinete de Munições da Força Pública - CSM/AM": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha \"Patrono do Comando de Policiamento do Interior Três - Coronel PM Paulo Monte Serrat Filho\"": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha \"Regente Feijó\"": {
                "entidade_concedente": "PMESP",
                "ordem": "V",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha 1º Centenário do 5º Batalhão de Policia Militar do Interior \"General Júlio Marcondes Salgado\"": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Batalhão Humaitá - 3º BPChq": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Capitão PM Alberto Mendes Júnior da PMESP": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Centenário da Academia de Polícia Militar do Barro Branco": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Centenário da Escola de Educação Física": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Centenário do Centro Odontológico": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Cinquentenário do Centro de Formação de Aperfeiçoamento de Praças": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Cinquentenário do Décimo Sexto Batalhão de Policia Militar Metropolitano": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Cinquentenário do Departamento de Suporte Administrativo do Comando Geral DSA/CG": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Comemorativa do 1º Centenário do 3° Grupamento de Incêndio do Corpo de Bombeiros 3° GB": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Comemorativa do Centenário do 1° Grupamento de Bombeiros": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Comemorativa do Centenário do 6º Grupamento de Incêndio - 6° GI": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Comemorativa do Centenário do Corpo de Bombeiro da Policia Militar do Estado de São Paulo": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Comemorativa do Cinquentenário de Criação do Décimo Terceiro Batalhão de Policia Militar do Interior": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Comemorativa do Cinquentenário do Centro de Processamento de Dados": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Comemorativa do Cinquentenário do Centro de Seleção, Alistamento e Estudos de Pessoal CSAEP": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Comemorativa do Sesquicentenário da Policia Militar do Estado de São Paulo": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Coronel Paul Balagny": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Cruz de Sangue em Bronze": {
                "entidade_concedente": "PMESP",
                "ordem": "11",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Cruz de Sangue em Bronze 2a Concessão": {
                "entidade_concedente": "PMESP",
                "ordem": "11",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Cruz de Sangue em Bronze 3a Concessão": {
                "entidade_concedente": "PMESP",
                "ordem": "11",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Cruz de Sangue em Ouro": {
                "entidade_concedente": "PMESP",
                "ordem": None,  # Valor ausente no documento
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Cruz de Sangue em Prata": {
                "entidade_concedente": "PMESP",
                "ordem": None,  # Valor ausente no documento
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do 1º Centenário do Centro Médico": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do 1º Centenário do Regimento de Polícia Montada \"9 de Julho\"": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Centenário da Aviação da Policia Militar do Estado de São Paulo - CAVPM": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Centenário da Corregedoria da Polícia Militar": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Centenário de Sétimo Grupamento de Bombeiros - 7º GB": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Centenário do 14º Batalhão de Polícia Militar Metropolitano": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Centenário do 1º Batalhão de Polícia de Choque Tobias de Aguiar": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Centenário do 2º Batalhão de Polícia Militar Metropolitano Coronel Herculano de Carvalho e Silva": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Centenário do 2º Grupamento de Incêndio do Corpo de Bombeiro - 2° GB": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Centenário do 6º Batalhão de Polícia Militar do Interior - \"Ten Cel Pedro Árbues": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
        "Medalha do Centenário do Oitavo Batalhão de Polícia Militar do Interior": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Centenário do Quarto Batalhão de Polícia Militar do Interior": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Cinquentenário da Diretoria de Saúde - DS": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Cinquentenário do 10º Batalhão de Polícia Militar Metropolitano \"Cel PM Bertholazzi\"": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Cinquentenário do 12º Batalhão de Polícia Militar Metropolitano": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Cinquentenário do Canil": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Cinquentenário do Centro de Suprimento e Manutenção de Material de Moto-mecanização  CMM": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Cinquentenário do Décimo Oitavo Batalhão de Polícia Militar do Interior": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Cinquentenário do Décimo Sétimo Batalhão de Polícia Militar do Interior": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Cinquentenário do Nono Batalhão de Polícia Militar Metropolitano": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Cinquentenário do Policiamento Florestal e de Mananciais - CPAmb": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Cinquentenário do Policiamento Rodoviário - CPRv": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Mérito Comunitário": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Mérito da Despesa de Pessoal CIAP": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha do Sesquicentenário do Corpo Musical CMUS": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Mérito da Diretoria de Pessoal": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Mérito de Logística da Polícia Militar do Estado de São Paulo - DL": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Mérito de Telecomunicação Cel Manoel de Jesus Trindade - DTIC": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Mérito do Estado-maior da Polícia Militar do Estado de São Paulo \"Desembargador Álvaro Lazzarini":{
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Mérito do Labor Financeiro - DFP": {
                "entidade_concedente": "PMESP",
                "ordem": "VI",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Pedro Dias de Campos em Grau Bronze": {
                "entidade_concedente": "PMESP",
                "ordem": "XII",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Pedro Dias de Campos em Grau Bronze 2a Concessão": {
                "entidade_concedente": "PMESP",
                "ordem": "XII",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Pedro Dias de Campos em Grau Bronze 3a Concessão": {
                "entidade_concedente": "PMESP",
                "ordem": "XII",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Pedro Dias de Campos em Grau Prata": {
                "entidade_concedente": "PMESP",
                "ordem": "XII",
                "tipo": "INTERNAS_PMESP"
            },
            "Medalha Pedro Dias de Campos em Grau Prata 2ª Concessão": {
                "entidade_concedente": "PMESP",
                "ordem": "XII",
                "tipo": "INTERNAS_PMESP"
            },
        "Medalha Pedro Dias de Campos em Grau Prata 3ª Concessão": {
                "entidade_concedente": "PMESP",
                "ordem": "XII",
                "tipo": "INTERNAS_PMESP"
            },
            "Título de \"Bombeiro Honorário\"": {
                "entidade_concedente": "PMESP",
                "ordem": "X",
                "tipo": "INTERNAS_PMESP"
            },

        # Medalhas Governamentais - Internacionais
            "Medalha Solidariedade de Timor-Leste": {
                "entidade_concedente": "República Democrática de Timor-Leste",
                "ordem": "IX",
                "tipo": "GOVERNAMENTAIS_INTERNACIONAIS"
            },
            "United Nations Medal - Haiti": {
                "entidade_concedente": "United Nations -ONU",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_INTERNACIONAIS"
            },
            "United Nations Medal –Missão Timor-Leste": {
                "entidade_concedente": "United Nations -ONU",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_INTERNACIONAIS"
            },

            # Medalhas Governamentais - Nível Federal
            "Medalha Amigo da Marinha": {
                "entidade_concedente": "Marinha do Brasil",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha Comemorativa ao Bicentenário da PMDF": {
                "entidade_concedente": "Presidente da República Federativa do Brasil",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha Comemorativa do Sexagenário de Criação da Policia do Exército": {
                "entidade_concedente": "Exército Brasileiro",
                "ordem": "IX",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha Concurso de Tiro ao Alvo": {
                "entidade_concedente": "Exército Brasileiro",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha da Ordem do Mérito Naval-Grau Grã-Cruz": {
                "entidade_concedente": "Marinha do Brasil",
                "ordem": "IX",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha da Ordem do Mérito Naval-Grau Grande Oficial": {
                "entidade_concedente": "Marinha do Brasil",
                "ordem": "IX",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha da Ordem do Mérito Naval-Grau Grau Cavalheiro": {
                "entidade_concedente": "Marinha do Brasil",
                "ordem": "IX",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha da Ordem do Mérito Naval-Grau Grau Comendador": {
                "entidade_concedente": "Marinha do Brasil",
                "ordem": "IX",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha da Ordem do Mérito Naval-Grau Grau Oficial": {
                "entidade_concedente": "Marinha do Brasil",
                "ordem": "IX",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha do Exército Brasileiro": {
                "entidade_concedente": "Exército Brasileiro",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha do Mérito Santos Dumont": {
                "entidade_concedente": "Ministro da Defesa",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha do Pacificador": {
                "entidade_concedente": "Exército Brasileiro",
                "ordem": "IX",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha Embaixador Sérgio Vieira de Mello": {
                "entidade_concedente": "Ministério das Relações Exteriores",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha Mérito da Aviação de Segurança Pública Major Ibes Carlos Pacheco": {
                "entidade_concedente": "Ministro de Estado da Justiça",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha Mérito Tamandaré": {
                "entidade_concedente": "Marinha do Brasil",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha Ordem do Mérito Militar": {
                "entidade_concedente": "Presidente da República Federativa do Brasil",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha do Exército Brasileiro": {
                "entidade_concedente": "Exército Brasileiro",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha Embaixador Sérgio Vieira de Mello": {
                "entidade_concedente": "Ministério das Relações Exteriores",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha Ordem Mérito Judiciário do STM": {
                "entidade_concedente": "Superior Tribunal Militar",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
            "Medalha Praça Mais Distinta": {
                "entidade_concedente": "Exército Brasileiro",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },
        "Medalha do Mérito da Força Nacional Soldado Luis Pedro de Souza Gomes": {
                "entidade_concedente": "Ministério da Justiça e Segurança Pública",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_FEDERAL"
            },

            # MEDALHAS GOVERNAMENTAIS - NÍVEL ESTADUAL
            "Medalha 9 de Julho": {
                "entidade_concedente": "Assembleia Legislativa do Estado de São Paulo",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Alferes Joaquim José da Silva Xavier - Tiradentes": {
                "entidade_concedente": "Governo do Distrito Federal",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Alferes Tiradentes": {
                "entidade_concedente": "Polícia Militar do Estado de Minas Gerais",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Brigadeiro Falcão": {
                "entidade_concedente": "Polícia Militar do Estado do Maranhão",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Cel Octávio Frota - Grau Grande Mérito": {
                "entidade_concedente": "Governo do Estado do Rio Grande do Sul",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Cel PM Joaquim António de Sarmento": {
                "entidade_concedente": "Polícia Militar do Estado do Paraná",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Comemorativa do Centenário da Caixa Beneficente da Polícia Militar de São Paulo": {
                "entidade_concedente": "Governo do Estado de São Paulo",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Comemorativa do Centenário do Corpo de Bombeiro do Estado do Paraná": {
                "entidade_concedente": "Polícia Militar do Estado do Paraná",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Comemorativa Jubileu de Brilhante da Casa Militar do Gabinete do Governador": {
                "entidade_concedente": "Governo do Estado de São Paulo",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Cruz do Mérito Policial": {
                "entidade_concedente": "Governo do Estado de São Paulo",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha da Casa Militar do Gabinete do Governador": {
                "entidade_concedente": "Governo do Estado de São Paulo",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha da Constituição": {
                "entidade_concedente": "Assembleia Legislativa do Estado de São Paulo",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha da Defesa Civil do Estado de São Paulo": {
                "entidade_concedente": "Governo do Estado de São Paulo",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha de Honra ao Mérito da Defesa Civil": {
                "entidade_concedente": "Governo do Mato Grosso",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha de Mérito de Defesa Civil": {
                "entidade_concedente": "Governo do Estado de Minas Gerais",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha de Serviços Relevantes a Ordem Pública": {
                "entidade_concedente": "Governo do Estado do Rio Grande do Sul",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha do Cinquentenário da Revolução Constitucionalista de 1932": {
                "entidade_concedente": "Assembleia Legislativa do Estado de São Paulo",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha do Cinquentenário do Corpo de Bombeiros Militar do Estado de Mato Grosso": {
                "entidade_concedente": "Assembleia Legislativa do Estado de Mato Grosso",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha do Guardião": {
                "entidade_concedente": "Governo do Estado de Goiás",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha do Mérito Cel PM Elísio Sobreira": {
                "entidade_concedente": "Governo do Estado da Paraíba",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha do Mérito da Aviação de Segurança Pública Major Ibes Carlos Pacheco": {
                "entidade_concedente": "Presidente da República",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha do Mérito da Casa Militar Cel QOC Fernando Antônio Soares Chaves": {
                "entidade_concedente": "Governo do Estado da Paraíba",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha do Mérito de Bombeiros Militar": {
                "entidade_concedente": "Governo do Estado de Alagoas",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha do Mérito de Polícia Judiciária Estadual": {
                "entidade_concedente": "Polícia Militar do Rio Grande do Norte",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha do Mérito Governador Jorge Teixeira de Oliveira": {
                "entidade_concedente": "Governo do Estado de Rondônia",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha do Mérito Policial Militar": {
                "entidade_concedente": "Governo do Estado de Mato Grosso do Sul",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha do Mérito Policial Militar": {
                "entidade_concedente": "Governo do Estado do Piauí",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha do Mérito Policial Militar": {
                "entidade_concedente": "Polícia Militar do Estado do Sergipe",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha do Mérito Policial Soldado Luiz Gonzaga": {
                "entidade_concedente": "Governo do Estado do Rio Grande do Norte",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha dos Bandeirantes": {
                "entidade_concedente": "Governo do Estado de São Paulo",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Duque de Caxias - Mérito Intelectual": {
            "entidade_concedente": "Comandante Geral da Polícia Militar do Distrito Federal",
            "ordem": "XII",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Governador Luis Domingues": {
            "entidade_concedente": "Governo do Estado do Maranhão",
            "ordem": "VI",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Guardião de Paiaguas": {
            "entidade_concedente": "Governo do Mato Grosso",
            "ordem": "VI",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Harpia 25 anos": {
            "entidade_concedente": "Governo do Espirito Santo",
            "ordem": "VI",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Hospital das Clínicas da Faculdade de Medicina da Universidade de São Paulo - HCFMUSP": {
            "entidade_concedente": "Governo do Estado de São Paulo",
            "ordem": "VI",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Imperador D. Pedro II": {
            "entidade_concedente": "Governo do Distrito Federal",
            "ordem": "X",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Imperador D. Pedro II": {
            "entidade_concedente": "Governo do Estado de Mato Grosso do Sul",
            "ordem": "VI",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Imperador Dom Pedro II": {
            "entidade_concedente": "Comandante Geral de Bombeiros do Estado de Rondônia",
            "ordem": "VI",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Luiz Gonzaga": {
            "entidade_concedente": "Assembleia Legislativa do Estado de São Paulo",
            "ordem": "V",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Mérito Avante Bombeiro": {
            "entidade_concedente": "Comandante Geral do Corpo de Bombeiros Militar do Estado do Rio de Janeiro",
            "ordem": "V",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Mérito Casa Militar": {
            "entidade_concedente": "Governo do Estado de Rondônia",
            "ordem": "VI",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Mérito Forte Príncipe da Beira": {
            "entidade_concedente": "Comandante Geral da Polícia Militar do Estado de Rondônia",
            "ordem": "V",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Mérito Institucional Zumbi dos Palmares": {
            "entidade_concedente": "Governo do Estado de Alagoas",
            "ordem": "V",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Mérito Monte Roraima": {
            "entidade_concedente": "Comandante Geral do Corpo de Bombeiros de Roraima",
            "ordem": "V",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Mérito Nestor Gomes": {
            "entidade_concedente": "Comandante Geral do Corpo de Bombeiros Militar do Espirito Santo",
            "ordem": "V",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Mérito Polícia Técnico Cientifica ""Governador Mario Covas": {
            "entidade_concedente": "Superintendente da Polícia Técnico Científica",
            "ordem": "V",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Ministro Mário Guimarães": {
            "entidade_concedente": "Tribunal Regional Eleitoral de São Paulo",
            "ordem": "VI",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Ordem Honorifica do Mérito Tiradentes Grau de Grā-Cruz": {
            "entidade_concedente": "Governo do Estado de Goiás",
            "ordem": "V",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Pernambucana do Mérito Musical Capitão Zuzinha": {
            "entidade_concedente": "Governador do Estado de Pernambuco",
            "ordem": "VI",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Pernambucana do Mérito Policial Militar": {
            "entidade_concedente": "Governo do Estado de Pernambuco",
            "ordem": "V",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Presidente Carlos Cavalcanti de Albuquerque": {
            "entidade_concedente": "Comandante do Corpo de Bombeiro do Estado do Paraná",
            "ordem": "VI",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Valor Cívico": {
            "entidade_concedente": "Governo do Estado de São Paulo",
            "ordem": "V",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Valor Militar em Bronze": {
            "entidade_concedente": "Governo do Estado de São Paulo",
            "ordem": "VII",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Valor Militar em Ouro": {
            "entidade_concedente": "Governo do Estado de São Paulo",
            "ordem": "VII",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Medalha Valor Militar em Prata": {
            "entidade_concedente": "Governo do Estado de São Paulo",
            "ordem": "VII",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Ordem Honorifica do Mérito Tiradentes Grau de Comendador": {
            "entidade_concedente": "Governo do Estado de Goiás",
            "ordem": "V",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            "Título Honorifico de Amigo da Polícia Militar do Estado de Roraima": {
            "entidade_concedente": "Polícia Militar do Estado do Roraima",
            "ordem": "VI",
            "tipo": "GOVERNAMENTAIS_NIVEL_ESTADUAL"
            },
            # MEDALHAS GOVERNAMENTAIS - NÍVEL MUNICIPAL
            "Barreta com cores do Município de Murutinga do Sul -SP": {
                "entidade_concedente": "Câmara Municipal de Murutinga do Sul",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Comenda Emília Valsechi Valdanha": {
                "entidade_concedente": "Câmara Municipal de Santa Gertrudes",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha \"Policial Padrão do Ano\"": {
                "entidade_concedente": "Câmara Municipal de Jahú",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Arauto da Paz": {
                "entidade_concedente": "Câmara Municipal de Campinas",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Conselheiro Francisco de Paula Mayrink": {
                "entidade_concedente": "Câmara Municipal de Mairinque",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha de Mérito Irmãos Takeo e Hirako Okubo": {
                "entidade_concedente": "Câmara Municipal de Mirante do Paranapanema",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha do Mérito do Município de Santo André": {
                "entidade_concedente": "Câmara Municipal de Santo André",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha do Mérito do Pessoal de São Bernardo do Campo": {
                "entidade_concedente": "Câmara Municipal de São Bernardo do Campo",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha do Mérito do Policial de Itaquaquecetuba": {
                "entidade_concedente": "Câmara Municipal de Itaquaquecetuba",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Exemplo Digno": {
                "entidade_concedente": "Câmara Municipal de Campinas",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Guilherme de Almeida": {
                "entidade_concedente": "Câmara Municipal de Campinas",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Jânio Quadros": {
                "entidade_concedente": "Câmara Municipal de São Paulo",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Legislativa de Mérito do Policial Militar de Diadema": {
                "entidade_concedente": "Câmara Municipal de Diadema",
                "ordem": "V",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Legislativo do Mérito Policial Militar de Itapecerica da Serra- 25º BPM/M": {
                "entidade_concedente": "Câmara Municipal de Itapecerica da Serra",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Mérito da Segurança Pública de Praia Grande": {
                "entidade_concedente": "Câmara Municipal da Estância Balneária de Praia Grande",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Mérito do Policial de São Caetano do Sul": {
                "entidade_concedente": "Câmara Municipal de São Caetano do Sul",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Mérito Policial": {
                "entidade_concedente": "Câmara Municipal do Guarujá",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Ordem do Mérito Cultural Carlos Gomes": {
                "entidade_concedente": "Câmara Municipal de Campinas",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Pérsio de Souza Queiroz Filho": {
                "entidade_concedente": "Câmara Municipal de São Vicente",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Reconhecimento Comunitário de Segurança": {
                "entidade_concedente": "Câmara Municipal de Botucatu",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Reconhecimento Comunitário de Segurança": {
                "entidade_concedente": "Câmara Municipal de Avaré",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Tiradentes": {
                "entidade_concedente": "Câmara Municipal de São Paulo",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Tiradentes": {
                "entidade_concedente": "Câmara Municipal de Mogi das Cruzes",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Tiradentes": {
                "entidade_concedente": "Câmara Municipal de Andradina",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Tiradentes": {
                "entidade_concedente": "Câmara Municipal de Ilha Solteira",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Mérito Cívico Marilia de Dirceu": {
                "entidade_concedente": "Câmara Municipal de Marilia",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },
            "Medalha Sargento Nilson Mikio Futura Júnior": {
                "entidade_concedente": "Gabinete de Gestão Integrada da Comarca da Estância de Atibaia",
                "ordem": "VI",
                "tipo": "GOVERNAMENTAIS_NIVEL_MUNICIPAL"
            },

            # MEDALHAS NÃO GOVERNAMENTAIS - ENTIDADES CIVIS
            "Colar \"Tenente Coronel Álvaro Martins\"": {
                "entidade_concedente": "Sociedade Veteranos de 32 - MMDC Núcleo Escola Superior de Bombeiros",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Cadete PM Ruytemberg Rocha o Cadete Constitucionalista": {
                "entidade_concedente": "Núcleo Cadete Ruytemberg Rocha da APMBB e Sociedade Veteranos 32 - MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Cadete PM Ruytemberg Rocha o Cadete PM Herói de 1932": {
                "entidade_concedente": "Núcleo Cadete Ruytemberg Rocha da APMBB e Sociedade Veteranos 32 - MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Cruz da Honra Constitucionalista": {
                "entidade_concedente": "Sociedade Veteranos de 32 - MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Cruz do Alvarenga e dos Heróis Anônimos": {
                "entidade_concedente": "Instituto Histórico, Geográfico e Genealógico de Sorocaba",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar da Vitória Evocativo aos 80 anos da Revolução Constitucionalista de 1932": {
            "entidade_concedente": "Sociedade Veteranos de 32 - MMDC",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Evocativo do Jubileu de Brilhante da Revolução Constitucionalista": {
            "entidade_concedente": "Instituto Histórico, Geográfico e Genealógico de Sorocaba",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar General de Brigada Médico João Severiano da Fonseca Patrono do Serviço de Saúde do Exército Brasileiro": {
            "entidade_concedente": "Academia de História Militar Terrestre do Brasil de São Paulo e pelo Hospital Militar de Área de São Paulo",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Bento Gonçalves": {
            "entidade_concedente": "Instituto Histórico, Geográfico e Genealógico do Grande ABC",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Heróis e Silva": {
            "entidade_concedente": "Sociedade Veteranos de 32 MMDC - Núcleo Ibirapuera",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Heróis de 32 - O triunfo": {
            "entidade_concedente": "Sociedade Veteranos de 32 MMDC - Núcleo Ibirapuera",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Heróis de 32 - Tributo ao Pantheon": {
            "entidade_concedente": "Sociedade Veteranos de 32 MMDC - Núcleo Ibirapuera",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Heróis de Araraquara": {
            "entidade_concedente": "Núcleo MMDC - Heróis de Araraquara",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Heróis de fogo": {
            "entidade_concedente": "Fundação de Apoio ao Corpo de Bombeiros da Policia Militar do Estado de São Paulo",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Heróis do Trem Blindado": {
            "entidade_concedente": "Núcleo MMDC - Jundiaí Heróis do Trem Blindado",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar O Patriarca da Independência José Bonifácio de Andrade e Silva": {
            "entidade_concedente": "Sociedade Amigos do Centro de Preparação de Oficiais da Reserva de São Paulo - SOAMI - CPOR/SP",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Ordem de Mérito Cruz do Anhembi": {
            "entidade_concedente": "Sociedade Amigos da Cidade",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Colar Visconde de Porto Seguro": {
            "entidade_concedente": "Instituto Histórico e Geográfico de São Paulo e outras",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Comenda Ordem de Mérito Cruz do Anhembi": {
            "entidade_concedente": "Sociedade Amigos da Cidade",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Cruz de Honra Legionária": {
            "entidade_concedente": "Legião dos Veteranos de Guerra de Guerra do Brasil - Seção Niterói",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Grã-Cruz Heróis de 32 - Sempre Viverão": {
            "entidade_concedente": "Sociedade Veteranos de 32 MMDC - Núcleo Ibirapuera",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Grã-Cruz Heróis de Fogo": {
            "entidade_concedente": "Fundação de Apoio ao Corpo de Bombeiros da Polícia Militar do Estado de São Paulo",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Grã-Cruz Ordem do Mérito Cruz do Anhembi": {
            "entidade_concedente": "Sociedade Amigos da Cidade",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Grande Colar Heróis de 32 Tributo aos Constitucionalista": {
            "entidade_concedente": "Sociedade Veteranos de 32 MMDC - Núcleo Ibirapuera",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Grão-Colar Ordem do Mérito Cruz do Anhembi": {
            "entidade_concedente": "Sociedade Amigos da Sociedade",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Asas da Vitória": {
            "entidade_concedente": "Legião dos Veteranos de Guerra de Guerra do Brasil - Seção Niterói",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Audazes Bombeiros": {
            "entidade_concedente": "Sociedade Veteranos de 32 - MMDC Núcleo Escola Superior de Bombeiros",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Bicentenário do Nascimento do Marechal Osório": {
            "entidade_concedente": "Academia de Estudo de Assuntos Históricos",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Brigadeiro José Vieira Couto de Magalhães": {
            "entidade_concedente": "Sociedade Geográfica Brasileira",
            "ordem": "V",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Cabo Augusto de Moraes": {
            "entidade_concedente": "Núcleo MMDC - Heróis de Araraquara",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Cabo Bento Martins de Souza": {
            "entidade_concedente": "Sociedade Veteranos de 32 - Núcleo MMDC Cabo Bento Martins de Souza",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Cadete Constitucionalista": {
            "entidade_concedente": "Núcleo Cadete Ruytemberg Rocha da APMBB e Sociedade Veteranos de 32- MMDC",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Capitão Franklin Mérito do Músico Militar": {
            "entidade_concedente": "Consultoria Nacional de Outorgas (CNO)",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Carmo Turano": {
            "entidade_concedente": "Sociedade Veteranos de 32 - MMDC de São José do Rio Preto",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Caxias - Patrono do Exército Brasileiro": {
            "entidade_concedente": "Academia de Estudo de Assuntos Históricos",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Cidadão Policial": {
            "entidade_concedente": "Associação para Valorização Policial do Estado de São Paulo - AVPESP",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Cinquentenário das Forças de Paz do Brasil ONU": {
            "entidade_concedente": "Associação Brasileira das Forças Internacionais de Paz da ONU - ABFIP ONU",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Cinquentenário do Batalhão Suez": {
            "entidade_concedente": "Associação Brasileira de Integrantes do Batalhão Suez",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Combatentes de 32": {
            "entidade_concedente": "Núcleo MMDC - Atibaia Soldado Bento Gonçalves",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Comemorativa de Vinte e Cinco Anos da Sociedade Veteranos de 32 MMDC": {
            "entidade_concedente": "Sociedade Veteranos de 32-MMDC de São José do Rio Preto",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Constitucionalista": {
            "entidade_concedente": "Sociedade Veteranos de 32 - MMDC",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Coronel PM Delfim Cerqueira Neves": {
            "entidade_concedente": "Associação dos Oficiais da Polícia Militar do Estado de São Paulo",
            "ordem": "V",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Cruz de Paz dos Veteranos da FEB": {
            "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção Campo Grande - MS",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Cruz do Mérito Filosófico e Cultural": {
            "entidade_concedente": "Sociedade Brasileira de Filosofia, literatura e Ensino",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha da Vitória": {
            "entidade_concedente": "Ordem dos Cavaleiros da Inconfidência Mineira OCIM",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha da Vitória": {
            "entidade_concedente": "Associação dos Ex-Combatentes do Brasil Seção Rio de Janeiro",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha de Honra ao Mérito Coronel Francisco vieira": {
            "entidade_concedente": "Núcleo Base MMDC de Itapira Luz da Pátria",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha do Bicentenário Dragões da Independência": {
            "entidade_concedente": "Consultoria Nacional de Outorgas (CNO)",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha do Mérito Ana Terra": {
            "entidade_concedente": "Instituto Histórico, Geográfico e Genealógico de Sorocaba",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha do Mérito Cívico Militar": {
            "entidade_concedente": "Academia de Medalhistica Militar",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha do Mérito da Academia Brasileira de Medalhística Militar (ABRAMMIL) Grau Cavaleiro": {
            "entidade_concedente": "Academia Brasileira de Medalhística Militar -ABRAMMIL",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Ordem do Mérito do Batalhão de Suez Grau Bronze": {
            "entidade_concedente": "Associação Brasileira de Integrantes do Batalhão de Suez",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Ordem do Mérito do Batalhão de Suez Grau Ouro": {
            "entidade_concedente": "Associação Brasileira de Integrantes do Batalhão de Suez",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Ordem do Mérito do Batalhão de Suez Grau Prata": {
            "entidade_concedente": "Associação Brasileira de Integrantes do Batalhão de Suez",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha do Mérito do Tiro de Guerra": {
            "entidade_concedente": "Academia de Estudos de Assuntos Históricos",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha do Mérito Juventude Constitucionalista": {
            "entidade_concedente": "Sociedade Veteranos de 32 MMDC",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha do Mérito Marechal Castelo Branco": {
            "entidade_concedente": "Academia Brasileira de Medalhística Militar -ABRAMMIL",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha do Mérito Marechal Castelo Branco Bronze": {
            "entidade_concedente": "Associação Campineira de Oficiais da Reserva do Exército (R/2) do NPOR do 28°BIB",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha do Mérito Marechal Castelo Branco Ouro": {
            "entidade_concedente": "Associação Campineira de Oficiais da Reserva do Exército (R/2) do NPOR do 28°BIB",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha do Mérito Marechal Castelo Branco Prata": {
            "entidade_concedente": "Associação Campineira de Oficiais da Reserva do Exército (R/2) do NPOR do 28°BIB",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha do Mérito Rondon": {
            "entidade_concedente": "Academia de Estudo de Assuntos Históricos",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha do Sesquicentenário do Corpo de Bombeiro Militar do Estado do Rio de Janeiro": {
            "entidade_concedente": "Legião dos Veteranos de Guerra do Brasil - Seção Niterói",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha dona May de Souza Neves": {
            "entidade_concedente": "Núcleo MMDC - Heróis de Araraquara",
            "ordem": "VI",
            "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Dráusio Marcondes de Souza": {
                "entidade_concedente": "Sociedade Veteranos de 32 MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Duque de Caxias": {
                "entidade_concedente": "Ordem dos Cavaleiros da Inconfidência Mineira - OCIM",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Esplendor de São Miguel Paulista": {
                "entidade_concedente": "Sociedade Veteranos de 32 MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Garra e Coragem": {
                "entidade_concedente": "Legião dos Veteranos de Guerra do Brasil - Seção Niterói",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha General Euclydes de Oliveira Figueiredo": {
                "entidade_concedente": "Núcleo MMDC Norte da Sociedade Veteranos de 32",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha General Francisco Alves do Nascimento Pinto": {
                "entidade_concedente": "Caixa Beneficente da Polícia Militar do Estado de São Paulo",
                "ordem": "V",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha General Plínio Pitaluga": {
                "entidade_concedente": "Associação dos Ex Combatentes do Brasil - Seção Rio de Janeiro",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Governador Pedro de Toledo": {
                "entidade_concedente": "Sociedade Veteranos de 32 MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Heróis Anônimos": {
                "entidade_concedente": "Núcleo MMDC - Jundiaí \"Heróis do Trem Blindado\"",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Heróis de 32 - Luta e Constituição": {
                "entidade_concedente": "Sociedade Veteranos de 32 MMDC - Núcleo Ibirapuera",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Heróis de Fogo": {
                "entidade_concedente": "Fundação Apoio ao Corpo de Bombeiros da Polícia Militar do Estado de São Paulo",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Heróis do Brasil": {
                "entidade_concedente": "Associação Nacional dos Veteranos da FEB - Seção Regional de São Bernardo do Campo",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Heróis do Trem Blindado": {
                "entidade_concedente": "Núcleo MMDC - Jundiaí \"Heróis do Trem Blindado\"",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Internacional dos Veteranos das Nações Unidas e Estados Americanos": {
                "entidade_concedente": "Organização Brasileira dos Veteranos das Nações Unidas e Estados Americanos",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Jubileu de Prata": {
                "entidade_concedente": "Associação Brasileira das Forças Internacionais de Paz da ONU - ABFIP ONU",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Lágrima da Terra": {
                "entidade_concedente": "Instituto Histórico, Geográfico e Genealógico de Sorocaba",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Leão de Judá": {
                "entidade_concedente": "Organização Institucional Teocrático da Coroa dos Arameus e das Auramitas",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Liberdade e Democracia": {
                "entidade_concedente": "Associação dos Ex- Combatentes do Brasil Seção São Paulo",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Luz da Pátria": {
                "entidade_concedente": "Sociedade Veteranos de 32 - MMDC Núcleo Escola Superior de Bombeiros",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mallet": {
                "entidade_concedente": "Núcleo MMDC Caetano de Campos da Secretaria da Educação do Estado de São Paulo",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Marechal Cordeiro de Farias (FEB)": {
                "entidade_concedente": "Associação dos Veteranos da Força Expedicionária Brasileira - Seção Florianópolis - SC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Marechal Falconiére": {
                "entidade_concedente": "Associação dos Veteranos da Força Expedicionária Brasileira - Seção Florianópolis - SC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Marechal João Propicio": {
                "entidade_concedente": "Consultoria Nacional de Outorgas (CNO)",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Marechal Machado Lopes": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção Campo Grande - MS",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Marechal Mascarenhas de Moraes": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Marechal Zenóbio da Costa": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Maria Della Costa": {
                "entidade_concedente": "Sociedade Veteranos de 32 - MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Martim Afonso de Souza": {
                "entidade_concedente": "Sociedade Veteranos de 32 - MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito Acadêmico Militar": {
                "entidade_concedente": "Academia Brasileira de Medalhística Militar - ABRAMMIL",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito da FEB": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção de Santos",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito da FEB - Campanha da Itália": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção Regional de São Bernardo do Campo",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito da FEB - Cruz de Sangue": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção Regional de São Bernardo do Campo",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito da Força Expedicionária Brasileira": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção Regional de São Bernardo do Campo",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito da Juventude Constitucionalista": {
                "entidade_concedente": "Sociedade Veteranos de 32 - MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito da Polícia Militar do Estado de São Paulo": {
                "entidade_concedente": "Associação dos Oficiais da Polícia Militar do Estado de São Paulo",
                "ordem": "V",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito do Ex-Combatente": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção Regional de São Bernardo do Campo",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito do Ex-Combatente": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção de Santos",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito Ex-Combatente do Brasil": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção Campinas",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito Funcional": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção Regional de São Bernardo do Campo",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito Histórico Tiradentes": {
                "entidade_concedente": "Academia Brasileira de Medalhística Militar - ABRAMMIL",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito Pedro Dias de Campos": {
                "entidade_concedente": "Sociedade Veteranos de 32 - MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Mérito Ruytemberg Rocha": {
                "entidade_concedente": "Núcleo Cadete Ruytemberg Rocha da APMBB e Sociedade Veteranos de 32 MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha MMDC - 70 Anos": {
                "entidade_concedente": "Sociedade Veteranos de 32 - MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha MMDC - Piratininga": {
                "entidade_concedente": "Sociedade Veteranos de 32 - MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Monsenhor João Batista de Carvalho": {
                "entidade_concedente": "Sociedade Veteranos de 32 - MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Nipo Brasileira": {
                "entidade_concedente": "Sociedade Brasileira de Cultura Japonesa e de Assistência Social",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Nove de Julho": {
                "entidade_concedente": "Sociedade Veteranos de 32 - MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Ordem do Mérito da Paz Ecumênica": {
                "entidade_concedente": "Sociedade Brasileira de Heráldica e Medalhística",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Ordem do Mérito do Ex-Combatente do Brasil": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção Campinas",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Ordem do Mérito Marechal José Bernardino Bormann": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção Regional de São Bernardo do Campo",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Paulo e Virgínia": {
                "entidade_concedente": "Sociedade Veteranos de 32 - MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Presidente Castelo Branco": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Presidente Getúlio Vargas": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Professor Lourenço Filho": {
                "entidade_concedente": "Sociedade Veteranos de 32 - MMDC",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Santos Dumont": {
                "entidade_concedente": "Instituto Histórico e Geográfico de Santos",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Sargento Max Wolf Filho": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção Regional de São Bernardo do Campo",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Sargento Mário Kozel Filho": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção Regional de São Bernardo do Campo",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Sargento Expedicionário Antônio Dias Adorno": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira - Seção Regional de São Bernardo do Campo",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Serviço de Saúde FEB": {
                "entidade_concedente": "Associação Nacional dos Veteranos da Força Expedicionária Brasileira",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Soldado da Paz": {
                "entidade_concedente": "Associação dos Integrantes do Batalhão Suez",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Souza Carvalho": {
                "entidade_concedente": "Associação Amigos Grupo Bandeirantes -\nAGRUBAN",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Tiradentes": {
                "entidade_concedente": "Associação Brasileira das Forças Internacionais de\nPaz e a Academia de Assuntos Histórico Militar",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            },
            "Medalha Valor Cívico": {
                "entidade_concedente": "Conselho Superior de Honrarias e Méritos dos\nAmigos e Ex-Militares do EB",
                "ordem": "VI",
                "tipo": "NAO_GOVERNAMENTAIS"
            }
        }


class MilitarMedalha(models.Model):
    id = models.AutoField(primary_key=True)
    cadastro = models.ForeignKey(
        Cadastro,
        related_name='medalhas_concedidas',
        on_delete=models.DO_NOTHING
    )
    medalha = models.ForeignKey(Medalha, on_delete=models.CASCADE)
    data_concessao = models.DateField()
    observacoes = models.TextField(blank=True, null=True)
    usuario_alteracao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    # NOVOS CAMPOS PARA ARMAZENAR DADOS NO MOMENTO DO REGISTRO
    entidade_concedente_registro = models.CharField(max_length=255, blank=True, null=True)
    ordem_registro = models.CharField(max_length=10, blank=True, null=True)
    tipo_registro = models.ForeignKey(TipoMedalha, on_delete=models.SET_NULL, null=True, blank=True, related_name='militar_medalhas_tipo') # Armazenar o TipoMedalha real

    def __str__(self):
        return f"{self.cadastro.nome_de_guerra} - {self.medalha.honraria}"

    class Meta:
        verbose_name = "Medalha de Militar"
        verbose_name_plural = "Medalhas de Militares"