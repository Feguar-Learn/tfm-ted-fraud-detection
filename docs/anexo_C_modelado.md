# Anexo C — Modelado (Fase 4)

Este anexo documenta la implementación y resultados de los cuatro modelos de detección de fraude entrenados sobre la tabla maestra de *features* de TED (4.256.060 adjudicaciones a nivel `ID_AWARD`). Todo el modelado vive en el notebook `notebooks/TFM_analysis.ipynb` (Fase 4 y Fase 4.6), que es el entregable único y reproducible; la lectura interpretativa de estos resultados está en la sección 5 de la memoria.

---

## 1. Diseño de los modelos

### 1.1 Features de entrada

27 *features* de entrada por adjudicación, derivadas del *feature engineering* de la Fase 2:

- **22 *red flags* OCDE binarias** (`RF_*`): acceso a la competencia, transparencia, estructura de ofertas, precio, conflicto de interés y concentración de ganador.
- **5 *features* continuas**: `RATIO_AWARD_EST` (ratio adjudicado/estimado, con valor solo cuando el cruce con CN aportó estimación), `VALUE_DEV_SECTOR` (*z-score* del log-valor respecto a la mediana sectorial), `WINNER_SHARE_BUYER`, `WINNER_SHARE_SECTOR` y `WINNER_VALUE_SHARE_BUYER` (cuotas de concentración del ganador).

**Tratamiento de nulos**: las continuas se escalan con `StandardScaler` ajustado solo en *train* (imputando los NaN con la media de *train* calculada ignorando los NaN), los valores escalados que eran nulos se ponen a 0 y se añade una **máscara binaria de nulo** por cada *feature* continua, de modo que la red distinga un 0 real de un valor ausente. La dimensión de entrada final es **32** (22 binarias + 5 continuas escaladas + 5 máscaras).

### 1.2 Pseudo-etiqueta

`RF_LABEL` = 1 cuando `RF_SCORE` (suma ponderada de las 22 *red flags*, normalizada por el máximo teórico de los pesos: 20,50) supera el percentil 95 del dataset completo (umbral 0,3122). Esto produce **222.676 positivos (5,23 %)**, una fracción viable para el entrenamiento supervisado débil. El significado exacto del *proxy* y sus límites se analizan en las secciones 3 y 5.6 de la memoria.

### 1.3 Partición estratificada

80/20 estratificada por `RF_LABEL` (semilla 0), que preserva la prevalencia del 5,23 % en ambos conjuntos.

---

## 2. Arquitecturas

### 2.1 Random Forest (supervisado distribuido, Spark MLlib)

- **Pipeline**: `VectorAssembler` + `RandomForestClassifier` + `TrainValidationSplit` con 4 combinaciones (`maxDepth` ∈ {6, 8}, `numTrees` ∈ {50, 100}). Se optó por `TrainValidationSplit` frente a `CrossValidator` porque el *k-fold* multiplicaba el tiempo de cómputo sin mejorar apenas las métricas.
- **Mejor configuración**: `numTrees=100`, `maxDepth=8`.
- **Datos**: parquet completo leído como Spark DataFrame (4,26M filas), con partición propia del motor (3.404.575 *train* / 851.485 *test*, ligeramente distinta a la de scikit-learn por el muestreo interno de Spark).
- **Salida**: probabilidad de la clase positiva.

### 2.2 Isolation Forest (baseline no supervisado, `sklearn`)

- **Algoritmo**: Liu et al. (2008); las anomalías se aíslan con menos particiones aleatorias que las observaciones normales.
- **Hiperparámetros**: `n_estimators=200`, `contamination='auto'`, `random_state=0`, `n_jobs=-1`.
- **Muestra de entrenamiento**: 200.000 filas muestreadas de las 3.226.707 normales de *train* (semilla 0); el coste del algoritmo crece con el número de muestras, por eso se limita.
- **Score de anomalía**: `decision_function` negado y normalizado a [0,1] con cuantiles robustos (P1, P99) sobre el *test*.

### 2.3 Autoencoder (no supervisado, TensorFlow/Keras)

