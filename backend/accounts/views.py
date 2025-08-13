# accounts/views.py
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
    SetPasswordForm 
)
from django.http import  JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from backend.accounts.services import send_mail_to_user, log_user_action, send_generated_password_email
from backend.efetivo.models import Cadastro, DetalhesSituacao, Promocao, Imagem # Certifique-se de que Imagem está importada
from django.contrib.auth import authenticate, update_session_auth_hash, login, logout as auth_logout, get_user_model #
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
import socket
from .models import User, UserActionLog, TermosAceite
from .forms import CustomUserChangeForm, UserPermissionChangeForm# CustomUserCreationForm não será usado diretamente para criar o User aqui
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
from datetime import datetime, timedelta # Importar timedelta
from .decorators import permissao_necessaria, permission_required, group_required

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
    # Verifica se o usuário está autenticado antes de tentar atualizar o histórico
    if request.user.is_authenticated:
        # Atualiza o histórico de login com o tempo de logout
        # Passa o IP e o nome do computador da última sessão registrada
        # Estes são os dados do login atual, que serão usados para encontrar a sessão aberta
        request.user.update_login_history(
            ip=request.user.last_login_ip, # Usa o IP do último login registrado
            computer_name=request.user.last_login_computer_name, # Usa o nome do PC do último login registrado
            logout_time=timezone.now() # Define o tempo de logout
        )
        request.user.is_online = False # Define explicitamente como offline
        # Salva o histórico de login atualizado e o status online
        request.user.save(update_fields=['login_history', 'is_online'])
        log_user_action(request.user, "Fez logout do sistema", request) # Log da ação de logout

    auth_logout(request) # Chama a função de logout do Django
    messages.info(request, "Você saiu da sua conta.")
    return redirect('accounts:login') # Redireciona para a página de login


@permissao_necessaria(level='admin')
@login_required
def user_list(request):
    # Verifica a permissão para visualizar a lista de usuários
    if not request.user.has_permission_level('gestor'): # Apenas gestores e admins podem ver
        messages.error(request, "Você não tem permissão para visualizar a lista de usuários.")
        return redirect('core:index') # Redireciona para uma página de erro ou home

    users = User.objects.all().order_by('email')
    log_user_action(request.user, "Visualizou a lista de usuários", request)
    return render(request, 'accounts/user_list.html', {'users': users})



@login_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    # Verifica permissões
    if not request.user.is_superuser and request.user.pk != user.pk:
        messages.error(request, "Você não tem permissão para visualizar este perfil.")
        return redirect('accounts:user_detail', pk=request.user.pk)
    
    # Gera o contexto
    context = {
        'user': user,
        'cadastro_info': user.cadastro,
        'last_login': user.last_login,
        'is_online': user.is_online,
        'last_login_ip': user.last_login_ip or "---",
        'last_login_computer_name': user.last_login_computer_name or "---",
        'login_history': user.login_history[-10:][::-1] if user.login_history else [],
        'has_termo_aceite': TermosAceite.objects.filter(usuario=user).exists()
    }
    
    return render(request, 'accounts/user_detail.html', context)


import os
import base64
from io import BytesIO
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import Paragraph
from reportlab.lib.utils import ImageReader
from django.conf import settings
from .models import User, TermosAceite

