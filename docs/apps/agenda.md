# App: Agenda

O app `agenda` é um módulo de produtividade pessoal integrado ao SisCoE. Ele fornece a cada usuário uma agenda privada para criar e gerenciar seus próprios lembretes e tarefas, ajudando na organização de compromissos e atividades.

---

## Modelo de Dados

A `agenda` utiliza dois modelos simples para representar os diferentes tipos de compromissos de um usuário. Cada registro é estritamente vinculado ao usuário que o criou.

-   **`Lembrete`**: Usado para eventos pontuais, que ocorrem em uma data e hora específicas.
-   **`Tarefa`**: Usado para atividades que têm uma duração, com data de início e data de término.

!!! abstract "Modelo `agenda.models.Lembrete`"
    ::: backend.agenda.models.Lembrete
        options:
          show_root_heading: false
          show_source: false

!!! abstract "Modelo `agenda.models.Tarefa`"
    ::: backend.agenda.models.Tarefa
        options:
          show_root_heading: false
          show_source: false

---

## Funcionalidades Principais

### Visualização em Calendário
A view principal do app, `calendario`, renderiza uma interface de calendário (provavelmente usando uma biblioteca JavaScript como FullCalendar) onde o usuário pode visualizar todos os seus lembretes e tarefas de forma gráfica e interativa.

### Gerenciamento de Eventos via AJAX
Para proporcionar uma experiência de usuário mais fluida e moderna, as operações mais comuns são realizadas de forma assíncrona, sem a necessidade de recarregar a página:
-   **Criação**: As views `lembrete_novo` e `tarefa_nova` recebem os dados do formulário via `POST` e retornam um `JsonResponse` indicando sucesso ou falha.
-   **Exclusão**: As views `excluir_lembrete` e `excluir_tarefa` também são acessadas via `POST` e retornam um `JsonResponse`, permitindo que o evento seja removido da interface do calendário dinamicamente.

### Notificações de Próximos Eventos
A view `eventos_proximos` fornece um endpoint que retorna um JSON com todos os lembretes e tarefas do usuário que ocorrerão nas próximas 48 horas. Essa funcionalidade é projetada para ser consumida por um script no frontend que pode exibir alertas ou notificações de "próximos eventos" para o usuário.

---

## Endpoints (URLs) Principais

| URL | View | Método | Descrição |
| --- | --- | --- | --- |
| `/calendario/` | `calendario` | GET | Renderiza a página principal da agenda com o calendário. |
| `/lembrete/novo/` | `lembrete_novo` | POST | (AJAX) Cria um novo lembrete. |
| `/tarefa/nova/` | `tarefa_nova` | POST | (AJAX) Cria uma nova tarefa. |
| `/lembrete/editar/<int:pk>/` | `lembrete_editar` | GET/POST | Página para editar um lembrete existente. |
| `/tarefa/editar/<int:pk>/` | `tarefa_editar` | GET/POST | Página para editar uma tarefa existente. |
| `/lembrete/excluir/<int:pk>/` | `excluir_lembrete` | POST | (AJAX) Exclui um lembrete. |
| `/tarefa/excluir/<int:pk>/` | `excluir_tarefa` | POST | (AJAX) Exclui uma tarefa. |
| `/eventos-proximos/` | `eventos_proximos` | GET | Retorna um JSON com os eventos das próximas 48 horas. |
