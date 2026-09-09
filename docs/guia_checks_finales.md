# Guía de checks finales antes de la entrega

Esta guía recorre, en orden, todas las verificaciones que deben salir en verde antes de entregar el TFM y publicar el repositorio: documentos, vídeo, reproducibilidad del notebook y estado del repo. Está pensada para ejecutarse de una vez el día de la entrega (30-60 minutos, sin contar la ejecución completa del notebook).

## 1. Placeholders y datos personales

| Dónde | Qué comprobar | Hecho |
|---|---|---|
| `README.md` | Sin `[Nombre Apellido1 Apellido2]` en la portada ni `<usuario>/<repo>` en la URL de clonado | ☐ |
| `LICENSE` | Nombre real en el copyright (sustituir el placeholder) | ☐ |
| `docs/presentacion_TFM.pptx` | Nombre real en las diapositivas 1 y 10 | ☐ |
| `docs/memoria_TFM.docx` | Portada con nombre, título y convocatoria correctos | ☐ |
| Todos los DOCX | Sin "TODO", "XXX" ni texto provisional | ☐ |

## 2. Documentos: regenerados y verificados

Los DOCX se generan desde los `.md` (fuente de la verdad). Si se ha tocado cualquier `.md`, regenerar todo y repetir el barrido:

```bash
env_analytics/bin/python docs/generator_memoria.py       # memoria_TFM.docx/pdf
env_analytics/bin/python docs/generator_anexos.py        # 5 anexos + combinado
env_analytics/bin/python docs/generator_presentacion.py  # PPTX + guía de grabación
```

Barrido de caracteres corruptos sobre los 7 DOCX (memoria + 5 anexos + combinado). Debe salir `OK` en todo:

```bash
env_analytics/bin/python - <<'EOF'
import re, glob
from docx import Document
files = ['docs/memoria_TFM.docx'] + sorted(glob.glob('docs/anexo_[A-E]_*.docx')) + ['docs/TFM_memoria_anexos.docx']
ok = True
for f in files:
    doc = Document(f)
    full = '\n'.join([p.text for p in doc.paragraphs] +
                     [c.text for t in doc.tables for r in t.rows for c in r.cells])
    issues = []
    if re.search(r'[\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF\uFF00-\uFFEF]', full): issues.append('CJK')
    if full.count(chr(96)): issues.append('backtick')
    if full.count(chr(0)): issues.append('NUL')
    if 'tablón' in full.lower(): issues.append('tablón')
    bad = [m.group(0) for m in re.finditer(r'\*+', full) if 'RF_*' not in full[max(0,m.start()-30):m.end()+10]]
    if bad: issues.append(f'asteriscos={bad[:3]}')
    if re.findall(r'\b(nosotros|nuestra|hice|hemos|quiero)\b', full, re.I): issues.append('1a persona')
    print(f"{f.split('/')[-1]:42s} {'OK' if not issues else 'FALLO: ' + ', '.join(issues)}")
    ok = ok and not issues
print('=== TODO OK ===' if ok else '=== CORREGIR Y REGENERAR ===')
EOF
```

Criterios de aceptación por documento:

- ☐ Los 7 DOCX abren en Word/Windows sin avisos de reparación.
- ☐ Memoria PDF: 22 páginas (portada + índice + 20 caras), figuras visibles.
- ☐ Anexo B contiene exactamente las 10 figuras `fig_*` (Fase 3) y ninguna de las antiguas.
- ☐ Anexos: cero rutas externas (`dashboard/`, `figures/`), solo remisiones internas (memoria, Anexo C).
- ☐ PPTX: 10 diapositivas, sin placeholder de nombre, figuras nítidas en vista presentación.

## 3. Vídeo

Checklist completo en `docs/guia_grabacion_video.docx` (sección 6). Resumen:

- ☐ Duración ≤ 5:00 (objetivo 4:40).
- ☐ Audio claro en todo el vídeo (probar con auriculares y sin ellos); sin saturación ni zumbido de red.
- ☐ Números clave se entienden al escuchar: 4.256.060 · 5,23 % · AUROC 1,0000 circular · 0,9846 / 0,8292 / 0,7278 · 0,21 ms.
- ☐ Exportado MP4 1080p y verificado en VLC (reproductor distinto al de grabación).
- ☐ Nombre real en diapositivas 1 y 10 del vídeo.

## 4. CRÍTICO: ejecutar el notebook fuera de la carpeta de OpenCode

El notebook es el entregable ejecutable, y la memoria promete reproducibilidad con semilla 0. La verificación vale solo si se ejecuta **desde una copia limpia del repo, fuera de `~/Escritorio/OpenCode/`**: si algo del entorno de trabajo (configuración de OpenCode, cachés, entornos, rutas absolutas) estuviera influyendo, esta prueba lo delata. Un tribunal que clone el repo obtendrá exactamente lo que esta copia produzca.

### 4.1 Copia limpia y entorno nuevo (5 min)

```bash
rsync -a \
  --exclude 'env_analytics/' --exclude '.git/' --exclude '.omo/' \
  --exclude '.codegraph' --exclude '.opencode/' --exclude '.venv/' \
  --exclude 'notebooks/.venv/' --exclude 'notebooks/models/' --exclude 'notebooks/.ipynb_checkpoints/' \
  --exclude 'dashboard/Old/' --exclude 'models/Old/' --exclude 'docs/figuras_old/' \
  --exclude 'data/' \
  --exclude 'Documentacion_Master/' --exclude 'info/' \
  --exclude 'docs/*.docx' --exclude 'docs/*.pdf' \
  /home/thykan/Escritorio/OpenCode/TFM/ /home/thykan/Escritorio/TFM/
```

