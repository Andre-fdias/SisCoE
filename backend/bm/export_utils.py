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

def export_bm_data(request, queryset, format_type):  # ← Nome principal corrigido
    try:
        if format_type == 'pdf':
            return export_to_pdf_bm(request, queryset)
        elif format_type == 'xlsx':
            return export_to_excel_bm(request, queryset)
        elif format_type == 'csv':
            return export_to_csv_bm(request, queryset)
        else:
            return HttpResponse("Formato não suportado", status=400)
    except Exception as e:
        return HttpResponse(f"Erro na exportação: {str(e)}", status=500)

def export_to_pdf_rpt(request, data):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="solicitacoes_rpt.pdf"'
    
    buffer = io.BytesIO()
    user = request.user

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

    # Cabeçalho
    try:
        logo_path = finders.find('img/logo.png')
        brasao_path = finders.find('img/brasao.png')
        
        logo_esquerda = Image(logo_path, width=12*mm, height=20*mm)
        logo_direita = Image(brasao_path, width=20*mm, height=20*mm)
        
        header_table = Table([
            [logo_esquerda, 
             Paragraph("15º Grupamento de Bombeiros Militar<br/>Solicitações de Alteração de Local", 
                      styles['Header']), 
             logo_direita]
        ], colWidths=[A4[0]*0.2, A4[0]*0.6, A4[0]*0.2])
        
        elements.append(header_table)
        elements.append(Spacer(1, 10*mm))
    except Exception as e:
        elements.append(Paragraph(f"Erro no cabeçalho: {str(e)}", styles['Normal']))

    # Organizar dados
    organized_data = OrderedDict()
    for item in data:
        sgb = item.sgb_destino
        posto = item.posto_secao_destino
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
    total_rpt = 0
    for sgb, postos in organized_data.items():
        sgb_block = []
        
        sgb_block.append(Paragraph(sgb, styles['SGB']))
        
        for posto, items in postos.items():
            table_data = [
                ['RE', 'Nome', 'Posto/Seção Atual', 'Destino', 'Data Pedido', 'Dias'],
                *[[
                    f'{item.cadastro.re}-{item.cadastro.dig}',
                    item.cadastro.nome_de_guerra,
                    item.cadastro.detalhes_situacao.last().posto_secao if item.cadastro.detalhes_situacao.exists() else '-',
                    f'{item.sgb_destino} - {item.posto_secao_destino}',
                    item.data_pedido.strftime('%d/%m/%Y'),
                    (datetime.now().date() - item.data_pedido).days
                ] for item in items]
            ]
            
            table = Table(table_data, 
                         colWidths=[25*mm, 40*mm, 40*mm, 50*mm, 25*mm, 20*mm],
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
            total_rpt += len(items)
        
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

    # Rodapé
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        
        # Informações do usuário
        user_info = ""
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            user_info = f"{profile.posto_grad} {profile.re}-{profile.dig} {request.user.last_name}"
        
        canvas.drawCentredString(
            A4[0]/2, 
            15*mm, 
            f"Emitido por: {user_info} | {datetime.now().strftime('%d/%m/%Y %H:%M')} | Página {doc.page} | Total de Solicitações: {total_rpt}"
        )
        canvas.restoreState()

    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

def export_to_excel_rpt(request, data):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="solicitacoes_rpt.xlsx"'
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Solicitações RPT"

    # Cabeçalho
    ws.append(["15º GRUPAMENTO DE BOMBEIROS - SOLICITAÇÕES DE ALTERAÇÃO DE LOCAL"])
    ws.append([f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
    ws.append([f"Emitido por: {request.user.get_full_name()}"])
    ws.append([])

    # Organizar dados
    organized_data = OrderedDict()
    for item in data:
        sgb = item.sgb_destino
        posto = item.posto_secao_destino
        organized_data.setdefault(sgb, OrderedDict()).setdefault(posto, []).append(item)

    # Preencher planilha
    for sgb, postos in organized_data.items():
        ws.append([f"SGB: {sgb}"])
        
        for posto, items in postos.items():
            ws.append([f"Posto/Seção: {posto}"])
            ws.append(['RE', 'Nome', 'Posto Atual', 'Destino', 'Data Pedido', 'Dias'])
            
            for item in items:
                ws.append([
                    f'{item.cadastro.re}-{item.cadastro.dig}',
                    item.cadastro.nome_de_guerra,
                    item.cadastro.detalhes_situacao.last().posto_secao if item.cadastro.detalhes_situacao.exists() else '-',
                    f'{item.sgb_destino} - {item.posto_secao_destino}',
                    item.data_pedido.strftime('%d/%m/%Y'),
                    (datetime.now().date() - item.data_pedido).days
                ])
            
            ws.append([f"Total {posto}: {len(items)}"])
            ws.append([])
        
        ws.append([f"Total {sgb}: {sum(len(items) for items in postos.values())}"])
        ws.append([])
    
    wb.save(response)
    return response

def export_to_csv_rpt(request, data):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="solicitacoes_rpt.csv"'
    response.write(u'\ufeff'.encode('utf8'))  # BOM para UTF-8
    
    writer = csv.writer(response, delimiter=';')
    
    # Cabeçalho
    writer.writerow(["15º GRUPAMENTO DE BOMBEIROS - SOLICITAÇÕES DE ALTERAÇÃO DE LOCAL"])
    writer.writerow([f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
    writer.writerow([f"Emitido por: {request.user.get_full_name()}"])
    writer.writerow([])

    # Organizar dados
    organized_data = OrderedDict()
    for item in data:
        sgb = item.sgb_destino
        posto = item.posto_secao_destino
        organized_data.setdefault(sgb, OrderedDict()).setdefault(posto, []).append(item)

    # Preencher CSV
    for sgb, postos in organized_data.items():
        writer.writerow([f"SGB: {sgb}"])
        
        for posto, items in postos.items():
            writer.writerow([f"Posto/Seção: {posto}"])
            writer.writerow(['RE', 'Nome', 'Posto Atual', 'Destino', 'Data Pedido', 'Dias'])
            
            for item in items:
                writer.writerow([
                    f'{item.cadastro.re}-{item.cadastro.dig}',
                    item.cadastro.nome_de_guerra,
                    item.cadastro.detalhes_situacao.last().posto_secao if item.cadastro.detalhes_situacao.exists() else '-',
                    f'{item.sgb_destino} - {item.posto_secao_destino}',
                    item.data_pedido.strftime('%d/%m/%Y'),
                    (datetime.now().date() - item.data_pedido).days
                ])
            
            writer.writerow([f"Total {posto}: {len(items)}"])
            writer.writerow([])
        
        writer.writerow([f"Total {sgb}: {sum(len(items) for items in postos.values())}"])
        writer.writerow([])
    
    return response