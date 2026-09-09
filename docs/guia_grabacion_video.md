# Guía de grabación del vídeo del TFM (máximo 5 minutos)

Este documento acompaña a `presentacion_TFM.pptx` y define el guion cronometrado, el procedimiento de grabación y la verificación final. El vídeo debe cubrir el contenido de la memoria en menos de 5 minutos, con tono impersonal y el mismo registro de la memoria: técnico, directo y sin exageraciones.

## 1. Datos clave antes de empezar

| Parámetro | Valor |
|---|---|
| Duración objetivo | 4:40 (margen de 20 s sobre el límite de 5:00) |
| Diapositivas | 10 (una por bloque, con portada y cierre) |
| Velocidad de habla | ~150 palabras/minuto (registro pausado) |
| Formato de salida | 1920×1080, 16:9, MP4 (H.264), audio AAC 192 kbps |
| Herramienta recomendada | Grabación integrada de PowerPoint (o OBS) |

Regla de oro: **el vídeo se graba por bloques, no de una sola toma**. Cada diapositiva se graba como un clip independiente y se ensambla después; así, un error en la diapositiva 7 no obliga a repetir las seis anteriores.

## 2. Guion cronometrado

Los tiempos son acumulados. Cada bloque indica: duración, diapositiva, texto orientativo para decir (redactado para leerse en voz alta a ~150 palabras/minuto) y la palabra clave de corte.

### Bloque 1 — Portada (0:00 → 0:20, 20 s)

**Diapositiva 1.** Presentar el trabajo y el marco.

> «Buenas, presento este Trabajo Fin de Máster sobre detección de patrones de fraude en la adjudicación de contratos públicos de la Unión Europea. El trabajo procesa la base de datos TED, el boletín oficial de licitaciones de la UE, entre 2018 y 2023: cuatro millones doscientas cincuenta mil adjudicaciones analizadas con las veintidós señales de alerta de la OCDE y cuatro modelos de machine learning.»

**Corte:** tras «machine learning».

### Bloque 2 — Problema y objetivo (0:20 → 0:50, 30 s)

**Diapositiva 2.** El porqué del trabajo.

> «El problema de partida es doble. Primero, el fraude en contratación pública cuesta miles de millones cada año, y el volumen de TED hace imposible revisarlo a mano. Segundo, no existen etiquetas de fraude confirmado: nadie dice qué contratos son fraudulentos. Por eso el objetivo no es sentenciar, sino priorizar: construir un sistema que ordene las adjudicaciones por riesgo para que un equipo de auditoría decida cuáles revisar. Los scores señalan; la investigación sigue siendo humana.»

**Corte:** tras «es humana».

### Bloque 3 — Datos (0:50 → 1:30, 40 s)

**Diapositiva 3.** El pipeline, de arriba abajo.

> «Los datos originales pesan unos siete gigas y medio y traen catorce millones de filas duplicadas entre dos tipos de aviso. Con PySpark se limpian, validan contra el esquema oficial y se cruzan ambos avisos, quedando cuatro millones doscientos cincuenta mil contratos únicos. Sobre ellos se codifican las veintidós red flags de la OCDE —sin convocatoria previa, oferta única, ganador recurrente, entre otras— más variables continuas y ratios. El resultado es la tabla maestra de sesenta y nueve columnas. La etiqueta de riesgo se construye con el índice OCDE: los contratos por encima del percentil noventa y cinco —cero coma treinta y uno dos— se marcan de alto riesgo: el cinco coma dos por ciento del total, doscientos veintidós mil contratos. Todo el pipeline usa semilla cero: es reproducible de principio a fin.»

**Corte:** tras «de principio a fin».

### Bloque 4 — EDA (1:30 → 2:00, 30 s)

**Diapositiva 4.** Dos gráficos, una idea.

> «El análisis descriptivo muestra que el riesgo no se reparte al azar. A la izquierda, la distribución del índice OCDE con el umbral del percentil noventa y cinco. A la derecha, la frecuencia de las veintidós señales: dominan las de acceso a la competencia —sin convocatoria previa, oferta única, adjudicación directa—. Por países, sectores y tipos de procedimiento hay perfiles sistemáticamente distintos: eso es justamente lo que los modelos pueden aprender.»

**Corte:** tras «aprender».

### Bloque 5 — Modelado y circularidad (2:00 → 2:40, 40 s)

**Diapositiva 5.** La tabla y el hallazgo crítico.

