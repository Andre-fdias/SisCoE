from django.test import TestCase
import pytest
from django.urls import reverse

# Create your tests here.

@pytest.mark.django_db
def test_homepage_status_code(client):
    """Testa se a página inicial retorna o status code 200."""
    response = client.get(reverse('core:index'))
    assert response.status_code == 200