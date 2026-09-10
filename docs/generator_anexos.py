#!/usr/bin/env python3
"""Genera los DOCX de los anexos desde los MD de docs/.

Salidas:
- TFM_memoria_anexos.docx  : los cinco anexos combinados (portada + salto de pagina entre anexos).
- anexo_A..E_*.docx        : un DOCX individual por anexo, para corregir por separado en Windows.

Estilo: A4, Arial 10pt interlineado 1.15 (igual que memoria_TFM.docx), imagenes 15cm
centradas con pie en cursiva.

Convenciones de los MD de anexos (difieren de la memoria):
- `---` separa secciones dentro de un anexo: NO es salto de pagina (solo se pagina entre anexos).
- Los bloques de codigo (```) se muestran en Consolas sin interpretar markdown inline.
- Las lineas `> ` son citas: parrafo con sangria y cursiva.
"""
import os
import re

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE = '/home/thykan/Escritorio/OpenCode/TFM'
DOCS = os.path.join(BASE, 'docs')
FIGDIR = DOCS  # rutas relativas tipo figuras/xxx.png
ANEXOS = [
    'anexo_A_calidad_datos.md',
    'anexo_B_eda.md',
    'anexo_C_modelado.md',
    'anexo_D_interpretabilidad.md',
    'anexo_E_productivizacion.md',
    'anexo_F_notebook.md',
]
DOCX_COMBINADO = os.path.join(DOCS, 'TFM_memoria_anexos.docx')

TITULO_MEMORIA = ('Detección de Patrones de Fraude en la Adjudicación de Contratos '
                  'Públicos de la Unión Europea (TED 2018-2023)')
META = [
    'Trabajo Fin de Máster — Anexos',
    'Máster Universitario en Data Science, Big Data y Business Analytics (UCM Online)',
    'Autor: Fernando Gutiérrez Arenas',
    'Tutores: Carlos Ortega, Santiago Mota',
    'Fecha: Septiembre 2026',
]


def _new_doc():
    doc = Document()
    st = doc.styles['Normal']
    st.font.name = 'Arial'
    st.font.size = Pt(10)
    st.paragraph_format.line_spacing = 1.15
    return doc


def add_inline(p, text, bold=False, italic=False, code_pt=Pt(9)):
    """Renderiza markdown inline tolerando negrita con cursiva anidada.

    Los spans `codigo` se apartan antes de dividir por negrita/cursiva para que
    un `**texto con `codigo` dentro**` no rompa el analisis.
    """
    stashes = []

    def stash(m):
        stashes.append(m.group(1))
        return f'\x00{len(stashes) - 1}\x00'

    text = re.sub(r'`([^`]+)`', stash, text)

    def emit_code(run_text, b, it):
        r = p.add_run(run_text)
        r.bold = b
        r.italic = it
        r.font.name = 'Consolas'
        if code_pt:
            r.font.size = code_pt

    def flush(s, b, it):
        m = re.fullmatch(r'\x00(\d+)\x00', s)
        if m:
            emit_code(stashes[int(m.group(1))], b, it)
            return
        for s2 in re.split(r'(\*\*(?:[^*]|\*(?!\*))+?\*\*)', s):
            if not s2:
                continue
            if s2.startswith('**') and s2.endswith('**') and len(s2) > 4:
                flush_inner(s2[2:-2], True, it)
            else:
                flush_inner(s2, b, it)

    def flush_inner(s, b, it):
        m = re.fullmatch(r'\x00(\d+)\x00', s)
        if m:
            emit_code(stashes[int(m.group(1))], b, it)
            return
        for s3 in re.split(r'(\*[^*]+\*)', s):
            if not s3:
                continue
            if s3.startswith('*') and s3.endswith('*') and len(s3) > 2:
                r = p.add_run(s3[1:-1])
                r.bold = b
                r.italic = True
            else:
                for s4 in re.split(r'(\x00\d+\x00)', s3):
                    if not s4:
                        continue
                    m2 = re.fullmatch(r'\x00(\d+)\x00', s4)
                    if m2:
                        emit_code(stashes[int(m2.group(1))], b, it)
                    else:
                        r = p.add_run(s4)
                        r.bold = b
                        r.italic = it

    flush(text, bold, italic)


def render_md(doc, lines):
    """Vuelca las lineas de un anexo en doc, interpretando el subconjunto de markdown usado."""
    i = 0
    en_codigo = False
    while i < len(lines):
        ln = lines[i]

        # bloque de codigo: lineas literales en Consolas
        if ln.strip().startswith('```'):
            en_codigo = not en_codigo
            i += 1
            continue
        if en_codigo:
            p = doc.add_paragraph()
            r = p.add_run(ln if ln.strip() else ' ')
            r.font.name = 'Consolas'
            r.font.size = Pt(8.5)
            i += 1
            continue

        m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', ln.strip())
        if m:
            ruta = os.path.join(FIGDIR, m.group(2))
            if os.path.exists(ruta):
                doc.add_picture(ruta, width=Cm(15))
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(m.group(1))
                r.italic = True
            else:
                p = doc.add_paragraph()
                r = p.add_run(f'[figura no encontrada: {ruta}]')
                r.italic = True
            i += 1
            continue

        if ln.startswith('# '):
            h = doc.add_heading('', 0)
            add_inline(h, ln[2:], code_pt=None)
            i += 1
            continue
        m = re.match(r'^(##|###)\s+(.*)', ln)
        if m:
            h = doc.add_heading('', 1 if m.group(1) == '##' else 2)
            add_inline(h, m.group(2), code_pt=None)
            i += 1
            continue

        if ln.strip() == '---':
            i += 1
            continue

        if ln.startswith('>'):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.75)
            add_inline(p, ln.lstrip('> ').strip(), italic=True)
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
                        p = cell.paragraphs[0]
                        add_inline(p, row[ci] if ci < len(row) else '')
                        if ri == 0:
                            for r in p.runs:
                                r.bold = True
            i += 1
            continue

        m = re.match(r'^\s*[-*]\s+(.*)', ln)
        if m:
            p = doc.add_paragraph(style='List Bullet')
            add_inline(p, m.group(1))
            i += 1
            continue

        m = re.match(r'^\s*(\d+)\.\s+(.*)', ln)
        if m:
            p = doc.add_paragraph()
            r = p.add_run(m.group(1) + '. ')
            r.bold = True
            add_inline(p, m.group(2))
            i += 1
            continue

        if ln.strip():
            p = doc.add_paragraph()
            add_inline(p, ln.strip())
        i += 1


def _leer(nombre):
    with open(os.path.join(DOCS, nombre), encoding='utf-8') as f:
        return f.read().split('\n')


def build_combinado():
    doc = _new_doc()
    doc.add_heading(TITULO_MEMORIA, 0)
    for i, ln in enumerate(META):
        p = doc.add_paragraph()
        add_inline(p, ln, bold=(i == 0))
    doc.add_page_break()

    primero = True
    for nombre in ANEXOS:
        if not primero:
            doc.add_page_break()
        primero = False
        render_md(doc, _leer(nombre))

    doc.save(DOCX_COMBINADO)
    print('DOCX combinado generado:', DOCX_COMBINADO)


def build_individuales():
    for nombre in ANEXOS:
        doc = _new_doc()
        render_md(doc, _leer(nombre))
        salida = os.path.join(DOCS, nombre.replace('.md', '.docx'))
        doc.save(salida)
        print('DOCX individual generado:', salida)


if __name__ == '__main__':
    build_combinado()
    build_individuales()