# Anexo E — Productivización (Fase 6)

Este anexo documenta la productivización del modelo de detección de fraude TED: la demo de inferencia que cubre los escenarios *online* y *batch*, y el *dashboard* de Tableau que pone el resultado en manos de un usuario final. La lectura para Negocio está en la sección 7 de la memoria y la descripción del *dashboard* en la sección 8. La demo de inferencia vive en el notebook `notebooks/TFM_analysis.ipynb` (Fase 6), que es el entregable único y reproducible.

---

## 1. Arquitectura del motor de inferencia

```
┌─────────────────────────────────────────────────────────────┐
│              Cliente (notebook / script / Tableau)          │
└──────────┬──────────────────────────────────────────────────┘
           │  predecir(df)  →  lista de dicts JSON
           ▼
┌─────────────────────────────────────────────────────────────┐
│              Motor de inferencia (notebook, Fase 6)          │
│  preprocesar_lote() → scaler + imputación + máscaras nulo    │
│  scores_dnn  → salida sigmoide          [modelo principal]  │
│  scores_ae   → error de reconstrucción  [complementario]    │
│  scores_if   → decision_function        [baseline]           │
└──────────┬──────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│            models/ (artefactos serializados)                 │
│  dnn.keras  autoencoder.keras  scaler.joblib                 │
│  isolation_forest.joblib  metrics.json                       │
└─────────────────────────────────────────────────────────────┘
```

### 1.1 Componentes

| Componente | Ubicación | Función |
|-----------|-----------|---------|
| Motor de inferencia | `notebooks/TFM_analysis.ipynb` (Fase 6) | Carga modelos, preprocesa, puntúa |
| Función `predecir()` | notebook | Puntúa un DataFrame y devuelve JSON por fila |
| Función `preprocesar_lote()` | notebook | Convierte crudo en matriz de 32 dimensiones |
| Modelos serializados | `models/` | `.keras` + `.joblib` + `metrics.json` |

### 1.2 Carga de modelos

La demo carga tres modelos desde `models/`, junto con el `StandardScaler` del entrenamiento:

- **DNN** (`dnn.keras`): modelo principal; su salida sigmoide es el *score* de riesgo.
- **Autoencoder** (`autoencoder.keras`): *score* de anomalía por error de reconstrucción, normalizado a [0,1] con cuantiles robustos (P1, P99) del propio lote.
- **Isolation Forest** (`isolation_forest.joblib`): *score* de anomalía por `decision_function` negada, normalizado a [0,1] con el mismo esquema.

El Random Forest de Spark no participa en la inferencia *online* porque exige una sesión de Spark activa, incompatible con una API ligera; su papel queda para el *scoring* *batch* masivo (sección 4).

---

## 2. Motor de inferencia

### 2.1 Preprocesado (`preprocesar_lote`)

La función convierte un DataFrame crudo en la matriz de 32 dimensiones que esperan los modelos, reproduciendo exactamente el preprocesado del entrenamiento:

- **Columnas ausentes**: las binarias `RF_*` se rellenan con 0 y las continuas con NaN.
- **Continuas**: conversión numérica estricta (`pd.to_numeric` con `errors='coerce'`), imputación de NaN con la media de *train* guardada en el *scaler* (`scaler_inf.mean_`) y escalado con `StandardScaler`.
- **Máscara de nulo**: 1 donde había NaN y 0 donde no, para que la red distinga un 0 real de un valor imputado.
- **Resultado**: concatenación de 22 binarias + 5 continuas escaladas + 5 máscaras = 32 dimensiones.

### 2.2 Salida de `predecir()`

Cada fila devuelve un diccionario JSON con esta estructura (salida literal del caso *online* del notebook):

```json
{
  "riesgo_score": 0.0,
  "riesgo_etiqueta": "BAJO",
  "autoencoder_score": 0.0,
  "iforest_score": 0.0,
  "modelo": "dnn_fusion",
  "num_banderas_activas": 0,
  "top_banderas": [],
  "latencia_ms": 105.92
}
```