```bash
cd /home/thykan/Escritorio/TFM
ls -a | grep -E "opencode|omo|codegraph" && echo "FALLO: hay restos" || echo "OK: sin restos de OpenCode"
du -sh --exclude=env_test .   # debe rondar los 35 MB (notebook, models, docs, dashboard)

python3 -m venv env_test
source env_test/bin/activate
pip install -r requirements.txt
```

Los datos no se copian: se enlazan después (sección 4.3). `data/` original (8,6 GB), `Documentacion_Master/` (4,7 GB) y los entornos virtuales quedan fuera de la copia.

### 4.2 Verificación rápida (10 min) — sin re-entrenar

Comprueba que el entorno nuevo resuelve las dependencias y que los artefactos serializados cargan e infieren:

```bash
python - <<'EOF'
import tensorflow, pyspark, shap, pandas, numpy, sklearn, joblib, keras
from pathlib import Path
print('imports OK ·', 'tensorflow', tensorflow.__version__, '· pyspark', pyspark.__version__)
dnn = keras.models.load_model('models/dnn_embeddings.keras')
print('DNN cargada:', dnn.count_params(), 'parámetros')
metrics = json.loads(Path('models/metrics.json').read_text())
print('metrics.json:', list(metrics)[:5], '...')
EOF
```

Criterio: sin errores de import, la DNN carga con sus parámetros y `metrics.json` contiene las métricas de la memoria.

### 4.3 Verificación completa (20-40 min) — ejecución de principio a fin

Hay un script que automatiza todo este apartado (entorno, datos enlazados, ejecución y comparación de métricas contra la memoria): `ejecutar_notebook.sh` dentro de la propia copia de verificación. Modo de uso:

```bash
/home/thykan/Escritorio/TFM/ejecutar_notebook.sh            # ejecución completa
/home/thykan/Escritorio/TFM/ejecutar_notebook.sh --rapido   # solo artefactos (2 min)
/home/thykan/Escritorio/TFM/ejecutar_notebook.sh --ui       # abrir JupyterLab para ejecutarlo a mano
```

El modo `--ui` abre JupyterLab (con URL y *token* en la terminal) sobre la copia de verificación, con su `env_test` como kernel: útil para ejecutar el notebook celda a celda observando los resultados, en lugar de de una tacada.

Si se prefiere hacerlo a mano, los pasos son:

```bash
ln -s /home/thykan/Escritorio/OpenCode/TFM/data data
java -version   # LTS en soporte: 17 o 21 (Spark 4.x no admite Java 8/11)

jupyter nbconvert --to notebook --execute --inplace notebooks/TFM_analysis.ipynb
```

Criterios de aceptación (semilla 0 ⇒ determinista):

- ☐ El notebook ejecuta las 60 celdas **sin errores y sin intervención** (en el `venv` nuevo: `source env_test/bin/activate` + `pip install jupyter` si falta).
- ☐ `models/metrics.json` regenerado con las mismas métricas que la memoria: RF 0,9979/0,9742/0,8983 · IF 0,8205/0,1894/0,2617 · AE 0,8566/0,2010/0,3171 · DNN 1,0000/1,0000/0,9259 · Exp B 0,9846/0,8292/0,7278.
- ☐ P95 de `RF_SCORE` = 0,3122 y 222.676 positivos (5,23%) en la celda de feature engineering.
- ☐ Las figuras regeneradas en `docs/figuras/` son visualmente idénticas a las entregadas.

Si algo falla aquí, el repo tal cual lo recibiría un evaluador está roto: corregir en el repo original y repetir esta sección completa.

### 4.4 Limpieza tras la verificación

```bash
deactivate
rm -rf /home/thykan/Escritorio/TFM
```

## 5. Repositorio GitHub

- ☐ `git status --short | grep -E "ted_muestra|env_analytics|\.venv|\.omo|\.bak|Documentacion_Master|Old/"` → vacío.
- ☐ Dry-run razonable: `git add -An --dry-run | wc -l` (~98 ficheros, ~41 MB) y sin nada de `data/` con contenido real.
- ☐ Crear repo **privado** en GitHub (privado es gratis; publicar tras el tribunal si se quiere).
- ☐ Primer commit y push siguiendo `GUIA_GITHUB.md`.
- ☐ **Prueba de clonado**: `git clone` a otra carpeta → comprobar que README, notebook, `models/` y `docs/` están y que el repo no pesa más de ~50 MB.
- ☐ La guía de clonado del README funciona en la copia clonada: `python -m venv` + `pip install -r requirements.txt` sin errores.

## 6. Checklist compacto final

| # | Check | Hecho |
|---|---|---|
| 1 | Placeholders sustituidos (README, LICENSE, PPTX, portada memoria) | ☐ |
| 2 | DOCX regenerados desde los .md finales | ☐ |
| 3 | Barrido de caracteres: 7 DOCX en OK | ☐ |
| 4 | Anexo B con las 10 figuras correctas; anexos sin rutas externas | ☐ |
| 5 | Vídeo ≤ 5:00, audio limpio, MP4 1080p verificado en VLC | ☐ |
| 6 | **Notebook ejecutado fuera de OpenCode, copia limpia + venv nuevo, sin errores** | ☐ |
| 7 | Métricas regeneradas idénticas a la memoria (semilla 0) | ☐ |
| 8 | Repo: exclusión-grep vacío, dry-run ~42-45 MB, commit + push | ☐ |
| 9 | Clone-test en carpeta apartada: venv + requirements sin errores | ☐ |
| 10 | Enlace de Tableau Public abierto y dashboard cargando con datos | ☐ |