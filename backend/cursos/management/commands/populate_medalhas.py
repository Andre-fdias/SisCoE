# management/commands/populate_medalhas.py
from django.core.management.base import BaseCommand
from sua_app.models import Medalha, TipoMedalha

class Command(BaseCommand):
    help = 'Popula o banco de dados com as medalhas do documento'
    
    def handle(self, *args, **kwargs):
        medalha_data = Medalha.get_medalha_data()
        
        for honraria, data in medalha_data.items():
            tipo = TipoMedalha.objects.get(tipo=data['tipo'])
            
            Medalha.objects.update_or_create(
                honraria=honraria,
                defaults={
                    'entidade_concedente': data['entidade_concedente'],
                    'ordem': data['ordem'],
                    'tipo': tipo
                }
            )