- **Arquitectura**: `32 → 24 → 4 → 24 → 32`, con cuello de botella de 4 unidades.
- **Capas**: densas con ReLU, `BatchNormalization` y `Dropout(0.1)` en encoder y decoder; la capa de reconstrucción no lleva activación.
- **Pérdida**: MSE (error de reconstrucción por muestra).
- **Optimizador**: Adam con LR 1e-3, `EarlyStopping` (paciencia 5, restaurando los mejores pesos) y `ReduceLROnPlateau` (factor 0,5, paciencia 3, mínimo 1e-6); 15 *epochs* con *batch* de 2048.
- **Entrenamiento**: solo sobre la clase mayoritaria (`RF_LABEL`=0; 3.226.707 filas). El modelo aprende la normalidad y las anomalías se reconstruyen con mayor error.
- **Score de anomalía**: error de reconstrucción por muestra, normalizado a [0,1] con cuantiles robustos (P1, P99) sobre el *test*.

### 2.4 DNN clasificadora (supervisada débil, TensorFlow/Keras)

- **Arquitectura**: `32 → 64 → 32 → 16 → 1`, con salida sigmoide.
- **Capas**: densas con ReLU, `BatchNormalization` y `Dropout(0.2)`.
- **Pérdida**: `binary_crossentropy` con `class_weight` de la clase positiva = n_neg/n_pos ≈ 18,11, para compensar el desbalanceo de la pseudo-etiqueta.
- **Optimizador**: Adam con LR 1e-3, `EarlyStopping` y `ReduceLROnPlateau` con la misma configuración que el autoencoder; 15 *epochs* con *batch* de 2048.
- **Entrenamiento**: sobre todo el conjunto de *train* (mayoritaria + minoritaria); el modelo aprende a reproducir y refinar la pseudo-etiqueta.
- **Salida**: probabilidad de la clase positiva (sigmoide).

### 2.5 Parámetros de las redes

| Red | Parámetros totales | Entrenables |
|-----|--------------------|-------------|
| Autoencoder | 2.004 | 1.908 |
| DNN clasificadora | 5.185 | 4.961 |

El Random Forest y el Isolation Forest son *ensembles* de árboles, sin parámetros entrenables en el sentido de las redes neuronales.

---

## 3. Resultados sobre el dataset completo

Entrenamiento sobre la totalidad de la tabla maestra a nivel `ID_AWARD`. Con un 5,23% de positivos, la evaluación se basa en métricas de *ranking* en lugar de *accuracy*: el AUROC (área bajo la curva ROC) mide la calidad del ordenamiento global, y el AUPRC (área bajo la curva de *precision-recall*), la precisión al revisar la cola superior del *ranking*, que es la relevante para priorizar inspecciones (Davis y Goadrich, 2006); el F1 se calcula en el umbral que optimiza el equilibrio entre precisión y *recall*.

- **Train**: 3.404.848 filas (80 %) — **Test**: 851.212 filas (20 %)
- **Positivos**: 178.141 en *train* (5,23 %) — 44.535 en *test* (5,23 %)
- **Partición**: estratificada por `RF_LABEL`, semilla 0
- **Dispositivo**: CPU local (el mismo equipo que hizo de *driver* de Spark, con hasta 48 GB de RAM para la JVM, ajustados automáticamente a la memoria disponible del equipo)

| Modelo | AUROC | AUPRC | F1 (umbral óptimo) | P@1 % | Tiempo (s) |
|--------|-------|-------|--------------------|-------|------------|
| Random Forest (Spark MLlib) | 0,9979 | 0,9742 | 0,8983 | 1,0000 | 254,9 |
| Isolation Forest | 0,8205 | 0,1894 | 0,2617 | 0,3407 | 0,3 |
| Autoencoder | 0,8566 | 0,2010 | 0,3171 | 0,3321 | 21,1 |
| **DNN** | **1,0000** | **1,0000** | **0,9259** | **1,0000** | 32,2 |

