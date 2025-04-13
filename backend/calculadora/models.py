from django.db import models

class CalculoMilitar(models.Model):
    data_admissao = models.DateField(verbose_name="Data de Admissão do Militar")
    tempo_ffaa_pm_cbm = models.IntegerField(verbose_name="Averbação FFAA/PM/CBM (dias)", default=0)
    tempo_inss_outros = models.IntegerField(verbose_name="Averbação INSS/Outros Órgãos (dias)", default=0)
    afastamentos = models.IntegerField(verbose_name="Afastamentos Descontáveis (dias)", default=0)

    def __str__(self):
        return f"Cálculo para {self.data_admissao}"