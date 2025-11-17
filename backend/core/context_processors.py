from django.conf import settings


def version_context_processor(request):
    """
    Context processor para adicionar a versão da aplicação ao contexto do template.
    Lê a versão a partir de settings.VERSION.
    """
    return {"APP_VERSION": getattr(settings, "VERSION", "N/A")}
