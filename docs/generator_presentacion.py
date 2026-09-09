#!/usr/bin/env python
"""Genera la presentacion del TFM (PPTX) y la guia de grabacion (DOCX).

Salidas:
- docs/presentacion_TFM.pptx : 10 diapositivas 16:9 para el video de max 5 min
- docs/guia_grabacion_video.docx : guia cronometrada (desde docs/guia_grabacion_video.md)

La presentacion es regenerable: editar aqui y re-ejecutar.
"""

import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

BASE = Path(__file__).resolve().parent
FIGS = BASE / 'figuras'

# Paleta (coherente con la memoria y el dashboard: azul marino + rojo E15759)
NAVY = RGBColor(0x1F, 0x38, 0x64)
RED = RGBColor(0xE1, 0x57, 0x59)
DARK = RGBColor(0x40, 0x40, 0x40)
GRAY = RGBColor(0x59, 0x59, 0x59)
LIGHT = RGBColor(0xF2, 0xF2, 0xF2)
ROSE = RGBColor(0xFD, 0xEC, 0xEA)   # resalte suave para filas/cajas clave
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN = RGBColor(0x2E, 0x7D, 0x32)

FONT = 'Arial'
SW, SH = Inches(13.333), Inches(7.5)


def _tf(shape, size, color=DARK, bold=False, align=PP_ALIGN.LEFT, italic=False):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    for p in tf.paragraphs:
        p.alignment = align
        for r in p.runs:
            r.font.name = FONT
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.italic = italic
            r.font.color.rgb = color
    return tf


def add_text(slide, l, t, w, h, text, size=16, color=DARK, bold=False,
             align=PP_ALIGN.LEFT, italic=False, anchor=MSO_ANCHOR.TOP, line_spacing=1.0):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    lines = text.split('\n')
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if line_spacing != 1.0:
            p.line_spacing = line_spacing
        r = p.add_run()
        r.text = line
        r.font.name = FONT
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
    return box


def add_bullets(slide, l, t, w, h, items, size=16, color=DARK, spacing=6, bullet_color=None):
    """items: lista de (texto, nivel) o str."""
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        text, level = (item, 0) if isinstance(item, str) else item
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(spacing)
        marker = '\u2022  ' if level == 0 else '\u2013  '
        r = p.add_run()
        r.text = marker + text
        r.font.name = FONT
        r.font.size = Pt(size - (2 if level else 0))
        r.font.color.rgb = color if level == 0 else GRAY
        if bullet_color and level == 0:
            r.font.bold = False
    return box


def add_rect(slide, l, t, w, h, fill=LIGHT, line=None, round_=False, adj=0.12):
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if round_ else MSO_SHAPE.RECTANGLE, l, t, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line:
        shp.line.color.rgb = line
        shp.line.width = Pt(1)
    else:
        shp.line.fill.background()
    if round_:
        try:
            shp.adjustments[0] = adj
        except Exception:
            pass
    shp.shadow.inherit = False
    return shp


def add_title(slide, text, num=None, total=10):
    """Barra de titulo estandar: texto navy + linea roja + pie."""
    add_text(slide, Inches(0.55), Inches(0.28), Inches(11.0), Inches(0.8),
             text, size=27, color=NAVY, bold=True)
    add_rect(slide, Inches(0.58), Inches(1.02), Inches(1.6), Pt(3.2), fill=RED)
    if num is not None:
        add_text(slide, Inches(12.35), Inches(0.34), Inches(0.75), Inches(0.5),
                 f'{num}/{total}', size=11, color=GRAY, align=PP_ALIGN.RIGHT)
    add_text(slide, Inches(0.55), Inches(7.08), Inches(9.5), Inches(0.35),
             'TFM \u00b7 Detecci\u00f3n de patrones de fraude en contratos p\u00fablicos (TED 2018-2023)',
             size=9, color=GRAY, italic=True)


def add_figure(slide, name, l, t, max_w, max_h, border=True):
    path = FIGS / name
    iw, ih = Image.open(path).size
    scale = min(max_w / iw, max_h / ih)
    w, h = int(iw * scale), int(ih * scale)
    # centrar dentro del hueco
    left = l + int((max_w - w) / 2)
    top = t + int((max_h - h) / 2)
    if border:
        add_rect(slide, left - Emu(19050), top - Emu(19050), w + Emu(38100), h + Emu(38100),
                 fill=WHITE, line=RGBColor(0xD0, 0xD0, 0xD0))
    return slide.shapes.add_picture(str(path), left, top, width=w, height=h)


