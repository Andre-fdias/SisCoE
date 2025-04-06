import io
import csv
from datetime import datetime
from collections import OrderedDict
from django.http import HttpResponse
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
from .models import Cadastro_rpt
from django.utils.html import strip_tags

POSTO_SECAO_MAP = {
    "EM": "EM",
    "703150000 - CMT": "CMT",
    "703159000 - SUB CMT": "SUB CMT",
    "703159100 - SEC ADM": "SEC ADM",
    "703159110 - B/1 E B/5": "B/1 E B/5",
    "703159110-1 - B/5": "B/5",
    "703159120 - AA": "AA",
    "703159130 - B/3 E MOTOMEC": "B/3 E MOTOMEC",
    "703159130-1 - MOTOMEC": "MOTOMEC",
    "703159131 - COBOM": "COBOM",
    "703159140 - B/4": "B/4",
    "703159150 - ST UGE": "ST UGE",
    "703159160 - ST PJMD": "ST PJMD",
    "703159200 - SEC ATIV TEC": "SEC ATIV TEC",
    "1ºSGB": "1ºSGB",
    "703151000 - CMT 1º SGB": "CMT 1º SGB",
    "703151100 - ADM PB CERRADO": "ADM PB CERRADO",
    "703151101 - EB CERRADO": "EB CERRADO",
    "703151102 - EB ZONA NORTE": "EB ZONA NORTE",
    "703151200 - ADM PB SANTA ROSÁLIA": "ADM PB SANTA ROSÁLIA",
    "703151201 - EB SANTA ROSÁLIA": "EB SANTA ROSÁLIA",
    "703151202 - EB ÉDEM": "EB ÉDEM",
    "703151300 - ADM PB VOTORANTIM": "ADM PB VOTORANTIM",
    "703151301 - EB VOTORANTIM": "EB VOTORANTIM",
    "703151302 - EB PIEDADE": "EB PIEDADE",
    "703151800 - ADM 1º SGB": "ADM 1º SGB",
    "2ºSGB": "2ºSGB",
    "703152000 - CMT 2º SGB": "CMT 2º SGB",
    "703152100 - ADM PB ITU": "ADM PB ITU",
    "703152101 - EB ITU": "EB ITU",
    "703152102 - EB PORTO FELIZ": "EB PORTO FELIZ",
    "703152200 - ADM PB SALTO": "ADM PB SALTO",
    "703152201 - EB SALTO": "EB SALTO",
    "703152300 - ADM PB SÃO ROQUE": "ADM PB SÃO ROQUE",
    "703152301 - EB SÃO ROQUE": "EB SÃO ROQUE",
    "703152302 - EB IBIÚNA": "EB IBIÚNA",
    "703152800 - ADM 2º SGB": "ADM 2º SGB",
    "703152900 - NUCL ATIV TEC 2º SGB": "NUCL ATIV TEC 2º SGB",
    "3ºSGB": "3ºSGB",
    "703153000 - CMT 3º SGB": "CMT 3º SGB",
    "703153100 - ADM PB ITAPEVA": "ADM PB ITAPEVA",
    "703153101 - EB ITAPEVA": "EB ITAPEVA",
    "703153102 - EB APIAÍ": "EB APIAÍ",
    "703153103 - EB ITARARÉ": "EB ITARARÉ",
    "703153104 - EB CAPÃO BONITO": "EB CAPÃO BONITO",
    "703153800 - ADM 3º SGB": "ADM 3º SGB",
    "703153900 - NUCL ATIV TEC 3º SGB": "NUCL ATIV TEC 3º SGB",
    "4ºSGB": "4ºSGB",
    "703154000 - CMT 4º SGB": "CMT 4º SGB",
    "703154100 - ADM PB ITAPETININGA": "ADM PB ITAPETININGA",
    "703154101 - EB ITAPETININGA": "EB ITAPETININGA",
    "703154102 - EB BOITUVA": "EB BOITUVA",
    "703154103 - EB ANGATUBA": "EB ANGATUBA",
    "703154200 - ADM PB TATUÍ": "ADM PB TATUÍ",
    "703154201 - EB TATUÍ": "EB TATUÍ",
    "703154202 - EB TIETÊ": "EB TIETÊ",
    "703154203 - EB LARANJAL PAULISTA": "EB LARANJAL PAULISTA",
    "703154800 - ADM 4º SGB": "ADM 4º SGB",
    "703154900 - NUCL ATIV TEC 4º SGB": "NUCL ATIV TEC 4º SGB",
    "5ºSGB": "5ºSGB",
    "703155000 - CMT 5º SGB": "CMT 5º SGB",
    "703155100 - ADM PB BOTUCATU": "ADM PB BOTUCATU",
    "703155101 - EB BOTUCATU": "EB BOTUCATU",
    "703155102 - EB ITATINGA": "EB ITATINGA",
    "703155200 - ADM PB AVARÉ": "ADM PB AVARÉ",
    "703155201 - EB AVARÉ": "EB AVARÉ",
    "703155202 - EB PIRAJU": "EB PIRAJU",
    "703155203 - EB ITAÍ": "EB ITAÍ",
    "703155800 - ADM 5º SGB": "ADM 5º SGB",
    "703155900 - NUCL ATIV TEC 5º SGB": "NUCL ATIV TEC 5º SGB"
}

