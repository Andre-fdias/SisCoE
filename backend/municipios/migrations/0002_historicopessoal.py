# Generated by Django 5.1.4 on 2025-04-02 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('municipios', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricoPessoal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_referencia', models.DateField()),
                ('total_cel', models.IntegerField()),
                ('total_ten_cel', models.IntegerField()),
                ('total_maj', models.IntegerField()),
                ('total_cap', models.IntegerField()),
                ('total_tenqo', models.IntegerField()),
                ('total_tenqa', models.IntegerField()),
                ('total_asp', models.IntegerField()),
                ('total_st_sgt', models.IntegerField()),
                ('total_cb_sd', models.IntegerField()),
                ('total_geral', models.IntegerField()),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