def add_table(slide, l, t, w, headers, rows, col_w=None, size=12, hi_row=None,
              note_col=None):
    n_r, n_c = len(rows) + 1, len(headers)
    gfx = slide.shapes.add_table(n_r, n_c, l, t, w, Inches(0.35 * n_r))
    table = gfx.table
    if col_w:
        total = sum(col_w)
        for i, cw in enumerate(col_w):
            table.columns[i].width = Emu(int(w * cw / total))
    # cabecera
    for j, htxt in enumerate(headers):
        c = table.cell(0, j)
        c.text = htxt
        c.fill.solid()
        c.fill.fore_color.rgb = NAVY
        _tf(c, size, color=WHITE, bold=True)
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
    # filas
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = table.cell(i + 1, j)
            c.text = str(val)
            hi = (hi_row is not None and i == hi_row)
            c.fill.solid()
            c.fill.fore_color.rgb = ROSE if hi else (LIGHT if i % 2 == 0 else WHITE)
            color = RED if (note_col is not None and j == note_col and val.startswith('*')) else DARK
            _tf(c, size, color=color, bold=hi, align=PP_ALIGN.CENTER if j else PP_ALIGN.LEFT)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
    return table


def new_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])  # blank


def chip(slide, l, t, w, big, small, h=Inches(1.05)):
    add_rect(slide, l, t, w, h, fill=LIGHT, round_=True)
    add_text(slide, l + Inches(0.12), t + Inches(0.08), w - Inches(0.24), Inches(0.5),
             big, size=21, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, l + Inches(0.12), t + Inches(0.56), w - Inches(0.24), Inches(0.45),
             small, size=11, color=GRAY, align=PP_ALIGN.CENTER)


# ---------------------------------------------------------------- diapositivas

def s1_portada(prs):
    s = new_slide(prs)
    add_rect(s, 0, 0, SW, Pt(10), fill=NAVY)
    add_rect(s, 0, Inches(2.62), SW, Pt(2.6), fill=RED)
    add_text(s, Inches(0.8), Inches(1.15), Inches(11.7), Inches(1.4),
             'Detecci\u00f3n de Patrones de Fraude en la Adjudicaci\u00f3n\nde Contratos P\u00fablicos de la UE (TED 2018-2023)',
             size=33, color=NAVY, bold=True, align=PP_ALIGN.CENTER, line_spacing=1.1)
    add_text(s, Inches(0.8), Inches(2.95), Inches(11.7), Inches(0.5),
             'Trabajo Fin de M\u00e1ster \u00b7 M\u00e1ster Universitario en Data Science, Big Data y Business Analytics \u00b7 UCM',
             size=15, color=GRAY, align=PP_ALIGN.CENTER)
    add_text(s, Inches(0.8), Inches(4.35), Inches(11.7), Inches(0.6),
             'Fernando Gutiérrez Arenas', size=19, color=DARK, bold=True, align=PP_ALIGN.CENTER)
    add_text(s, Inches(0.8), Inches(4.95), Inches(11.7), Inches(0.5),
             'Curso 2025-2026', size=13, color=GRAY, align=PP_ALIGN.CENTER)
    add_text(s, Inches(0.8), Inches(6.55), Inches(11.7), Inches(0.5),
             '22 *red flags* OCDE + 4 modelos de *machine learning* sobre 4.256.060 adjudicaciones'
             .replace('*', ''), size=12, color=GRAY, italic=True, align=PP_ALIGN.CENTER)


