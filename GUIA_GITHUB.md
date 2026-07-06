# Guía: publicar el TFM en GitHub

Paso a paso para montar este proyecto en GitHub desde cero. Tiempo estimado: 10-15 minutos.

---

## 0. Qué se sube y qué no (ya configurado en `.gitignore`)

| Se sube | No se sube |
|---|---|
| `notebooks/TFM_analysis.ipynb` (~1 MB) | `data/` completo (~8,6 GB: raw, processed, features) |
| `docs/` (memoria, anexos MD+DOCX, generadores, figuras) | `Documentacion_Master/` (4,7 GB: material del máster, videos, tareas) |
| `models/` (~15 MB de artefactos) | `dashboard/ted_muestra_500k.csv` (95 MB) |
| `dashboard/` (twbx 15 MB, capturas) | `notebooks/models/` duplicados |
| `README.md`, `requirements.txt`, `LICENSE`, `GUIA_GITHUB.md` | `env_analytics/`, `notebooks/.venv/` (entornos) |
|  | backups (`*.bak`, `*.bak2`), caches, `.omo/`, `.codegraph` |

Total estimado del repo: **~40 MB** — cabe de sobra en GitHub sin Git LFS.

---

## 1. Crear el repositorio en GitHub

1. Entra en <https://github.com/new>
2. **Repository name**: p. ej. `tfm-fraude-ted` (sin espacios ni tildes)
3. **Visibility**:
   - ⚠️ **Importante**: el repo incluye tu memoria y anexos del TFM. Si tu universidad usa Turnitin o similar contra repos públicos, elige **Private** — es **gratis con cualquier cuenta de GitHub** (los privados son ilimitados desde 2019; el Student Pack solo añade extras como Copilot, no es necesario para esto). O sube tras la defensa.
   - Si lo haces público, el README ya advierte de la nota ética y la licencia MIT cubre el código.
   - Si solicitas el Student Pack y te piden pruebas: email `@estudiantes.ucm.es` verificado + justificante de matrícula (UCM lo emite) o captura del expediente con nombre y curso. **Ningún paso de esta guía depende de tenerlo.**
4. **NO** inicialices con README/.gitignore/license (ya tenemos los nuestros; evitaría conflictos)
5. *Create repository* — GitHub te mostrará la URL; copia la de SSH o HTTPS.

> **Consejo** (opcional): añade *topics* en el repo: `fraud-detection`, `public-procurement`, `spark`, `tensorflow`, `tableau`, `xai`, `anomaly-detection`, `master-thesis`.

---

## 2. Inicializar git en local

```bash
cd ~/Escritorio/OpenCode/TFM

# identidad (solo si no la tienes configurada globalmente)
git config user.name "Tu Nombre"
git config user.email "tu@email.com"

git init -b main
```

---

## 3. Revisar qué se va a subir (¡antes del primer commit!)

```bash
git add .
git status --short | head -50        # mira lo que entra
git status --short | wc -l           # nº total de ficheros

# Comprobación de seguridad: nada de esto debe aparecer
git status --short | grep -E "data/(raw|processed|features)/[^.]|ted_muestra|env_analytics|\.venv|\.omo|\.codegraph|\.bak|Documentacion_Master"
# (no debe devolver nada; los .gitkeep de data/ sí son normales)

# Tamaño total que se subiría (aprox)
git ls-files --cached --others --exclude-standard -z | xargs -0 du -ch 2>/dev/null | tail -1
```

Si algo pesado se coló, corrige `.gitignore`, haz `git rm -r --cached <fichero>` y repite.

---

## 4. Primer commit y push

```bash
git commit -m "TFM: pipeline TED de fraude en contratación pública (EDA, modelado, SHAP, inferencia, dashboard)"
git remote add origin git@github.com:<usuario>/tfm-fraude-ted.git   # o https://github.com/<usuario>/<repo>.git
git push -u origin main
```

Con HTTPS te pedirá usuario + token (GitHub ya no acepta contraseña; genera un token en *Settings → Developer settings → Personal access tokens*, con permiso `repo`).

---

## 5. Ajustes recomendados en la web de GitHub

1. **About** (engranaje a la derecha): descripción corta + link si hay dashboard público en Tableau Public.
2. **Topics**: los sugeridos en el paso 1.
3. **Branch protection** (opcional): *Settings → Branches → Add rule* sobre `main`, *Require a pull request before merging* si vas a colaborar.
4. **Badge de licencia** (opcional): ya referenciado en el README.

---

## 6. Flujo de trabajo habitual después

```bash
# ciclo normal
git add <ficheros>
git commit -m "descripción del cambio"
git push

# ver qué cambió sin subir aún
git status
git diff

# deshacer cambios locales de un fichero (¡cuidado, pierde edits!)
git checkout -- <fichero>
```

> **No** hagas `git push --force` salvo que sepas exactamente qué rompes.

---

## 7. Opcional: Git LFS (solo si algún día subes los parquet o el CSV)

Si en el futuro quieres versionar ficheros de 50-500 MB (parquets, muestras CSV):

```bash
sudo apt install git-lfs
git lfs install
git lfs track "*.parquet" "*.twbx" "dashboard/ted_muestra_500k.csv"
git add .gitattributes
git commit -m "chore: git-lfs para ficheros grandes"
```

Límites gratuitos de GitHub LFS: 1 GB de almacenamiento / 1 GB de ancho de banda al mes. Para este repo **no es necesario hoy**.

---

## 8. Opcional: ejecutar el notebook en Colab/Kaggle

El notebook corre en CPU local, pero si quisieras re-ejecutarlo en la nube:

- **Kaggle Notebooks**: 20 GB RAM gratis, sube `requirements.txt` como *dataset* o usa `!pip install -r requirements.txt` en la primera celda (pyspark y tensorflow-cpu ya vienen preinstalados).
- **Colab**: ojo, el plan gratuito tiene ~12 GB de RAM; la Fase 2 (4,26M filas) puede quedarse corta. Ajusta `spark.driver.memory` hacia abajo y carga en Pandas solo las columnas necesarias (el notebook ya lo hace).

---

## 9. Troubleshooting

| Problema | Solución |
|---|---|
| `git push` rechazado por ficheros > 100 MB | Algo pesado se coló: `git rm -r --cached <ruta>`, añádelo a `.gitignore`, commit, push de nuevo |
| `error: src refspec main` | Tu rama es `master`: `git branch -M main` antes del push |
| Permisos SSH denegados | Configura tu clave: `ssh-keygen -t ed25519` y súbela a GitHub → *Settings → SSH keys* |
| Cambié `.gitignore` pero el fichero sigue subido | `git rm -r --cached <ruta>` (el ignore solo afecta a ficheros no trackeados) |
| `git config: could not lock file` | Estás fuera del repo; ejecuta dentro de `~/Escritorio/OpenCode/TFM` |
| Token HTTPS caducado | Regénralo en *Settings → Developer settings* y actualiza el remote |
| `java: command not found` al correr Spark | `sudo apt install default-jdk` y verifica con `java -version` |

---

## 10. Checklist final antes de publicar

- [ ] `git status --short | grep -E "ted_muestra|env_analytics|\.venv|\.omo|\.bak|Documentacion_Master"` → vacío
- [ ] Tamaño total del repo < 50 MB (comando del paso 3)
- [ ] README con tu nombre real (sustituye `[Nombre Apellido1 Apellido2]` en README/LICENSE si quieres)
- [ ] Decisión de visibilidad tomada (Private es gratis con cualquier cuenta; ver paso 1.3)
- [ ] Primer commit y push hechos, y `github.com/<usuario>/<repo>` abre con el README renderizado