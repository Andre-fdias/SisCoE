FROM python:3.11-slim-bookworm

# Configuração do locale
RUN apt-get update && apt-get install -y locales && \
    sed -i '/pt_BR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG pt_BR.UTF-8
ENV LC_ALL pt_BR.UTF-8

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV DOCKER_CONTAINER 1

RUN mkdir /app
WORKDIR /app
EXPOSE 8000

# Instala dependências do sistema para PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Cria a pasta de logs
RUN mkdir -p /app/logs

COPY requirements.txt .
RUN pip install -U pip && pip install -r requirements.txt

COPY manage.py .
COPY backend backend

# Comando único (tudo no runtime)
CMD bash -c "python manage.py collectstatic --noinput && python manage.py migrate && python manage.py create_superuser && gunicorn backend.wsgi:application -b 0.0.0.0:8000"