Las métricas (AUROC, AUPRC, F1, P@1%) de esta tabla coinciden con la tabla comparativa de la sección 5.7 de la memoria y con los artefactos `models/metrics.json` (dispositivo `cpu`, semilla 0); los tiempos, medidos en cada ejecución, se citan aquí tal como los imprimió el notebook. El Random Forest aportó además su *feature importance* nativa, con el top 5 (`RF_NO_PRIOR_NOTICE` 0,148, `RF_OUT_OF_DIRECTIVES` 0,121, `RF_SINGLE_BID` 0,120, `RF_NEGOTIATED_NO_CALL` 0,119, `RF_AWARD_NO_PUBLICATION` 0,095) comentado en la sección 5.2 de la memoria.

---

## 4. Experimentos de validación contra la circularidad (Fase 4.6)

Como se documenta en la sección 5.6 de la memoria, el AUROC de 1,0 de la DNN (y el 0,9979 del RF) evidencian circularidad: la etiqueta es función de las mismas *features* que recibe el modelo. Para responder si el *deep learning* extrae señal más allá de las 22 *red flags*, se entrenaron tres variantes sin las binarias OCDE en la entrada, sobre las 16 variables crudas (`NUMBER_OFFERS`, licitadores de otros países, correcciones, valores, `LOG_AWARD_VALUE`, mediana sectorial, lotes, duración, `HAS_CN` y las 5 continuas) y las 6 categóricas de entidad (`CAE_NATIONALID`, `WIN_NATIONALID`, `CPV`, país del ganador, país del comprador, `TOP_TYPE`):

| Modelo | Entrada | AUROC | AUPRC | F1 | Tiempo |
|--------|---------|-------|-------|----|--------|
| Baseline (22 *red flags*) | 32 dimensiones | 1,0000 | 1,0000 | 0,9259 | 32,2 s |
| Experimento A — solo variables crudas | 32 dimensiones (16 crudas + 16 máscaras de nulo) | 0,9576 | 0,5148 | 0,5427 | 32,2 s |
| Solo *embeddings* | 68 dimensiones (vectores de las 6 categóricas) | 0,9446 | 0,6817 | 0,6261 | 62,0 s |
| Experimento B — crudas + *entity embeddings* | 100 dimensiones (32 numéricas + 68 de *embedding*) | 0,9846 | 0,8292 | 0,7278 | 64,8 s |

Las dimensiones de *embedding* por categórica fueron 16 para comprador, ganador y CPV, 8 para los dos países y 4 para el tipo de procedimiento. Las cardinalidades tras la limpieza y el recorte de colas quedaron en 20.000 compradores, 30.000 ganadores, 5.001 CPV, 199 países de ganador, 49 países y 10 tipos de procedimiento; la limpieza previa (códigos ISO válidos de dos letras, los 9 códigos de procedimiento TED, resto a "OTHER") está descrita en la sección 5.6 de la memoria.

El Experimento B es el mejor resultado sin circularidad y el que se presenta como resultado principal; quedó guardado como `models/dnn_embeddings.keras`, y sus métricas quedan impresas en la celda de resultados del notebook (sección 5.7 de la memoria).

---

## 5. Análisis crítico de los resultados

### 5.1 DNN: AUROC = 1,0 — fuga de información por diseño

La DNN alcanza métricas casi perfectas, lo que **no significa** que detecte fraude real con precisión perfecta. La causa es una fuga de información estructural: la pseudo-etiqueta `RF_LABEL` se deriva de `RF_SCORE`, que es una combinación lineal ponderada de las mismas 22 `RF_*` que la DNN ve como entrada; la red aprende a reproducir la regla que generó la etiqueta, es decir, memoriza el umbral P95 sobre `RF_SCORE`. Esto es esperable en un esquema *weakly-supervised* con pseudo-etiquetas derivadas de las propias *features*. La utilidad de la DNN es triple: refinar la frontera de decisión con combinaciones no lineales entre *red flags*, calibrar la salida como probabilidad interpretable (frente al `RF_SCORE`, un ratio sin escala probabilística), y productivizar, porque el archivo `.keras` se sirve con baja latencia sin recalcular las 22 *red flags* en tiempo de ejecución.

### 5.2 Autoencoder: detección sin supervisión

