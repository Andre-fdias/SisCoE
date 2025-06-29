# Generated by Django 5.2 on 2025-06-16 23:22

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lp', '0002_remove_historicolp_data_inicio_periodo_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='lp',
            options={'ordering': ['-data_cadastro'], 'verbose_name': 'Licença Prêmio', 'verbose_name_plural': 'Licenças Prêmio'},
        ),
        migrations.AlterUniqueTogether(
            name='lp',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='lp',
            name='data_conclusao',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Data de Conclusão'),
        ),
        migrations.AlterField(
            model_name='historicolp',
            name='data_alteracao',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Data da Alteração'),
        ),
        migrations.AlterField(
            model_name='historicolp',
            name='lp',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lp.lp', verbose_name='Licença Prêmio'),
        ),
        migrations.AlterField(
            model_name='historicolp',
            name='situacao_lp',
            field=models.CharField(choices=[('Aguardando', 'Aguardando'), ('Concedido', 'Concedido'), ('Concluído', 'Concluído')], max_length=30, verbose_name='Situação da LP'),
        ),
        migrations.AlterField(
            model_name='historicolp',
            name='status_lp',
            field=models.CharField(choices=[('aguardando_requisitos', 'Aguardando Requisitos'), ('apta_concessao', 'Apta para Concessão'), ('concedido', 'Concedido'), ('lancado_sipa', 'Lançado no SIPA'), ('publicado', 'Publicado'), ('concluido', 'Concluído'), ('indenizada', 'Indenizada')], max_length=30, verbose_name='Status da LP'),
        ),
        migrations.AlterField(
            model_name='historicolp',
            name='usuario_alteracao',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Usuário da Alteração'),
        ),
        migrations.AlterField(
            model_name='lp',
            name='data_atualizacao',
            field=models.DateTimeField(auto_now=True, verbose_name='Última Atualização'),
        ),
        migrations.AlterField(
            model_name='lp',
            name='data_cadastro',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Data de Cadastro'),
        ),
        migrations.AlterField(
            model_name='lp',
            name='status_lp',
            field=models.CharField(choices=[('aguardando_requisitos', 'Aguardando Requisitos'), ('apta_concessao', 'Apta para Concessão'), ('concedido', 'Concedido'), ('lancado_sipa', 'Lançado no SIPA'), ('publicado', 'Publicado'), ('concluido', 'Concluído'), ('indenizada', 'Indenizada')], default='aguardando_requisitos', max_length=30, verbose_name='Status da LP'),
        ),
    ]
