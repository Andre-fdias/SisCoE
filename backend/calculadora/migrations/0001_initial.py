# Generated by Django 5.1.4 on 2025-03-18 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CalculoMilitar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_admissao', models.DateField(verbose_name='Data de Admissão do Militar')),
                ('tempo_ffaa_pm_cbm', models.IntegerField(default=0, verbose_name='Averbação FFAA/PM/CBM (dias)')),
                ('tempo_inss_outros', models.IntegerField(default=0, verbose_name='Averbação INSS/Outros Órgãos (dias)')),
                ('afastamentos', models.IntegerField(default=0, verbose_name='Afastamentos Descontáveis (dias)')),
            ],
        ),
    ]
