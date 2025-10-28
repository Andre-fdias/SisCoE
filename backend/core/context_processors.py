from django.conf import settings
import os

def version_context_processor(request):
    """
    Context processor para adicionar a versão da aplicação ao contexto do template.
    Lê a versão do arquivo VERSION na raiz do projeto.
    """
    version = "N/A"
    try:
        version_file_path = os.path.join(settings.BASE_DIR, 'VERSION')
        with open(version_file_path, 'r') as f:
            version = f.read().strip()
    except FileNotFoundError:
        pass  # Mantém "N/A" se o arquivo não for encontrado
    return {'APP_VERSION': version}