El autoencoder (AUROC 0,8566, AUPRC 0,2010) **no usa la pseudo-etiqueta en el entrenamiento**: aprende la normalidad solo de la clase mayoritaria. Que alcance un AUROC de 0,85 sobre el 5,23 % de alto riesgo sin ninguna supervisión indica que las anomalías tienen una estructura distinguible en el espacio de 32 *features*. Es el modelo llamado a detectar patrones no cubiertos por las 22 *red flags* OCDE, es decir, tipologías emergentes o no descritas en la literatura de referencia.

### 5.3 Isolation Forest: baseline robusto

IF (AUROC 0,8205, AUPRC 0,1894) confirma que el problema es separable con métodos clásicos no supervisados, aunque queda por debajo del autoencoder. Su ventaja es la simplicidad y el coste de entrenamiento (0,3 s), lo que lo hace útil como referencia (*baseline*) y verificación de cordura (*sanity check*).

### 5.4 Recomendación de uso

- **DNN** para el *scoring* de riesgo prioritario (alta precisión sobre los perfiles que cumplen las reglas OCDE conocidas).
- **Autoencoder** para anomalías emergentes (patrones no cubiertos por las reglas pero estadísticamente atípicos).
- **Isolation Forest** como referencia no supervisada y contraste.

Esta combinación es la que se productivizó en el motor de inferencia (Anexo E).

---

## 6. Artefactos guardados en `models/`

| Archivo | Tamaño | Descripción |
|--------|--------|-------------|
| `autoencoder.keras` | 70 KB | Autoencoder (15 *epochs* sobre 3,2M filas normales) |
| `dnn.keras` | 120 KB | DNN clasificadora (15 *epochs* sobre 3,4M filas) |
| `dnn_embeddings.keras` | 10,8 MB | Modelo B (crudas + *entity embeddings*, Fase 4.6) |
| `isolation_forest.joblib` | 2,4 MB | Isolation Forest (200 árboles, muestra de 200k normales) |
| `scaler.joblib` | 687 B | `StandardScaler` ajustado sobre las continuas de *train* |
| `spark_rf_pipeline/` | — | Pipeline RF de Spark MLlib (`VectorAssembler` + RF con la mejor configuración) |
| `metrics.json` | 1,7 KB | Metadatos (dispositivo, semilla, lista de *features*) y métricas completas de los 4 modelos de la Fase 4 |

Las métricas de los experimentos de validación (A, solo *embeddings*, B) no se serializan: quedan impresas en las celdas de resultados del notebook y recogidas en la tabla de la sección 5.7 de la memoria.

---

## 7. Reproducibilidad

El modelado completo vive en el notebook, que se ejecuta de principio a fin con semilla 0:

```bash
# Ejecutar el notebook completo (Fase 4 + Fase 4.6)
jupyter nbconvert --to html --execute notebooks/TFM_analysis.ipynb
```

El entrenamiento se ejecuta en CPU local con TensorFlow/Keras y Spark MLlib. Los tiempos por modelo sobre la tabla maestra completa son ~255 s el Random Forest (Spark), ~32 s la DNN, ~32 s el Experimento A, ~65 s el Experimento B, ~21 s el autoencoder y ~0,3 s el Isolation Forest.

Antes de entrenar con TensorFlow hubo que liberar la memoria del *driver* de Spark con `spark.stop()` y cargar en Pandas solo las columnas necesarias (las 69 del *parquet* con 4,26M de filas agotan la memoria); ambos ajustes operativos están comentados en la sección 5.1 de la memoria.

---

## 8. Estado del pipeline

- **Fase 5 (SHAP)**: interpretabilidad de la DNN, ejecutada y documentada en el Anexo D.
- **Fase 6 (Productivización)**: demo de inferencia *online* y *batch*, ejecutada y documentada en el Anexo E.
- **Dashboard Tableau**: muestra de 500.000 adjudicaciones con `Score_Modelo` para visualización, documentada en la sección 8 de la memoria y en el Anexo E (sección 5).
- **Reentrenamiento**: las métricas en CPU son definitivas (4,26M filas, 15 *epochs*) y el pipeline es reproducible con la misma semilla y el mismo dataset.