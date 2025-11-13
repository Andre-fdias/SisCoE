FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema INCLUINDO DOCKER CLI
RUN apt-get update && apt-get install -y \
    locales \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    curl \
    postgresql-client \
    # INSTALAR DOCKER CLI
    docker.io \
    && sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && rm -rf /var/lib/apt/lists/*

# Configurar variáveis de ambiente do locale
ENV LANG=pt_BR.UTF-8
ENV LANGUAGE=pt_BR:pt
ENV LC_ALL=pt_BR.UTF-8

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar projeto
COPY . .

# Criar diretórios para static e media files
RUN mkdir -p /app/staticfiles /app/media

# Expor porta
EXPOSE 8000

# Comando padrão
CMD ["sh", "-c", "python manage.py collectstatic --noinput && daphne -b 0.0.0.0 -p 8000 backend.asgi:application"]