def s2_problema(prs):
    s = new_slide(prs)
    add_title(s, 'El problema y el objetivo', 2)
    add_bullets(s, Inches(0.6), Inches(1.45), Inches(6.9), Inches(3.2), [
        'El fraude en la contrataci\u00f3n p\u00fablica cuesta miles de millones al a\u00f1o a los presupuestos de la UE.',
        'TED publica cada adjudicaci\u00f3n, pero el volumen hace imposible la revisi\u00f3n manual.',
        'No hay etiquetas de fraude confirmado: hay que construir la se\u00f1al de riesgo.',
        'Objetivo: un sistema que priorice autom\u00e1ticamente qu\u00e9 adjudicaciones revisar.',
    ], size=17, spacing=10)
    add_rect(s, Inches(0.6), Inches(4.85), Inches(6.9), Inches(1.55), fill=ROSE, round_=True)
    add_text(s, Inches(0.85), Inches(5.0), Inches(6.4), Inches(1.3),
             'Priorizar, no sentenciar: los *scores* ordenan el trabajo del auditor;'
             .replace('*', '') + '\nla investigaci\u00f3n corresponde a la revisi\u00f3n humana.',
             size=15, color=DARK, bold=True, line_spacing=1.15)
    chip(s, Inches(7.9), Inches(1.5), Inches(4.7), '4.256.060', 'adjudicaciones consolidadas (2018-2023)')
    chip(s, Inches(7.9), Inches(2.75), Inches(4.7), '~7,5 GB', 'CSV originales TED \u00b7 13,9M filas CAN+CN')
    chip(s, Inches(7.9), Inches(4.0), Inches(4.7), '22', 'red flags OCDE (2016) codificadas')
    chip(s, Inches(7.9), Inches(5.25), Inches(4.7), '4 modelos', 'RF \u00b7 Isolation Forest \u00b7 Autoencoder \u00b7 DNN')


def s3_datos(prs):
    s = new_slide(prs)
    add_title(s, 'Datos: de TED crudo a la tabla maestra', 3)
    pasos = [
        ('CSV originales TED', '~7,5 GB \u00b7 13,9M filas (CAN + CN)'),
        ('Limpieza y validaci\u00f3n XSD con PySpark', 'esquema, tipos, nulos'),
        ('Cruce CAN\u2190CN + deduplicaci\u00f3n', 'contratos consolidados'),
        ('Feature engineering', '22 red flags + 5 continuas + ratios'),
        ('Tabla maestra', '4.256.060 \u00d7 69 columnas'),
    ]
    y = Inches(1.5)
    for i, (t1, t2) in enumerate(pasos):
        last = i == len(pasos) - 1
        add_rect(s, Inches(0.7), y, Inches(7.0), Inches(0.82),
                 fill=ROSE if last else LIGHT, round_=True)
        add_text(s, Inches(0.95), y + Inches(0.09), Inches(6.6), Inches(0.35),
                 t1, size=15, color=NAVY if last else DARK, bold=True)
        add_text(s, Inches(0.95), y + Inches(0.44), Inches(6.6), Inches(0.32),
                 t2, size=12, color=GRAY)
        if not last:
            add_text(s, Inches(3.9), y + Inches(0.82), Inches(0.6), Inches(0.3),
                     '\u25bc', size=13, color=RED, align=PP_ALIGN.CENTER)
        y += Inches(1.06)
    add_rect(s, Inches(8.2), Inches(1.5), Inches(4.5), Inches(2.6), fill=WHITE,
             line=RGBColor(0xD0, 0xD0, 0xD0), round_=True)
    add_text(s, Inches(8.45), Inches(1.68), Inches(4.0), Inches(0.4),
             'Etiqueta de riesgo', size=15, color=NAVY, bold=True)
    add_bullets(s, Inches(8.45), Inches(2.15), Inches(4.1), Inches(1.9), [
        'RF_SCORE: suma ponderada de las 22 red flags, normalizada',
        'RF_LABEL: alto riesgo si score \u2265 P95 = 0,3122',
    ], size=13, spacing=8)
    chip(s, Inches(8.2), Inches(4.5), Inches(2.15), '5,23%', 'contratos de alto riesgo')
    chip(s, Inches(10.55), Inches(4.5), Inches(2.15), '222.676', 'positivos en la tabla maestra')
    add_text(s, Inches(8.2), Inches(5.9), Inches(4.5), Inches(0.8),
             'Semilla global 0 en todo el pipeline: resultados reproducibles.',
             size=12, color=GRAY, italic=True)


