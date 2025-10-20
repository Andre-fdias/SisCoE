# App: BM (Bombeiro Municipal)

O app `bm` é o módulo do SisCoE dedicado ao cadastro e gerenciamento de pessoal dos **Bombeiros Municipais**. Ele funciona como um sistema de registros paralelo ao app `efetivo`, mas focado especificamente nesta categoria de pessoal.

---

## Modelo de Dados

O app possui um modelo de dados simples e direto para armazenar as informações dos bombeiros municipais.

-   **`Cadastro_bm`**: O modelo principal. Armazena os dados pessoais e funcionais de cada bombeiro municipal, como nome, CPF, CNH, datas de admissão e nascimento, e sua lotação (SGB e posto/seção).
-   **`Imagem_bm`**: Um modelo para armazenar a foto de perfil do bombeiro municipal.

!!! abstract "Modelo `bm.models.Cadastro_bm`"
    ::: backend.bm.models.Cadastro_bm
        options:
          show_root_heading: false
          show_source: false

---

## Funcionalidades Principais

### Gerenciamento de Cadastros (CRUD)
O app fornece uma interface completa para o ciclo de vida do cadastro de um bombeiro municipal:
-   **Criar**: A view `cadastrar_bm` permite adicionar novos bombeiros ao sistema.
-   **Listar**: A view `listar_bm` exibe uma lista de todos os bombeiros municipais cadastrados.
-   **Visualizar**: A view `ver_bm` mostra a ficha detalhada de um bombeiro específico.
-   **Editar**: A view `editar_bm` permite a atualização dos dados cadastrais.
-   **Excluir**: A view `excluir_bm` remove o registro de um bombeiro, exigindo confirmação com senha para segurança.

### Importação e Exportação de Dados
Uma funcionalidade poderosa do módulo `bm` é a capacidade de gerenciar dados em massa:
-   **Importação (`importar_bm`)**: Permite que administradores façam o upload de um arquivo CSV ou Excel para cadastrar múltiplos bombeiros de uma só vez. O sistema valida as colunas e os dados antes de importá-los.
-   **Exportação (`exportar_bm`)**: Através do `export_utils.py`, o sistema pode gerar e exportar a relação de efetivo dos bombeiros municipais em múltiplos formatos:
    -   **PDF**: Um relatório formatado e profissional.
    -   **Excel (XLSX)**: Uma planilha para análises e uso externo.
    -   **CSV**: Um formato de texto simples para integração com outros sistemas.

---

## Endpoints (URLs) Principais

| URL | View | Nome da URL | Descrição |
| --- | --- | --- | --- |
| `/` | `listar_bm` | `listar_bm` | Página principal do app, lista todos os bombeiros municipais. |
| `/cadastrar/` | `cadastrar_bm` | `cadastrar_bm` | Exibe o formulário para criar um novo bombeiro municipal. |
| `/ver/<int:pk>/` | `ver_bm` | `ver_bm` | Mostra a ficha detalhada de um bombeiro. |
| `/editar/<int:pk>/` | `editar_bm` | `editar_bm` | Permite a edição dos dados de um bombeiro. |
| `/excluir/<int:pk>/` | `excluir_bm` | `excluir_bm` | Processa a exclusão de um bombeiro. |
| `/importar/` | `importar_bm` | `importar_bm` | Página para upload de arquivos para importação em massa. |
| `/exportar/` | `exportar_bm` | `exportar_bm` | Endpoint para baixar os dados em diferentes formatos. |