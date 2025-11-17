from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from backend.chat.views import ChatView

urlpatterns = [
    path("admin/", admin.site.urls),  # noqa E501
    path(
        "control-panel/",
        include("backend.control_panel.urls", namespace="control_panel"),
    ),
    # path('', RedirectView.as_view(url='/control-panel/', permanent=False)),
    path("chat/", ChatView.as_view(), name="chat-page"),  # Página do Chat
    path("api/chat/", include("backend.chat.urls")),  # API do Chat
    path("crm/", include("backend.crm.urls", namespace="crm")),  # noqa E501
    path("tickets/", include("backend.tickets.urls", namespace="tickets")),  # noqa E501
    path("efetivo/", include("backend.efetivo.urls", namespace="efetivo")),  # noqa E501
    path(
        "adicional/", include("backend.adicional.urls", namespace="adicional")
    ),  # noqa E501
    path("accounts/", include("backend.accounts.urls")),  # noqa E501
    path("lp/", include("backend.lp.urls", namespace="lp")),  # noqa E501
    path("rpt/", include("backend.rpt.urls", namespace="rpt")),  # noqa E501
    path("bm/", include("backend.bm.urls", namespace="bm")),  # noqa E501
    path(
        "municipios/", include("backend.municipios.urls", namespace="municipios")
    ),  # noqa E501
    path(
        "documentos/", include("backend.documentos.urls", namespace="documentos")
    ),  # noqa E501
    path("cursos/", include("backend.cursos.urls", namespace="cursos")),  # noqa E501
    path("agenda/", include("backend.agenda.urls", namespace="agenda")),  # noqa E501
    path(
        "calculadora/", include("backend.calculadora.urls", namespace="calculadora")
    ),  # noqa E501
    path("prometheus/", include("django_prometheus.urls")),
    path("", include("backend.core.urls", namespace="core")),  # noqa E501
]

# Servir arquivos estáticos e media em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Handlers para páginas de erro personalizadas
handler400 = "backend.control_panel.views.handler400"
handler403 = "backend.control_panel.views.handler403"
handler404 = "backend.control_panel.views.handler404"
handler500 = "backend.control_panel.views.handler500"
