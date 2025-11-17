# Dockerfile - VERSÃO CORRIGIDA
FROM python:3.11-slim

# Evita que o Python escreve arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE 1
# Garante que a saída do python seja logada
ENV PYTHONUNBUFFERED 1

# Argumento para o GID do Docker
ARG DOCKER_GID

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
    locales \
    && echo "pt_BR.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen pt_BR.UTF-8 \
    && /usr/sbin/update-locale LANG=pt_BR.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# Define as variáveis de ambiente para o locale
ENV LANG pt_BR.UTF-8
ENV LANGUAGE pt_BR.UTF-8
ENV LC_ALL pt_BR.UTF-8

# Cria diretório da aplicação
WORKDIR /app

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o projeto
COPY . .

# Cria grupo docker com o GID passado e usuário não-root para segurança - CORRIGIDO
RUN if [ -n "$DOCKER_GID" ]; then \
        groupadd -g $DOCKER_GID docker && \
        useradd -m -u 1000 -g docker appuser && \
        chown -R appuser:docker /app; \
    else \
        useradd -m -u 1000 appuser && \
        chown -R appuser:appuser /app; \
    fi

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Comando para rodar a aplicação
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]