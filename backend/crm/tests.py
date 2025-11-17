# backend/crm/tests.py
from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse

from backend.crm.forms import ContactForm


class ContactFormTest(TestCase):
    def test_contact_form_valid_data(self):
        """Testa se o formulário é válido com dados corretos"""
        form_data = {
            "name": "João Silva",
            "email": "joao@example.com",
            "title": "Assunto do contato",
            "body": "Mensagem de teste para o formulário de contato.",
        }
        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_contact_form_invalid_data(self):
        """Testa se o formulário é inválido com dados incorretos"""
        # Testa email inválido
        form_data = {
            "name": "João Silva",
            "email": "email-invalido",
            "title": "Assunto do contato",
            "body": "Mensagem de teste.",
        }
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_contact_form_missing_fields(self):
        """Testa se o formulário é inválido quando campos obrigatórios estão faltando"""
        # Testa sem nome
        form_data = {
            "email": "joao@example.com",
            "title": "Assunto do contato",
            "body": "Mensagem de teste.",
        }
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

        # Testa sem email
        form_data = {
            "name": "João Silva",
            "title": "Assunto do contato",
            "body": "Mensagem de teste.",
        }
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_contact_form_field_lengths(self):
        """Testa validação de comprimento dos campos"""
        # Testa nome muito longo
        form_data = {
            "name": "A" * 256,  # Excede max_length=255
            "email": "joao@example.com",
            "title": "Assunto",
            "body": "Mensagem",
        }
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

        # Testa título muito longo
        form_data = {
            "name": "João Silva",
            "email": "joao@example.com",
            "title": "A" * 101,  # Excede max_length=100
            "body": "Mensagem",
        }
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)


class SendContactViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("crm:send_contact")
        self.valid_data = {
            "name": "Maria Santos",
            "email": "maria@example.com",
            "title": "Dúvida sobre o produto",
            "body": "Gostaria de mais informações sobre o produto X.",
        }

    def test_send_contact_post_success(self):
        """Testa envio bem-sucedido do formulário de contato"""
        response = self.client.post(self.url, self.valid_data)

        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)

        # Verifica se o email foi enviado
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Dúvida sobre o produto")
        self.assertEqual(mail.outbox[0].from_email, "maria@example.com")
        self.assertEqual(mail.outbox[0].to, ["localhost"])

    def test_send_contact_get_method_not_allowed(self):
        """Testa que método GET não é permitido"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_send_contact_invalid_form(self):
        """Testa comportamento com formulário inválido"""
        invalid_data = self.valid_data.copy()
        invalid_data["email"] = "email-invalido"  # Email inválido

        response = self.client.post(self.url, invalid_data)

        # Deve retornar erro 400 quando o formulário é inválido
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)  # Nenhum email enviado

    def test_send_contact_missing_data(self):
        """Testa envio com dados faltantes"""
        incomplete_data = {
            "name": "João Silva",
            # email faltando
            "title": "Assunto",
            "body": "Mensagem",
        }

        response = self.client.post(self.url, incomplete_data)

        # Deve retornar erro 400 quando o formulário é inválido
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_contact_email_content(self):
        """Testa o conteúdo do email enviado"""
        self.client.post(self.url, self.valid_data)

        email = mail.outbox[0]
        self.assertEqual(email.subject, "Dúvida sobre o produto")
        self.assertEqual(email.body, "Gostaria de mais informações sobre o produto X.")
        self.assertEqual(email.from_email, "maria@example.com")
        self.assertEqual(email.to, ["localhost"])


# Testes para URLs
class URLsTest(TestCase):
    def test_send_contact_url(self):
        """Testa se a URL de contato está correta"""
        url = reverse("crm:send_contact")
        # A URL inclui o namespace 'crm', então o caminho completo é '/crm/contact/'
        self.assertEqual(url, "/crm/contact/")