@login_required
def generate_termo_pdf(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if not request.user.is_superuser and request.user.pk != user.pk:
        messages.error(request, "Você não tem permissão para gerar este documento.")
        return redirect('accounts:user_detail', pk=request.user.pk)
    
    termo = TermosAceite.objects.filter(usuario=user).order_by('-data_aceite').first()
    
    if not termo:
        messages.error(request, "Nenhum termo de aceite encontrado.")
        return redirect('accounts:user_detail', pk=pk)
    
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    
    width, height = letter
    margin = 50
    line_height = 12
    y_position = height - margin
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontSize=9, leading=12))
    
    # Cabeçalho: Logo e Título
    try:
        logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'logo-siscoe-light.png')
        pdf.drawImage(logo_path, margin, y_position - 15, width=60, height=25, preserveAspectRatio=True)
    except FileNotFoundError:
        pass
    
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin + 70, y_position - 5, "TERMO DE RESPONSABILIDADE PARA ACESSO AO SISCOE")
    
    y_position -= 40
    
    # Dados Institucionais com o brasão à esquerda
    y_position -= 20
    
    try:
        brasao_path = os.path.join(settings.STATIC_ROOT, 'img', 'brasaoSP.png')
        # Posição do brasão alinhada com o texto
        pdf.drawImage(brasao_path, margin, y_position - 15, width=40, height=40, preserveAspectRatio=True)
    except FileNotFoundError:
        pass
    
    text_x = margin + 50
    text_y = y_position
    
    pdf.setFont("Helvetica", 9)
    pdf.drawString(text_x, text_y, "SECRETARIA DA SEGURANÇA PÚBLICA")
    text_y -= line_height
    pdf.drawString(text_x, text_y, "POLÍCIA MILITAR DO ESTADO DE SÃO PAULO")
    text_y -= line_height
    pdf.drawString(text_x, text_y, f"Sorocaba, {termo.data_aceite.strftime('%d/%m/%Y')}")
    
    y_position = text_y - line_height * 2
    
    # Dados do Militar
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y_position, "IDENTIFICAÇÃO DO MILITAR:")
    y_position -= line_height
    
    pdf.setFont("Helvetica", 9)
    cadastro = user.cadastro
    posto_grad = cadastro.ultima_promocao.posto_grad if hasattr(cadastro, 'ultima_promocao') and cadastro.ultima_promocao else ""
    
    pdf.drawString(margin, y_position, f"Nome: {posto_grad} {cadastro.nome}")
    y_position -= line_height
    pdf.drawString(margin, y_position, f"RE: {cadastro.re}-{cadastro.dig}")
    y_position -= line_height
    pdf.drawString(margin, y_position, f"CPF: {cadastro.cpf}")
    y_position -= line_height * 2
    
    # 1. FINALIDADE
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y_position, "1. FINALIDADE")
    y_position -= line_height
    
    p = Paragraph("O acesso ao sistema é exclusivo para fins institucionais, em conformidade com as atribuições funcionais do usuário e com as disposições da Instrução Policial-Militar I-31-PM (3ª edição, 2022) e da Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018).", styles['Justify'])
    p_width, p_height = p.wrap(width - 2 * margin, height)
    p.drawOn(pdf, margin, y_position - p_height)
    y_position -= p_height + 10
    
    # 2. OBRIGAÇÕES DO USUÁRIO
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y_position, "2. OBRIGAÇÕES DO USUÁRIO")
    y_position -= line_height
    
    declaracao = f"Eu, {posto_grad} {cadastro.re}-{cadastro.dig} {cadastro.nome}, inscrito no CPF {cadastro.cpf}, declaro estar ciente e de acordo com os seguintes termos:"
    p = Paragraph(declaracao, styles['Justify'])
    p_width, p_height = p.wrap(width - 2 * margin, height)
    p.drawOn(pdf, margin, y_position - p_height)
    y_position -= p_height + 10
    
    obrigacoes = [
        "• Utilizar o sistema de forma ética, responsável e em consonância com as normas da PMESP e da LGPD",
        "• Manter a confidencialidade de senhas e credenciais de acesso, sendo integralmente responsável por seu uso",
        "• Não compartilhar, divulgar ou acessar dados sem autorização legal ou institucional",
        "• Não utilizar o sistema para fins ilícitos, difamatórios, políticos, comerciais ou que violem direitos de terceiros",
        "• Comunicar imediatamente ao Oficial de Telemática da OPM qualquer violação de segurança ou uso indevido"
    ]
    
    for item in obrigacoes:
        pdf.setFont("Helvetica", 9)
        pdf.drawString(margin + 10, y_position, item)
        y_position -= line_height
    
    y_position -= line_height
    
    # 3. LGPD
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y_position, "3. LGPD")
    y_position -= line_height
    
    p = Paragraph("Os dados pessoais tratados no sistema estão sujeitos às normas da LGPD, incluindo os princípios de finalidade, adequação, necessidade e transparência. O usuário consente com o tratamento de seus dados pessoais para fins de controle de acesso, auditoria e cumprimento de obrigações legais.", styles['Justify'])
    p_width, p_height = p.wrap(width - 2 * margin, height)
    p.drawOn(pdf, margin, y_position - p_height)
    y_position -= p_height + 10
    
    # 4. AUDITORIA E MONITORAMENTO
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y_position, "4. AUDITORIA E MONITORAMENTO")
    y_position -= line_height
    
    p = Paragraph("A PMESP reserva-se o direito de monitorar e auditar o uso do sistema, conforme previsto no Artigo 7º da I-31-PM. Em caso de irregularidades, o usuário estará sujeito às sanções administrativas, civis e penais cabíveis.", styles['Justify'])
    p_width, p_height = p.wrap(width - 2 * margin, height)
    p.drawOn(pdf, margin, y_position - p_height)
    y_position -= p_height + 10
    
    # 5. PENALIDADES
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y_position, "5. PENALIDADES")
    y_position -= line_height
    
    p = Paragraph("Descumprimento deste termo acarretará medidas disciplinares, conforme o Regulamento Geral da PMESP e a legislação vigente, podendo resultar em suspensão ou cancelamento do acesso, ações disciplinares e medidas legais cabíveis.", styles['Justify'])
    p_width, p_height = p.wrap(width - 2 * margin, height)
    p.drawOn(pdf, margin, y_position - p_height)
    y_position -= p_height + 10
    
    # 6. DISPOSIÇÕES FINAIS
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y_position, "6. DISPOSIÇÕES FINAIS")
    y_position -= line_height
    
    disposicoes = [
        "Este termo entra em vigor na data de sua publicação.",
        "Dúvidas ou esclarecimentos devem ser dirigidos ao 15º Grupamento de Bombeiros via e-mail: 15gb@policiamilitar.sp.gov.br.",
        "Referências Legais:",
        "• I-31-PM (3ª edição, 2022)",
        "• LGPD (Lei nº 13.709/2018)",
        "• Decreto Federal nº 7.845/2012 (sigilo de informações)"
    ]
    
    for item in disposicoes:
        pdf.setFont("Helvetica", 9)
        pdf.drawString(margin if not item.startswith("•") else margin + 10, y_position, item)
        y_position -= line_height
    
    y_position -= line_height * 2
    
    # Declaração de Ciência e Aceite
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y_position, "DECLARAÇÃO DE CIÊNCIA E ACEITE")
    y_position -= line_height
    
    pdf.setFont("Helvetica", 9)
    y_position -= 15
    
    # Desenha a linha para assinatura física e o nome abaixo
    pdf.line(margin, y_position, margin + 200, y_position)
    y_position -= 15 # Espaço para o nome não sobrepor a linha
    pdf.drawString(margin, y_position, f"Nome: {posto_grad} {cadastro.nome} - RE: {cadastro.re}-{cadastro.dig}")
    y_position -= line_height * 2
    
    # Se houver assinatura digital, desenha-a de forma clara
    try:
        signature_data = termo.signature_data
        if signature_data.startswith('data:image'):
            signature_data = signature_data.split(',')[1]
        
        signature_img = ImageReader(BytesIO(base64.b64decode(signature_data)))
        pdf.drawString(margin, y_position, "Assinatura Eletrônica Registrada:")
        y_position -= 40
        pdf.drawImage(signature_img, margin, y_position, width=200, height=40, preserveAspectRatio=True)
        y_position -= 50
    except:
        # Se não houver assinatura digital, apenas ajusta a posição
        y_position -= 20
    
    # Rodapé
    pdf.setFont("Helvetica-Oblique", 8)
    pdf.drawCentredString(width / 2, margin - 20, '"Nós, Policiais Militares, sob a proteção de Deus, estamos compromissados com a Defesa da Vida, da Integridade Física e da Dignidade da Pessoa Humana"')
    
    pdf.save()
    buffer.seek(0)
    
    response = FileResponse(buffer, as_attachment=True, filename=f"termo_aceite_{cadastro.re}.pdf")
    return response