def export_rpt_data(request, export_format='xlsx', **filters):
    queryset = Cadastro_rpt.objects.all()
    
    if filters.get('status'):
        queryset = queryset.filter(status=filters['status'])
    if filters.get('posto_secao_destino'):
        queryset = queryset.filter(posto_secao_destino=filters['posto_secao_destino'])

    if export_format == 'pdf':
        return export_to_pdf_rpt(request, queryset)
    elif export_format == 'xlsx':
        return export_to_excel_rpt(request, queryset)
    elif export_format == 'csv':
        return export_to_csv_rpt(request, queryset)
    else:
        raise ValueError("Formato de exportação não suportado")

def export_to_pdf_rpt(request, data):
    buffer = io.BytesIO()
    user = request.user

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

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    elements = []

    try:
        logo_path = finders.find('img/logo.png')
        brasao_path = finders.find('img/brasao.png')
        
        logo_esquerda = Image(logo_path, width=12*mm, height=20*mm)
        logo_direita = Image(brasao_path, width=20*mm, height=20*mm)
        
        header_table = Table([
            [logo_esquerda, 
             Paragraph("Relação de Prioridade de Transferência<br/>15º Grupamento de Bombeiros Militar", 
                      styles['Header']), 
             logo_direita]
        ], colWidths=[A4[0]*0.2, A4[0]*0.6, A4[0]*0.2])
        
        elements.append(header_table)
        elements.append(Spacer(1, 10*mm))
    except Exception as e:
        elements.append(Paragraph(f"Erro no cabeçalho: {str(e)}", styles['Normal']))

    styles.add(ParagraphStyle(
        name='SGB',
        fontSize=11,
        leading=13,
        spaceBefore=8*mm,
        textColor=colors.HexColor('#004080'),
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='Posto',
        fontSize=10,
        leading=12,
        spaceBefore=2*mm,
        textColor=colors.HexColor('#606060')
    ))

    table_header = [
        'Posto/Grad', 'RE', 'Nome de Guerra', 
        'SGB Origem', 'Posto Origem',
        'Data Pedido', 'Dias'
    ]

    organized_data = OrderedDict()
    for item in data:
        sgb = POSTO_SECAO_MAP.get(item.sgb_destino, item.sgb_destino)
        posto = POSTO_SECAO_MAP.get(item.posto_secao_destino, item.posto_secao_destino)
        organized_data.setdefault((sgb, posto), []).append(item)

    total_geral = 0
    for (sgb, posto), items in organized_data.items():
        section = []
        
        section.append(Paragraph(sgb, styles['SGB']))
        section.append(Paragraph(posto, styles['Posto']))
        section.append(Spacer(1, 4*mm))

        table_data = [table_header]
        for item in items:
            posto_grad = strip_tags(item.cadastro.promocoes.last().grad) if item.cadastro.promocoes.exists() else '-'
            sgb_origem = POSTO_SECAO_MAP.get(
                item.cadastro.detalhes_situacao.last().sgb, 
                item.cadastro.detalhes_situacao.last().sgb
            ) if item.cadastro.detalhes_situacao.exists() else '-'
            
            posto_origem = POSTO_SECAO_MAP.get(
                item.cadastro.detalhes_situacao.last().posto_secao,
                item.cadastro.detalhes_situacao.last().posto_secao
            ) if item.cadastro.detalhes_situacao.exists() else '-'

            table_data.append([
                posto_grad,
                f'{item.cadastro.re}-{item.cadastro.dig}',
                item.cadastro.nome_de_guerra,
                sgb_origem,
                posto_origem,
                item.data_pedido.strftime('%d/%m/%Y'),
                str((datetime.now().date() - item.data_pedido).days)
            ])

        table = Table(table_data, 
                    colWidths=[25*mm, 20*mm, 35*mm, 20*mm, 30*mm, 20*mm, 15*mm],
                    style=[
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),
                        ('FONTSIZE', (0,0), (-1,-1), 8),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ])
        
        section.append(table)
        section.append(Spacer(1, 5*mm))
        section.append(Paragraph(f"Total: {len(items)}", styles['Posto']))
        
        elements.extend(section)
        total_geral += len(items)
        elements.append(Spacer(1, 10*mm))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        footer_text = (
            f"Emitido por: {user.get_full_name()} | "
            f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
            f"Total geral: {total_geral} | "
            f"Página {doc.page}"
        )
        canvas.drawCentredString(A4[0]/2, 15*mm, footer_text)
        canvas.restoreState()

    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer, "relatorio_rpt.pdf"

