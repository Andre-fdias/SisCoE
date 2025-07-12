# accounts/urls.py
from django.contrib.auth.views import LoginView
from django.urls import path, include

from backend.accounts import views as v


# A ordem das urls é importante por causa do slug, quando existir.
user_patterns = [
    path('', v.user_list, name='user_list'),  # noqa E501
    path('create/', v.user_create, name='user_create'),  # noqa E501
    path('<int:pk>/', v.user_detail, name='user_detail'),  # noqa E501
    path('<int:pk>/update/', v.user_update, name='user_update'),  # noqa E501
    # Novas URLs adicionadas aqui
    path('<int:pk>/access_history/', v.access_history, name='access_history'),
    path('<int:pk>/action_history/', v.user_action_history, name='user_action_history'),
]



urlpatterns = [
    path('login/', v.login_view, name='login'),  # noqa E501
    path('logout/', v.my_logout, name='logout'),  # noqa E501
    path('register/', v.signup, name='signup'),  # noqa E501
    path('reset/<uidb64>/<token>/', v.MyPasswordResetConfirm.as_view(), name='password_reset_confirm'),  # noqa E501
    path('reset/done/', v.MyPasswordResetComplete.as_view(), name='password_reset_complete'),  # noqa E501
    path('password_reset/', v.MyPasswordReset.as_view(), name='password_reset'),  # noqa E501
    path('password_reset/done/', v.MyPasswordResetDone.as_view(), name='password_reset_done'),  # noqa E501
    path('verificar_cpf/', v.verificar_cpf, name='verificar_cpf'),  # Adiciona a URL para verificação de CPF
    path('users/', include(user_patterns)), # Inclui as URLs dos usuários
    path('all_list/', v.all_users_list, name='all_list'), # Adicionado: URL para o histórico de login de todos os usuários
    path('all_user_action_history/', v.all_user_action_history, name='all_user_action_history'), # URL para o histórico de ações de todos os usuários
]