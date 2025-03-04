# Generated by Django 5.1.4 on 2025-03-04 18:03

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Posto',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('sgb', models.CharField(choices=[('', ' '), ('EM', ' EM'), ('1ºSGB', '1ºSGB'), ('2ºSGB', '2ºSGB'), ('3ºSGB', '3ºSGB'), ('4ºSGB', '4ºSGB'), ('5ºSGB', '5ºSGB')], max_length=30)),
                ('posto_secao', models.CharField(choices=[('', ' '), ('703150000 - CMT', 'CMT'), ('703159000 - SUB CMT', 'SUB CMT'), ('703159100 - SEC ADM', 'SEC ADM'), ('703159110 - B/1 E B/5', 'B/1 E B/5'), ('703159110-1 - B/5', 'B/5'), ('703159120 - AA', 'AA'), ('703159130 - B/3 E MOTOMEC', 'B/3 E MOTOMEC'), ('703159130-1 - MOTOMEC', 'MOTOMEC'), ('703159131 - COBOM', 'COBOM'), ('703159140 - B/4', 'B/4'), ('703159150 - ST UGE', 'ST UGE'), ('703159160 - ST PJMD', 'ST PJMD'), ('703159200 - SEC ATIV TEC', 'SEC ATIV TEC'), ('703151000 - CMT 1º SGB', 'CMT 1º SGB'), ('703151100 - ADM PB CERRADO', 'ADM PB CERRADO'), ('703151101 - EB CERRADO', 'EB CERRADO'), ('703151102 - EB ZONA NORTE', 'EB ZONA NORTE'), ('703151200 - ADM PB SANTA ROSÁLIA', 'ADM PB SANTA ROSÁLIA'), ('703151201 - EB SANTA ROSÁLIA', 'EB SANTA ROSÁLIA'), ('703151202 - EB ÉDEM', 'EB ÉDEM'), ('703151300 - ADM PB VOTORANTIM', 'ADM PB VOTORANTIM'), ('703151301 - EB VOTORANTIM', 'EB VOTORANTIM'), ('703151302 - EB PIEDADE', 'EB PIEDADE'), ('703151800 - ADM 1º SGB', 'ADM 1º SGB'), ('703152000 - CMT 2º SGB', 'CMT 2º SGB'), ('703152100 - ADM PB ITU', 'ADM PB ITU'), ('703152101 - EB ITU', 'EB ITU'), ('703152102 - EB PORTO FELIZ', 'EB PORTO FELIZ'), ('703152200 - ADM PB SALTO', 'ADM PB SALTO'), ('703152201 - EB SALTO', 'EB SALTO'), ('703152300 - ADM PB SÃO ROQUE', 'ADM PB SÃO ROQUE'), ('703152301 - EB SÃO ROQUE', 'EB SÃO ROQUE'), ('703152302 - EB IBIÚNA', 'EB IBIÚNA'), ('703152800 - ADM 2º SGB', 'ADM 2º SGB'), ('703152900 - NUCL ATIV TEC 2º SGB', 'NUCL ATIV TEC 2º SGB'), ('703153000 - CMT 3º SGB', 'CMT 3º SGB'), ('703153100 - ADM PB ITAPEVA', 'ADM PB ITAPEVA'), ('703153101 - EB ITAPEVA', 'EB ITAPEVA'), ('703153102 - EB APIAÍ', 'EB APIAÍ'), ('703153103 - EB ITARARÉ', 'EB ITARARÉ'), ('703153104 - EB CAPÃO BONITO', 'EB CAPÃO BONITO'), ('703153800 - ADM 3º SGB', 'ADM 3º SGB'), ('703153900 - NUCL ATIV TEC 3º SGB', 'NUCL ATIV TEC 3º SGB'), ('703154000 - CMT 4º SGB', 'CMT 4º SGB'), ('703154100 - ADM PB ITAPETININGA', 'ADM PB ITAPETININGA'), ('703154101 - EB ITAPETININGA', 'EB ITAPETININGA'), ('703154102 - EB BOITUVA', 'EB BOITUVA'), ('703154103 - EB ANGATUBA', 'EB ANGATUBA'), ('703154200 - ADM PB TATUÍ', 'ADM PB TATUÍ'), ('703154201 - EB TATUÍ', 'EB TATUÍ'), ('703154202 - EB TIETÊ', 'EB TIETÊ'), ('703154203 - EB LARANJAL PAULISTA', 'EB LARANJAL PAULISTA'), ('703154800 - ADM 4º SGB', 'ADM 4º SGB'), ('703154900 - NUCL ATIV TEC 4º SGB', 'NUCL ATIV TEC 4º SGB'), ('703155000 - CMT 5º SGB', 'CMT 5º SGB'), ('703155100 - ADM PB BOTUCATU', 'ADM PB BOTUCATU'), ('703155101 - EB BOTUCATU', 'EB BOTUCATU'), ('703155102 - EB ITATINGA', 'EB ITATINGA'), ('703155200 - ADM PB AVARÉ', 'ADM PB AVARÉ'), ('703155201 - EB AVARÉ', 'EB AVARÉ'), ('703155202 - EB PIRAJU', 'EB PIRAJU'), ('703155203 - EB ITAÍ', 'EB ITAÍ'), ('703155800 - ADM 5º SGB', 'ADM 5º SGB'), ('703155900 - NUCL ATIV TEC 5º SGB', 'NUCL ATIV TEC 5º SGB')], max_length=120)),
                ('posto_atendimento', models.CharField(choices=[('', ' '), ('EB AVARÉ', 'EB AVARÉ'), ('EB APIAÍ', 'EB APIAÍ'), ('EB ITAPETININGA', 'EB ITAPETININGA'), ('EB ITARARÉ', 'EB ITARARÉ'), ('EB SÃO ROQUE', 'EB SÃO ROQUE'), ('EB CAPÃO BONITO', 'EB CAPÃO BONITO'), ('EB CERRADO', 'EB CERRADO'), ('EB ANGATUBA', 'EB ANGATUBA'), ('EB BOTUCATU', 'EB BOTUCATU'), ('EB SALTO', 'EB SALTO'), ('EB ITAÍ', 'EB ITAÍ'), ('EB BOITUVA', 'EB BOITUVA'), ('EB TATUÍ', 'EB TATUÍ'), ('EB TIETÊ', 'EB TIETÊ'), ('EB LARANJAL PAULISTA', 'EB LARANJAL PAULISTA'), ('EB PIRAJU', 'EB PIRAJU'), ('EB IBIÚNA', 'EB IBIÚNA'), ('EB ITAPEVA', 'EB ITAPEVA'), ('EB ITATINGA', 'EB ITATINGA'), ('EB ITU', 'EB ITU'), ('EB PIEDADE', 'EB PIEDADE'), ('EB PORTO FELIZ', 'EB PORTO FELIZ'), ('EB VOTORANTIM', 'EB VOTORANTIM'), ('EB SANTA ROSÁLIA', 'EB SANTA ROSÁLIA'), ('EB ZONA NORTE', 'EB ZONA NORTE'), ('EB ÉDEM', 'EB ÉDEM')], max_length=50)),
                ('cidade_posto', models.CharField(choices=[('', ' '), ('Sorocaba', 'Sorocaba'), ('Votorantim', 'Votorantim'), ('Piedade', 'Piedade'), ('Itu', 'Itu'), ('Porto Feliz', 'Porto Feliz'), ('Salto', 'Salto'), ('São Roque', 'São Roque'), ('Ibiúna', 'Ibiúna'), ('Itapeva', 'Itapeva'), ('Itararé', 'Itararé'), ('Apiaí', 'Apiaí'), ('Capão Bonito', 'Capão Bonito'), ('Itapetininga', 'Itapetininga'), ('Angatuba', 'Angatuba'), ('Boituva', 'Boituva'), ('Tatuí', 'Tatuí'), ('Tietê', 'Tietê'), ('Laranjal Paulista', 'Laranjal Paulista'), ('Botucatu', 'Botucatu'), ('Itaí', 'Itaí'), ('Avaré', 'Avaré'), ('Itatinga', 'Itatinga'), ('Piraju', 'Piraju')], max_length=50)),
                ('tipo_cidade', models.CharField(choices=[('', ' '), ('Administrativo', ' Administrativo'), ('Operacional', 'Operacional')], max_length=50)),
                ('op_adm', models.CharField(choices=[('', ' '), ('Sede', 'Sede'), ('Apoio', 'Apoio')], max_length=50)),
                ('quartel', models.ImageField(blank=True, help_text='Formato: PNG/JPG. Tamanho máximo: 2MB', null=True, upload_to='img/quartel/%Y/%m/%d/', verbose_name='Quartel')),
                ('data_criacao', models.DateTimeField(default=django.utils.timezone.now)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Pessoal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cel', models.IntegerField()),
                ('ten_cel', models.IntegerField()),
                ('maj', models.IntegerField()),
                ('cap', models.IntegerField()),
                ('tenqo', models.IntegerField()),
                ('tenqa', models.IntegerField()),
                ('asp', models.IntegerField()),
                ('st_sgt', models.IntegerField()),
                ('cb_sd', models.IntegerField()),
                ('posto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pessoal', to='municipios.posto')),
            ],
        ),
        migrations.CreateModel(
            name='Contato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telefone', models.CharField(max_length=20)),
                ('rua', models.CharField(max_length=100)),
                ('numero', models.CharField(max_length=10)),
                ('complemento', models.CharField(blank=True, max_length=100, null=True)),
                ('bairro', models.CharField(max_length=100)),
                ('cidade', models.CharField(max_length=100)),
                ('cep', models.CharField(max_length=9)),
                ('email', models.EmailField(max_length=254)),
                ('longitude', models.FloatField()),
                ('latitude', models.FloatField()),
                ('posto', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='contato', to='municipios.posto', verbose_name='Contato do Posto')),
            ],
        ),
        migrations.CreateModel(
            name='Cidade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.TextField(blank=True, help_text='Informações relevantes sobre o município', verbose_name='Descrição')),
                ('municipio', models.CharField(choices=[('', ' '), ('Águas de Santa Bárbara', 'Águas de Santa Bárbara'), ('Apiaí', 'Apiaí'), ('Barra do Chapéu', 'Barra do Chapéu'), ('Alambari', 'Alambari'), ('Bom Sucesso de Itararé', 'Bom Sucesso de Itararé'), ('Alumínio', 'Alumínio'), ('Buri', 'Buri'), ('Capão Bonito', 'Capão Bonito'), ('Araçoiaba da Serra', 'Araçoiaba da Serra'), ('Angatuba', 'Angatuba'), ('Anhembi', 'Anhembi'), ('Araçariguama', 'Araçariguama'), ('Arandu', 'Arandu'), ('Areiópolis', 'Areiópolis'), ('Avaré', 'Avaré'), ('Campina do Monte Alegre', 'Campina do Monte Alegre'), ('Barão de Antonina', 'Barão de Antonina'), ('Boituva', 'Boituva'), ('Capela do Alto', 'Capela do Alto'), ('Botucatu', 'Botucatu'), ('Bofete', 'Bofete'), ('Cerqueira César', 'Cerqueira César'), ('Cerquilho', 'Cerquilho'), ('Cesário Lange', 'Cesário Lange'), ('Conchas', 'Conchas'), ('Coronel Macedo', 'Coronel Macedo'), ('Fartura', 'Fartura'), ('Guapiara', 'Guapiara'), ('Guareí', 'Guareí'), ('Iaras', 'Iaras'), ('Ibiúna', 'Ibiúna'), ('Iperó', 'Iperó'), ('Itaberá', 'Itaberá'), ('Itaí', 'Itaí'), ('Itaoca', 'Itaoca'), ('Itapetininga', 'Itapetininga'), ('Itapeva', 'Itapeva'), ('Itapirapuã Paulista', 'Itapirapuã Paulista'), ('Itaporanga', 'Itaporanga'), ('Itararé', 'Itararé'), ('Itatinga', 'Itatinga'), ('Itu', 'Itu'), ('Jumirim', 'Jumirim'), ('Laranjal Paulista', 'Laranjal Paulista'), ('Mairinque', 'Mairinque'), ('Manduri', 'Manduri'), ('Nova Campina', 'Nova Campina'), ('Paranapanema', 'Paranapanema'), ('Pardinho', 'Pardinho'), ('Pereiras', 'Pereiras'), ('Piedade', 'Piedade'), ('Pilar do Sul', 'Pilar do Sul'), ('Piraju', 'Piraju'), ('Porangaba', 'Porangaba'), ('Porto Feliz', 'Porto Feliz'), ('Pratânia', 'Pratânia'), ('Quadra', 'Quadra'), ('Ribeira', 'Ribeira'), ('Ribeirão Branco', 'Ribeirão Branco'), ('Ribeirão Grande', 'Ribeirão Grande'), ('Riversul', 'Riversul'), ('Salto', 'Salto'), ('Salto de Pirapora', 'Salto de Pirapora'), ('São Manuel', 'São Manuel'), ('São Miguel Arcanjo', 'São Miguel Arcanjo'), ('São Paulo', 'São Paulo'), ('São Roque', 'São Roque'), ('Sarapuí', 'Sarapuí'), ('Sarutaiá', 'Sarutaiá'), ('Sorocaba', 'Sorocaba'), ('Taguaí', 'Taguaí'), ('Tapiraí', 'Tapiraí'), ('Taquarituba', 'Taquarituba'), ('Taquarivaí', 'Taquarivaí'), ('Tatuí', 'Tatuí'), ('Tejupá', 'Tejupá'), ('Tietê', 'Tietê'), ('Torre de Pedra', 'Torre de Pedra'), ('Votorantim', 'Votorantim')], max_length=100, verbose_name='Município')),
                ('longitude', models.FloatField()),
                ('latitude', models.FloatField()),
                ('bandeira', models.ImageField(blank=True, help_text='Formato: PNG/JPG. Tamanho máximo: 2MB', null=True, upload_to='img/bandeiras/%Y/%m/%d/', verbose_name='Bandeira municipal')),
                ('posto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cidades', to='municipios.posto', verbose_name='Posto vinculado')),
            ],
            options={
                'verbose_name': 'Cidade',
                'verbose_name_plural': 'Cidades',
            },
        ),
    ]
