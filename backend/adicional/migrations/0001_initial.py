# Generated by Django 5.1.4 on 2025-03-04 18:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('efetivo', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cadastro_adicional',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_adicional', models.IntegerField(choices=[(1, '01'), (2, '02'), (3, '03'), (4, '04'), (5, '05'), (6, '06'), (7, '07'), (8, '08')])),
                ('data_ultimo_adicional', models.DateField()),
                ('numero_lp', models.IntegerField(choices=[(1, '01'), (2, '02'), (3, '03'), (4, '04'), (5, '05'), (6, '06'), (7, '07'), (8, '08')])),
                ('data_ultimo_lp', models.DateField()),
                ('numero_prox_adicional', models.IntegerField(choices=[(1, '01'), (2, '02'), (3, '03'), (4, '04'), (5, '05'), (6, '06'), (7, '07'), (8, '08')], default=1)),
                ('proximo_adicional', models.DateField(blank=True, null=True)),
                ('mes_proximo_adicional', models.IntegerField(blank=True, null=True)),
                ('ano_proximo_adicional', models.IntegerField(blank=True, null=True)),
                ('dias_desconto_adicional', models.IntegerField(blank=True, default=0, null=True)),
                ('situacao_adicional', models.CharField(choices=[('', ' '), ('Aguardando', 'Aguardando'), ('Concedido', 'Concedido')], default='Aguardando')),
                ('numero_prox_lp', models.IntegerField(choices=[(1, '01'), (2, '02'), (3, '03'), (4, '04'), (5, '05'), (6, '06'), (7, '07'), (8, '08')], default=1)),
                ('proximo_lp', models.DateField(blank=True, null=True)),
                ('mes_proximo_lp', models.IntegerField(blank=True, null=True)),
                ('ano_proximo_lp', models.IntegerField(blank=True, null=True)),
                ('dias_desconto_lp', models.IntegerField(blank=True, default=0, null=True)),
                ('situacao_lp', models.CharField(choices=[('', ' '), ('Aguardando', 'Aguardando'), ('Concedido', 'Concedido')], default='Aguardando')),
                ('cadastro', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='efetivo.cadastro')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='HistoricoCadastro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_alteracao', models.DateTimeField(auto_now_add=True)),
                ('situacao_adicional', models.CharField(max_length=20)),
                ('situacao_lp', models.CharField(max_length=20)),
                ('numero_prox_adicional', models.IntegerField()),
                ('proximo_adicional', models.DateField()),
                ('mes_proximo_adicional', models.IntegerField()),
                ('ano_proximo_adicional', models.IntegerField()),
                ('dias_desconto_adicional', models.IntegerField()),
                ('numero_prox_lp', models.IntegerField()),
                ('proximo_lp', models.DateField()),
                ('mes_proximo_lp', models.IntegerField()),
                ('ano_proximo_lp', models.IntegerField()),
                ('dias_desconto_lp', models.IntegerField()),
                ('Cadastro_adicional', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adicional.cadastro_adicional')),
                ('usuario_alteracao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
