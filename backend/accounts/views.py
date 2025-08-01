# accounts/views.py
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
    SetPasswordForm 
)
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from backend.accounts.services import send_mail_to_user, log_user_action, send_generated_password_email
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem # Certifique-se de que Imagem está importada
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
import socket
from .models import User, UserActionLog, TermosAceite
from .forms import CustomUserChangeForm# CustomUserCreationForm não será usado diretamente para criar o User aqui
from django.utils import timezone
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm # Não será usado diretamente
from datetime import datetime
from django.utils.timezone import make_naive, is_aware
from .utils import get_client_ip, get_computer_name
import logging
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_http_methods
import random
import string
from django.contrib import messages
from django.db import transaction # Para garantir atomicidade nas operações
import smtplib
import json
import base64
import io
from PIL import Image as PILImage # Importa PIL.Image como PILImage para evitar conflito
from django.contrib.auth.forms import PasswordChangeForm # Importação adicionada
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


from django.urls import reverse_lazy
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from .services import send_email  # Importe a função do seu serviço
from .brevo_service import send_brevo_email

class MyPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    success_url = reverse_lazy('accounts:password_reset_done')
    
    def send_mail(self, subject_template_name, email_template_name,
                 context, from_email, to_email, html_email_template_name=None):
        """
        Sobrescreve o método para usar exclusivamente o Brevo
        """
        subject = render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())
        
        html_content = render_to_string(email_template_name, context)
        
        return send_brevo_email(
            subject=subject,
            html_content=html_content,
            to_email=to_email,
            from_email=from_email,
            from_name=settings.DEFAULT_FROM_NAME
        )