> «Se entrenaron cuatro modelos: un Random Forest distribuido con Spark, Isolation Forest y un autoencoder como métodos no supervisados, y una red neuronal profunda supervisada. La red alcanzó un AUROC de uno exacto. Un uno perfecto en datos reales no es normal, y al revisarlo apareció el hallazgo crítico del trabajo: circularidad. La etiqueta se calcula sumando las veintidós red flags, que son exactamente la entrada del modelo: la red no detecta fraude, reproduce la fórmula de la etiqueta. Es un fallo de planteamiento, no de implementación, y está documentado como tal en la memoria.»

**Corte:** tras «documentado».

### Bloque 6 — Experimentos A/B (2:40 → 3:15, 35 s)

**Diapositiva 6.** El resultado honesto.

> «Para responder a la pregunta de fondo —si el deep learning extrae señal más allá de las red flags— se repitió el entrenamiento sin ellas. Solo con variables numéricas crudas, el AUROC baja a cero coma noventa y cinco. Solo con la identidad de las entidades —comprador, ganador, sector— mediante embeddings, cero coma noventa y cinco también pero con mejor precisión en la cola de riesgo. Y combinando ambas señales, el Experimento B alcanza un AUROC de cero coma noventa y ocho y un AUPRC de cero coma ochenta y tres. La lección: el fraude se concentra en actores reincidentes, no en el tamaño del contrato. Este es el resultado principal y honesto del trabajo.»

**Corte:** tras «del trabajo».

### Bloque 7 — SHAP (3:15 → 3:45, 30 s)

**Diapositiva 7.** Explicabilidad.

> «Un score alto no sirve de nada si no se puede explicar. Con SHAP se descompone cada predicción en contribuciones por variable. Lo relevante: el modelo, sin que nadie se lo indicara, coloca arriba las mismas señales de competencia que marca la literatura OCDE —sin convocatoria previa, oferta única, pocas ofertas en contratos de gran valor—. Y cada alerta individual se explica del tipo: es sospechoso porque tiene oferta única y el ganador es recurrente. Eso es exactamente lo que un auditor necesita recibir.»

**Corte:** tras «recibir».

### Bloque 8 — Productivización (3:45 → 4:15, 30 s)

**Diapositiva 8.** Del notebook al uso.

> «La última fase saca los modelos del notebook. La función predecir recibe una adjudicación nueva y devuelve el score, una etiqueta cualitativa y la lista de red flags activas que justifican la alerta, con una latencia de dos décimas de milisegundo por predicción en batch. Y para el uso diario, un dashboard interactivo en Tableau Public sobre una muestra de quinientos mil contratos: vista ejecutiva con mapa y KPIs, y vista de investigación para bajar al contrato concreto y ver por qué está marcado.»

**Corte:** tras «marcado».

### Bloque 9 — Conclusiones (4:15 → 4:35, 20 s)

**Diapositiva 9.** Cierre honesto.

> «Como conclusiones: un sistema completo, de unos siete gigas y medio crudos a alertas explicables, con la señal validada sin circularidad. Limitaciones asumidas: no hay etiquetas reales de fraude ni validación judicial, así que esto prioriza revisiones, no acusa a nadie. Trabajo futuro: embeddings de texto sobre los títulos, validación con bases de OLAF y despliegue con monitorización.»

**Corte:** tras «monitorización».

### Bloque 10 — Cierre (4:35 → 4:40, 5 s)

**Diapositiva 10.**

> «Gracias.»

**Fin del vídeo.**

## 3. Resumen de tiempos

| Bloque | Diapositiva | Empieza | Duración |
|---|---|---|---|
| 1. Portada | 1 | 0:00 | 20 s |
| 2. Problema | 2 | 0:20 | 30 s |
| 3. Datos | 3 | 0:50 | 40 s |
| 4. EDA | 4 | 1:30 | 30 s |
| 5. Modelado + circularidad | 5 | 2:00 | 40 s |
| 6. Experimentos A/B | 6 | 2:40 | 35 s |
| 7. SHAP | 7 | 3:15 | 30 s |
| 8. Productivización | 8 | 3:45 | 30 s |
| 9. Conclusiones | 9 | 4:15 | 20 s |
| 10. Cierre | 10 | 4:35 | 5 s |
| **Total** | | | **4:40** |

## 4. Preparación de la grabación

