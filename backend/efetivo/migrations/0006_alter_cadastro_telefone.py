# Generated by Django 5.2 on 2025-04-14 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('efetivo', '0005_alter_detalhessituacao_usuario_alteracao'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cadastro',
            name='telefone',
            field=models.CharField(max_length=15),
        ),
    ]
