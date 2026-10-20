# Auditoría estructural de corpus de Mini-Juztina

Reglas 1.2. 779 registros: **302 estructuralmente aptos** y **477 requieren revisión**.

No se realizó cotejo oficial ni verificación de vigencia. No se indexó en ChromaDB. La aptitud es estructural y heurística, no jurídica.

## Por archivo

- `constitucion.jsonl`: 211 registros, 0 aptos, 211 en revisión.
- `codigo_penal_articulos.jsonl`: 568 registros, 302 aptos, 266 en revisión.

## Hallazgos

Los conteos se superponen: un registro puede presentar varios hallazgos. Las detecciones de mezclas, títulos y OCR son indicios para cotejo, no errores jurídicos demostrados.

- `cabecera_pagina_en_texto`: 42 registros.
- `colofon_en_texto`: 1 registros.
- `encabezado_jerarquico_en_texto`: 57 registros.
- `etiqueta_articulo_invalida`: 1 registros.
- `etiqueta_y_cabecera_discrepan`: 1 registros.
- `jerarquia_con_interrogacion`: 8 registros.
- `jerarquia_parcial`: 699 registros.
- `nota_editorial_o_sin_contenido`: 5 registros.
- `numeracion_jerarquica_sospechosa`: 23 registros.
- `numeral_final_sin_contenido`: 4 registros.
- `observacion_del_extractor`: 1 registros.
- `origen_marcado_para_revision`: 211 registros.
- `pagina_solo_aproximada`: 117 registros.
- `posible_mezcla_articulos_o_versiones`: 52 registros.
- `posible_titulo_arrastrado`: 283 registros.
- `posible_titulo_nominal_con_punto`: 1 registros.
- `referencia_duplicada`: 2 registros.
- `salto_numeracion_local`: 3 registros.
- `sin_pagina_pdf_exacta`: 779 registros.
- `texto_identico_no_vacio`: 2 registros.
- `texto_vacio`: 12 registros.

## Casos concretos para cotejar

- `referencia_duplicada`: constitucion.jsonl, línea 188, etiqueta 183; constitucion.jsonl, línea 189, etiqueta 183. No se determina automáticamente si son errores o coincidencias legítimas.
- `texto_identico_no_vacio`: codigo_penal_articulos.jsonl, línea 287, etiqueta 221; codigo_penal_articulos.jsonl, línea 292, etiqueta 224. No se determina automáticamente si son errores o coincidencias legítimas.
- `constitucion.jsonl`, línea 108, etiqueta `102-8`: etiqueta_articulo_invalida.
- `constitucion.jsonl`, línea 158, etiqueta `182`: salto_numeracion_local.
- `constitucion.jsonl`, línea 182, etiqueta `276`: salto_numeracion_local.
- `constitucion.jsonl`, línea 188, etiqueta `183`: etiqueta_y_cabecera_discrepan; observacion_del_extractor; salto_numeracion_local.
- `codigo_penal_articulos.jsonl`, línea 144, etiqueta `Artículo 121-A`: texto_vacio.
- `codigo_penal_articulos.jsonl`, línea 147, etiqueta `Artículo 122-A`: texto_vacio.
- `codigo_penal_articulos.jsonl`, línea 223, etiqueta `Artículo 173-A`: texto_vacio.
- `codigo_penal_articulos.jsonl`, línea 239, etiqueta `Artículo 182`: texto_vacio.
- `codigo_penal_articulos.jsonl`, línea 246, etiqueta `Artículo 186`: numeral_final_sin_contenido.
- `codigo_penal_articulos.jsonl`, línea 250, etiqueta `Artículo 189`: numeral_final_sin_contenido.
- `codigo_penal_articulos.jsonl`, línea 298, etiqueta `Artículo 236`: texto_vacio.
- `codigo_penal_articulos.jsonl`, línea 299, etiqueta `Artículo 238`: texto_vacio.
- `codigo_penal_articulos.jsonl`, línea 300, etiqueta `Artículo 239`: texto_vacio.
- `codigo_penal_articulos.jsonl`, línea 301, etiqueta `Artículo 240`: texto_vacio.
- `codigo_penal_articulos.jsonl`, línea 302, etiqueta `Artículo 241`: numeral_final_sin_contenido.
- `codigo_penal_articulos.jsonl`, línea 319, etiqueta `Artículo 270`: texto_vacio.
- `codigo_penal_articulos.jsonl`, línea 427, etiqueta `Artículo 334`: texto_vacio.
- `codigo_penal_articulos.jsonl`, línea 473, etiqueta `Artículo 374`: texto_vacio.
- `codigo_penal_articulos.jsonl`, línea 558, etiqueta `Artículo 443`: texto_vacio.
- `codigo_penal_articulos.jsonl`, línea 566, etiqueta `Artículo 450`: numeral_final_sin_contenido.

## Cobertura observada, sin inferir catálogo vigente

- `constitucion.jsonl`: 3 etiquetas numéricas no observadas entre 1 y la última etiqueta numérica leída (206): 152, 176, 196.
- `codigo_penal_articulos.jsonl`: 49 etiquetas numéricas no observadas entre 1 y la última etiqueta numérica leída (452): 47, 49, 57, 78, 84, 125, 129, 194, 209, 210, 211, 212, 213, 215, 216, 220, 222, 223, 227, 230, 231, 233, 234, 235, 237, 247, 249, 252, 253, 254, 255, 256, 257, 258, 261, 262, 263, 264, 265, 266, 267, 268, 269, 272, 317, 324, 361, 363, 386.
Estos huecos no demuestran derogaciones ni omisiones jurídicas: también pueden obedecer a extracción o etiquetas erróneas. No se generan artículos para rellenarlos.

## Preservación y normalización

Las cadenas `texto` se exportan literalmente. No se eliminan encabezados, notas, títulos ni errores sospechosos; los registros se ponen en revisión. Se conserva el registro original completo y su procedencia en `audit_records.jsonl` y, para rechazados, `review_required.jsonl`.

Los duplicados se ponen TODOS en revisión, sin seleccionar una supuesta versión correcta. Un texto vacío no se interpreta como artículo derogado. Las páginas aproximadas no se convierten en localizadores exactos. `pagina_pdf` queda null cuando no hay página exacta declarada.

Los campos `parte` y `seccion` del Código Penal permanecen en el original de trazabilidad; no se equiparan a título/capítulo. `version_fuente` identifica el archivo y su fuente declarada, sin afirmar autenticidad o vigencia.

## Archivos

- `articles_structurally_accepted.jsonl`: únicamente aptos, verificados con `core.corpus.read_corpus`, sin indexar.
- `review_required.jsonl`: cada registro pendiente, original completo, candidato normalizado y motivos.
- `audit_records.jsonl`: trazabilidad de TODOS los registros, incluidos los aceptados.
- `audit_report.json`: estadísticas, duplicados, huecos observados, SHA-256 y mapeos.

No se crea `articles.jsonl`: evita activar el corpus de producción antes de su revisión y autorización.

## Siguientes pasos

- Cotejar con PDFs oficiales, incluidos límites, títulos arrastrados y notas de versiones.
- Resolver duplicados, etiquetas sospechosas, páginas y huecos sin inferir texto.
- Calibrar recuperación y abstención después de resolver el corpus.
- Esperar autorización explícita antes de publicar articles.jsonl o indexar en ChromaDB.
