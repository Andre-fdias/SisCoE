from django.core.management.base import BaseCommand
from backend.efetivo.models import CatEfetivo
from datetime import date


class Command(BaseCommand):
    help = "Verifica e atualiza categorias de efetivo com data de término expirada"

    def handle(self, *args, **options):
        hoje = date.today()
        categorias = CatEfetivo.objects.filter(
            data_termino__lt=hoje,
            tipo__in=[
                "LSV",
                "LTS",
                "LTS FAMILIA",
                "CONVAL",
                "ELEIÇÃO",
                "LP",
                "FERIAS",
                "RESTRICAO",
            ],
        )

        atualizadas = 0
        for categoria in categorias:
            # Criar histórico antes de alterar
            HistoricoCatEfetivo.objects.create(
                cat_efetivo=categoria,
                tipo=categoria.tipo,
                data_inicio=categoria.data_inicio,
                data_termino=categoria.data_termino,
                observacao=f"Alteração automática para ATIVO - Data de término expirada em {hoje}",
                usuario_alteracao=None,  # Ou um usuário sistema
            )

            # Atualizar categoria para ATIVO
            categoria.tipo = "ATIVO"
            categoria.data_termino = None
            categoria.save()
            atualizadas += 1

        self.stdout.write(
            self.style.SUCCESS(f"Atualizadas {atualizadas} categorias expiradas")
        )