- `riesgo_score` (0-1): probabilidad de la DNN de que la adjudicación sea de alto riesgo.
- `riesgo_etiqueta`: BAJO (< 0,3), MEDIO (0,3-0,7) o ALTO (> 0,7), según los umbrales fijados en el motor (`UMBRAL_BAJO = 0.3`, `UMBRAL_ALTO = 0.7`).
- `autoencoder_score` e `iforest_score`: *scores* complementarios de anomalía (0-1).
- `num_banderas_activas` y `top_banderas`: número y top 5 de *red flags* activas, cada una con su código `RF_*` y su descripción legible en español.
- `latencia_ms`: latencia media por predicción de la llamada.

El resultado no es una caja negra: junto al *score* devuelve la lista de *red flags* activas, de modo que un auditor puede leer "este contrato es sospechoso porque tiene oferta única, sin convocatoria previa y el ganador es recurrente" y empezar a trabajar el caso sin re-revisar los datos del contrato.

---

## 3. Escenarios de uso

### 3.1 Online (una adjudicación)

Se construye un diccionario con las 27 *features* y se pasa como DataFrame de una fila. El caso de bajo riesgo del notebook (todas las *red flags* a 0, continuas competitivas: `RATIO_AWARD_EST` 0,95, cuotas de ganador del 15-20%) devuelve `riesgo_score` 0,0, etiqueta BAJO y 0 banderas activas. La `latencia_ms` de esa primera llamada (105,92 ms) incluye el calentamiento de la sesión de TensorFlow; las llamadas posteriores operan a la velocidad del caso *batch*.

### 3.2 Batch (1.000 adjudicaciones)

Muestra aleatoria de 1.000 adjudicaciones del *parquet* de *features* (semilla 0) pasada por `predecir()`. Salida literal del notebook:

```
--- Distribucion de Riesgo (Muestra de 1.000 adjudicaciones) ---
BAJO    955
ALTO     45

--- Resumen de Rendimiento y Metricas del Lote ---
  -> Indice de Riesgo Medio (Score): 0.0450
  -> Latencia de Inferencia:         0.20 ms / prediccion
```

- 45 de 1.000 (4,5%) clasificadas como ALTO y ninguna como MEDIO, coherente con la distribución de la pseudo-etiqueta de la tabla maestra (5,23% de positivos concentrados en la cola del *score*).
- **Latencia media de 0,20 ms por predicción**, usable para una API en producción. La mayor parte del tiempo total se consume en la carga inicial de los modelos, no en la inferencia.

---

## 4. División de roles para un despliegue real

- **Random Forest (Spark)**: *scoring* *batch* masivo sobre el histórico o volúmenes grandes que lleguen por Spark; escala al histórico completo sin más recursos.
- **DNN + Autoencoder + Isolation Forest (Keras/sklearn)**: inferencia *online*, donde la baja latencia importa más que la capacidad distribuida. Son modelos ligeros (4.961 y 1.908 parámetros entrenables las redes; 200 árboles el Isolation Forest) y responden en milisegundos sin necesidad de un clúster.

---

## 5. Dashboard interactivo en Tableau

Como complemento al motor de inferencia, se construyó un *dashboard* en Tableau Public para que el resultado sea explorable sin conocimientos técnicos (sección 8 de la memoria y Figuras 12 y 13).

### 5.1 Muestra de datos

Se extrajo del *parquet* de *features* una muestra aleatoria simple de 500.000 adjudicaciones (semilla 0) para alimentar el *dashboard*: con el parquet completo (4,26M filas) Tableau Public responde lento y supera los límites cómodos de la plataforma, y con la muestra el agregado se calcula fluido.

- **Representatividad**: al ser aleatoria y no estratificada, mantiene las proporciones reales de la tabla maestra. La comparativa con la iteración anterior (estratificada 50/50, 200.000 filas) muestra por qué se descartó:

  | Métrica | Tabla maestra | Muestra 50/50 (descartada) | Muestra aleatoria |
  |---|---|---|---|
  | % de alto riesgo | 5,23% | 50,00% | 5,24% |
  | Índice de riesgo medio | 0,166 | 0,254 | 0,166 |
  | % procedimiento abierto | 86,10% | 66,48% | 86,10% |

  Una muestra estratificada por etiqueta sobre-representa los procedimientos de alto riesgo (el abierto cae del 86% al 66%) y distorsiona todas las medias; con la aleatoria, porcentajes, medias y distribuciones del *dashboard* coinciden con la realidad (26.202 casos de alto riesgo en los 500k, suficientes para poblar cualquier gráfico filtrando por `Etiqueta_Riesgo`=1).

