# Dockerfile - VERSÃO MELHORADA
FROM python:3.11-slim

# Evita que o Python escreve arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE 1
# Garante que a saída do python seja logada
ENV PYTHONUNBUFFERED 1

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    postgresql-dev \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório da aplicação
WORKDIR /app

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o projeto
COPY . .

# Cria usuário não-root para segurança
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Comando para rodar a aplicação
CMD ["gunicorn", "SISCOE.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
