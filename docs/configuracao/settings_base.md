# Configurações Base (`base.py`)

O arquivo `backend/settings/base.py` é o pilar da configuração do Django no SisCoE. Ele contém todas as configurações que são **comuns a todos os ambientes** (desenvolvimento e produção).

Os arquivos `dev.py` e `prod.py` importam todas as configurações de `base.py` (`from .base import *`) e, em seguida, sobrescrevem ou adicionam apenas o que for específico para cada ambiente.

---

## Variáveis de Ambiente

Este arquivo utiliza a biblioteca `python-decouple` para carregar configurações sensíveis ou que variam entre ambientes. As seguintes variáveis são lidas do arquivo `.env` ou do ambiente do sistema:

!!! tip "Arquivo `.env_example`"
    O arquivo `.env_example` na raiz do projeto serve como um template para todas as variáveis de ambiente necessárias.

-   **`SECRET_KEY`**: A chave secreta do Django, essencial para a segurança criptográfica do projeto.
-   **`DEFAULT_FROM_EMAIL`**: O endereço de e-mail padrão usado para enviar e-mails do sistema.
-   **`GROQ_API_KEY`**: Chave de API para o serviço Groq (provavelmente usado para alguma funcionalidade de IA).
-   **`WEATHER_API_KEY`**: Chave de API para um serviço de previsão do tempo.

!!! warning "Atenção"
    Nunca coloque informações sensíveis (como senhas ou chaves de API) diretamente neste arquivo. Use sempre o `decouple` para carregá-las a partir de variáveis de ambiente.

---

## Configurações Principais

### `INSTALLED_APPS`
Lista todas as aplicações que compõem o projeto, incluindo as apps do próprio Django, apps de terceiros e as apps internas do SisCoE.

```python
INSTALLED_APPS = [
    # Django Apps
    'django.contrib.admin',
    # ...

    # Apps de Terceiros
    'import_export',      # Para importação/exportação de dados no admin
    'widget_tweaks',      # Facilita a renderização de formulários
    'compressor',         # Comprime arquivos estáticos (CSS, JS)
    # ...

    # Apps do SisCoE
    'backend.core',
    'backend.accounts',
    # ...
]
```

### `MIDDLEWARE`
Define os middlewares que processam as requisições e respostas globalmente. Além dos middlewares padrão do Django, o SisCoE inclui alguns customizados:

-   **`whitenoise.middleware.WhiteNoiseMiddleware`**: Para servir arquivos estáticos de forma eficiente em produção.
-   **`backend.accounts.middleware.UserActionLoggingMiddleware`**: Registra ações importantes do usuário.
-   **`backend.core.middleware.JSONMessagesMiddleware`**: Permite que mensagens do Django sejam enviadas em respostas JSON (útil para AJAX/HTMX).
-   **`backend.accounts.middleware.ForcePasswordChangeMiddleware`**: Força o usuário a trocar a senha se a flag `must_change_password` estiver ativa.
-   **`backend.accounts.middleware.UpdateLastActivityMiddleware`**: Atualiza a informação de "visto por último" do usuário.

### `AUTH_USER_MODEL`
Define o modelo customizado de usuário (`accounts.User`) para autenticação, permitindo a adição de campos como `permissoes` e `cadastro`.

```python
AUTH_USER_MODEL = 'accounts.User'
```

### Arquivos Estáticos e Mídias
-   **`STATIC_URL`**: `/static/` - URL base para servir arquivos estáticos.
-   **`STATIC_ROOT`**: `BASE_DIR / 'staticfiles'` - Diretório onde o comando `collectstatic` reunirá todos os arquivos estáticos para produção.
-   **`STATICFILES_STORAGE`**: `whitenoise.storage.CompressedManifestStaticFilesStorage` - Configura o `Whitenoise` para gerenciar o armazenamento e versionamento dos arquivos estáticos, otimizando o cache no navegador.
-   **`MEDIA_URL`** e **`MEDIA_ROOT`**: Configurações para o armazenamento de arquivos enviados pelos usuários (fotos de perfil, documentos, etc.).

### Logging
A configuração de `LOGGING` é definida para registrar informações úteis para depuração e monitoramento:
-   **Handlers**: `console` (para exibir logs no terminal) e `file` (para salvar logs em `debug.log`).
-   **Rotação de Arquivos**: O arquivo `debug.log` é rotativo, com um tamanho máximo de 5MB e mantendo até 5 arquivos de backup.