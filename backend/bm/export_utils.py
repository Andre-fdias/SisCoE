import io
import os
import csv
from datetime import datetime
from collections import OrderedDict
from django.http import HttpResponse
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, 
    Paragraph, Spacer, KeepTogether, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from openpyxl import Workbook
from django.contrib.staticfiles import finders
import math

def export_bm_data(request, queryset, format_type):
    data = queryset.filter(situacao='Efetivo').order_by('sgb', 'posto_secao', 'nome')
    
    if format_type == 'pdf':
        return export_to_pdf_military(request, data)
    elif format_type == 'xlsx':
        return export_to_excel_military(request, data)
    elif format_type == 'csv':
        return export_to_csv_military(request, data)
    else:
        return HttpResponse("Formato não suportado", status=400)

# ==============================================
# FUNÇÃO PARA EXPORTAÇÃO PDF
# ==============================================
def export_to_pdf_military(request, data):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relacao_efetivo.pdf"'
    
    buffer = io.BytesIO()
    user = request.user
    usuario = user.get_full_name() or user.email or str(user)

    # Configurar estilos
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Header',
        fontSize=12,
        leading=14,
        alignment=1,
        spaceAfter=4*mm,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#002060')
    ))
    
    # Configurar documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    elements = []

    # Função auxiliar para buscar imagens
    def get_image_path(file):
        path = finders.find(f'img/{file}')
        if not path:
            raise FileNotFoundError(f"Arquivo estático img/{file} não encontrado!")
        return path

    # Adicionar cabeçalho com 3 partes
    try:
        logo_esquerda = Image(
            get_image_path('logo.png'),
            width=12*mm,
            height=20*mm
        )
        logo_direita = Image(
            get_image_path('brasao.png'),
            width=20*mm,
            height=20*mm
        )
        
        # Adicionando estilo para alinhar a imagem da esquerda à esquerda
        table_style = TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Alinha a imagem da esquerda ao centro
            ('ALIGN', (1, 0), (1, 0), 'CENTER'), # Centraliza o texto
            ('ALIGN', (2, 0), (2, 0), 'CENTER'),  # Alinha a imagem da direita ao centro
        ])
        
        header_table = Table([
            [logo_esquerda, 
             Paragraph("Corpo de Bombeiros do Estado de São Paulo<br/>Comando de Bombeiros do Interior - 1<br/>15º Grupamento de Bombeiros", 
                       ParagraphStyle(name='Header', alignment=1)), 
             logo_direita]
        ], colWidths=[A4[0]*0.2, A4[0]*0.6, A4[0]*0.2], style=table_style)
        
        elements.append(header_table)
        elements.append(Spacer(1, 10*mm))
    except Exception as e:
        elements.append(Paragraph(f"Erro ao carregar logos ou cabeçalho: {str(e)}", styles['Normal']))

    # Processar dados
    organized_data = OrderedDict()
    for item in data:
        sgb = item.sgb
        posto = item.posto_secao
        organized_data.setdefault(sgb, OrderedDict()).setdefault(posto, []).append(item)

    # Estilos para conteúdo
    styles.add(ParagraphStyle(
        name='SGB',
        fontSize=11,
        leading=13,
        spaceBefore=8*mm,
        textColor=colors.HexColor('#004080')
    ))
    
    styles.add(ParagraphStyle(
        name='Posto',
        fontSize=10,
        leading=12,
        spaceBefore=5*mm,
        textColor=colors.HexColor('#606060')
    ))

    # Adicionar conteúdo
    total_bom = 0
    for sgb, postos in organized_data.items():
        sgb_block = []
        
        sgb_block.append(Paragraph(sgb, styles['SGB']))
        
        for posto, items in postos.items():
            table_data = [
                ['Nome', 'Data Nasc.', 'ESB', 'OVB'],
                *[[item.nome, 
                   item.nasc.strftime('%d/%m/%Y') if item.nasc else '-', 
                   item.esb, 
                   item.ovb] for item in items]
            ]
            
            table = Table(table_data, 
                         colWidths=[70*mm, 25*mm, 20*mm, 25*mm],
                         style=[
                             ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),
                             ('FONTSIZE', (0,0), (-1,-1), 8),
                             ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                             ('LEADING', (0,0), (-1,-1), 9),
                         ])
            
            sgb_block.extend([
                Paragraph(posto, styles['Posto']),
                table,
                Paragraph(f"Total {posto}: {len(items)}", ParagraphStyle(
                    name='TotalPosto',
                    fontSize=9,
                    alignment=2,
                    spaceBefore=2*mm
                )),
                Spacer(1, 5*mm)
            ])
            total_bom += len(items)
        
        sgb_block.append(Paragraph(
            f"Total {sgb}: {sum(len(items) for items in postos.values())}",
            ParagraphStyle(
                name='TotalSGB',
                fontSize=10,
                alignment=2,
                textColor=colors.HexColor('#004080'),
                spaceBefore=5*mm
            )
        ))
        
        elements.append(KeepTogether(sgb_block))
        elements.append(Spacer(1, 10*mm))

    # Adicionar total geral
    elements.append(Paragraph(f"Total de Bombeiros Municipais: {total_bom}", styles['Normal']))

    # Rodapé
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        
        # CORREÇÃO: Verificar se profile existe de forma mais segura
        user_info = ""
        if hasattr(request.user, 'profile') and request.user.profile:
            posto_grad = getattr(request.user.profile, 'posto_grad', '')
            re = getattr(request.user.profile, 're', '')
            dig = getattr(request.user.profile, 'dig', '')
            cpf = getattr(request.user.profile, 'cpf', '')
            user_info = f"{posto_grad} {re}-{dig} {request.user.last_name}"
        else:
            user_info = f"{request.user.get_full_name() or request.user.username}"
        
        canvas.drawCentredString(
            A4[0]/2, 
            15*mm, 
            f"Emitido por: {user_info} | {datetime.now().strftime('%d/%m/%Y %H:%M')} | Página {doc.page} | Total de Bombeiros Municipais: {total_bom}"
        )
        canvas.restoreState()
    
    def add_watermark(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 40)
        canvas.setFillGray(0.9, 0.2)  # Cor e transparência da marca d'água
        
        # Desenha a marca d'água repetidamente na diagonal
        text = request.user.profile.cpf if hasattr(request.user, 'profile') and request.user.profile else ''
        angle = 45  # Ângulo da diagonal
        
        for x in range(-500, int(A4[0] * 2), 300):
            for y in range(-500, int(A4[1] * 2), 200):
                canvas.saveState()
                canvas.translate(x, y)
                canvas.rotate(angle)
                canvas.drawCentredString(0, 0, text)
                canvas.restoreState()
        canvas.restoreState()

    def on_page(canvas, doc):
        footer(canvas, doc)
        add_watermark(canvas, doc)
        
    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

