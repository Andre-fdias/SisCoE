#!/bin/bash
# scripts/create_chat_app.sh

# Este script serve como uma referência dos comandos executados para criar e configurar o app de chat.
# Execute este script a partir da raiz do projeto.

# 1. Criar o app Django
# python manage.py startapp chat backend/chat

# 2. Adicionar dependências (exemplo, as versões podem variar)
# echo "djangorestframework==3.15.1" >> requirements.txt
# echo "channels==4.0.0" >> requirements.txt
# echo "channels_redis==4.2.0" >> requirements.txt
# echo "daphne==4.1.2" >> requirements.txt
# echo "drf-nested-routers==0.93.4" >> requirements.txt

# 3. Instalar dependências
# pip install -r requirements.txt

# 4. Criar migrações após definir os modelos
# python manage.py makemigrations chat

# 5. Aplicar migrações ao banco de dados
# python manage.py migrate

# 6. Coletar arquivos estáticos (para produção)
# python manage.py collectstatic --noinput

# 7. Iniciar o servidor de desenvolvimento ASGI
# daphne -p 8000 backend.asgi:application

echo "Script de referência criado. Os comandos estão comentados para evitar execução acidental."
echo "Consulte a documentação e os arquivos de código para entender a implementação completa."
