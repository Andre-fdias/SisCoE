from role_permissions.roles import AbstractUserRole

class Basico(AbstractUserRole):
    available_permissions = {
        'view_index': True,
        'view_dashboard': True,
        # 'view_profile': True, # Removido, pois o Profile foi excluído
        'view_lembrete': True,
        'add_lembrete': True,
        'change_own_lembrete': True,
        'delete_own_lembrete': True,
        'view_tarefa': True,
        'add_tarefa': True,
        'change_own_tarefa': True,
        'delete_own_tarefa': True,
        'view_documento': True,
        'view_calcular_tempo_servico': True,
    }

class SGB(Basico):  # Herda de Basico
    available_permissions = Basico.available_permissions.copy()
    available_permissions.update({
        'view_cadastro': True,
        'view_promocao': True,
        'view_detalhessituacao': True,
        'view_catefetivo': True,
        'view_posto': True,
        'view_municipio': True,
        'view_rpt': True,
        'view_adicional': True,
    })

class Visitante(AbstractUserRole):
    available_permissions = {
        'view_index': True,
        'view_documento': True,
    }

class Gestor(SGB):  # Herda de SGB
    available_permissions = SGB.available_permissions.copy()
    available_permissions.update({
        'add_cadastro': True,
        'change_cadastro': True,
        'delete_cadastro': True,
        'add_documento': True,
        'change_documento': True,
        'delete_documento': True,
        'add_rpt': True,
        'change_rpt': True,
        'delete_rpt': True,
        'view_user': True, # Mantido, pois a visualização de usuários ainda é relevante
    })

class Admin(AbstractUserRole):
    available_permissions = {
        # Admin tem todas as permissões
    }
