from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('rpt', '0001_initial'),  # substitua pelo nome da sua última migração
    ]

    operations = [
        migrations.RenameField(
            model_name='cadastro_rpt',
            old_name='data_alteracao',
            new_name='create',
        ),
        migrations.RenameField(
            model_name='historicorpt',
            old_name='data_alteracao',
            new_name='create',
        ),
    ]