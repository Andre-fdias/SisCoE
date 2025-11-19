# image_utils.py (ou o nome do seu arquivo utils.py)
from PIL import Image, ImageDraw, ImageFont
import os
from io import BytesIO
import json
import logging
import random
from faker import Faker
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction, models
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import Cadastro, Promocao, DetalhesSituacao, CatEfetivo, Imagem

logger = logging.getLogger(__name__)
User = get_user_model()


def add_cpf_to_image(image_path, cpf, output_path):
    # Abra a imagem
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    # Defina a fonte e o tamanho do texto
    font_path = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Caminho para a fonte
    )
    # Verifique se a fonte existe, caso contrário use uma fonte padrão
    if not os.path.exists(font_path):
        font_path = "arial.ttf"  # Exemplo de fonte genérica no Windows
        try:
            # Tenta carregar uma fonte padrão do Pillow
            font = ImageFont.truetype(font_path, 36)
        except IOError:
            # Fallback para a fonte padrão do Pillow se arial.ttf não for encontrada
            font = ImageFont.load_default()
    else:
        font = ImageFont.truetype(font_path, 36)

    # Defina a posição do texto
    text_position = (10, 10)  # Posição (x, y) do texto na imagem

    # Adicione o texto na imagem
    draw.text(text_position, cpf, font=font, fill="red")

    # Salve a imagem com o CPF
    image.save(output_path)


def generate_fake_image(text="Fake Image", width=400, height=300):
    """Gera uma imagem simples com texto para uso em cadastros fake."""
    img = Image.new("RGB", (width, height), color=(73, 109, 137))
    d = ImageDraw.Draw(img)

    # Tenta carregar uma fonte. Use uma fonte padrão se a específica não for encontrada.
    try:
        font = ImageFont.truetype(
            "arial.ttf", 30
        )  # Substitua por um caminho de fonte real se disponível
    except IOError:
        font = ImageFont.load_default()  # Fallback para fonte padrão

    text_color = (255, 255, 255)  # Branco

    # Centralizar texto
    bbox = d.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) / 2
    y = (height - text_height) / 2

    d.text((x, y), text, fill=text_color, font=font)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
