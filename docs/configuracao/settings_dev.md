# Configurações de Desenvolvimento (`dev.py`)

O arquivo `backend/settings/dev.py` contém as configurações específicas para o **ambiente de desenvolvimento local**. Ele herda todas as configurações de `base.py` (`from .base import *`) e as ajusta para facilitar a depuração e o desenvolvimento ágil.

!!! info "Como Ativar"
    Para usar estas configurações, a variável de ambiente `DJANGO_SETTINGS_MODULE` deve ser definida como `backend.settings.dev`.

---

## Configurações Específicas

### `DEBUG`

Definido como `True` para ativar o modo de debug do Django. Isso habilita páginas de erro detalhadas e o recarregamento automático do servidor quando há alterações no código.

```python
DEBUG = True
```

!!! warning "Segurança"
    O modo `DEBUG` **nunca** deve ser ativado em um ambiente de produção, pois ele expõe informações sensíveis sobre a aplicação.

### `ALLOWED_HOSTS`

Permite que o servidor de desenvolvimento seja acessado localmente através de `localhost` e `127.0.0.1`.

```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
```

### `DATABASES`

Sobrescreve a configuração do banco de dados para usar o **SQLite3**. Este banco de dados é baseado em um único arquivo (`db.sqlite3`) e não requer um servidor separado, o que o torna ideal para o desenvolvimento local.

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### `EMAIL_BACKEND`

Configura o backend de e-mail para `console.EmailBackend`. Com isso, qualquer e-mail enviado pela aplicação (ex: redefinição de senha) não será de fato enviado, mas sim **impresso no console** onde o servidor está rodando.

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### `CACHES`

Para o ambiente de desenvolvimento, um cache em memória (`LocMemCache`) é utilizado. É rápido, eficiente para testes e não possui dependências externas.

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

### Segurança Relaxada

As diretivas de segurança de cookies são desativadas para permitir o funcionamento do site em HTTP local, sem a necessidade de configurar HTTPS no ambiente de desenvolvimento.

```python
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
```