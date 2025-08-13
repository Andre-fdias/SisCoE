# backend/accounts/urls.py
from django.contrib.auth.views import LoginView
from django.urls import path, include
from .decorators import permissao_necessaria
from backend.accounts import views as v

app_name = 'accounts' # Define o namespace para este aplicativo de URLs

# Padrões de URL para gestão de usuários
user_management_patterns = [
    path('', v.user_list, name='user_list'),
    path('<int:pk>/', v.user_detail, name='user_detail'),
    path('<int:pk>/access_history/', v.access_history, name='access_history'), # URL para histórico de acessos
    path('<int:pk>/action_history/', v.user_action_history, name='user_action_history'), # URL para histórico de ações
    path('<int:pk>/change_password/', v.change_password_view, name='change_password_view'),
    path('<int:pk>/permission_update/', v.user_permission_update, name='user_permission_update'), # Altera permissões
    path('user/<int:pk>/termo-pdf/', v.generate_termo_pdf, name='generate_termo_pdf'),
]

urlpatterns = [
    path('login/', v.login_view, name='login'),
    path('logout/', v.my_logout, name='logout'),
    path('register/', v.signup, name='signup'), # Agora esta é a view de confirmação/criação
    path('reset/<uidb64>/<token>/', v.MyPasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('reset/done/', v.MyPasswordResetComplete.as_view(), name='password_reset_complete'),
    path('password_reset/', v.MyPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', v.MyPasswordResetDone.as_view(), name='password_reset_done'),


      # URLs de gestão de usuários (incluindo a lista e edição de permissões)
    path('users/', include(user_management_patterns)),
    path('acesso-negado/', v.acesso_negado, name='acesso_negado'),

    # URLs para históricos globais
    path('global_access_history/', v.global_access_history, name='global_access_history'),
    path('global_action_history/', v.global_user_action_history, name='global_user_action_history'),

    path('verificar-cpf/', v.verificar_cpf, name='verificar_cpf'),

   # NOVA ROTA: Troca de senha forçada no primeiro login
    path('force-password-change/', v.force_password_change_view, name='force_password_change'),
    path('admin-login/', v.admin_login, name='admin_login'), # Adicionada para consistência
]
