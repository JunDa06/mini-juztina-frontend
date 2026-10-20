# Verificación de la auditoría estructural

Fecha: 20 de octubre de 2026. Python 3.13.15. Reglas de auditoría 1.2.

## Resultados finales

- 779 registros originales: 211 constitucionales y 568 penales.
- 302 estructuralmente aptos, todos del Código Penal.
- 477 requieren revisión: 211 constitucionales y 266 penales.
- 779 identificadores únicos y trazables a archivo SHA-256 y línea original.
- Las 779 cadenas de texto normalizadas candidatas coinciden literalmente con
  sus cadenas originales. También se compararon los objetos originales completos.
- Los 302 aptos pasaron el lector real `core.corpus.read_corpus`, con nombres
  canónicos, campos exigidos, IDs únicos y referencias no duplicadas.
- Cada registro pertenece exactamente a una de las dos salidas: aceptados o revisión.
- Los SHA-256 de las tres salidas JSONL coinciden con el manifiesto de `audit_report.json`.
- No se creó `data/processed/articles.jsonl` ni `storage/chroma`.

## Pruebas automatizadas

Comando ejecutado desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -q
```

**62 pruebas aprobadas**: 37 existentes del motor/API y 25 nuevas de auditoría.
Las nuevas prueban preservación literal de Unicode, saltos y espacios; campos
compatibles; duplicados sin descarte arbitrario; páginas aproximadas; marcadores
de extracción; OCR; encabezados mezclados; discrepancias de etiquetas;
numeración romana; etiquetas ambiguas sin adivinar; títulos arrastrados;
numerales finales vacíos; JSON/UTF-8 inválido y claves duplicadas;
procedencia; determinismo de IDs; originales intactos y rechazo de sobreescritura.
Los datos sintéticos usados por estas pruebas se generaron exclusivamente en
directorios temporales y nunca se incorporaron al corpus real.

No se ejecutó `tests.integration_local`, porque ese programa realiza indexación
Chroma temporal y esta fase prohíbe indexar. Los tracebacks de timeout emitidos
por las pruebas existentes son escenarios negativos esperados, no fallos de la suite.

## Integridad de originales

- `constitucion.jsonl`:
  `13024e099fb66be51495cca19ecffad1bd4286c6f8c55d42694ba45eb7667935`
- `codigo_penal_articulos.jsonl`:
  `09427616d524e625b5afd967429b18aaba2f5feb8b73e5a2f6dcdf6958d8eb8c`

Los hashes fueron comprobados antes y después de la normalización.
No se modificaron originales, React, FastAPI ni el motor RAG.

## Hallazgos destacados

- Constitución: los 211 registros declaran `borrador_ocr_requiere_revision`.
  La etiqueta 183 aparece dos veces (líneas 188 y 189); en la línea 188 el
  encabezado literal dice 182 y el extractor declara haber cambiado la etiqueta
  por continuidad. No se adoptó esa corrección como válida.
- Etiqueta `102-8` y saltos locales `151 → 182 → 153`, `175 → 276 → 177`,
  `181 → 183 → 183`: conservados sin inferir los números pretendidos.
- Código Penal: 12 textos vacíos; dos artículos distintos, 221 y 224,
  con texto idéntico no vacío. Todos esos registros quedan en revisión.
- Cuatro textos penales terminan en numeral aislado: etiquetas 186, 189,
  241 y 450. No se completaron sus enumeraciones.
- Se señalaron posibles títulos, capítulos, notas editoriales y versiones
  incrustadas. Los conteos de estas señales son superpuestos y heurísticos;
  no demuestran por sí solos errores jurídicos.
- No hay páginas PDF exactas declaradas. Las 117 páginas constitucionales
  aproximadas se conservan en el original de trazabilidad; `pagina_pdf` queda null.

## Reproducir sin sobrescribir resultados

El normalizador rechaza sobrescribir salidas existentes. Usar otro directorio nuevo:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.audit_corpus --output .cache/auditoria-comparacion-nueva
```

No llama a Chroma ni a Ollama. Solo valida el contrato del lector y escribe
los artefactos de auditoría. La clasificación se basa en las reglas documentadas,
no en cotejo oficial, autenticación del documento o verificación de vigencia.

**Pendiente:** cotejo humano con PDFs oficiales y revisión de todos los indicios,
incluidos posibles falsos positivos y problemas no detectados automáticamente.
La auditoría jurídica no está completada. Se espera autorización antes de indexar.
