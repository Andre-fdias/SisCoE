from django.db.models.signals import post_save, pre_save # Importe ambos os signals
from django.dispatch import receiver
from .models import Cadastro, CatEfetivo, HistoricoCatEfetivo # Certifique-se de importar todos os modelos necessários
from backend.core.models import Profile # Importe o modelo Profile do app core
from datetime import date
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# --- Signal para Cadastro ---
@receiver(post_save, sender=Cadastro)
def sync_cadastro_to_profiles(sender, instance, created, **kwargs):
    """
    Signal para sincronizar dados de um Cadastro com seus Profiles associados.
    Executa quando um objeto Cadastro é salvo (criado ou atualizado).
    """
    print(f"DEBUG: [efetivo.signals] Signal post_save de Cadastro disparado para RE: {instance.re}. Created: {created}")
    if kwargs.get('raw', False):
        print("DEBUG: [efetivo.signals] Signal sync_cadastro_to_profiles ignorado devido a raw=True (carregamento de fixtures/dumps).")
        return
        
    try:
        # Pega todos os perfis que estão linkados a este Cadastro
        # O related_name='profiles' no Profile.cadastro permite isso: instance.profiles.all()
        profiles = instance.profiles.all() 
        print(f"DEBUG: [efetivo.signals] Encontrados {profiles.count()} Profiles associados ao Cadastro {instance.re}.")

        for profile in profiles:
            print(f"DEBUG: [efetivo.signals] Chamando sync_with_cadastro para Profile {profile.user.email} (ID: {profile.pk}).")
            profile.sync_with_cadastro() # Chama o método para copiar dados
            profile.save() # Salva o Profile para persistir as mudanças
            print(f"DEBUG: [efetivo.signals] Profile {profile.user.email} (ID: {profile.pk}) salvo após sincronização do Cadastro.")

        logger.info(f"Cadastro {instance.nome_de_guerra} (RE: {instance.re}) {'criado' if created else 'atualizado'} e sincronizou com {profiles.count()} Profiles.")

    except Exception as e:
        print(f"ERRO: [efetivo.signals] No signal sync_cadastro_to_profiles para Cadastro {instance.re}: {e}")
        logger.error(f"Erro ao sincronizar Cadastro {instance.re} com Profiles: {e}", exc_info=True)


# --- Signal para CatEfetivo (post_save) ---
@receiver(post_save, sender=CatEfetivo)
def criar_historico_apos_save(sender, instance, created, **kwargs):
    """
    Signal para criar um registro de histórico após a atualização de um CatEfetivo.
    """
    print(f"DEBUG: [efetivo.signals] Signal post_save de CatEfetivo disparado para ID: {instance.pk}. Created: {created}")
    if kwargs.get('raw', False):
        print("DEBUG: [efetivo.signals] Signal criar_historico_apos_save ignorado devido a raw=True.")
        return

    if not created:  # Só cria histórico para atualizações, não para criações
        try:
            # Certifique-se de que CatEfetivo.criar_registro_historico() existe e está implementado
            instance.criar_registro_historico()
            logger.info(f"Histórico criado para CatEfetivo {instance.pk} após atualização.")
            print(f"DEBUG: [efetivo.signals] Histórico criado para CatEfetivo {instance.pk}.")
        except AttributeError:
            print(f"ERRO: [efetivo.signals] Método 'criar_registro_historico' não encontrado no modelo CatEfetivo. Certifique-se de que ele está definido.")
            logger.error(f"Método 'criar_registro_historico' não encontrado no modelo CatEfetivo. ID: {instance.pk}", exc_info=True)
        except Exception as e:
            print(f"ERRO: [efetivo.signals] Ao criar histórico para CatEfetivo {instance.pk}: {e}")
            logger.error(f"Erro ao criar histórico para CatEfetivo {instance.pk}: {e}", exc_info=True)


# --- Signal para CatEfetivo (pre_save) ---
@receiver(pre_save, sender=CatEfetivo)
def verificar_data_termino(sender, instance, **kwargs):
    """
    Signal para verificar a data de término de um CatEfetivo antes de salvar.
    Se a data de término já passou, muda o tipo para 'ATIVO' e anula a data de término.
    Cria um registro no HistoricoCatEfetivo para esta alteração automática.
    """
    print(f"DEBUG: [efetivo.signals] Signal pre_save de CatEfetivo disparado para ID: {instance.pk}.")
    if kwargs.get('raw', False):
        print("DEBUG: [efetivo.signals] Signal verificar_data_termino ignorado devido a raw=True.")
        return

    if instance.data_termino and instance.data_termino < date.today():
        print(f"DEBUG: [efetivo.signals] Data de término ({instance.data_termino}) expirada para CatEfetivo {instance.pk}.")
        # Se a data de término já passou, muda para ATIVO
        if instance.tipo != 'ATIVO': # Só altera se não for já ATIVO para evitar loops desnecessários
            old_tipo = instance.tipo
            instance.tipo = 'ATIVO'
            instance.data_termino = None
            print(f"DEBUG: [efetivo.signals] CatEfetivo {instance.pk} alterado de '{old_tipo}' para 'ATIVO'. Data de término anulada.")
            
            # Cria histórico (se o HistoricoCatEfetivo tiver campo para usuario_alteracao, pode ser None para automático)
            try:
                # É importante ter certeza de que o `usuario_alteracao` não seja obrigatório ou seja tratado
                # quando a alteração é automática pelo sistema.
                HistoricoCatEfetivo.objects.create(
                    cat_efetivo=instance,
                    tipo=instance.tipo,
                    data_inicio=instance.data_inicio,
                    data_termino=instance.data_termino,
                    observacao="Alteração automática para ATIVO - Data de término expirada",
                    # usuario_alteracao=None # Descomente se o campo aceitar None e você quiser registrar assim
                )
                logger.info(f"CatEfetivo {instance.pk} alterado automaticamente para ATIVO devido a data de término expirada.")
                print(f"DEBUG: [efetivo.signals] Histórico de alteração automática para ATIVO criado para CatEfetivo {instance.pk}.")
            except Exception as e:
                print(f"ERRO: [efetivo.signals] Ao criar histórico para CatEfetivo {instance.pk} na verificação de data de término: {e}")
                logger.error(f"Erro ao criar histórico para CatEfetivo {instance.pk} na verificação de data de término: {e}", exc_info=True)