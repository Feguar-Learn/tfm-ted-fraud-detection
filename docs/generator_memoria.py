#!/usr/bin/env python3
"""Genera memoria_TFM.pdf y memoria_TFM.docx desde memoria_TFM.md.

Estilo: A4, Helvetica 10/13 (PDF) y Arial 10pt interlineado 1.15 (DOCX), H2 13, H3 11, imagenes 15cm centradas.
"""
import os
import re

BASE = '/home/thykan/Escritorio/OpenCode/TFM'
MD = os.path.join(BASE, 'docs', 'memoria_TFM.md')
PDF_OUT = os.path.join(BASE, 'docs', 'memoria_TFM.pdf')
DOCX_OUT = os.path.join(BASE, 'docs', 'memoria_TFM.docx')
DOCX_COMBINADO_ANEXOS = os.path.join(BASE, 'docs', 'TFM_memoria_anexos.docx')
FIGDIR = os.path.join(BASE, 'docs')  # rutas relativas tipo figuras/xxx.png


def build_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle, PageBreak, Image, HRFlowable)
    from reportlab.lib.utils import ImageReader

    with open(MD, encoding='utf-8') as f:
        lines = f.read().split('\n')

    st_p = ParagraphStyle('p', fontName='Helvetica', fontSize=10, leading=13,
                          spaceAfter=4)
    st_titulo = ParagraphStyle('titulo', parent=st_p, fontName='Helvetica-Bold',
                               fontSize=15, leading=19, spaceAfter=10)
    st_meta = ParagraphStyle('meta', parent=st_p, fontSize=11, leading=15)
    st_li = ParagraphStyle('li', parent=st_p, leftIndent=10, spaceAfter=1)
    st_num = ParagraphStyle('num', parent=st_p, leftIndent=10, spaceAfter=1)
    st_cap = ParagraphStyle('cap', parent=st_p, fontSize=9, alignment=1,
                            spaceAfter=8)
    st_cell = ParagraphStyle('cell', fontName='Helvetica', fontSize=8.5,
                             leading=10.5)
    st_cellh = ParagraphStyle('cellh', parent=st_cell, fontName='Helvetica-Bold')
    H = {'##': ('Helvetica-Bold', 13, 10, 4), '###': ('Helvetica-Bold', 11, 6, 3)}

    def inline(t):
        t = t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
        t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', t)
        t = re.sub(r'`([^`]+)`', r'<font face="Courier" size="9">\1</font>', t)
        return t

    story = []
    portada = True
    i = 0
    while i < len(lines):
        ln = lines[i]

        # imagen markdown
        m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', ln.strip())
        if m:
            ruta = os.path.join(FIGDIR, m.group(2))
            if os.path.exists(ruta):
                iw, ih = ImageReader(ruta).getSize()
                w = 150 * mm
                h = w * ih / iw
                story.append(Spacer(1, 4))
                story.append(Image(ruta, width=w, height=h))
                story.append(Paragraph(f'<i>{inline(m.group(1))}</i>', st_cap))
            else:
                story.append(Paragraph(f'[figura no encontrada: {ruta}]', st_p))
            i += 1
            continue

        # heading portada (# )
        if ln.startswith('# '):
            story.append(Paragraph(inline(ln[2:]), st_titulo))
            i += 1
            continue

        m = re.match(r'^(##|###)\s+(.*)', ln)
        if m:
            f_, sz, sb, sa = H[m.group(1)]
            story.append(Paragraph(inline(m.group(2)), ParagraphStyle(
                'h', fontName=f_, fontSize=sz, leading=sz + 3.5,
                spaceBefore=sb, spaceAfter=sa)))
            if m.group(1) == '##':
                # tras el indice (primer ## ) salta de pagina
                if portada and 'ndice' in m.group(2):
                    portada = False
                elif portada:
                    portada = False
                    story.append(PageBreak())
                elif 'ndice' in m.group(2):
                    pass
            i += 1
            continue

        if ln.strip() == '---':
            story.append(PageBreak())
            i += 1
            continue

        if ln.startswith('|'):
            rows = [ln]
            while i + 1 < len(lines) and lines[i + 1].startswith('|'):
                i += 1
                rows.append(lines[i])
            cells = [[c.strip() for c in r.strip().strip('|').split('|')]
                     for r in rows]
            cells = [r for r in cells if not all(
                re.fullmatch(r':?-{2,}:?', c or '---') for c in r)]
            if cells:
                data = []
                for ri, row in enumerate(cells):
                    stl = st_cellh if ri == 0 else st_cell
                    data.append([Paragraph(inline(c), stl) for c in row])
                ncols = max(len(r) for r in data)
                data = [r + [''] * (ncols - len(r)) for r in data]
                w = (A4[0] - 32 * mm) / ncols
                t = Table(data, colWidths=[w] * ncols, repeatRows=1)
                t.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#bbbbbb')),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 3),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 3)]))
                story.append(t)
                story.append(Spacer(1, 6))
            i += 1
            continue

        m = re.match(r'^\s*[-*]\s+(.*)', ln)
        if m:
            story.append(Paragraph('&bull; ' + inline(m.group(1)), st_li))
            i += 1
            continue

        m = re.match(r'^\s*(\d+)\.\s+(.*)', ln)
        if m:
            story.append(Paragraph(f'{m.group(1)}. ' + inline(m.group(2)), st_num))
            i += 1
            continue

        if ln.strip():
            story.append(Paragraph(inline(ln), st_p))
        else:
            story.append(Spacer(1, 3))
        i += 1

    doc = SimpleDocTemplate(PDF_OUT, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title='Memoria TFM')
    doc.build(story)
    print('PDF generado:', PDF_OUT)


