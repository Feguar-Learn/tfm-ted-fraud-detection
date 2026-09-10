# Anexo F. Cuaderno de ejecución completo

## 1. Objeto

Este anexo incorpora a la memoria el cuaderno de ejecución completa del trabajo, `TFM_analysis.ipynb`, en su versión exportada a HTML: `TFM_anexo_F_notebook.html`. Es el documento más importante de los anexos, porque contiene el pipeline íntegro —de la descarga de los CSV de TED a la demo de inferencia— ejecutado de principio a fin con semilla 0, con su código, sus salidas y sus figuras.

## 2. Contenido del cuaderno

El cuaderno se organiza en las seis fases del trabajo:

| Fase | Contenido | Resultados verificables en las salidas |
|------|-----------|----------------------------------------|
| 1. Datos y limpieza | Descarga de los CSV de TED (CAN + CN), validación XSD, deduplicación y cruce CAN←CN con PySpark | 4.256.060 adjudicaciones consolidadas |
| 2. Feature engineering | Las 22 *red flags* OCDE, 5 continuas, ratios y `RF_SCORE`/`RF_LABEL` | P95 = 0,3122 · 222.676 positivos (5,23%) |
| 3. Análisis descriptivo | Las 10 figuras del EDA (Figuras 1-10 de la memoria) | Figuras con el prefijo `fig_` |
| 4. Modelado | Random Forest (Spark MLlib), Isolation Forest, autoencoder y DNN | Métricas de la sección 5.7 de la memoria |
| 5. Interpretabilidad | SHAP (`GradientExplainer`) sobre la DNN | Top 10 de características (Figura 11) |
| 6. Despliegue | Motor de inferencia (`predecir()`) con demo *online* y *batch* | 0,20 ms por predicción en *batch* |

Las salidas impresas de las celdas reproducen las cifras citadas en la memoria y en los anexos A-E; el cuaderno es, por tanto, la fuente verificable de todos los resultados del trabajo.

## 3. Reproducibilidad

El cuaderno se ejecuta de principio a fin con semilla 0 (global del trabajo, fijada en la primera celda). La copia `.ipynb` original está en el repositorio (`notebooks/TFM_analysis.ipynb`) con sus salidas ya calculadas; el HTML de este anexo es el volcado visual de ese mismo fichero y no requiere ejecución para su consulta. Los requisitos de ejecución (Python 3.12, PySpark 4.2.0, TensorFlow 2.21.0 y demás dependencias en `requirements.txt` del repositorio) y los criterios de verificación figuran en la memoria (secciones 2 y 9) y en el Anexo E.