class MyPasswordResetDone(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class MyPasswordResetConfirm(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.user
        new_password = form.cleaned_data['new_password1']
        current_site = get_current_site(self.request)
        
        # Prepara o contexto para o e-mail
        context = {
            'user': user,
            'password': new_password,
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': current_site.domain,
            'cadastro_data': getattr(user, 'cadastro', None),
        }
        
        # Renderiza o template
        html_content = render_to_string('email/password_reset_success.html', context)
        
        # Envia via Brevo
        send_email(
            subject='Sua senha foi redefinida - SisCoE',
            html_content=html_content,
            recipient_email=user.email
        )
        
        return response

class MyPasswordResetComplete(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


@require_http_methods(["POST", "GET"])
def verificar_cpf(request):
    logger.debug("verificar_cpf view called.")
    if request.method == 'POST':
        logger.debug("Method is POST.")
        cpf = request.POST.get('cpf', '')
        logger.debug(f"Received CPF for search: {cpf}")
        if not cpf:
            messages.error(request, 'Por favor, informe um CPF.')
            logger.debug("CPF is empty, rendering verificacao_cpf.html.")
            return render(request, 'registration/verificacao_cpf.html')

        try:
            cadastro = Cadastro.objects.filter(cpf=cpf).first()
            logger.debug(f"Cadastro found: {cadastro}")

            if not cadastro:
                messages.error(request, 'CPF não encontrado na base de dados. Por favor, entre em contato com o administrador para ser cadastrado.')
                logger.debug("Cadastro not found, rendering verificacao_cpf.html.")
                return render(request, 'registration/verificacao_cpf.html')

            # Verifica se já existe usuário com este cadastro
            if User.objects.filter(cadastro=cadastro).exists():
                messages.warning(request, 'Este CPF já possui uma conta de usuário. Por favor, faça login ou redefina sua senha.')
                # Redireciona para landing com parâmetro para abrir modal de login
                return redirect(reverse('core:landing') + '?open_login_modal=true')
            

            detalhes_situacao = DetalhesSituacao.objects.filter(cadastro=cadastro).first()
            logger.debug(f"DetalhesSituacao found: {detalhes_situacao}")

            if not detalhes_situacao or \
               detalhes_situacao.situacao != "Efetivo" or \
               detalhes_situacao.cat_efetivo != "ATIVO":
                messages.error(request, 'Seu CPF não atende aos requisitos de situação para cadastro. Por favor, entre em contato com o administrador.')
                logger.debug("CPF does not meet requirements, rendering verificacao_cpf.html.")
                return render(request, 'registration/verificacao_cpf.html')

            logger.debug("All checks passed, preparing cadastro_data for session.")
            
            # Tenta obter o posto_grad da última promoção. Se não houver promoção, define como None.
            posto_grad_value = None
            if cadastro.ultima_promocao:
                posto_grad_value = cadastro.ultima_promocao.posto_grad

            cadastro_data = {
                'id': cadastro.id,
                're': cadastro.re,
                'dig': cadastro.dig,
                'nome': cadastro.nome,
                'nome_de_guerra': cadastro.nome_de_guerra,
                'cpf': cadastro.cpf,
                'posto_grad': posto_grad_value, # CORRIGIDO AQUI
                'email': cadastro.email,
            }

            if hasattr(cadastro, 'image') and cadastro.image:
                try:
                    with cadastro.image.open('rb') as f:
                        encoded_img = base64.b64encode(f.read()).decode('ascii')
                        cadastro_data['image_url'] = f"data:{cadastro.image.file.content_type};base64,{encoded_img}"
                        logger.debug("Image processed for session.")
                except Exception as e:
                    logger.warning(f"Não foi possível processar a imagem do Cadastro {cadastro.id} para pré-visualização: {e}")
                    cadastro_data['image_url'] = None
            else:
                cadastro_data['image_url'] = None
                logger.debug("No image found for cadastro.")

            request.session['cadastro_data_for_signup'] = cadastro_data
            logger.debug("Cadastro data stored in session, redirecting to signup.")
            return redirect('accounts:signup')

        except Exception as e:
            logger.error(f"Erro ao verificar CPF: {e}", exc_info=True)
            messages.error(request, f'Erro interno do servidor ao verificar CPF: {str(e)}')
            logger.debug("Exception caught, rendering verificacao_cpf.html.")
            return render(request, 'registration/verificacao_cpf.html')
    else: # GET request
        logger.debug("Method is GET, rendering verificacao_cpf.html.")
        return render(request, 'registration/verificacao_cpf.html')


@require_http_methods(["GET", "POST"])
def signup(request):
    cadastro_data = request.session.get('cadastro_data_for_signup')

    if not cadastro_data:
        messages.error(request, "Sessão de cadastro expirada ou inválida. Por favor, verifique seu CPF novamente.")
        return redirect('accounts:verificar_cpf')

    if request.method == 'POST':
        terms_accepted = request.POST.get('terms') == 'true'
        signature_data = request.POST.get('signature_data')

        if not terms_accepted or not signature_data:
            messages.error(request, "Você deve aceitar os Termos e Condições e fornecer sua assinatura para criar sua conta.")
            return render(request, 'registration/registration_form.html', {'cadastro_data': cadastro_data})

        try:
            cadastro_id = cadastro_data.get('id')
            cadastro_obj = get_object_or_404(Cadastro, id=cadastro_id)
            
            # Verifica se já existe um usuário com este cadastro
            if User.objects.filter(cadastro=cadastro_obj).exists():
                messages.error(request, 'Já existe uma conta associada a este cadastro militar. Por favor, faça login ou recupere sua senha.')
                # Redireciona para landing com parâmetro para abrir modal de login
                return redirect(reverse('core:capa') + '?open_login_modal=true')

            detalhes_situacao = DetalhesSituacao.objects.filter(cadastro=cadastro_obj).first()

            if not detalhes_situacao or \
               detalhes_situacao.situacao != "Efetivo" or \
               detalhes_situacao.cat_efetivo != "ATIVO":
                messages.error(request, 'Seu status militar não permite o cadastro no momento. Por favor, entre em contato com o administrador.')
                if 'cadastro_data_for_signup' in request.session:
                    del request.session['cadastro_data_for_signup']
                return redirect('accounts:verificar_cpf')

            generated_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

            user = User.objects.create_user(
                email=cadastro_obj.email,
                password=generated_password,
                first_name=cadastro_obj.nome,
                last_name=cadastro_obj.nome_de_guerra,
                cadastro=cadastro_obj,
                must_change_password=True # NOVO: Força a troca de senha no primeiro login
            )
            user.is_active = True
            user.save()

            TermosAceite.objects.create(
                usuario=user,
                ip_address=get_client_ip(request),
                signature_data=signature_data,
                versao_termos="1.0"
            )

            send_generated_password_email(request, user, generated_password)

            messages.success(request, 'Sua conta foi criada com sucesso! Uma senha foi enviada para o seu e-mail.')
            if 'cadastro_data_for_signup' in request.session:
                del request.session['cadastro_data_for_signup']
            # Redireciona para landing com parâmetro para abrir modal de login
            return redirect(reverse('core:capa') + '?open_login_modal=true')

        except Exception as e:
            logger.error(f"Erro ao criar conta ou enviar e-mail: {e}", exc_info=True)
            messages.error(request, f'Erro ao criar a conta: {str(e)}. Por favor, tente novamente ou entre em contato com o suporte.')
            return render(request, 'registration/registration_form.html', {'cadastro_data': cadastro_data})
    else:
        return render(request, 'registration/registration_form.html', {'cadastro_data': cadastro_data})
    

@login_required
def change_password_view(request, pk):
    """
    View para permitir que um usuário altere sua própria senha.
    """
    # Apenas o próprio usuário pode alterar sua senha
    user_to_change = get_object_or_404(User, pk=pk)
    if not request.user.pk == user_to_change.pk:
        messages.error(request, "Você não tem permissão para alterar a senha de outro usuário.")
        return redirect('accounts:user_detail', pk=request.user.pk)

    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Atualiza a data da última alteração de senha
            user.last_password_change = timezone.now()
            user.save()
            # Atualiza a sessão para evitar logout
            update_session_auth_hash(request, user)
            # Loga a ação do usuário
            log_user_action(request.user, 'Alterou a própria senha')
            messages.success(request, 'Sua senha foi alterada com sucesso!', extra_tags='alert-success')
            return redirect('accounts:user_detail', pk=user.pk)
        else:
            messages.error(request, 'Erro ao alterar a senha. Por favor, corrija os erros abaixo.')
    else:
        form = PasswordChangeForm(user=request.user)
    
    context = {
        'form': form,
        'user_to_change': user_to_change
    }
    return render(request, 'accounts/change_password.html', context)



# Lógica de login atualizada para verificar a situação do Cadastro
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password) # Passa request para authenticate


            if user is not None:
                
                # VERIFICA SE O USUÁRIO PRECISA TROCAR A SENHA
                if user.must_change_password:
                    login(request, user)  # Adicione esta linha para autenticar o usuário antes do redirecionamento
                    messages.info(request, "Por favor, defina uma nova senha para sua conta.")
                    return redirect('accounts:force_password_change') 


                # Verifica a situação do Cadastro antes de permitir o login
                if hasattr(user, 'cadastro') and user.cadastro:
                    detalhes_situacao = DetalhesSituacao.objects.filter(cadastro=user.cadastro).first()
                    if detalhes_situacao and \
                       detalhes_situacao.situacao == "Efetivo" and \
                       detalhes_situacao.cat_efetivo == "ATIVO":
                        login(request, user)
                        log_user_action(user, "User logged in", request)
                        messages.success(request, f'Bem-vindo, {user.first_name}!')
                        return redirect('core:index')
                    else:
                        # Se não atender às condições, desativa o usuário e impede o login
                        if user.is_active:
                            user.is_active = False
                            user.save()
                            log_user_action(user, "User deactivated due to invalid Cadastro status", request)
                        messages.error(request, 'Sua conta está inativa ou não atende aos requisitos de acesso. Por favor, entre em contato com o administrador.')
                        # Redireciona para landing com parâmetro para abrir modal de login
                        return redirect(reverse('core:capa') + '?open_login_modal=true')
                else:
                    # Se o usuário não tiver um cadastro associado (caso raro, mas possível)
                    if user.is_active:
                        user.is_active = False
                        user.save()
                        log_user_action(user, "User deactivated due to missing Cadastro association", request)
                    messages.error(request, 'Sua conta não está associada a um cadastro válido. Por favor, entre em contato com o administrador.')
                    # Redireciona para landing com parâmetro para abrir modal de login
                    return redirect(reverse('core:capa') + '?open_login_modal=true')
            else:
                messages.error(request, 'Nome de usuário ou senha inválidos.')
                # Redireciona para landing com parâmetro para abrir modal de login
                return redirect(reverse('core:capa') + '?open_login_modal=true')
        else:
            messages.error(request, 'Nome de usuário ou senha inválidos.')
            # Redireciona para landing com parâmetro para abrir modal de login
            return redirect(reverse('core:capa') + '?open_login_modal=true')
    else:
        # Para requisições GET para /accounts/login/, redireciona para a landing page
        return redirect('core:capa')



from django.contrib import messages
from django.shortcuts import redirect, reverse
from django.contrib.auth import authenticate, login

@require_http_methods(["POST"])
def admin_login(request):
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        if user.is_superuser:
            login(request, user)
            messages.success(request, "Acesso administrativo concedido!")
            return redirect('core:index')
        else:
            messages.error(request, "Acesso restrito a administradores")
    else:
        messages.error(request, "Credenciais inválidas")
    
    # Mantém o email digitado para não precisar digitar novamente
    request.session['admin_login_username'] = username
    return redirect(reverse('core:capa') + '?admin_login_error=1')



@login_required
@require_http_methods(["GET", "POST"])
def force_password_change_view(request):
    if not request.user.must_change_password:
        return redirect('core:index')

    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    
                    # Atualiza TODOS os campos necessários
                    user.must_change_password = False
                    user.last_password_change = timezone.now()
                    user.is_active = True  # Garante que o usuário está ativo
                    user.save()
                    
                    # Atualiza a sessão
                    update_session_auth_hash(request, user)
                    
                    # Limpa a sessão de cadastro se existir
                    if 'cadastro_data_for_signup' in request.session:
                        del request.session['cadastro_data_for_signup']
                    
                    messages.success(request, "Senha alterada com sucesso!")
                    return redirect('core:index')
            except Exception as e:
                logger.error(f"Erro ao atualizar senha: {str(e)}")
                messages.error(request, "Erro ao atualizar senha. Tente novamente.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SetPasswordForm(request.user)
    
    return render(request, 'accounts/force_password_change.html', {
        'form': form,
        'user': request.user
    })



@login_required
def my_logout(request):
    log_user_action(request.user, "User logged out", request)
    logout(request)
    messages.info(request, 'Você foi desconectado com sucesso.')
    return redirect('core:capa')



@login_required
def user_list(request):
    users = User.objects.all().order_by('email')
    return render(request, 'user_list.html', {'users': users})



@login_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    # Verifica se o usuário tem permissão para ver este perfil
    if not request.user.is_superuser and request.user.pk != user.pk:
        messages.error(request, "Você não tem permissão para visualizar este perfil.")
        return redirect('accounts:user_detail', pk=request.user.pk)
    
    # Prepara o contexto com todas as informações necessárias
    context = {
        'user': user,
        'cadastro_info': user.cadastro,
        'last_login': user.last_login,
        'is_online': user.is_online,
        'last_login_ip': user.last_login_ip or "---",
        'last_login_computer_name': user.last_login_computer_name or "---",
        'login_history': user.login_history[-10:][::-1] if user.login_history else [],
    }
    
    return render(request, 'accounts/user_detail.html', context)


@login_required
def user_create(request):
    if not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para criar usuários.")
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST) # Usar CustomUserCreationForm
        if form.is_valid():
            user = form.save()
            log_user_action(request.user, f'Criou o usuário {user.email}', request)
            messages.success(request, 'Usuário criado com sucesso!')
            return redirect('accounts:user_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'user_form.html', {'form': form, 'action': 'create'})

@login_required
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if not request.user.is_superuser and request.user != user:
        messages.error(request, "Você não tem permissão para editar este usuário.")
        return redirect('accounts:user_list')

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            log_user_action(request.user, f'Atualizou o usuário {user.email}', request)
            messages.success(request, 'Usuário atualizado com sucesso!')
            return redirect('accounts:user_detail', pk=user.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = CustomUserChangeForm(instance=user)
    return render(request, 'user_form.html', {'form': form, 'action': 'update', 'user': user})

@login_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para excluir usuários.")
        return redirect('accounts:user_list')

    if request.method == 'POST':
        if str(request.user.pk) == str(pk):
            messages.error(request, "Você não pode excluir sua própria conta.")
            return redirect('accounts:user_list')
        
        password = request.POST.get('password')
        if not request.user.check_password(password):
            messages.error(request, "Senha incorreta. A exclusão foi cancelada.")
            return redirect('accounts:user_detail', pk=pk)

        email_deleted_user = user.email
        user.delete()
        log_user_action(request.user, f'Excluiu o usuário {email_deleted_user}', request)
        messages.success(request, 'Usuário excluído com sucesso!')
        return redirect('accounts:user_list')
    
    return render(request, 'user_confirm_delete.html', {'user': user})


@login_required
def access_history(request, pk):
    user = get_object_or_404(User, pk=pk)
    if not request.user.is_superuser and request.user != user:
        messages.error(request, "Você não tem permissão para visualizar este histórico.")
        return redirect('accounts:user_list')

    login_records = user.login_history
    login_records.reverse()
    for i, record in enumerate(login_records):
        record['counter'] = len(login_records) - i

    return render(request, 'access_history.html', {'user': user, 'login_records': login_records})


@login_required
def all_user_action_history(request):
    if not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para visualizar o histórico de ações de todos os usuários.")
        return redirect('core:index')

    action_logs = UserActionLog.objects.all()
    users = User.objects.all().order_by('email')

    selected_user_id = request.GET.get('user')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    selected_user = None
    if selected_user_id:
        action_logs = action_logs.filter(user__id=selected_user_id)
        selected_user = get_object_or_404(User, id=selected_user_id)

    if start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        if start_date_obj and not is_aware(start_date_obj):
            start_date_obj = timezone.make_aware(start_date_obj)
        action_logs = action_logs.filter(timestamp__gte=start_date_obj)

    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        if end_date_obj and not is_aware(end_date_obj):
            end_date_obj = timezone.make_aware(end_date_obj)
        action_logs = action_logs.filter(timestamp__lte=end_date_obj)

    action_logs = action_logs.order_by('-timestamp')

    return render(request, 'accounts/all_user_action_history.html', {
        'action_logs': action_logs,
        'users': users,
        'selected_user': selected_user,
        'start_date': start_date,
        'end_date': end_date,
    })

@login_required
def user_action_history(request, pk):
    user = get_object_or_404(User, pk=pk)
    if not request.user.is_superuser and request.user != user:
        messages.error(request, "Você não tem permissão para visualizar este histórico.")
        return redirect('accounts:user_list')
        
    action_logs = UserActionLog.objects.filter(user=user).order_by('-timestamp')
    return render(request, 'accounts/user_action_history.html', {'user': user, 'action_logs': action_logs})

