# 🧭 SisCoE — Sistema de Controle de Efetivo

> **SisCoE** é uma plataforma completa de gestão operacional e administrativa, projetada para otimizar o controle de efetivo, escalas, documentos, treinamentos e muito mais — centralizando todas as operações em um único sistema integrado.

---

## 📘 Sumário
- [Descrição Geral](#descrição-geral)
- [Arquitetura e Tecnologias](#arquitetura-e-tecnologias)
- [Instalação e Configuração](#instalação-e-configuração)
- [Uso e Execução](#uso-e-execução)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Funcionalidades Principais](#funcionalidades-principais)
- [Testes e Qualidade de Código](#testes-e-qualidade-de-código)
- [Contribuição](#contribuição)
- [Licença](#licença)
- [Contato](#contato)

---

## 🧩 Descrição Geral

O **SisCoE** foi desenvolvido para [coloque aqui o propósito exato, ex: “gerenciar de forma eficiente o efetivo de corporações militares, otimizando escalas, cursos e atividades administrativas”].

O sistema integra diversos módulos especializados:
- Gestão de pessoal (efetivo)
- Planejamento e escalas
- CRM (relacionamento com colaboradores e parceiros)
- Cursos e certificações
- Documentos e relatórios

---

## ⚙️ Arquitetura e Tecnologias

| Camada | Tecnologias |
|--------|--------------|
| **Backend** | Django, Python 3.10+ |
| **Frontend** | JavaScript, Tailwind CSS, Flowbite, FullCalendar.js |
| **Banco de Dados** | PostgreSQL (produção), SQLite3 (desenvolvimento) |
| **Infra e Deploy** | Gunicorn, Whitenoise, Nginx, Docker (opcional) |
| **Integrações** | Brevo (SMTP e notificações por e-mail) |
| **Documentação** | MkDocs + Material for MkDocs |

---

## 🧰 Instalação e Configuração

### Pré-requisitos
- Python 3.10+
- Node.js e npm
- Git
- PostgreSQL (para produção)

### Passo a passo

```bash
# 1. Clonar o repositório
git clone git@github.com:Andre-fdias/SisCoE.git
cd SisCoE

# 2. Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate   # No Windows: venv\Scripts\activate

# 3. Instalar dependências Python
pip install -r requirements.txt

# 4. Instalar dependências do frontend
npm install

# 5. Configurar variáveis de ambiente
cp .envexample .env
# Edite o arquivo .env conforme seu ambiente

# 6. Criar o banco e aplicar migrações
python manage.py makemigrations
python manage.py migrate

# 7. Criar usuário administrador
python manage.py createsuperuser
```

## 🖥️ Uso e Execução

Execute o servidor de desenvolvimento:

```bash
python manage.py runserver
```

Acesse em: 👉 http://127.0.0.1:8000

- **Painel administrativo:** `/admin`
- **Interface principal:** `/`

## 🗂️ Estrutura do Projeto

```
.
├── backend/            # Contém toda a lógica principal da aplicação Django
│   ├── accounts/       # Gestão de usuários, autenticação e perfis
│   ├── adicional/      # Lógica para adicionais e benefícios
│   ├── agenda/         # Módulo de agenda e calendário
│   ├── bm/             # Funcionalidades relacionadas a Bombeiros Municipais
│   ├── calculadora/    # Ferramenta de cálculo de tempo de serviço(em desenvolvimento)
│   ├── core/           # Funcionalidades centrais e compartilhadas
│   ├── crm/            # Módulo de Customer Relationship Management
│   ├── cursos/         # Gestão de cursos e Medalhas
│   ├── documentos/     # Upload e gerenciamento de documentos, sistema de galeria para educação a distancia
│   ├── efetivo/        # Controle de pessoal e efetivo
│   ├── lp/             # Módulo de Licença Prêmio
│   ├── municipios/     # Gestão de municípios e dados geográficos
│   ├── rpt/            # Geração de Relação de Transferência
│   ├── settings/       # Arquivos de configuração do Django (dev, prod)
│   ├── static/         # Arquivos estáticos globais do backend
│   └── templates/      # Templates HTML globais do backend
├── docs/               # Arquivos da documentação do projeto (MkDocs)
├── node_modules/       # Dependências do frontend (gerenciado pelo npm)
├── static/             # Arquivos estáticos coletados para produção
├── venv/               # Ambiente virtual do Python
├── .env.example        # Arquivo de exemplo para variáveis de ambiente
├── requirements.txt    # Dependências do Python (pip)
├── package.json        # Dependências do frontend (npm)
├── manage.py           # Utilitário de linha de comando do Django
└── README.md           # Este arquivo
```

## 🔍 Funcionalidades Principais

| Módulo | Descrição |
|---|---|
| **Accounts** | Controle de usuários, autenticação e permissões |
| **Efetivo** | Escalas, lotações e controle de pessoal |
| **CRM** | Relacionamento e registro de interações |
| **Agenda** | Agendamento e calendário de eventos |
| **Cursos** | Gestão de cursos, certificados e progressão |
| **Documentos** | Upload e controle documental com versionamento |
| **RPT** | Relatórios administrativos e estatísticos |
| **Calculadora** | Ferramenta integrada de cálculo |

## 🧪 Testes e Qualidade de Código

Execute todos os testes automatizados:

```bash
python manage.py test
```

Verifique lint e estilo de código (se estiver configurado):

```bash
# Exemplo com flake8 e black
flake8
black --check .
```

## 🤝 Contribuição

Contribuições são muito bem-vindas!
Siga o fluxo padrão de Git Flow:

```bash
# Criar nova branch de feature
git checkout -b feature/nome-da-feature

# Commit semântico
git commit -m "feat(efetivo): adiciona cálculo de adicionais"

# Push e criação de PR
git push origin feature/nome-da-feature
```

Antes de abrir o PR:

- ✅ Execute todos os testes
- 📝 Documente o que foi alterado
- 📚 Atualize a documentação (`docs/`)

## 📘 Documentação Técnica (MkDocs)

A documentação detalhada por app está em `docs/`, e pode ser visualizada localmente com:

```bash
mkdocs serve
```

Acesse: 👉 http://127.0.0.1:8001

Cada módulo (accounts, crm, efetivo, etc.) possui uma seção explicando suas models, views, signals, e endpoints.

## 🪪 Licença

Distribuído sob a licença MIT.
Consulte o arquivo `LICENSE` para mais detalhes.

## 📞 Contato

👤 **André Fonseca Dias**

📧 andrefonsecadias21@gmail.com

🔗 **GitHub:** [Andre-fdias](https://github.com/Andre-fdias)

## 🧱 Extras

- 📚 **Documentação:** `docs/`
- 🚀 **Deploy:** (adicione link de produção se houver)
- 🔄 **CI/CD:** Configurável via GitHub Actions (`.github/workflows/deploy.yml`)