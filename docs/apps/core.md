# App: Core

O app `core` é o coração da interface do usuário e da orquestração de dados no SisCoE. Diferente de outros apps, ele não gerencia um domínio de negócio específico com seus próprios models. Em vez disso, sua principal função é agregar dados de múltiplos apps e apresentá-los de forma coesa nas páginas principais do sistema.

!!! info "Arquitetura do App Core"
    Este app funciona como um **agregador e apresentador**. Ele busca informações dos apps `efetivo`, `agenda`, `documentos`, entre outros, e as consolida em dashboards e páginas principais, além de gerenciar funcionalidades transversais como permissões e busca global.

---

## Responsabilidades Principais

-   **Páginas Principais**: Fornece as views e templates para a landing page, a página inicial pós-login e o dashboard de BI.
-   **Controle de Acesso**: Implementa o sistema de papéis e permissões usando a biblioteca `django-role-permissions`.
-   **Agregação de Dados**: Suas views reúnem dados de vários apps para criar uma experiência de usuário unificada.
-   **Funcionalidades Transversais**: Contém a lógica para a busca global e o calendário de eventos.
-   **Utilitários**: Oferece middlewares e template tags customizadas para uso em todo o projeto.

---

## Sistema de Papéis (Roles)

O controle de acesso no SisCoE é gerenciado pelo `django-role-permissions` e configurado em `core/roles.py`. Os seguintes papéis são definidos:

!!! note "Papel: `Basico`"
    **Descrição**: Papel fundamental com permissões de visualização essenciais.
    **Permissões Chave**:
    - Visualizar dashboard e perfil.
    - Gerenciar seus próprios lembretes e tarefas.
    - Visualizar documentos e calcular tempo de serviço.

!!! note "Papel: `SGB`"
    **Herda de**: `Basico`
    **Descrição**: Destinado a usuários que operam no nível de um Subgrupamento de Bombeiros (SGB).
    **Permissões Adicionais**:
    - Visualizar cadastros, promoções e situações do efetivo.
    - Acessar relatórios (`rpt`) e adicionais.

!!! note "Papel: `Gestor`"
    **Herda de**: `SGB`
    **Descrição**: Usuários com capacidade de gerenciar (criar, editar, excluir) os dados do sistema.
    **Permissões Adicionais**:
    - Gerenciamento completo do cadastro de efetivo.
    - Gerenciamento de documentos e relatórios.
    - Visualização de usuários do sistema.

!!! note "Papel: `Visitante`"
    **Descrição**: Papel com acesso muito limitado, geralmente para usuários não autenticados ou com pouquíssimas permissões.
    **Permissões Chave**:
    - Apenas visualizar a página inicial e documentos públicos.

!!! warning "Papel: `Admin`"
    **Descrição**: Papel de superusuário com acesso irrestrito a todas as funcionalidades. Este papel não tem limitações.

---

## Views e Endpoints

As views do app `core` são o ponto de entrada para as principais páginas do sistema.

<div class="tabbed-set" data-tabs="1-3">
<div class="tabbed-content">

<details>
<summary><code>/</code> (Página de Entrada)</summary>
<div markdown>
**View**: `capa(request)`
**Template**: `landing.html`

Renderiza a página de entrada (landing page) para usuários não autenticados.
</div>
</details>

<details>
<summary><code>/home</code> (Página Inicial)</summary>
<div markdown>
**View**: `index(request)`
**Template**: `index.html`

Esta é a página principal que um usuário vê após o login. É uma view complexa que agrega múltiplas informações:
- Aniversariantes do mês.
- Documentos recentes.
- Lembretes e tarefas do usuário.
- Hierarquia de comando (Comandante, Subcomandante, Chefes).
- Imagens para o carrossel da página inicial.
</div>
</details>

<details>
<summary><code>/dashboard/</code></summary>
<div markdown>
**View**: `dashboard_view(request)`
**Template**: `dashboard.html`

Renderiza o dashboard de Business Intelligence (BI), que exibe métricas e gráficos sobre o efetivo:
- Efetivo fixado vs. existente.
- Percentual de "claro" (vagas não preenchidas).
- Distribuição de efetivo por SGB.
- Movimentações recentes.
- Gráficos de distribuição por idade, posto/graduação e saúde.
</div>
</details>

<details>
<summary><code>/calendario/</code></summary>
<div markdown>
**View**: `CalendarioView.as_view()`
**Template**: `calendario.html`

Exibe um calendário completo com eventos do grupamento, feriados nacionais, estaduais e municipais.
</div>
</details>

<details>
<summary><code>/search/</code></summary>
<div markdown>
**View**: `global_search_view(request)`
**Template**: `global_search/results.html`

Processa as requisições da barra de busca global, utilizando a classe `GlobalSearch` para encontrar resultados em múltiplos apps.
</div>
</details>

</div>
</div>

---

## Componentes Adicionais

### Middleware

-   **`JSONMessagesMiddleware`**: Intercepta respostas JSON e injeta nelas quaisquer mensagens pendentes do `django.contrib.messages`. Útil para requisições AJAX/HTMX onde a resposta não é uma página HTML completa.

### Comandos de Gerenciamento

-   **`link_profiles`**: Um comando customizado (`python manage.py link_profiles`) que provavelmente é usado para associar perfis de usuário a outros registros no sistema (possivelmente legados, dado que o model `Profile` foi removido).

### Template Tags

O app `core` fornece várias template tags customizadas em `core/templatetags/`:
- `dict_filters.py`: Filtros para manipulação de dicionários nos templates.
- `messages_extras.py` e `messages_tag.py`: Tags e filtros para aprimorar a exibição de mensagens do Django.