1. **Ensayo con cronómetro**: leer el guion completo dos veces con reloj en mano. Si un bloque pasa de su duración, recortar frases del guion (no hablar más rápido). El objetivo es pasar el ensayo completo en 4:40 o menos antes de grabar nada.
2. **Texto en pantalla**: poner el guion en un segundo monitor o impreso. Nunca leer mirando fijo: los bloques están redactados para decirse, no para recitarse; si una frase no sale natural, reescribirla a gusto propio manteniendo los datos.
3. **Diapositivas**: abrir `presentacion_TFM.pptx` en modo presentador con la vista de temporizador visible. Avanzar con la barra espaciadora solo al empezar cada bloque.
4. **Audio (cadena real: Audio-Technica XLR → Behringer)**:
   - **Windows**: seleccionar la entrada USB del Behringer como dispositivo de grabación predeterminado (PowerPoint graba el micrófono por defecto del sistema); samplerate 48.000 Hz (el estándar de vídeo) y desactivar cualquier "mejora" o refuerzo de Windows, que bombean la ganancia.
   - **Phantom (+48 V)**: si el Audio-Technica es condensador (p. ej. AT2020), activar el interruptor +48 V del Behringer. Si es dinámico (p. ej. ATR2100 por XLR), dejarlo desactivado.
   - **Ganancia**: decir en voz alta la frase más fuerte del guion y ajustar el *gain* para que los picos queden entre -12 y -6 dB, sin llegar nunca a 0 dB (recorte). Mejor corto que saturado.
   - **Distancia y oclusivas**: condensador a 15-25 cm con filtro antipop (o hablar ligeramente fuera del eje del micro); dinámico a 5-15 cm, pegado. Las "p" y "b" que saltan son oclusivas: con pop filter o eje desplazado desaparecen.
   - **Sala**: los condensadores recogen más sala que un micro de auriculares, así que el eco pesa el doble: habitación amueblada, cerca del micro, y si suena a "baño", manta o ropa colgada detrás.
   - **Monitorización**: auriculares enchufados a la salida del propio Behringer (monitorización directa) para oír zumbido o saturación en vivo, no descubrirlos después.
   - **Control previo**: grabar 10 s de silencio (¿hay zumbido de red?) y 20 s de voz (¿se oye claro?). Si hay zumbido, probar otro puerto USB o alejar los cables de alimentación del cable del micro.
5. **Comprobar el nombre** en las diapositivas 1 y 10 (deben mostrar "Fernando Gutiérrez Arenas", ya corregido en la presentación entregada).

## 5. Procedimiento de grabación (PowerPoint integrado)

1. Abrir la presentación → pestaña *Presentación con diapositivas* → *Grabar presentación con diapositivas* → *Empezar la grabación desde el principio*.
2. Grabar bloque a bloque: iniciar la grabación en la diapositiva del bloque, decir el texto, detener la grabación (o pausar) al llegar a la palabra de corte. Repetir el bloque hasta que salga limpio y pasar al siguiente.
3. Alternativa con OBS (más control): grabar pantalla completa a 1080p con la presentación a pantalla completa y el audio del micrófono; los cortes entre bloques se hacen después en el editor.
4. Exportar: *Archivo → Exportar → Crear un vídeo* → 1080p, usar los tiempos grabados → MP4.

## 6. Verificación final (checklist)

- [ ] Duración total ≤ 5:00 (objetivo 4:40).
- [ ] Se oye claro en todo el vídeo (probar con auriculares y sin).
- [ ] Ningún bloque se siente corrido; los números clave se entienden: 4.256.060, 5,23 %, AUROC 1,0000 circular, 0,9846 / 0,8292 / 0,7278 del Experimento B, 0,21 ms.
- [ ] El placeholder de nombre está sustituido en diapositivas 1 y 10.
- [ ] No aparece primera persona en exceso; el registro es el de la memoria: técnico, impersonal, sin vender.
- [ ] Cada transición de diapositiva coincide con el corte del guion.
- [ ] Exportado a MP4 1080p y verificado en otro reproductor (VLC).

## 7. Si sobra o falta tiempo en la práctica

- **Sobra tiempo** (vídeo < 4:30): alargar los bloques 3 y 5 —son los que más contenido técnico condensan— añadiendo un ejemplo concreto (por qué una adjudicación directa sin convocatoria es sospechosa).
- **Falta tiempo** (> 4:50): recortar el bloque 4 (EDA) a una frase —«el riesgo se concentra en patrones sistemáticos, no al azar»— y acortar el bloque 9 a conclusiones sin trabajo futuro.