- **Formato**: 38 columnas: 15 dimensiones y medidas del contrato (año, país, sector CPV, nº de ofertas, valores, ratios, cuotas de concentración, `Indice_Riesgo`, `Etiqueta_Riesgo`, `Num_RedFlags_Activas`, `Tipo_Procedimiento_Desc`), las 22 *red flags* OCDE renombradas al español, y `Score_Modelo`. Separador `;` y decimal `,` (configuración española), codificación UTF-8 con BOM para que Excel y Tableau lo abran sin configurar nada. La equivalencia con el *parquet* origen es directa: `Indice_Riesgo` = `RF_SCORE`, `Etiqueta_Riesgo` = `RF_LABEL`, `Num_RedFlags_Activas` = `RF_COUNT`, y cada flag en español con su código OCDE `RF_*`; `Tipo_Procedimiento_Desc` traduce los 9 códigos de procedimiento TED (OPE → Procedimiento Abierto, NIC → Negociado sin licitación, AWP → Adjudicación directa fuera de ámbito, etc.).

- **Doble métrica**: `Score_Modelo` (0-1, probabilidad de alto riesgo según la DNN con *entity embeddings* del Experimento B, Anexo C sección 4, calculada sobre la muestra con la misma semilla 0) e `Indice_Riesgo` (0-1, la suma ponderada de las 22 *red flags* interpretable). Ambos miden el mismo riesgo desde perspectivas complementarias: el índice es descomponible en las *red flags* que lo activan, justificable ante un auditor; el *score* del modelo incorpora además la identidad de las entidades (reincidencia y concentración de compradores y ganadores). La regla de diseño: el *score* para priorizar qué revisar y el índice para explicar por qué.

### 5.2 Diseño de las vistas

El libro final (empaquetado con sus datos) es el resultado de un proceso de iteración con una versión previa sobre la que se refinó el diseño; el sistema se organiza en dos vistas complementarias, de lo global al detalle:

**Vista ejecutiva (Dashboard 1)** — foto global del riesgo por país, con la información más importante arriba a la izquierda (*Z-layout*):

- Cabecera con título institucional, logotipo TED y selector de año.
- Cinco tarjetas KPI (hojas de texto con la medida a 24-28 pt): nº de *red flags* medias (`AVG(Num_RedFlags_Activas)`), total de adjudicaciones, valor total adjudicado (`SUM` con separador de miles y unidades de millones) y % de alto riesgo, calculado como `AVG(Etiqueta_Riesgo)` × 100 con formato porcentual (que como `Etiqueta_Riesgo` es 0/1, la media × 100 da el porcentaje directo; sin formato porcentual la tarjeta mostraría "0,05" en vez de "5,2%", el primer error detectado y corregido en el diseño).
- Evolución temporal 2018-2023 por país con doble eje sincronizado de `AVG(Score_Modelo)` (línea negra continua de promedio global anual sobre las series nacionales sin romper la escala).
- Mapa coroplético por país con gradiente continuo por `AVG(Score_Modelo)` (leyenda *score* 0,0010 - 0,4111), tamaño de círculo por volumen de contratos y *tooltip* con las dos métricas de riesgo más el % de alto riesgo y el valor total por país.

**Vista de investigación (Dashboard 2)** — baja al detalle: el auditor selecciona país/sector/año y ve qué contratos concretos revisar y por qué. Barra de filtros superior (año con *slider*, sector CPV, tipo de procedimiento y el selector de eje Y) y disposición 2×2:

- *Scatter* dinámico (agregación desactivada para ver puntos sueltos): eje X `Score_Modelo`, eje Y gestionado por un parámetro `Seleccion Eje Y` y un campo calculado `CASE` que resuelve la variable elegida. De las nueve opciones iniciales se conservaron solo las tres con dispersión estadística real (valor estimado, valor de adjudicación, nº de *red flags* activas): las otras seis degeneraban en rectas planas o colapsos discretos que hacían ilegible el gráfico. La categoría de riesgo va al frente de la leyenda y el *overplotting* se trata con opacidad al 13-15%, borde fino y tamaño de punto mínimo; para variables de valor, el eje Y se fija a rango constante (mínimo 1.000, máximo 10⁹) en lugar de escala logarítmica, cuyas etiquetas apiladas resultaban ilegibles.
- Panel de frecuencia de las 22 *red flags* en "vista completa" sin scroll, y tabla Top 10 de adjudicaciones de mayor riesgo (índice de riesgo, país, valor con separador de miles, *red flags* activas) con un botón textual "Ver flags" que abre un *tooltip* enriquecido con las alertas activas; las columnas que no informaban (códigos CPV crudos, procedimiento repetido en 9 de 10 filas, nº de ofertas casi siempre 1) se retiraron de la tabla y se movieron al *tooltip*.
- **Filtros cruzados**: todo proviene de la misma fuente, así que el mapa y los filtros de año, sector y procedimiento se propagan a todas las vistas (excepto a la de frecuencia global, que hace de referencia no filtrada con la que comparar el perfil del subconjunto seleccionado).

Las capturas finales son las Figuras 12 y 13 de la memoria.

### 5.3 Proceso de diseño y depuración

El diseño no salió a la primera: se trabajó con capturas de pantalla iterativas y una auditoría del XML del libro, de las que salieron tres bloques de incidencias resueltas:

- **Correcciones**: KPI de % alto riesgo mostrando 0,05 en lugar de 5,2% (falta de formato porcentual); línea de evolución temporal duplicada por una píldora `AVG(Score_Modelo)` restante de un doble eje abortado; seis opciones degeneradas del parámetro de eje Y reducidas a las tres con dispersión real; y columnas de la tabla Top 10 que no informaban, movidas al *tooltip*.
- **Consistencia**: formatos numéricos uniformes en KPIs y tabla (separador de miles, unidades de millones, 0 decimales); eje del *scatter* de logarítmico a rango fijo; top 10 de *red flags* en el panel de frecuencia (las 22 amontonadas eran ilegibles); opacidad del *scatter*; y *tooltips* enriquecidos en *scatter*, mapa y Top 10.
- **Estética**: paleta unificada gris-rojo (#e6e6e6 → #e15759) en todas las hojas con alias de leyenda ("Sin riesgo alto" / "Alto riesgo"); tipografía jerarquizada (títulos 12, ejes 9, KPI 24-28); cierre de huecos de composición; y orden de tabulación revisado (título → filtros → visuales principales → KPIs).

La versión final consolidó el diseño en un único libro empaquetado con los datos, publicado en Tableau Public. La iteración previa (Libro2, sobre la muestra estratificada de 200.000 filas) se conserva apartada como material histórico, fuera de la entrega.

---

## 6. Reproducibilidad

```bash
# Ejecutar el notebook completo (incluye la Fase 6 de despliegue)
jupyter nbconvert --to html --execute notebooks/TFM_analysis.ipynb
```

La demo de inferencia se ejecuta en CPU con TensorFlow/Keras; la carga de los tres modelos tarda unos segundos y la inferencia en *batch* ronda los 0,20 ms por predicción. El *dashboard* se abre directamente en Tableau Public con el libro empaquetado entregado, o reconstruyendo las vistas sobre la muestra CSV desde cero.

---

## 7. Decisiones de diseño

1. **DNN como modelo principal**: el `riesgo_score` es la salida sigmoide de la DNN. El autoencoder e Isolation Forest acompañan como *scores* complementarios para anomalías no cubiertas por las reglas OCDE.
2. **Imputación con máscara**: las continuas ausentes se imputan con la media de *train* tras el *scaler* y se marca la ausencia con una máscara binaria, para que el modelo distinga un 0 real de un valor imputado.
3. **Salida explicable**: `predecir()` devuelve no solo el *score* sino las *red flags* activas, para que el auditor justifique cada alerta sin re-revisar los datos del contrato.
4. **Random Forest fuera de la API** *online*: requiere sesión de Spark activa; su papel es el *scoring* *batch* masivo.
5. **Muestra aleatoria para Tableau**: preserva las proporciones reales de la tabla maestra (frente a la estratificada 50/50 de una iteración anterior), de modo que las agregaciones del *dashboard* son representativas del total.