def s4_eda(prs):
    s = new_slide(prs)
    add_title(s, 'An\u00e1lisis descriptivo: d\u00f3nde est\u00e1 el riesgo', 4)
    add_figure(s, 'fig_rf_score_p95.png', Inches(0.55), Inches(1.35), Inches(6.1), Inches(3.4))
    add_figure(s, 'fig_frecuencia_flags.png', Inches(6.95), Inches(1.35), Inches(5.9), Inches(3.9))
    add_text(s, Inches(0.55), Inches(4.85), Inches(6.1), Inches(0.4),
             'Distribuci\u00f3n del \u00edndice RF_SCORE con el umbral del P95',
             size=11, color=GRAY, italic=True, align=PP_ALIGN.CENTER)
    add_text(s, Inches(6.95), Inches(5.35), Inches(5.9), Inches(0.4),
             'Frecuencia de las 22 red flags OCDE',
             size=11, color=GRAY, italic=True, align=PP_ALIGN.CENTER)
    add_bullets(s, Inches(0.6), Inches(5.7), Inches(12.2), Inches(1.3), [
        'Las red flags m\u00e1s frecuentes son las de acceso a la competencia: sin convocatoria previa, oferta única y adjudicaci\u00f3n directa.',
        'El riesgo no se reparte al azar: pa\u00edses, sectores y tipos de procedimiento con perfiles sistem\u00e1ticamente distintos (86,10% son procedimientos abiertos).',
    ], size=14, spacing=6)


def s5_modelado(prs):
    s = new_slide(prs)
    add_title(s, 'Modelado: cuatro modelos y una alerta', 5)
    headers = ['Modelo', 'Tipo', 'AUROC', 'AUPRC', 'F1']
    rows = [
        ['Random Forest (Spark MLlib)', 'Supervisado distribuido', '0,9979*', '0,9742*', '0,8983*'],
        ['Isolation Forest', 'No supervisado', '0,8205', '0,1894', '0,2617'],
        ['Autoencoder (Keras)', 'No supervisado', '0,8566', '0,2010', '0,3171'],
        ['DNN clasificador (Keras)', 'Supervisado d\u00e9bil', '1,0000*', '1,0000*', '0,9259*'],
    ]
    add_table(s, Inches(0.6), Inches(1.5), Inches(8.1), headers, rows,
              col_w=[2.6, 2.0, 1.1, 1.1, 1.1], size=12.5, note_col=2)
    add_text(s, Inches(0.6), Inches(3.6), Inches(8.0), Inches(0.4),
             '* M\u00e9tricas infladas por circularidad (v\u00e9ase abajo). La etiqueta deriva de las mismas features de entrada.',
             size=11, color=GRAY, italic=True)
    add_rect(s, Inches(0.6), Inches(4.35), Inches(8.1), Inches(2.1), fill=ROSE, round_=True)
    add_text(s, Inches(0.85), Inches(4.55), Inches(7.6), Inches(1.8),
             'El hallazgo cr\u00edtico: circularidad\n'
             'Un AUROC de 1,0000 en datos reales no es normal. RF_LABEL se calcula desde '
             'RF_SCORE, que es la suma de las 22 red flags: exactamente la entrada de la DNN. '
             'El modelo aprende la funci\u00f3n de la etiqueta. Fallo de planteamiento, no de implementaci\u00f3n.',
             size=13.5, color=DARK, line_spacing=1.2)
    chip(s, Inches(9.05), Inches(1.5), Inches(3.6), '0,21 ms', 'por predicci\u00f3n en batch (CPU)')
    chip(s, Inches(9.05), Inches(2.75), Inches(3.6), '5,23%', 'prevalencia de la clase positiva')
    chip(s, Inches(9.05), Inches(4.0), Inches(3.6), '69', 'columnas en la tabla maestra')
    chip(s, Inches(9.05), Inches(5.25), Inches(3.6), '252 s', 'Random Forest sobre 3,4M de train')


