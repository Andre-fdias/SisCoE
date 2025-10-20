# SisCoE - Sistema de Controle de Efetivo

## Descrição do Projeto

O SisCoE é um sistema de gestão completo, desenvolvido para [adicionar aqui o propósito principal, ex: otimizar a administração de uma instituição, gerenciar recursos de bombeiros, etc.]. Ele oferece uma plataforma robusta para o controle de diversas áreas, incluindo gestão de pessoal, relacionamento com o cliente (CRM), agendamento, cursos e documentação.

**Tecnologias Utilizadas:**

*   **Backend:** Python, Django
*   **Frontend:** JavaScript, Tailwind CSS, FullCalendar.js, Flowbite
*   **Banco de Dados:** PostgreSQL (para produção) e SQLite3 (para desenvolvimento)
*   **Outras Ferramentas:** Node.js, npm, Brevo (para e-mails), Gunicorn, Whitenoise

**Público-Alvo:**

Este projeto é destinado a [adicionar público-alvo, ex: administradores de sistemas, gestores de RH, etc.] que necessitam de uma ferramenta centralizada para gerenciar as operações do dia a dia.

---

## Instalação

Siga os passos abaixo para configurar o ambiente de desenvolvimento local.

**Pré-requisitos:**

*   Python 3.10+ (com `pip` e `venv`)
*   Node.js e npm
*   Git

**Passo a Passo:**

1.  **Clone o Repositório:**

    ```bash
    git clone [URL do seu repositório]
    cd SisCoE
    ```

2.  **Crie e Ative um Ambiente Virtual (venv):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  **Instale as Dependências do Python:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Instale as Dependências do Node.js:**

    ```bash
    npm install
    ```

5.  **Configure as Variáveis de Ambiente:**

    Copie o arquivo de exemplo `.envexample` e renomeie-o para `.env`. Em seguida, preencha as variáveis com suas credenciais.

    ```bash
    cp .envexample .env
    ```

    Abra o arquivo `.env` e preencha as chaves de API e outras configurações necessárias.

6.  **Aplique as Migrações do Banco de Dados:**

    Como o ambiente de desenvolvimento usa SQLite, este comando criará o arquivo `db.sqlite3` e o schema do banco.

    ```bash
    python manage.py migrate
    ```

---

## Uso

Para iniciar o servidor de desenvolvimento local, execute o seguinte comando:

```bash
python manage.py runserver
```

O sistema estará acessível em `http://127.0.0.1:8000`.

---

## Funcionalidades

*   **Gestão de Contas:** Controle de usuários, permissões e autenticação.
*   **CRM:** Módulo para gerenciamento de relacionamento com clientes.
*   **Controle de Efetivo:** Ferramentas para administrar o pessoal.
*   **Agenda:** Sistema de calendário para agendamento de eventos e tarefas.
*   **Cursos:** Gerenciamento de cursos e matrículas.
*   **Documentos:** Repositório para upload e gestão de documentos.
*   **Relatórios:** Geração de relatórios (módulo RPT).
*   **Calculadora:** Ferramenta de cálculo integrada.
*   E muito mais.

---

## Testes

Para executar a suíte de testes automatizados do projeto, utilize o comando:

```bash
python manage.py test
```

---

## Contribuição

Contribuições são bem-vindas! Se você deseja ajudar no desenvolvimento do SisCoE, siga estes passos:

1.  **Faça um Fork** do projeto.
2.  **Crie uma Branch** para sua nova funcionalidade (`git checkout -b feature/nova-feature`).
3.  **Faça o Commit** de suas alterações (`git commit -m 'Adiciona nova feature'`).
4.  **Faça o Push** para a sua branch (`git push origin feature/nova-feature`).
5.  **Abra um Pull Request**.

Por favor, mantenha um estilo de código consistente e adicione testes para novas funcionalidades.

---

## Licença

Este projeto está licenciado sob a licença [Nome da Licença]. Veja o arquivo `LICENSE` para mais detalhes. (Adicionar arquivo LICENSE se necessário).

---

## Contato

**André Fonseca Dias**

*   **E-mail:** andrefonsecadias21@gmail.com
*   **GitHub:** [Andre-fdias](https://github.com/Andre-fdias)

---

## Extras

*   **Documentação Adicional:** [Link para a documentação, se houver]
*   **Deploy:** [Link para o ambiente de produção, se houver]