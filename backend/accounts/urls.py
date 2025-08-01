# backend/accounts/urls.py
from django.contrib.auth.views import LoginView
from django.urls import path, include

from backend.accounts import views as v

app_name = 'accounts' # Define o namespace para este aplicativo de URLs

user_patterns = [
    path('', v.user_list, name='user_list'),
    path('create/', v.user_create, name='user_create'),
    path('<int:pk>/', v.user_detail, name='user_detail'),
    path('<int:pk>/update/', v.user_update, name='user_update'),
    path('<int:pk>/access_history/', v.access_history, name='access_history'),
    path('<int:pk>/action_history/', v.user_action_history, name='user_action_history'),
    path('<int:pk>/change_password/', v.change_password_view, name='change_password_view'),
]

urlpatterns = [
    path('login/', v.login_view, name='login'),
    path('logout/', v.my_logout, name='logout'),
    path('register/', v.signup, name='signup'), # Agora esta é a view de confirmação/criação
    path('reset/<uidb64>/<token>/', v.MyPasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('reset/done/', v.MyPasswordResetComplete.as_view(), name='password_reset_complete'),
    path('password_reset/', v.MyPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', v.MyPasswordResetDone.as_view(), name='password_reset_done'),
    path('users/', include(user_patterns)),
    path('verificar-cpf/', v.verificar_cpf, name='verificar_cpf'),

   # NOVA ROTA: Troca de senha forçada no primeiro login
    path('force-password-change/', v.force_password_change_view, name='force_password_change'),
       path('admin-login/', v.admin_login, name='admin_login'),
  
    path('all_user_action_history/', v.all_user_action_history, name='all_user_action_history'),
]
