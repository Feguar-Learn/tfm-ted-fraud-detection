# Anexo A — Reporte de calidad del dataset TED (Fase 1)

Este anexo documenta la limpieza y el control de calidad de los datos TED en los que se apoya la memoria (sección 2). El procesamiento completo vive en el notebook `notebooks/TFM_analysis.ipynb` (celdas de limpieza CAN/CN y cruce), que es el entregable único y reproducible.

## Resumen del procesamiento

| Dataset | Filas raw | Filas limpias | Reducción | Nivel de análisis |
|---------|-----------|---------------|-----------|-------------------|
| Contract Award Notices (CAN) 2018-2023 | 6.198.063 | 4.256.060 | 31,3 % | `ID_AWARD` (adjudicación) |
| Contract Notices (CN) 2018-2023 | 7.716.823 | 4.901.725 | 36,5 % | (`ID_NOTICE_CN`, `ID_LOT`) |
| **Tabla maestra fusionada (CAN+CN)** | — | **4.256.060** | — | `ID_AWARD` |

## Criterios de limpieza aplicados

### Contract Award Notices (CAN)
1. **`CANCELLED != 1`**: descarte de notices canceladas (25 notices, código 1.1 del codebook).
2. **`ID_AWARD` no nulo**: descarte de filas que no son adjudicaciones reales (corresponden a encabezados de notice sin sección V).
3. **`ISO_COUNTRY_CODE` y `CPV` no nulos**: metadatos mínimos para el análisis.
4. **`INFO_ON_NON_AWARD` no en {PROCUREMENT_UNSUCCESSFUL, PROCUREMENT_DISCONTINUED}**: descarte de adjudicaciones no realizadas (983.894 filas, 15,9 % del raw).
5. **Deduplicación por `ID_AWARD`**: en caso de correcciones posteriores, se conserva la fila con `DT_AWARD` más reciente y mayor `CORRECTIONS` (codebook 3.6).
6. **Normalización de categóricas**: trim + upper; valores `""`, `N/A`, `NA`, `NULL` → NULL.

### Contract Notices (CN)
1. **`CANCELLED != 1`**: 1.216 notices canceladas descartadas.
2. **`ISO_COUNTRY_CODE` y `CPV` no nulos**: metadatos mínimos.
3. **Cálculo de `DURATION_M`** (Anexo II del codebook):
   - Si `DURATION` existe (meses), se usa directamente.
   - Si no, se calcula como `(CONTRACT_COMPLETION − CONTRACT_START) / 30,4`.
4. **Deduplicación por `(ID_NOTICE_CN, ID_LOT)`**: se conserva la fila con mayor `CORRECTIONS`.
5. **Normalización de categóricas**: igual que en el CAN.

### Cruce CAN ← CN
- Clave: `CAN.ID_NOTICE_CAN = CN.FUTURE_CAN_ID` (codebook sección 4).
- Tipo: **LEFT JOIN** desde el CAN, que conserva las 4.256.060 adjudicaciones de la tabla maestra.
- Si un CAN tiene varios CN asociados (republicación del concurso), se conserva el primer CN publicado (menor `ID_NOTICE_CN`).
- Se añade la columna `HAS_CN` (1 si la adjudicación tiene CN asociado, 0 si no).

| HAS_CN | Filas | % |
|--------|-------|---|
| 1 (con CN) | 2.797.768 | 65,8 % |
| 0 (sin CN) | 1.458.292 | 34,2 % |

> El 34,2 % de adjudicaciones sin CN corresponde a procedimientos AWP (award without prior publication) y NOC/NOP (negotiated without call for competition) — ambos constituyen *red flags* OCDE directas.

## Cobertura temporal

| Año | Adjudicaciones | Concursos |
|-----|----------------|-----------|
| 2018 | 615.435 | 700.933 |
| 2019 | 675.316 | 812.146 |
| 2020 | 690.921 | 812.262 |
| 2021 | 760.030 | 825.160 |
| 2022 | 750.959 | 890.302 |
| 2023 | 763.399 | 860.922 |

## Top 10 países por número de adjudicaciones

| País | Adjudicaciones | % del total |
|------|----------------|-------------|
| PL (Polonia) | 810.807 | 19,0 % |
| FR (Francia) | 636.969 | 15,0 % |
| RO (Rumanía) | 492.255 | 11,6 % |
| DE (Alemania) | 439.284 | 10,3 % |
| ES (España) | 248.449 | 5,8 % |
| CZ (Chequia) | 183.714 | 4,3 % |
| SI (Eslovenia) | 174.326 | 4,1 % |
| IT (Italia) | 156.890 | 3,7 % |
| UK (Reino Unido) | 131.955 | 3,1 % |
| SE (Suecia) | 115.029 | 2,7 % |

## Esquema XML dominante (XSD_VERSION)

| XSD_VERSION | Filas | % |
|-------------|-------|---|
| R209.S3 | 1.772.034 | 41,6 % |
| R209.S5 | 1.588.494 | 37,3 % |
| R209.S4 | 535.457 | 12,6 % |
| R209.S2 | 255.424 | 6,0 % |
| R208.S3 | 49.669 | 1,2 % |
| R208.S4 | 43.855 | 1,0 % |
| R208.S5 | 11.127 | 0,3 % |

> El 97,5 % de los registros usan XSD 2.0.9 (R209), lo que garantiza la disponibilidad de las variables críticas para el *feature engineering* (`ID_LOT`, `WIN_NATIONALID`, `B_ACCELERATED`, `B_CONTRACTOR_SME`, etc.).