# Views para Histórico

@login_required
def access_history(request, pk):
    user_obj = get_object_or_404(User, pk=pk)

    # Permite que o próprio utilizador ou um superutilizador veja o histórico
    if not (request.user == user_obj or request.user.is_superuser):
        messages.error(request, "Não tem permissão para visualizar este histórico de acessos.")
        return redirect('accounts:user_detail', pk=user_obj.pk)

    # Data limite - 2 meses atrás
    two_months_ago = timezone.now() - timedelta(days=60)
    
    # Agora, o histórico de login vem do campo JSONField do modelo User
    login_history_data = user_obj.login_history if user_obj.login_history else []

    # Processar os dados do histórico para exibição
    processed_login_history = []
    for entry in login_history_data:
        login_time_str = entry.get('login_time')
        logout_time_str = entry.get('logout_time')
        
        login_time = datetime.fromisoformat(login_time_str) if login_time_str else None
        logout_time = datetime.fromisoformat(logout_time_str) if logout_time_str else None

        # Pular registros com data de login anterior a 2 meses
        if login_time and login_time < two_months_ago:
            continue

        duration = None
        if login_time and logout_time:
            delta = logout_time - login_time
            total_seconds = int(delta.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            duration = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
        elif login_time and not logout_time:
            duration = "Ativo" # Sessão ainda ativa

        processed_login_history.append({
            'login_time': login_time,
            'logout_time': logout_time,
            'ip': entry.get('ip'),
            'computer_name': entry.get('computer_name'),
            'duration': duration,
            'status_display': "Online" if logout_time is None else "Offline"
        })
    
    # Ordenar o histórico, se necessário (o JSONField não garante ordem)
    processed_login_history.sort(key=lambda x: x['login_time'] if x['login_time'] else datetime.min, reverse=True)

    context = {
        'user': user_obj,
        'login_history': processed_login_history, # Passa os dados processados
        'history_limit': "2 meses", # Adiciona informação sobre o limite
    }
    log_user_action(request.user, f"Visualizou o histórico de acessos de {user_obj.email}", request)
    return render(request, 'accounts/access_history.html', context)


@login_required
def user_action_history(request, pk):
    user_obj = get_object_or_404(User, pk=pk)

    # Permite que o próprio utilizador ou um superutilizador veja o histórico
    if not (request.user == user_obj or request.user.is_superuser):
        messages.error(request, "Não tem permissão para visualizar este histórico de ações.")
        return redirect('accounts:user_detail', pk=user_obj.pk)

    # Data limite - 2 meses atrás
    two_months_ago = timezone.now() - timedelta(days=60)
    
    # Filtrar ações dos últimos 2 meses
    action_logs = UserActionLog.objects.filter(
        user=user_obj,
        timestamp__gte=two_months_ago
    ).order_by('-timestamp')

    context = {
        'user': user_obj,
        'action_logs': action_logs,
        'history_limit': "2 meses", # Adiciona informação sobre o limite
    }
    log_user_action(request.user, f"Visualizou o histórico de ações de {user_obj.email}", request)
    return render(request, 'accounts/user_action_history.html', context)






# View para alterar permissões de um usuário específico (apenas para Gestores e Admins)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from .models import User
from .forms import UserPermissionChangeForm


@login_required
@permissao_necessaria(level='admin')
def user_permission_update(request, pk):
    user_to_edit = get_object_or_404(User, pk=pk)
    
    # Verificação de permissões
    if request.user == user_to_edit:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Você não pode alterar suas próprias permissões por esta tela.'
            }, status=403)
        messages.error(request, "Você não pode alterar suas próprias permissões por esta tela.")
        return redirect('accounts:user_detail', pk=user_to_edit.pk)
    
    if not request.user.is_superuser:
        if user_to_edit.is_superuser:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Você não tem permissão para alterar as permissões de um superusuário.'
                }, status=403)
            messages.error(request, "Você não tem permissão para alterar as permissões de um superusuário.")
            return redirect('accounts:user_list')
        
        if user_to_edit.permissoes == 'admin' and not request.user.has_permission_level('admin'):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Você não tem permissão para alterar as permissões de um administrador.'
                }, status=403)
            messages.error(request, "Você não tem permissão para alterar as permissões de um administrador.")
            return redirect('accounts:user_list')
        
        if not request.user.has_permission_level('gestor'):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Você não tem permissão para acessar a gestão de permissões de usuários.'
                }, status=403)
            messages.error(request, "Você não tem permissão para acessar a gestão de permissões de usuários.")
            return redirect('accounts:user_list')

    if request.method == 'POST':
        form = UserPermissionChangeForm(request.POST, instance=user_to_edit, current_user=request.user)
        if form.is_valid():
            # Validação adicional para garantir que as permissões não estão sendo alteradas indevidamente
            if user_to_edit.is_superuser and not request.user.is_superuser:
                form.cleaned_data['is_superuser'] = user_to_edit.is_superuser
                form.cleaned_data['is_admin'] = user_to_edit.is_admin
                form.cleaned_data['permissoes'] = user_to_edit.permissoes
            
            elif user_to_edit.permissoes == 'admin' and request.user.has_permission_level('gestor') and not request.user.is_superuser:
                form.cleaned_data['is_admin'] = user_to_edit.is_admin
                form.cleaned_data['permissoes'] = user_to_edit.permissoes

            user = form.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f"Permissões de {user.email} atualizadas com sucesso!",
                    'user': {
                        'is_active': user.is_active,
                        'is_admin': user.is_admin,
                        'is_superuser': user.is_superuser,
                        'permissoes': user.permissoes,
                        'must_change_password': user.must_change_password
                    }
                })
            
            messages.success(request, f"Permissões de {user.email} atualizadas com sucesso!")
            return redirect('accounts:user_list')
        
        # Formulário inválido
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Erro de validação',
                'errors': form.errors
            }, status=400)
        
        messages.error(request, "Erro ao atualizar as permissões. Verifique os dados.")
        return redirect('accounts:user_list')
    
    # Método GET - Não deveria acontecer para AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'Método não permitido'
        }, status=405)
    
    # Se não for AJAX, renderize o template normalmente
    form = UserPermissionChangeForm(instance=user_to_edit, current_user=request.user)
    return render(request, 'accounts/user_permission_update.html', {
        'form': form,
        'user_to_edit': user_to_edit
    })



