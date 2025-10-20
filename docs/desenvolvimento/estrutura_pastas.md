# Estrutura de Pastas do Projeto

A organização do código-fonte do SisCoE segue as convenções do Django, com uma estrutura clara que separa as responsabilidades e facilita a navegação e manutenção.

## Estrutura Geral da Raiz

```
/home/andre/Repositorio/SisCoE/
├── backend/            # Contém todo o código-fonte do Django.
├── contrib/            # Scripts de utilidade para o projeto.
├── docker/             # Arquivos de configuração do Docker.
├── docs/               # Arquivos da documentação (MkDocs).
├── import/             # Scripts e arquivos para importação de dados.
├── node_modules/       # Dependências do frontend (gerado pelo npm).
├── static/             # Arquivos estáticos coletados pelo Django para produção.
├── venv/               # Ambiente virtual do Python.
├── .env_example        # Exemplo de arquivo de variáveis de ambiente.
├── docker-compose.yml  # Orquestração dos contêineres Docker.
├── Dockerfile          # Definição do contêiner da aplicação.
├── manage.py           # Utilitário de linha de comando do Django.
├── mkdocs.yml          # Arquivo de configuração do MkDocs.
├── package.json        # Dependências e scripts do Node.js.
├── requirements.txt    # Dependências do Python.
└── tailwind.config.js  # Configuração do Tailwind CSS.
```

---

## Diretório `backend/`

Este é o coração do projeto, onde toda a lógica da aplicação Django reside.

```
backend/
├── backend/            # Diretório principal do projeto Django.
│   ├── __init__.py
│   ├── asgi.py         # Configuração para servidores ASGI.
│   ├── settings/       # Módulo de configurações (base.py, dev.py, prod.py).
│   ├── urls.py         # Roteador de URLs principal.
│   └── wsgi.py         # Configuração para servidores WSGI.
│
├── accounts/           # App Django: Gestão de usuários, autenticação e perfis.
├── adicional/          # App Django: Funcionalidades adicionais.
├── agenda/             # App Django: Gerenciamento de agendas e eventos.
├── bm/                 # App Django: Gestão de Batalhões.
├── calculadora/        # App Django: Ferramentas de cálculo.
├── core/               # App Django: Funcionalidades centrais e compartilhadas.
├── crm/                # App Django: Módulo de CRM.
├── cursos/             # App Django: Gestão de cursos e matrículas.
├── documentos/         # App Django: Gerenciamento de documentos.
├── efetivo/            # App Django: Controle do efetivo de pessoal.
├── lp/                 # App Django: Logística.
├── municipios/         # App Django: Gestão de municípios.
└── rpt/                # App Django: Geração de relatórios.
```

### Estrutura de um App Django Típico (`backend/<app>/`)

Cada aplicativo dentro do `backend/` segue uma estrutura padronizada que organiza suas responsabilidades:

```
<app_name>/
├── __init__.py
├── admin.py          # Registro dos models na interface de admin do Django.
├── apps.py           # Configuração do aplicativo.
├── forms.py          # Definição de formulários.
├── models.py         # Definição dos modelos de dados (tabelas do banco).
├── signals.py        # Definição de sinais para eventos.
├── tests.py          # Testes unitários e de integração para o app.
├── urls.py           # Rotas de URL específicas do app.
├── views.py          # Lógica de negócio (controllers).
├── migrations/       # Arquivos de migração do banco de dados (gerados).
├── static/           # Arquivos estáticos específicos do app (CSS, JS, imagens).
└── templates/        # Templates HTML específicos do app.
```

!!! tip "Boas Práticas de Design de Apps"
    - **Baixo Acoplamento**: Cada app deve ser o mais independente possível, evitando dependências circulares.
    - **Alta Coesão**: A lógica dentro de um app deve ser focada em uma única e bem definida responsabilidade de negócio.

---

## Outros Diretórios e Arquivos Importantes

-   **`docs/`**: Contém todos os arquivos Markdown que geram esta documentação.
-   **`static/` (na raiz)**: Este diretório não é para ser usado diretamente. Ele é o destino do comando `python manage.py collectstatic`, que reúne todos os arquivos estáticos de todos os apps em um único lugar para serem servidos em produção.
-   **`venv/`**: O ambiente virtual que isola as dependências Python do projeto. Não é versionado (está no `.gitignore`).
-   **Arquivos de Configuração**: `requirements.txt` (Python) e `package.json` (Node.js) definem as dependências do projeto. O arquivo `.env` (criado a partir do `.env_example`) guarda as variáveis de ambiente e segredos, mantendo-os fora do controle de versão.