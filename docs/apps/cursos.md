# App: Cursos

O app `cursos`, apesar do nome, possui uma responsabilidade dupla: ele é o módulo responsável por gerenciar tanto as **qualificações (cursos)** quanto as **condecorações (medalhas)** dos militares.

Ele funciona como um registro central do desenvolvimento profissional e dos méritos de cada indivíduo no sistema.

---

## Modelo de Dados

O app utiliza dois modelos principais, um para cada tipo de registro.

-   **`Curso`**: Armazena os detalhes de um curso concluído por um militar, incluindo o nome do curso, a data e o boletim de publicação.
-   **`Medalha`**: Armazena os detalhes de uma medalha ou honraria recebida por um militar. O campo `honraria` é um `CharField` com uma lista de `choices` pré-definidas extremamente extensa, cobrindo centenas de condecorações militares e civis.

!!! abstract "Modelo `cursos.models.Curso`"
    ::: backend.cursos.models.Curso
        options:
          show_root_heading: false
          show_source: false

!!! abstract "Modelo `cursos.models.Medalha`"
    ::: backend.cursos.models.Medalha
        options:
          show_root_heading: false
          show_source: false

---

## Funcionalidades Principais

### Gerenciamento de Qualificações
O app oferece um CRUD (Create, Read, Update, Delete) completo tanto para Cursos quanto para Medalhas. Uma característica notável é a **criação em lote**, onde a interface permite ao usuário adicionar múltiplos cursos ou medalhas para um mesmo militar em uma única operação.

### Interface Dupla: Admin e Usuário
As funcionalidades são espelhadas em duas interfaces distintas:
-   **Visão do Administrador**: Views como `curso_list` e `medalha_list` permitem que gestores com as devidas permissões gerenciem os registros de todos os militares.
-   **Visão do Usuário ("Meus...")**: Views como `user_curso_list` e `user_medalha_list` permitem que o próprio usuário logado visualize, adicione e gerencie seus próprios cursos e medalhas, promovendo a autonomia e a manutenção dos dados.

### Importação e Exportação (`django-import-export`)
O app integra-se com a biblioteca `django-import-export` através dos arquivos `resources.py` (`CursoResource`, `MedalhaResource`). Isso adiciona, diretamente na interface de **administração do Django**, funcionalidades poderosas para:
-   **Exportar** todos os dados de cursos ou medalhas para formatos como CSV, XLSX, etc.
-   **Importar** dados em massa a partir de uma planilha, facilitando a carga inicial de dados ou atualizações em lote.

---

## Endpoints (URLs) Principais

O app possui um conjunto de URLs para cada entidade (Cursos e Medalhas) e para cada tipo de interface (Admin e Usuário).

| URL | View | Interface | Descrição |
| --- | --- | --- | --- |
| `/cursos/` | `curso_list` | Admin | Lista os cursos de todos os militares. |
| `/cursos/cadastrar/` | `curso_create` | Admin | Formulário para cadastrar cursos para um militar. |
| `/medalhas/` | `medalha_list` | Admin | Lista as medalhas de todos os militares. |
| `/medalhas/cadastrar/` | `medalha_create` | Admin | Formulário para cadastrar medalhas para um militar. |
| `/meus-cursos/` | `user_curso_list` | Usuário | Lista os cursos do usuário logado. |
| `/meus-cursos/novo/` | `user_curso_create` | Usuário | Permite ao usuário logado adicionar um novo curso a seu perfil. |
| `/meus-medalhas/` | `user_medalha_list` | Usuário | Lista as medalhas do usuário logado. |
| `/meus-medalhas/novo/` | `user_medalha_create` | Usuário | Permite ao usuário logado adicionar uma nova medalha a seu perfil. |