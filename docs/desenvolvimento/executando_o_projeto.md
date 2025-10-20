# Executando o Projeto

Este guia fornece as instruções para configurar e executar o projeto SisCoE em um ambiente de desenvolvimento local, bem como para visualizar e publicar a documentação.

---

## Pré-requisitos

Antes de começar, garanta que você tenha os seguintes softwares instalados em sua máquina:
-   **Python** (versão 3.10 ou superior)
-   **Node.js** e **npm** (para as dependências de frontend e Tailwind CSS)
-   **Git** (para controle de versão)
-   **Docker** e **Docker Compose** (opcional, para executar o ambiente de produção)

---

## 1. Configuração do Ambiente Local

### Clone o Repositório
Primeiro, clone o repositório do projeto para a sua máquina local:
```bash
git clone https://github.com/Andre-fdias/SisCoE.git
cd SisCoE
```

### Crie e Ative um Ambiente Virtual
É uma boa prática usar um ambiente virtual para isolar as dependências do projeto.
```bash
# Criar o ambiente virtual
python -m venv venv

# Ativar no Linux/macOS
source venv/bin/activate

# Ativar no Windows
.\venv\Scripts\activate
```

### Instale as Dependências
O projeto possui dependências Python e Node.js.

1.  **Dependências Python:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Dependências Node.js:**
    ```bash
    npm install
    ```

### Configure as Variáveis de Ambiente
1.  Copie o arquivo de exemplo `.env_example` para um novo arquivo chamado `.env`:
    ```bash
    cp .env_example .env
    ```
2.  Abra o arquivo `.env` em um editor de texto e preencha as variáveis necessárias, como a `SECRET_KEY`. Para desenvolvimento, uma chave simples gerada aleatoriamente é suficiente.

---

## 2. Executando a Aplicação (Desenvolvimento)

### Aplique as Migrações do Banco de Dados
Este comando cria o arquivo de banco de dados SQLite e aplica o schema necessário.
```bash
python manage.py migrate
```

### Crie um Superusuário
Você precisará de um usuário administrador para acessar a interface de administração do Django.
```bash
python manage.py createsuperuser
```
Siga as instruções no terminal para definir o e-mail e a senha.

### Compile o Tailwind CSS
Para que os estilos sejam aplicados corretamente, execute o comando de compilação do Tailwind CSS.
```bash
npm run build
```

### Inicie o Servidor de Desenvolvimento
Agora, você pode iniciar o servidor do Django.
```bash
python manage.py runserver
```
A aplicação estará disponível em `http://127.0.0.1:8000/`.

---

## 3. Trabalhando com a Documentação

### Visualizando Localmente
Para visualizar esta documentação em sua máquina local, com recarregamento automático ao salvar alterações:
1.  Certifique-se de que as dependências em `requirements.txt` estão instaladas (o que inclui `mkdocs` e `mkdocs-material`).
2.  Execute o comando:
    ```bash
    mkdocs serve
    ```
3.  A documentação estará disponível em `http://127.0.0.1:8001/`.

### Publicando no GitHub Pages
Para publicar a documentação no GitHub Pages, use o seguinte comando:
```bash
mkdocs gh-deploy
```
Este comando irá construir o site estático e fazer o push para a branch `gh-pages` do seu repositório, tornando-o disponível online.

---

## 4. Executando em Produção (com Docker)

O projeto inclui um `Dockerfile` e um `docker-compose.yml` para facilitar a execução em um ambiente de produção containerizado.

1.  **Configure o `.env`**: Certifique-se de que seu arquivo `.env` está preenchido com as configurações de produção (banco de dados PostgreSQL, `DEBUG=False`, `ALLOWED_HOSTS`, etc.).
2.  **Construa e Inicie os Contêineres**:
    ```bash
    docker-compose up --build -d
    ```
    -   `--build`: Força a reconstrução das imagens.
    -   `-d`: Executa os contêineres em modo "detached" (em segundo plano).

3.  **Execute as Migrações (no contêiner)**:
    ```bash
    docker-compose exec web python manage.py migrate
    ```

A aplicação estará disponível no endereço e porta que você configurou em seu ambiente de produção.