def build_docx():
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    with open(MD, encoding='utf-8') as f:
        lines = f.read().split('\n')

    doc = Document()
    st = doc.styles['Normal']
    st.font.name = 'Arial'
    st.font.size = Pt(10)
    st.paragraph_format.line_spacing = 1.15

    def add_runs(p, text):
        for part in re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)', text):
            if not part:
                continue
            if part.startswith('**') and part.endswith('**'):
                r = p.add_run(part[2:-2])
                r.bold = True
            elif part.startswith('*') and part.endswith('*') and len(part) > 2:
                r = p.add_run(part[1:-1])
                r.italic = True
            elif part.startswith('`') and part.endswith('`'):
                r = p.add_run(part[1:-1])
                r.font.name = 'Consolas'
                r.font.size = Pt(9)
            else:
                p.add_run(part)

    i = 0
    while i < len(lines):
        ln = lines[i]

        m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', ln.strip())
        if m:
            ruta = os.path.join(FIGDIR, m.group(2))
            if os.path.exists(ruta):
                doc.add_picture(ruta, width=Cm(15))
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(m.group(1))
                r.italic = True
            i += 1
            continue

        if ln.startswith('# '):
            doc.add_heading(ln[2:], 0)
            i += 1
            continue
        m = re.match(r'^(##|###)\s+(.*)', ln)
        if m:
            doc.add_heading(m.group(2), 1 if m.group(1) == '##' else 2)
            i += 1
            continue

        if ln.strip() == '---':
            doc.add_page_break()
            i += 1
            continue

        if ln.startswith('|'):
            rows = [ln]
            while i + 1 < len(lines) and lines[i + 1].startswith('|'):
                i += 1
                rows.append(lines[i])
            cells = [[c.strip() for c in r.strip().strip('|').split('|')]
                     for r in rows]
            cells = [r for r in cells if not all(
                re.fullmatch(r':?-{2,}:?', c or '---') for c in r)]
            if cells:
                ncols = max(len(r) for r in cells)
                table = doc.add_table(rows=len(cells), cols=ncols)
                table.style = 'Table Grid'
                for ri, row in enumerate(cells):
                    for ci in range(ncols):
                        cell = table.cell(ri, ci)
                        cell.text = ''
                        p = cell.paragraphs[0]
                        add_runs(p, row[ci] if ci < len(row) else '')
                        if ri == 0:
                            for r in p.runs:
                                r.bold = True
            i += 1
            continue

        m = re.match(r'^\s*[-*]\s+(.*)', ln)
        if m:
            p = doc.add_paragraph(style='List Bullet')
            add_runs(p, m.group(1))
            i += 1
            continue

        m = re.match(r'^\s*(\d+)\.\s+(.*)', ln)
        if m:
            p = doc.add_paragraph()
            r = p.add_run(m.group(1) + '. ')
            r.bold = True
            add_runs(p, m.group(2))
            i += 1
            continue

        if ln.strip():
            p = doc.add_paragraph()
            add_runs(p, ln.strip())
        i += 1

    doc.save(DOCX_OUT)
    print('DOCX generado:', DOCX_OUT)


def pages_y_cuerpo():
    import pymupdf
    d = pymupdf.open(PDF_OUT)
    total = len(d)
    # No se puede anclar al titulo '1. Introducción...': portada e indice
    # comparten la pagina 1 y el indice contiene los titulos de seccion.
    FRASE_INICIO_CUERPO = 'La elección de este dataset'
    cuerpo_ini = None
    biblio_fin = None
    for n, pg in enumerate(d):
        t = pg.get_text()
        if cuerpo_ini is None and FRASE_INICIO_CUERPO in t:
            cuerpo_ini = n
        if '10. Bibliografía' in t:
            biblio_fin = n
    print(f'TOTAL paginas PDF: {total}')
    print(f'Cuerpo comienza en pagina {cuerpo_ini + 1 if cuerpo_ini is not None else "?"}')
    caras_cuerpo = total - cuerpo_ini if cuerpo_ini is not None else None
    print(f'Caras cuerpo+biblio (debe ser <= 20): {caras_cuerpo}')
    return total, caras_cuerpo


def build_docx_con_anexos():
    """DOCX final: cuerpo de la memoria + portada 'Anexos' + los 6 anexos.

    El combinado de anexos ya trae su propia portada; se reutiliza tal cual,
    insertando solo una hoja separadora. Los anexos no cuentan para el limite
    de 20 caras (cuerpo + bibliografia).
    """
    import copy
    from docx import Document as DocxDocument

    cuerpo = DocxDocument(DOCX_OUT)
    anexos = DocxDocument(DOCX_COMBINADO_ANEXOS)

    cuerpo.add_page_break()
    h = cuerpo.add_heading('Anexos', 0)
    p = cuerpo.add_paragraph()
    r = p.add_run('Documentos adjuntos A-F: calidad de los datos, análisis '
                  'descriptivo, modelado, interpretabilidad, productivización '
                  'y cuaderno de ejecución.')
    r.italic = True

    for el in list(anexos.element.body):
        if el.tag.endswith('}sectPr'):
            continue
        cuerpo.element.body.append(copy.deepcopy(el))

    salida = os.path.join(BASE, 'docs', 'memoria_TFM_con_anexos.docx')
    cuerpo.save(salida)
    print('DOCX con anexos adjuntos:', salida)


if __name__ == '__main__':
    build_pdf()
    build_docx()
    pages_y_cuerpo()
    build_docx_con_anexos()