def s6_experimentos(prs):
    s = new_slide(prs)
    add_title(s, 'Experimentos sin circularidad: el resultado honesto', 6)
    headers = ['Experimento', 'Entrada', 'AUROC', 'AUPRC', 'F1']
    rows = [
        ['Baseline', '22 red flags (circular)', '1,0000', '1,0000', '0,9259'],
        ['A \u2014 variables crudas', '20 dims num\u00e9ricas + m\u00e1scaras', '0,9576', '0,5148', '0,5427'],
        ['Solo embeddings', 'identidades (comprador, ganador, CPV\u2026)', '0,9446', '0,6817', '0,6261'],
        ['B \u2014 crudas + embeddings', 'combinaci\u00f3n', '0,9846', '0,8292', '0,7278'],
    ]
    add_table(s, Inches(0.6), Inches(1.5), Inches(11.4), headers, rows,
              col_w=[2.4, 3.6, 1.2, 1.2, 1.2], size=12.5, hi_row=3)
    add_bullets(s, Inches(0.65), Inches(3.85), Inches(11.9), Inches(2.9), [
        'La identidad pesa m\u00e1s que la magnitud: solo embeddings (AUPRC 0,68) ya supera a las variables crudas (0,51). El fraude se concentra en actores reincidentes, no en el tama\u00f1o del contrato.',
        'La combinaci\u00f3n gana a cada parte por separado (AUPRC 0,83): las crudas capturan anomal\u00edas de magnitud y los embeddings, anomal\u00edas de identidad.',
        'Resultado principal del trabajo: Experimento B \u2014 AUROC 0,9846 \u00b7 AUPRC 0,8292 \u00b7 F1 0,7278, sin circularidad.',
    ], size=15, spacing=10)


def s7_shap(prs):
    s = new_slide(prs)
    add_title(s, 'Interpretabilidad: explicar cada alerta con SHAP', 7)
    add_figure(s, 'fig_shap_top10.png', Inches(0.55), Inches(1.35), Inches(7.3), Inches(4.6))
    add_text(s, Inches(0.55), Inches(6.1), Inches(7.3), Inches(0.4),
             'Top 10 caracter\u00edsticas por valor SHAP medio absoluto (DNN, GradientExplainer)',
             size=11, color=GRAY, italic=True, align=PP_ALIGN.CENTER)
    add_rect(s, Inches(8.25), Inches(1.6), Inches(4.5), Inches(4.4), fill=LIGHT, round_=True)
    add_bullets(s, Inches(8.5), Inches(1.85), Inches(4.05), Inches(4.0), [
        'El modelo, sin que nadie se lo indicara, coloca arriba las red flags de competencia: sin convocatoria previa (0,03), oferta única (0,0221) y pocas ofertas en contratos de alto valor (0,0156).',
        'Coherente con la literatura OCDE: buena se\u00f1al de que el modelo aprendi\u00f3 el fen\u00f3meno, no ruido.',
        'Cada alerta se descompone en contribuciones: "+0,15 por oferta única, -0,02 por duraci\u00f3n".',
    ], size=14, spacing=12)


def s8_dashboard(prs):
    s = new_slide(prs)
    add_title(s, 'Productivizaci\u00f3n: motor de inferencia y dashboard', 8)
    add_figure(s, 'Dashboard1.png', Inches(0.55), Inches(1.35), Inches(8.3), Inches(4.55))
    add_text(s, Inches(0.55), Inches(6.0), Inches(8.3), Inches(0.4),
             'Vista ejecutiva: KPIs, evoluci\u00f3n anual y mapa de riesgo por pa\u00eds (Tableau Public)',
             size=11, color=GRAY, italic=True, align=PP_ALIGN.CENTER)
    add_rect(s, Inches(9.2), Inches(1.6), Inches(3.55), Inches(4.7), fill=LIGHT, round_=True)
    add_bullets(s, Inches(9.42), Inches(1.85), Inches(3.15), Inches(4.3), [
        'predecir(): score, etiqueta BAJO/MEDIO/ALTO y las red flags activas que justifican la alerta.',
        '0,21 ms por predicci\u00f3n en batch; inferencia online usable en producci\u00f3n.',
        'Dashboard sobre muestra aleatoria de 500.000 contratos (seed 0, proporciones intactas).',
        'Vista ejecutiva + vista de investigaci\u00f3n: decidir qu\u00e9 revisar y por qu\u00e9.',
    ], size=13, spacing=10)


