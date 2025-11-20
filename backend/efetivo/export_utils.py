import io
from datetime import datetime
from collections import OrderedDict
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    KeepTogether,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from openpyxl import Workbook
import csv
from django.contrib.staticfiles import finders

def export_efetivo_data(request, queryset, format_type):
    """
    Função principal que despacha a exportação para o formato correto.
    """
    # Garante que o queryset está ordenado para o agrupamento
    data = queryset.order_by('detalhes_situacao__sgb', 'detalhes_situacao__posto_secao', 'promocoes__posto_grad', 'nome_de_guerra')

    if format_type == "pdf":
        return export_to_pdf_efetivo(request, data)
    # Outros formatos podem ser adicionados aqui (xlsx, csv)
    # elif format_type == "xlsx":
    #     return export_to_excel_efetivo(request, data)
    # elif format_type == "csv":
    #     return export_to_csv_efetivo(request, data)
    else:
        return HttpResponse("Formato não suportado", status=400)

def export_to_pdf_efetivo(request, data):
    """
    Gera um relatório em PDF para a lista de militares do efetivo.
    """
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="relacao_efetivo.pdf"'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=25 * mm,  # Aumentar margem inferior para o rodapé
    )

    elements = []
    styles = getSampleStyleSheet()

    # Estilos personalizados
    styles.add(ParagraphStyle(name="Header", fontSize=12, leading=14, alignment=1, spaceAfter=4 * mm, fontName="Helvetica-Bold", textColor=colors.HexColor("#002060")))
    styles.add(ParagraphStyle(name="SGB", fontSize=11, leading=13, spaceBefore=8 * mm, textColor=colors.HexColor("#004080"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Posto", fontSize=10, leading=12, spaceBefore=5 * mm, textColor=colors.HexColor("#333333"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Total", fontSize=9, alignment=2, spaceBefore=2 * mm))

    # Função auxiliar para buscar imagens
    def get_image_path(file):
        path = finders.find(f"img/{file}")
        if not path:
            raise FileNotFoundError(f"Arquivo estático img/{file} não encontrado!")
        return path

    # Cabeçalho do documento
    try:
        logo_esquerda = Image(get_image_path("logo.png"), width=12 * mm, height=20 * mm)
        logo_direita = Image(get_image_path("brasao.png"), width=20 * mm, height=20 * mm)
        header_table = Table(
            [[
                logo_esquerda,
                Paragraph("Corpo de Bombeiros do Estado de São Paulo<br/>Comando de Bombeiros do Interior - 1<br/>15º Grupamento de Bombeiros", styles['Header']),
                logo_direita,
            ]],
            colWidths=[doc.width * 0.2, doc.width * 0.6, doc.width * 0.2],
            style=TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]),
        )
        elements.append(header_table)
        elements.append(Spacer(1, 10 * mm))
    except Exception as e:
        elements.append(Paragraph(f"Erro ao carregar cabeçalho: {str(e)}", styles["Normal"]))

    # Organizar dados por SGB e Posto/Seção
    organized_data = OrderedDict()
    for militar in data:
        detalhe = militar.detalhes_situacao.last()
        if detalhe:
            sgb = detalhe.sgb or "SGB não definido"
            posto_secao = detalhe.posto_secao or "Posto/Seção não definido"
            organized_data.setdefault(sgb, OrderedDict()).setdefault(posto_secao, []).append(militar)

    # Construir tabelas
    total_geral = 0
    for sgb, postos in organized_data.items():
        sgb_total = 0
        sgb_elements = [Paragraph(f"<b>SGB:</b> {sgb}", styles["SGB"])]

        for posto_secao, militares in postos.items():
            posto_total = len(militares)
            sgb_total += posto_total
            total_geral += posto_total

            sgb_elements.append(Paragraph(f"<b>Posto/Seção:</b> {posto_secao}", styles["Posto"]))
            
            table_data = [["Posto/Grad", "Nome de Guerra", "RE-Dig", "Situação"]]
            for militar in militares:
                promocao = militar.promocoes.last()
                detalhe = militar.detalhes_situacao.last()
                
                table_data.append([
                    promocao.posto_grad if promocao else "-",
                    militar.nome_de_guerra or "-",
                    f"{militar.re}-{militar.dig}" if militar.re else "-",
                    detalhe.get_situacao_display() if detalhe else "-",
                ])

            table = Table(table_data, colWidths=[30*mm, 60*mm, 30*mm, 50*mm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E0E0E0")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            sgb_elements.append(table)
            sgb_elements.append(Paragraph(f"Total no Posto: {posto_total}", styles["Total"]))
            sgb_elements.append(Spacer(1, 5 * mm))

        elements.append(KeepTogether(sgb_elements))

    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph(f"<b>Total Geral de Militares:</b> {total_geral}", styles["Normal"]))

    # Funções para rodapé e marca d'água
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        user_info = ""
        if hasattr(request.user, "cadastro") and request.user.cadastro:
            cadastro = request.user.cadastro
            posto_grad = getattr(cadastro, "posto_grad", "")
            re = getattr(cadastro, "re", "")
            user_info = f"{posto_grad} {re} {request.user.last_name}"
        else:
            user_info = f"{request.user.get_full_name() or request.user.username}"
        
        canvas.drawCentredString(
            A4[0] / 2, 15 * mm,
            f"Emitido por: {user_info} | {datetime.now().strftime('%d/%m/%Y %H:%M')} | Página {doc.page}"
        )
        canvas.restoreState()

    def add_watermark(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 40)
        canvas.setFillGray(0.9, 0.2)
        text = ""
        if hasattr(request.user, "cadastro") and request.user.cadastro:
            text = getattr(request.user.cadastro, "cpf", "")
        
        angle = 45
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