# ==============================================
# FUNÇÃO PARA EXPORTAÇÃO EXCEL
# ==============================================
def export_to_excel_military(request, data):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="relacao_efetivo.xlsx"'
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Efetivo"
    
    # Cabeçalho
    ws.append(["15º GRUPAMENTO DE BOMBEIROS MILITARES - RELAÇÃO DE EFETIVO"])
    ws.append([f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
    ws.append([f"Emitido por: {request.user.get_full_name()}"])
    ws.append([])
    
    # Organizar dados
    organized_data = OrderedDict()
    for item in data:
        sgb = item.sgb
        posto = item.posto_secao
        organized_data.setdefault(sgb, OrderedDict()).setdefault(posto, []).append(item)
    
    # Preencher planilha
    for sgb, postos in organized_data.items():
        ws.append([sgb])
        
        for posto, items in postos.items():
            ws.append([posto])
            ws.append(['Nome', 'Data Nascimento', 'ESB', 'OVB'])
            
            for item in items:
                ws.append([
                    item.nome,
                    item.nasc.strftime('%d/%m/%Y') if item.nasc else '',
                    item.esb,
                    item.ovb
                ])
            
            ws.append([f"Total {posto}: {len(items)}"])
            ws.append([])
        
        ws.append([f"Total {sgb}: {sum(len(items) for items in postos.values())}"])
        ws.append([])
    
    wb.save(response)
    return response

# ==============================================
# FUNÇÃO PARA EXPORTAÇÃO CSV
# ==============================================
def export_to_csv_military(request, data):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="relacao_efetivo.csv"'
    
    writer = csv.writer(response, delimiter=';')
    
    # Cabeçalho
    writer.writerow(["15º GRUPAMENTO DE BOMBEIROS MILITARES - RELAÇÃO DE EFETIVO"])
    writer.writerow([f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
    writer.writerow([f"Emitido por: {request.user.get_full_name()}"])
    writer.writerow([])
    
    # Organizar dados
    organized_data = OrderedDict()
    for item in data:
        sgb = item.sgb
        posto = item.posto_secao
        organized_data.setdefault(sgb, OrderedDict()).setdefault(posto, []).append(item)
    
    # Preencher CSV
    for sgb, postos in organized_data.items():
        writer.writerow([f"SGB: {sgb}"])
        
        for posto, items in postos.items():
            writer.writerow([f"Posto/Seção: {posto}"])
            writer.writerow(['Nome', 'Data Nascimento', 'ESB', 'OVB'])
            
            for item in items:
                writer.writerow([
                    item.nome,
                    item.nasc.strftime('%d/%m/%Y') if item.nasc else '',
                    item.esb,
                    item.ovb
                ])
            
            writer.writerow([f"Total {posto}: {len(items)}"])
            writer.writerow([])
        
        writer.writerow([f"Total {sgb}: {sum(len(items) for items in postos.values())}"])
        writer.writerow([])
    
    return response