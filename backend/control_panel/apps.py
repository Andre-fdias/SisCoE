# /home/andre/Repositorio/SisCoE/backend/control_panel/apps.py
from django.apps import AppConfig

class ControlPanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.control_panel'  # ← CORRIGIDO: nome completo
    verbose_name = 'Painel de Controle'