# View para histórico global de acessos (apenas para Gestores e Admins)

@login_required
@permissao_necessaria(level='admin')
def global_access_history(request):
    if not request.user.has_permission_level('gestor'):
        messages.error(request, "Você não tem permissão para visualizar o histórico de acessos de todos os usuários.")
        return redirect('core:index')

    all_users = User.objects.all().order_by('email')
    
    # Data limite padrão - 2 meses atrás
    two_months_ago = timezone.now() - timedelta(days=60)
    
    # Filtros
    selected_user_id = request.GET.get('user')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Se não houver filtro de data, aplica o limite de 2 meses
    if not start_date_str:
        start_date_obj = two_months_ago
    else:
        start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d')

    filtered_history = []

    # Iterar sobre todos os usuários ou um usuário selecionado
    users_to_process = []
    if selected_user_id:
        try:
            users_to_process.append(User.objects.get(id=selected_user_id))
        except User.DoesNotExist:
            messages.warning(request, "Usuário selecionado para filtro não encontrado.")
    else:
        users_to_process = all_users

    for user_obj in users_to_process:
        login_history_data = user_obj.login_history if user_obj.login_history else []
        for entry in login_history_data:
            login_time_str = entry.get('login_time')
            logout_time_str = entry.get('logout_time')
            
            login_time = datetime.fromisoformat(login_time_str) if login_time_str else None
            logout_time = datetime.fromisoformat(logout_time_str) if logout_time_str else None

            # Pular registros sem data de login ou anteriores ao limite
            if not login_time or login_time < start_date_obj:
                continue

            # Aplicar filtro de data final se especificado
            if end_date_str:
                end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
                if login_time.date() >= end_date_obj.date():
                    continue

            duration = None
            if login_time and logout_time:
                delta = logout_time - login_time
                total_seconds = int(delta.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                duration = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
            elif login_time and not logout_time:
                duration = "Ativo"

            filtered_history.append({
                'user': user_obj,
                'user_email': user_obj.email,
                'user_full_name': user_obj.get_full_name(),
                'login_time': login_time,
                'logout_time': logout_time,
                'ip': entry.get('ip'),
                'computer_name': entry.get('computer_name'),
                'duration': duration,
                'status_display': "Online" if logout_time is None else "Offline"
            })
    
    # Ordenar o histórico pela data de login (mais recente primeiro)
    filtered_history.sort(key=lambda x: x['login_time'] if x['login_time'] else datetime.min, reverse=True)

    context = {
        'all_users': all_users,
        'selected_user_id': selected_user_id,
        'start_date': start_date_obj.strftime('%Y-%m-%d') if not start_date_str else start_date_str,
        'end_date': end_date_str,
        'global_login_history': filtered_history,
        'history_limit': "2 meses (padrão)" if not start_date_str else None,
    }
    log_user_action(request.user, "Visualizou o histórico global de acessos", request)
    return render(request, 'accounts/global_access_history.html', context)


@login_required
@permissao_necessaria(level='admin')
def global_user_action_history(request):
    if not request.user.has_permission_level('gestor'):
        messages.error(request, "Você não tem permissão para visualizar o histórico de ações de todos os usuários.")
        return redirect('core:index')

    all_users = User.objects.all().order_by('email')
    
    # Data limite padrão - 2 meses atrás
    two_months_ago = timezone.now() - timedelta(days=60)
    
    # Inicializa o queryset com o filtro de tempo padrão
    action_logs = UserActionLog.objects.filter(
        timestamp__gte=two_months_ago
    )

    # Filtros
    selected_user_id = request.GET.get('user')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if selected_user_id:
        action_logs = action_logs.filter(user__id=selected_user_id)
    
    # Se houver filtro de data inicial, substitui o limite padrão de 2 meses
    if start_date_str:
        start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d')
        action_logs = action_logs.filter(timestamp__gte=start_date_obj)
    
    if end_date_str:
        end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        action_logs = action_logs.filter(timestamp__lt=end_date_obj)

    action_logs = action_logs.order_by('-timestamp')

    context = {
        'all_users': all_users,
        'selected_user_id': selected_user_id,
        'start_date': start_date_str if start_date_str else two_months_ago.strftime('%Y-%m-%d'),
        'end_date': end_date_str,
        'global_action_logs': action_logs,
        'history_limit': "2 meses (padrão)" if not start_date_str else None,
    }
    log_user_action(request.user, "Visualizou o histórico global de ações", request)
    return render(request, 'accounts/global_user_action_history.html', context)




from django.shortcuts import render
from django.http import HttpResponseForbidden

def acesso_negado(request):
    return render(request, 'accounts/acesso_negado.html', status=403)