## Calidad por columna (tabla maestra fusionada)

### Variables monetarias

| Columna | % nulos | Media | Máx. | Observaciones |
|---------|---------|-------|------|---------------|
| `AWARD_VALUE_EURO_FIN_1` | 2,5 % | 1,9 × 10⁸ | 1,14 × 10¹³ | Outliers extremos; truncado según el método de Winsor |
| `VALUE_EURO_FIN_1_CN` (estimado) | 65,0 % | — | — | Solo con HAS_CN=1; imputación por mediana sector/país |
| `AWARD_EST_VALUE_EURO` | — | — | — | Estimación previa; uso como respaldo |
| Ratio adjudicado/estimado | — | 73.526 | 3,66 × 10⁹ | Outliers; truncado a [P1, P99] según el método de Winsor |

### Variables de competencia

| Columna | % nulos | Media | Distribución |
|---------|---------|-------|--------------|
| `NUMBER_OFFERS` | 3,0 % | 56 (con outliers) | 1 oferta: 32 %, 2: 18 %, 3: 13 %, ≥10: 6 % |
| `NUMBER_TENDERS_SME` | — | — | — |
| `NUMBER_TENDERS_OTHER_EU` | — | — | — |
| `NUMBER_TENDERS_NON_EU` | — | — | — |

> **Red flag clave**: el 32 % de adjudicaciones se realizaron con una sola oferta (falta de competencia).

### Variables categóricas de procedimiento

| Columna | % nulos | Valores principales |
|---------|---------|---------------------|
| `TOP_TYPE` | bajo | OPE (open), NIC/NIP (negotiated w/ call), NOC/NOP (negotiated w/o call), AWP (award w/o prior pub), RES (restricted) |
| `B_ACCELERATED` | bajo | Y / N |
| `TYPE_OF_CONTRACT` | 0 % | W (Works), U (Supplies), S (Services) |
| `B_EU_FUNDS` | — | Y / N |
| `B_ELECTRONIC_AUCTION` | — | Y / N |
| `CRIT_CODE` | — | L (Lowest price), M (Most economically advantageous) |
| `INFO_UNPUBLISHED` | 3,0 % | Y = secciones confidenciales marcadas (*red flag* directa) |

### Identificación de comprador y adjudicatario

| Columna | % nulos | Uso en el *feature engineering* |
|---------|---------|--------------------------------|
| `CAE_NATIONALID` | ~20 % | Detección de autocontratación (vs `WIN_NATIONALID`) |
| `CAE_NAME` | < 5 % | Construcción de histórico de comprador |
| `WIN_NATIONALID` | ~25 % | Detección de autocontratación y ganador recurrente |
| `WIN_NAME` | < 5 % | Construcción de histórico de adjudicatario |
| `WIN_COUNTRY_CODE` | ~10 % | Detección de ganador offshore |

## Hallazgos de calidad detectados

1. **Columnas con valores sucios mezclados**: `B_AWARDED_TO_A_GROUP` e `INFO_UNPUBLISHED` contienen en algunos registros textos erróneos (nombres de empresas en griego, números de ID, etc.). En el *feature engineering* se filtraron a valores válidos (`Y`/`N`/`NULL`).
2. **Outliers extremos en monetarios**: los valores máximos de 10¹³ € en `AWARD_VALUE_EURO_FIN_1` son errores de captura. Se aplicó truncado a [P1, P99] por país y por sector CPV según el método de Winsor.
3. **Outliers en `NUMBER_OFFERS`**: un máximo de 46 millones de ofertas es un error. Se truncó a [0, P99] por país.
4. **`DURATION_M_CN` con valores negativos y máximos de 10⁷**: errores de captura; se acotó a [0, 600] meses (50 años) por sentido de negocio.
5. **24,6 % de CN sin `FUTURE_CAN_ID`**: CN que no desembocaron en un CAN publicado dentro del periodo, o cuyas adjudicaciones aún no se publicaron.

## Conclusiones para el feature engineering

- La tabla maestra fusionada tiene cobertura suficiente para construir 15-20 *features* de *red flags* OCDE.
- Las variables críticas (`TOP_TYPE`, `B_ACCELERATED`, `NUMBER_OFFERS`, `AWARD_VALUE_EURO_FIN_1`, `INFO_UNPUBLISHED`, `WIN_NATIONALID`, `CAE_NATIONALID`, `HAS_CN`) están presentes en >95 % de las filas o tienen un significado claro cuando faltan (*red flag* directa).
- Los outliers se trataron con truncado por cuantiles condicionado a país y sector CPV (división de 2-3 dígitos) según el método de Winsor.
- Los nulos en `VALUE_EURO_FIN_1_CN` se imputaron por mediana sector+país+año cuando fue posible, y por mediana de país en caso contrario.

## Archivos generados

| Archivo | Tamaño | Descripción |
|--------|--------|-------------|
| `data/processed/can_clean.parquet` | 1,1 GB | CAN limpio, nivel `ID_AWARD` |
| `data/processed/cn_clean.parquet` | 555 MB | CN limpio, nivel (`ID_NOTICE_CN`, `ID_LOT`) |
| `data/processed/ted_merged.parquet` | 1,1 GB | Tabla maestra fusionada CAN+CN, nivel `ID_AWARD` (4.256.060 filas) |

**Compresión**: Snappy. **Formato**: *Parquet* columnar.