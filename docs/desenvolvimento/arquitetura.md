# Arquitetura do Backend

O backend do SisCoE é construído sobre o framework **Django**, seguindo uma arquitetura de **Monolito Modular**. Esta abordagem combina a simplicidade de desenvolvimento de um projeto monolítico com a organização e o baixo acoplamento de um sistema modular.

!!! success "Princípio do Monolito Modular"
    A aplicação é desenvolvida e implantada como uma única unidade (monolito), mas seu código é organizado em **aplicativos (apps) Django independentes**. Cada app encapsula uma funcionalidade de negócio específica (ex: `accounts`, `efetivo`, `cursos`), promovendo a reutilização de código e a manutenibilidade.

---

## Padrão MVT (Model-View-Template)

O Django implementa uma variação do padrão MVC (Model-View-Controller), conhecido como **MVT (Model-View-Template)**. A lógica é organizada da seguinte forma:

```mermaid
graph TD
    A[Usuário] --> B{Roteador de URL (urls.py)};
    B --> C{View (views.py)};
    C --> D[Model (models.py)];
    D --> E[Banco de Dados];
    C --> F[Template (templates/*.html)];
    F --> G[Conteúdo Renderizado (HTML)];
    G --> A;

    subgraph "Lógica de Negócio"
        C
    end

    subgraph "Camada de Dados"
        D
        E
    end

    subgraph "Camada de Apresentação"
        F
        G
    end
```

- **Model (`models.py`)**: Representa a estrutura dos dados, definindo os campos e comportamentos do banco de dados. Os models do SisCoE estão localizados em `backend/<app>/models.py`.

- **View (`views.py`)**: É a lógica de negócio que processa as requisições do usuário, interage com os models e renderiza os templates. As views estão em `backend/<app>/views.py`.

- **Template (`templates/`)**: É a camada de apresentação, responsável por renderizar o HTML que o usuário vê. Os templates estão em `backend/<app>/templates/`.

- **URL Dispatcher (`urls.py`)**: Mapeia as URLs requisitadas pelo navegador para as `Views` correspondentes.

!!! example "Exemplo de Fluxo de Requisição"
    1.  O navegador de um usuário faz uma requisição para `/efetivo/1/`.
    2.  O **URL Dispatcher** principal do Django (`backend/urls.py`) identifica que o padrão `efetivo/` pertence ao app `efetivo` e repassa a requisição para o `urls.py` desse app.
    3.  O `urls.py` do app `efetivo` mapeia o restante do caminho (`1/`) para a view `detalhe_efetivo`.
    4.  A **View** `detalhe_efetivo` é executada. Ela utiliza o **Model** `Efetivo` para buscar no banco de dados o registro com `id=1`.
    5.  A view, de posse do objeto `efetivo`, renderiza o **Template** `detalhe_efetivo.html`, passando o objeto como contexto.
    6.  O template é processado, inserindo os dados do efetivo no HTML.
    7.  O HTML final é retornado como resposta ao navegador do usuário.

---

## Frontend e Arquivos Estáticos

O frontend não é desacoplado (não é uma SPA). Ele é renderizado diretamente pelo Django, utilizando uma combinação de:

-   **Tailwind CSS:** Para estilização rápida e moderna.
-   **Flowbite & FullCalendar.js:** Para componentes de UI interativos, como modais, datepickers e calendários.
-   **JavaScript:** Para interatividade no lado do cliente.

!!! info "Gerenciamento de Estáticos"
    Os arquivos estáticos (`.css`, `.js`, `.img`) são gerenciados pelo `whitenoise` em produção para garantir alta performance e cacheamento eficiente.

---

## Banco de Dados e Configurações

### 🗄️ Banco de Dados

O sistema é configurado para usar dois bancos de dados, dependendo do ambiente:

-   **Desenvolvimento:** **SQLite3**, para simplicidade e rapidez na configuração local.
-   **Produção:** **PostgreSQL**, para robustez, escalabilidade e segurança dos dados.

### ⚙️ Configurações (Settings)

A configuração do Django é modularizada na pasta `backend/settings/` para separar as preocupações de cada ambiente:

-   `base.py`: Contém todas as configurações comuns a ambos os ambientes.
-   `dev.py`: Configurações específicas para o ambiente de desenvolvimento (ex: `DEBUG=True`, banco de dados SQLite).
-   `prod.py`: Configurações para o ambiente de produção (ex: `DEBUG=False`, configurações de segurança).

As variáveis de ambiente são gerenciadas pela biblioteca `python-decouple`, que as lê a partir de um arquivo `.env`, garantindo que segredos e configurações sensíveis não sejam expostos no código-fonte.