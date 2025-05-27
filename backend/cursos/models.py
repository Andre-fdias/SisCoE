from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import locale
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from backend.efetivo.models import Cadastro
from django.conf import settings

class Medalha(models.Model):

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
    cadastro = models.ForeignKey( Cadastro, related_name='medalhas_concedidas', on_delete=models.DO_NOTHING)
    honraria = models.CharField(max_length=255, choices=HONRARIA_CHOICES)
    bol_g_pm_lp = models.CharField(max_length=50, null=True, blank=True, verbose_name="BOL GPm LP")
    data_publicacao_lp = models.DateField(null=True, blank=True, verbose_name="Data Publicação LP")
    observacoes = models.TextField(blank=True, null=True)
    usuario_alteracao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        # Assuming 'cadastro' has a 'nome' attribute. Adjust if different.
        return f"{self.honraria} para {self.cadastro.nome}"



    class Meta:
        verbose_name = "Curso" # Como discutimos antes, isso pode ser confuso já que o modelo é Medalha
        verbose_name_plural = "Cursos" # Mesma observação
        # Original:
        # ordering = ['-data_publicacao'] # Ordenação padrão

        # CORREÇÃO:
        ordering = ['-data_publicacao_lp'] # Ordenação padrão


class Curso(models.Model):

    CURSOS_CHOICES = (
        ('Atendimento Pré-Hospitalar Tático', 'Atendimento Pré-Hospitalar Tático'),
        ('Gestão pela Qualidade_Oficial', 'Gestão Contemporânea pela Qualidade'),
        ('Administração de Projetos', 'Administração de Projetos '),
        ('Gestão por Processos', 'Gestão por Processos '),
        ('Gestão Qualidade', 'Gestão Qualidade '),
        ('Comunicação Social', 'Comunicação Social '),
        ('Gestores de Defesa Civil', 'Gestores de Defesa Civil '),
        ('Operador RPAS', 'Operador de RPAS '),
        ('Tripulante Operacional', 'Tripulante Operacional'),
        ('Pressurização Escadas', ' Pressurização de Escadas '),
        ('Atendente COPOM', 'Atendente COPOM '),
        ('Ferramentas Inteligentes', 'Ferramentas Inteligentes '),
        ('Supervisão COPOM', 'Supervisão Operacional'),
        ('Operador COPOM', 'Operador de COPOM '),
        ('Investigação PM', 'Investigação PM'),
        ('PJM', 'Polícia Judiciária Militar '),
        ('Capacitação Tutores EAD', 'Capacitação de Tutores Ead'),
        ('Finanças Públicas', 'Finanças Públicas '),
        ('Auxiliar Encarregado Adiantamentos', 'Auxiliar de Encarregado de Adiantamentos '),
        ('Gestão de Contratos', 'Gestão de Contratos'),
        ('Técnico Logística', 'Técnico Logística '),
        ('Administrador Logística', 'Administrador Logística '),
        ('Operador RH', 'OOperador RH'),
        ('Técnico RH', 'Técnico em RH'),
        ('Administrador RH', 'Administrador RH'),
        ('CBEF', 'Ed Fisica PM'),
        ('OVB', 'OVB'),
        ('Abordagem Suicídio', 'Abordagem Suicídio '),
        ('CEP_Bombeiros_Civis', 'Bombeiros - Civis - 1'),
        ('Salvamento Aquático', 'Salvamento Aquático '),
        ('DREM', 'DREM'),
        ('REM', 'REM'),
        ('Produtos Perigosos', 'Produtos Perigosas'),
        ('CMAUT', 'CMAUT'),
        ('Operações Bote ', 'Operações com Bote '),
        ('Salvamento Terrestre', 'Salvamento Terrestre '),
        ('Salvamento Veicular', 'Salvamento Veicular'),
        ('Guarda-Vidas', 'Guarda-Vidas'),
        ('CSALT', 'CSALT'),
        ('MOB', 'MOB'),
        ('BREC', 'BREC'),
        ('CFS', 'CFS'),
        ('CBS', 'CBS'),
        ('CBCS', 'CBCS'),
        ('CBO', 'CBO'),
        ('Técnicas de Ensino', 'Técnicas de Ensino'),
     
    )

    cadastro = models.ForeignKey(Cadastro, on_delete=models.CASCADE, related_name='cursos')
    curso = models.CharField(max_length=255, choices=CURSOS_CHOICES)
   
    data_publicacao = models.DateField(verbose_name="Data de Publicação") # Campo único para data
    bol_publicacao = models.CharField(max_length=255, verbose_name="BOL Publicação")
    observacoes = models.TextField(blank=True, null=True)
    usuario_alteracao = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_alteracao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['-data_publicacao'] # Ordenação padrão

    def __str__(self):
        # SIMPLIFIQUE O __str__ PARA NÃO USAR outro_curso
        # if self.curso == 'OUTRO' and self.outro_curso:
        #     curso_nome = self.outro_curso
        # else:
        curso_nome = self.get_curso_display() # Obtém o nome legível da escolha
        
        nome_cadastro = "Militar Desconhecido"
        if self.cadastro and hasattr(self.cadastro, 'nome') and self.cadastro.nome:
            nome_cadastro = self.cadastro.nome
        elif self.cadastro and hasattr(self.cadastro, 're') and self.cadastro.re:
             nome_cadastro = f"RE {self.cadastro.re}"

        return f"{curso_nome} - {nome_cadastro}"

    def save(self, *args, **kwargs):
        # REMOVA A LÓGICA DE DEFINIR outro_curso como None
        # if self.curso != 'OUTRO':
        #     self.outro_curso = None
        super().save(*args, **kwargs)

 
    # Mapeamento de tags para os cursos
    CURSOS_TAGS = {
        # Administrativo
        'Gestão pela Qualidade_Oficial': 'Administrativo',
        'Administração de Projetos': 'Administrativo',
        'Gestão por Processos': 'Administrativo',
        'Gestão Qualidade': 'Administrativo',
        'Comunicação Social': 'Administrativo',
        'Gestores de Defesa Civil': 'Administrativo',
        'Pressurização Escadas': 'Administrativo',
        'Atendente COPOM': 'Administrativo',
        'Ferramentas Inteligentes': 'Administrativo',
        'Supervisão COPOM': 'Administrativo',
        'Operador COPOM': 'Administrativo',
        'Investigação PM': 'Administrativo',
        'PJM': 'Administrativo',
        'Finanças Públicas': 'Administrativo',
        'Auxiliar Encarregado Adiantamentos': 'Administrativo',
        'Gestão de Contratos': 'Administrativo',
        'Técnico Logística': 'Administrativo',
        'Administrador Logística': 'Administrativo',
        'Operador RH': 'Administrativo',
        'Técnico RH': 'Administrativo',
        'Administrador RH': 'Administrativo',
        'CBEF': 'Administrativo',  # Ed Fisica PM
        'OVB': 'Administrativo',

        # Operacional
        'Abordagem Suicídio': 'Operacional',
        'CEP_Bombeiros_Civis': 'Operacional',
        'Salvamento Aquático': 'Operacional',
        'DREM': 'Operacional',
        'REM': 'Operacional',
        'Produtos Perigosos': 'Operacional',
        'CMAUT': 'Operacional',
        'Operações Bote': 'Operacional',
        'Salvamento Terrestre': 'Operacional',
        'Salvamento Veicular': 'Operacional',
        'Guarda-Vidas': 'Operacional',
        'CSALT': 'Operacional',
        'MOB': 'Operacional',
        'BREC': 'Operacional',
        'CFS': 'Operacional',
        'CBS': 'Operacional',
        'CBCS': 'Operacional',
        'CBO': 'Operacional',
        'Operador RPAS': 'Operacional',
        'Tripulante Operacional': 'Operacional',
        'Atendimento Pré-Hospitalar Tático': 'Operacional',
    }