def export_to_excel_rpt(request, data):
    buffer = io.BytesIO()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "RPT"

    headers = [
        'Posto/Grad', 'RE', 'Nome de Guerra', 
        'SGB Origem', 'Posto Origem', 
        'Data Pedido', 'Dias'
    ]
    
    ws.append(["RELATÓRIO DE PRIORIDADE DE TRANSFERÊNCIA - 15º GBM"])
    ws.append([f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
    ws.append([f"Emitido por: {request.user.get_full_name()}"])
    ws.append([])
    ws.append(headers)

    for item in data:
        posto_grad = strip_tags(item.cadastro.promocoes.last().grad) if item.cadastro.promocoes.exists() else '-'
        sgb_origem = POSTO_SECAO_MAP.get(
            item.cadastro.detalhes_situacao.last().sgb, 
            item.cadastro.detalhes_situacao.last().sgb
        ) if item.cadastro.detalhes_situacao.exists() else '-'
        
        posto_origem = POSTO_SECAO_MAP.get(
            item.cadastro.detalhes_situacao.last().posto_secao,
            item.cadastro.detalhes_situacao.last().posto_secao
        ) if item.cadastro.detalhes_situacao.exists() else '-'

        ws.append([
            posto_grad,
            f'{item.cadastro.re}-{item.cadastro.dig}',
            item.cadastro.nome_de_guerra,
            sgb_origem,
            posto_origem,
            item.data_pedido.strftime('%d/%m/%Y'),
            (datetime.now().date() - item.data_pedido).days
        ])

    for col in range(1, len(headers)+1):
        column_letter = chr(64 + col)
        ws.column_dimensions[column_letter].width = 20

    wb.save(buffer)
    buffer.seek(0)
    return buffer, "relatorio_rpt.xlsx"

def export_to_csv_rpt(request, data):
    buffer = io.BytesIO()
    buffer.write(b'\xEF\xBB\xBF')
    
    wrapper = io.TextIOWrapper(
        buffer,
        encoding='utf-8-sig',
        newline='',
        write_through=True
    )
    
    writer = csv.writer(wrapper, delimiter=';', quoting=csv.QUOTE_ALL)

    try:
        headers = [
            'Posto/Grad', 'RE', 'Nome de Guerra', 
            'SGB Origem', 'Posto Origem', 
            'Data Pedido', 'Dias'
        ]
        
        writer.writerow(["RELATÓRIO DE PRIORIDADE DE TRANSFERÊNCIA - 15º GBM"])
        writer.writerow([f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
        writer.writerow([f"Emitido por: {request.user.get_full_name()}"])
        writer.writerow([])
        writer.writerow(headers)

        for item in data:
            posto_grad = strip_tags(item.cadastro.promocoes.last().grad) if item.cadastro.promocoes.exists() else '-'
            sgb_origem = POSTO_SECAO_MAP.get(
                item.cadastro.detalhes_situacao.last().sgb, 
                item.cadastro.detalhes_situacao.last().sgb
            ) if item.cadastro.detalhes_situacao.exists() else '-'
            
            posto_origem = POSTO_SECAO_MAP.get(
                item.cadastro.detalhes_situacao.last().posto_secao,
                item.cadastro.detalhes_situacao.last().posto_secao
            ) if item.cadastro.detalhes_situacao.exists() else '-'

            writer.writerow([
                posto_grad,
                f'{item.cadastro.re}-{item.cadastro.dig}',
                item.cadastro.nome_de_guerra,
                sgb_origem,
                posto_origem,
                item.data_pedido.strftime('%d/%m/%Y'),
                (datetime.now().date() - item.data_pedido).days
            ])
            
    finally:
        wrapper.flush()
        buffer.seek(0)

    return buffer, "relatorio_rpt.csv"