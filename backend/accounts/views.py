# accounts/views.py
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView
)
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from backend.accounts.services import send_mail_to_user, log_user_action # Ensure log_user_action is imported
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem  # Ajuste a importaÃ§Ã£o conforme necessÃ¡rio
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
import socket
from .models import User, UserActionLog # Ensure UserActionLog is imported
from .forms import CustomUserForm
from django.utils import timezone
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from datetime import datetime
from django.utils.timezone import make_naive, is_aware
from .utils import get_client_ip, get_computer_name
import logging
logger = logging.getLogger(__name__)



def my_logout(request):
    user = request.user
    user.update_login_history(None, None, logout_time=timezone.now())
    user.is_online = False
    user.save()
    log_user_action(user, "User logged out", request)
    logout(request)
    return redirect('core:capa')

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name')


from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from .forms import CustomUserForm
# from .services import log_user_action # Already imported at the top
import random
import string

def signup(request):
    logger.info("Entrou na view signup.")
    signup_data = request.session.get('signup_data', None)
    
    if not signup_data:
        logger.warning("signup_data não encontrado na sessão. Redirecionando para verificar_cpf.")
        return redirect('verificar_cpf')

    if request.method == 'POST':
        logger.info("Requisição POST recebida em signup.")
        form = CustomUserForm(request.POST)
        if form.is_valid():
            logger.info("Formulário de CustomUser é válido.")
            try:
                # Salva o usuário e obtém a senha gerada
                user, password = form.save() 
                logger.info(f"Usuário {user.email} salvo com sucesso.")
                
                # Envia o email com a senha
                current_site = get_current_site(request)
                subject = 'Sua conta foi criada'
                message = render_to_string('email/account_created_email.html', {
                    'user': user,
                    'password': password,
                    'domain': current_site.domain,
                })
                user.email_user(subject, message)
                logger.info(f"Email enviado para {user.email}.")
                
                # Log da ação
                log_user_action(user, "Conta criada com senha gerada automaticamente", request)
                logger.info("Ação de criação de conta logada.")
                
                # Limpa a sessão
                if 'signup_data' in request.session:
                    del request.session['signup_data']
                    logger.info("signup_data removido da sessão.")
                
                logger.info("Redirecionando para a página de login.")
                return redirect('login') 
            
            except Exception as e:
                logger.error(f"Erro ao criar conta ou enviar email: {str(e)}", exc_info=True)
                form.add_error(None, f"Erro ao enviar email: {str(e)}")
        else:
            logger.warning(f"Formulário de CustomUser inválido. Erros: {form.errors}")
            # Se o formulário não é válido, ele vai renderizar a página novamente com os erros
    else:
        logger.info("Requisição GET recebida em signup. Pré-preenchendo formulário.")
        initial = {
            'email': signup_data['email'],
            'first_name': signup_data['first_name'],
            'last_name': signup_data['last_name']
        }
        form = CustomUserForm(initial=initial)
    
    logger.info("Renderizando registration_form.html.")
    return render(request, 'registration/registration_form.html', {'form': form})


class MyPasswordResetConfirm(PasswordResetConfirmView):
    '''
    Requer password_reset_confirm.html
    '''

    def form_valid(self, form):
        self.user.is_active = True
        self.user.save()
        return super(MyPasswordResetConfirm, self).form_valid(form)


class MyPasswordResetComplete(PasswordResetCompleteView):
    '''
    Requer password_reset_complete.html
    '''
    ...


class MyPasswordReset(PasswordResetView):
    '''
    Requer
    registration/password_reset_form.html
    registration/password_reset_email.html
    registration/password_reset_subject.txt  Opcional
    '''
    ...


class MyPasswordResetDone(PasswordResetDoneView):
    '''
    Requer
    registration/password_reset_done.html
    '''
    ...

User = get_user_model()

def verificar_cpf(request):
    template_name = 'registration/verificacao_cpf.html'
    message = None

    if request.method == 'POST':
        cpf = request.POST.get('cpf')
        try:
            # Verifica se o CPF está cadastrado
            cadastro = Cadastro.objects.get(cpf=cpf)
            
            # Verifica se o usuário é ativo
            detalhes_situacao = DetalhesSituacao.objects.filter(
                cadastro=cadastro
            ).order_by('-data_alteracao').first()
            
            if detalhes_situacao and detalhes_situacao.situacao == 'Efetivo':
                # Verifica se o usuário já está cadastrado
                if get_user_model().objects.filter(email=cadastro.email).exists():
                    message = 'Usuário já cadastrado. Por favor, faça login.'
                else:
                    # Armazena os dados na sessão para o signup
                    request.session['signup_data'] = {
                        'email': cadastro.email,
                        'first_name': cadastro.nome.split()[0], # Assuming first name is the first part
                        'last_name': cadastro.nome_de_guerra,
                        'cpf': cadastro.cpf
                    }
                    return redirect('signup')
            else:
                message = 'Você não é um funcionário ativo. Por favor, procure o setor de RH.'
        except Cadastro.DoesNotExist:
            message = 'CPF não encontrado. Por favor, procure o setor de RH.'
        except Exception as e:
            message = f"Ocorreu um erro: {e}"

    return render(request, template_name, {'message': message})

@login_required
def user_list(request):
    template_name = 'accounts/user_list.html'
    object_list = User.objects.exclude(email='admin@email.com')
    context = {'object_list': object_list}
    return render(request, template_name, context)