def s9_conclusiones(prs):
    s = new_slide(prs)
    add_title(s, 'Conclusiones, limitaciones y trabajo futuro', 9)
    add_rect(s, Inches(0.6), Inches(1.5), Inches(6.0), Inches(3.3), fill=LIGHT, round_=True)
    add_text(s, Inches(0.85), Inches(1.7), Inches(5.5), Inches(0.4),
             'Conclusiones', size=17, color=NAVY, bold=True)
    add_bullets(s, Inches(0.85), Inches(2.2), Inches(5.55), Inches(2.5), [
        'Sistema completo: de 7,5 GB crudos a alertas explicables.',
        'Se\u00f1al real m\u00e1s all\u00e1 de las red flags (Experimento B).',
        'Herramienta de priorizaci\u00f3n para auditor\u00eda p\u00fablica, con motor de inferencia y dashboard.',
    ], size=13.5, spacing=8)
    add_rect(s, Inches(6.85), Inches(1.5), Inches(5.9), Inches(3.3), fill=WHITE,
             line=RGBColor(0xD0, 0xD0, 0xD0), round_=True)
    add_text(s, Inches(7.1), Inches(1.7), Inches(5.4), Inches(0.4),
             'Limitaciones (asumidas y documentadas)', size=17, color=NAVY, bold=True)
    add_bullets(s, Inches(7.1), Inches(2.2), Inches(5.45), Inches(2.5), [
        'Sin etiquetas reales de fraude: RF_LABEL es un proxy de reglas.',
        'Circularidad detectada y corregida con los experimentos A/B.',
        'Sin validaci\u00f3n con casos judiciales ni bases de OLAF.',
    ], size=13.5, spacing=8)
    add_rect(s, Inches(0.6), Inches(5.1), Inches(12.15), Inches(1.35), fill=ROSE, round_=True)
    add_text(s, Inches(0.85), Inches(5.28), Inches(11.6), Inches(1.0),
             'Trabajo futuro: embeddings de texto sobre los t\u00edtulos de los contratos \u00b7 '
             'validaci\u00f3n con bases externas (OLAF, autoridades nacionales) \u00b7 '
             'despliegue del motor de inferencia con monitorizaci\u00f3n de deriva.',
             size=14.5, color=DARK, line_spacing=1.2)


def s10_cierre(prs):
    s = new_slide(prs)
    add_rect(s, 0, 0, SW, Pt(10), fill=NAVY)
    add_text(s, Inches(0.8), Inches(2.3), Inches(11.7), Inches(1.0),
             'Gracias', size=44, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_text(s, Inches(0.8), Inches(3.55), Inches(11.7), Inches(0.5),
             'Fernando Gutiérrez Arenas \u00b7 M\u00e1ster en Data Science, Big Data y Business Analytics \u00b7 UCM',
             size=15, color=GRAY, align=PP_ALIGN.CENTER)
    add_rect(s, Inches(3.4), Inches(4.6), Inches(6.5), Pt(2.2), fill=RED)
    add_text(s, Inches(0.8), Inches(4.95), Inches(11.7), Inches(0.9),
             'Entregables: memoria + 5 anexos \u00b7 notebook reproducible \u00b7 modelos serializados\n'
             'motor de inferencia \u00b7 dashboard en Tableau Public',
             size=13.5, color=DARK, align=PP_ALIGN.CENTER, line_spacing=1.3)


def build_pptx():
    prs = Presentation()
    prs.slide_width = SW
    prs.slide_height = SH
    for fn in (s1_portada, s2_problema, s3_datos, s4_eda, s5_modelado,
               s6_experimentos, s7_shap, s8_dashboard, s9_conclusiones, s10_cierre):
        fn(prs)
    out = BASE / 'presentacion_TFM.pptx'
    prs.save(out)
    print(f'PPTX generado: {out}')


def build_guia_docx():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'generator_anexos', BASE / 'generator_anexos.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    md = (BASE / 'guia_grabacion_video.md').read_text(encoding='utf-8')
    doc = mod._new_doc()
    mod.render_md(doc, md.splitlines())
    out = BASE / 'guia_grabacion_video.docx'
    doc.save(out)
    print(f'DOCX generado: {out}')


if __name__ == '__main__':
    build_pptx()
    if (BASE / 'guia_grabacion_video.md').exists():
        build_guia_docx()