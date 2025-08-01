# Generated by Django 5.2.4 on 2025-07-31 18:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Documento',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('data_publicacao', models.DateField()),
                ('data_documento', models.DateField()),
                ('numero_documento', models.CharField(max_length=100)),
                ('assunto', models.CharField(max_length=200)),
                ('descricao', models.TextField()),
                ('assinada_por', models.CharField(max_length=100)),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('tipo', models.CharField(choices=[('PDF', 'PDF'), ('VIDEO', 'Vídeo'), ('AUDIO', 'Áudio'), ('DOC', 'Documento'), ('SHEET', 'Planilha'), ('IMAGEM', 'Imagem'), ('TEXT', 'Texto'), ('OUTRO', 'Outro')], default='OUTRO', max_length=10)),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Arquivo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arquivo', models.FileField(upload_to='documentos/')),
                ('tipo', models.CharField(choices=[('PDF', 'PDF'), ('VIDEO', 'Vídeo'), ('AUDIO', 'Áudio'), ('DOC', 'Documento'), ('SHEET', 'Planilha'), ('IMAGEM', 'Imagem'), ('TEXT', 'Texto'), ('OUTRO', 'Outro')], max_length=10)),
                ('documento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='arquivos', to='documentos.documento')),
            ],
        ),
    ]