@login_required
def user_detail(request, pk):
    template_name = 'accounts/user_detail.html'
    instance = get_object_or_404(User, pk=pk)

    context = {'object': instance}
    return render(request, template_name, context)



def user_create(request):
    template_name = 'accounts/user_form.html'
    
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Here you can add logic to send the password by email
            log_user_action(request.user, f"Created user {user.email}", request)
            return redirect('user_detail', pk=user.pk)
    else:
        # Verifica se veio da verificação de CPF
        if 'signup_data' in request.session:
            signup_data = request.session.pop('signup_data') # Pop to remove it after use
            initial = {
                'email': signup_data['email'],
                'first_name': signup_data['first_name'],
                'last_name': signup_data['last_name']
            }
            form = CustomUserForm(initial=initial)
        else:
            form = CustomUserForm()
    
    context = {'form': form}
    return render(request, template_name, context)


@login_required
def user_update(request, pk):
    template_name = 'accounts/user_form.html'
    instance = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = CustomUserForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('user_detail', pk=pk)  # Redireciona para a página de detalhes do usuário após a atualização
    else:
        form = CustomUserForm(instance=instance)

    context = {
        'object': instance,
        'form': form,
    }
    return render(request, template_name, context)


# from .services import log_user_action # Already imported at the top

def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            user_ip = get_client_ip(request)
            user_computer_name = get_computer_name(user_ip)
            user.update_login_history(user_ip, user_computer_name, login_time=timezone.now())
            user.is_online = True
            user.last_login_ip = user_ip
            user.last_login_computer_name = user_computer_name
            user.last_login = timezone.now()
            user.save()
            login(request, user)
            log_user_action(user, "User logged in", request)
            return redirect('core:index')
    return render(request, 'registration/login.html', {'form': form})


@login_required
def user_update(request, pk):
    template_name = 'accounts/user_form.html'
    instance = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = CustomUserForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            log_user_action(request.user, f"Updated user {instance.email}", request)
            return redirect('user_detail', pk=pk)
    else:
        form = CustomUserForm(instance=instance)

    context = {
        'object': instance,
        'form': form,
    }
    return render(request, template_name, context)


from django.utils import timezone
from datetime import datetime

@login_required
def access_history(request):
    user = request.user
    login_history = []
    for entry in user.login_history:
        login_time_str = entry.get('login_time')
        logout_time_str = entry.get('logout_time')
        
        # Converte as strings de volta para objetos datetime
        login_time = datetime.fromisoformat(login_time_str) if login_time_str else None
        logout_time = datetime.fromisoformat(logout_time_str) if logout_time_str else None
        
        # Converte para o fuso horário local
        login_time = timezone.localtime(login_time) if login_time else None
        logout_time = timezone.localtime(logout_time) if logout_time else None
        
        duration = user.get_login_duration(login_time_str, logout_time_str)
        # Ensure format_datetime handles None gracefully, or only call it if time exists
        formatted_login_time = user.format_datetime(login_time.isoformat()) if login_time else "N/A"
        formatted_logout_time = user.format_datetime(logout_time.isoformat()) if logout_time else "N/A"
        
        login_history.append({
            'login_time': formatted_login_time,
            'ip': entry.get('ip'),
            'computer_name': entry.get('computer_name'),
            'logout_time': formatted_logout_time,
            'duration': duration,
            'is_online': user.is_online, # This seems to apply to the current user's online status, not past entries
        })
    return render(request, 'accounts/access_history.html', {'login_history': login_history})


from django.db.models import Q
from django.utils.dateparse import parse_datetime


@login_required
def all_user_action_history(request):
    users = User.objects.all()
    selected_user = request.GET.get('user')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    action_logs = UserActionLog.objects.all()

    if selected_user:
        action_logs = action_logs.filter(user__email=selected_user)

    if start_date:
        # Make sure the start_date is parsed as datetime and then made timezone aware
        start_date_obj = parse_datetime(start_date)
        if start_date_obj and not is_aware(start_date_obj):
            start_date_obj = timezone.make_aware(start_date_obj)
        action_logs = action_logs.filter(timestamp__gte=start_date_obj)

    if end_date:
        # Make sure the end_date is parsed as datetime and then made timezone aware
        end_date_obj = parse_datetime(end_date)
        if end_date_obj and not is_aware(end_date_obj):
            end_date_obj = timezone.make_aware(end_date_obj)
        action_logs = action_logs.filter(timestamp__lte=end_date_obj)

    action_logs = action_logs.order_by('-timestamp')

    return render(request, 'accounts/all_user_action_history.html', {
        'action_logs': action_logs,
        'users': users,
        'selected_user': selected_user,
        'start_date': start_date, # Pass back for form pre-filling
        'end_date': end_date,     # Pass back for form pre-filling
    })


# from .models import UserActionLog # Already imported at the top

@login_required
def user_action_history(request, pk):
    user = get_object_or_404(User, pk=pk)
    action_logs = UserActionLog.objects.filter(user=user).order_by('-timestamp')
    return render(request, 'accounts/user_action_history.html', {'action_logs': action_logs, 'user': user})


@login_required
def all_users_list(request):
    users = User.objects.all()
    return render(request, 'accounts/all_list.html', {'users': users})