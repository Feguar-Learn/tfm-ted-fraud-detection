# Anexo D — Interpretabilidad SHAP (Fase 5)

Este anexo documenta el análisis de interpretabilidad de la DNN clasificadora mediante SHAP (SHapley Additive exPlanations). SHAP atribuye la salida del modelo a cada *feature* de entrada, midiendo su contribución marginal a la predicción respecto a un valor de referencia. Para redes neuronales, la biblioteca `shap` implementa el método basado en gradientes (*Gradient-based*), que propaga el gradiente de la salida respecto a las entradas y se accede con `GradientExplainer`.

El análisis vive en el notebook `notebooks/TFM_analysis.ipynb` (Fase 5), que es el entregable único y reproducible. La lectura interpretativa condensada está en la sección 6 de la memoria, y la crítica a la circularidad que limita este análisis, en la sección 5.6 y en el Anexo C (sección 5.1).

---

## 1. Metodología

### 1.1 Modelo interpretado

Se interpretó la **DNN clasificadora** (`dnn.keras`), el modelo con mejores métricas de la Fase 4 (AUROC 1,0 y AUPRC 1,0 sobre 4,26M filas), con arquitectura `32 → 64 → 32 → 16 → 1` y salida sigmoide. Recibe como entrada 32 dimensiones: las 22 *red flags* OCDE binarias, las 5 *features* continuas escaladas y las 5 máscaras binarias de nulo.

### 1.2 Configuración SHAP

- **Explainer**: `shap.GradientExplainer` (basado en gradientes, con *backprop*).
- **Valor de referencia** (*background*): 100 muestras aleatorias del conjunto de *train*, extraídas con `np.random.default_rng(0)`.
- **Datos explicados**: 5.000 muestras del conjunto de *test* (`X_test[:5000]`).
- **Salida**: valores SHAP de dimensión (5.000, 32), la contribución de cada *feature* al logit de la DNN para cada muestra.

### 1.3 Nombres legibles

Las 32 *features* de entrada se renombraron para visualización: las 22 *red flags* con su descripción en español, las 5 continuas con su nombre y las 5 máscaras de nulo con el sufijo "(Nulo)".

---

## 2. Resultados

### 2.1 Top 10 de características por |SHAP| medio

Valor absoluto medio de SHAP por *feature*, ordenado de mayor a menor impacto global:

| # | Característica | SHAP medio absoluto |
|---|----------------|---------------------|
| 1 | Sin convocatoria previa | 0,0300 |
| 2 | Oferta única | 0,0221 |
| 3 | Pocas ofertas alto valor | 0,0156 |
| 4 | Concentración de valor | 0,0138 |
| 5 | Ganador recurrente | 0,0132 |
| 6 | Outlier sectorial | 0,0110 |
| 7 | Negociado sin licitación | 0,0096 |
| 8 | Ganador domina sector | 0,0091 |
| 9 | Adjudicado muy por debajo | 0,0088 |
| 10 | Adjudicación no publicada | 0,0047 |

**Hallazgos**:

- **Sin convocatoria previa** es la *feature* más importante, seguida de **oferta única**. Ambas son *red flags* de acceso a la competencia, lo que confirma que la falta de competencia real es el predictor más fuerte de fraude según la OCDE.
- Las tres primeras (sin convocatoria, oferta única, pocas ofertas en contratos de alto valor) concentran la mayor parte de la importancia, y las tres son *red flags* de acceso a la competencia.
- Las *features* continuas no aparecen en la parte alta del ranking: las binarias, alineadas con la etiqueta, dominan la explicación. Esto refuerza que la DNN está muy ligada a las reglas OCDE, esperable por la circularidad de la pseudo-etiqueta (Anexo C, sección 5.1).

### 2.2 Gráfico de barras

El notebook genera un gráfico de barras horizontales con el top 10 de características por |SHAP| medio, con el valor numérico anotado al final de cada barra y el mismo azul corporativo `#2874A6` del resto de gráficas del trabajo. Corresponde a la Figura 11 de la memoria (`figuras/fig_shap_top10.png`).

---

## 3. Análisis crítico

### 3.1 Validación del enfoque híbrido

SHAP confirma que la DNN aprende un patrón coherente con la teoría OCDE:

1. **Las *red flags* de acceso a la competencia** (sin convocatoria, oferta única, pocas ofertas alto valor) son las más importantes, en línea con la literatura OCDE que las considera los predictores más potentes de fraude.
2. **La oferta única** es la segunda *feature* más importante, confirmando el hallazgo empírico de la OCDE: la falta de competencia es el predictor de fraude más robusto.
3. El ranking de SHAP comparte con la *feature importance* del Random Forest sus señales dominantes: `RF_NO_PRIOR_NOTICE` encabeza ambos rankings y `RF_SINGLE_BID` figura en el top 3 de los dos. A partir de ahí el orden difiere: SHAP sube `RF_FEW_BIDS_HIGH_VALUE` al tercer puesto porque captura el impacto marginal con interacciones (en el RF queda en sexta posición, tras `RF_OUT_OF_DIRECTIVES` y `RF_NEGOTIATED_NO_CALL`), mientras que la *importance* del RF mide la reducción de impureza en los árboles.

### 3.2 Limitaciones

1. **Fuga de información**: la DNN se entrenó con una pseudo-etiqueta derivada de las mismas 22 *red flags* que recibe como entrada. SHAP refleja ese sesgo: las *features* principales son las *red flags* con mayor peso en `RF_SCORE`. SHAP no puede revelar patrones que el modelo no aprendió.
2. **Ausencia de etiquetas reales**: SHAP explica cómo el modelo llega a su predicción, no si la predicción es correcta. La validación empírica requeriría casos confirmados de fraude, que TED no contiene.
3. **Referencia de 100 muestras**: el valor base de SHAP depende del *background*. Con 100 muestras el valor base es estable pero puede no capturar toda la variabilidad; para un despliegue en producción se recomienda ampliarlo a 500-1.000 muestras.

### 3.3 Recomendaciones para producción

- **Incluir SHAP en la API**: cada predicción debería acompañarse de sus 5 valores SHAP principales, de modo que el auditor vea qué *red flags* dispararon la alerta (el motor de inferencia del Anexo E ya devuelve las banderas activas, el paso siguiente sería la contribución marginal exacta).
- **Panel de interpretabilidad**: integrar los valores SHAP en Tableau para exploración interactiva por país, sector y comprador.
- **Seguimiento de deriva**: comparar la distribución de los valores SHAP periódicamente para detectar cambios en los patrones de fraude.

---

## 4. Artefactos guardados

El notebook no serializa la matriz de valores SHAP: la ejecución de referencia (100 muestras de fondo, 5.000 de *test*, semilla 0) produce como salida el top 10 de características impreso en la celda y el gráfico de barras de la Figura 11 de la memoria. Los valores citados en este anexo (0,0300 · 0,0221 · 0,0156) son los de esa ejecución y coinciden con la figura.

---

## 5. Reproducibilidad

```bash
# Ejecutar el notebook completo (incluye la Fase 5 de SHAP)
jupyter nbconvert --to html --execute notebooks/TFM_analysis.ipynb
```

El cálculo de SHAP se ejecuta en CPU con TensorFlow/Keras; para 5.000 muestras con 100 de referencia tarda unos segundos.