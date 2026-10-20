# Verificación del piloto, sin indexación

Fecha: 20 de octubre de 2026. Entorno: Python 3.13.15.

## Resultados observados

- Preparados diez candidatos con el contrato real de `core.corpus.read_corpus`.
- Constitución: 1, 2, 3, 7, 7-A. Todos siguen en revisión.
- Código Penal: 16, 25, 111, 124, 288. Todos pertenecen a los estructuralmente aptos.
- Los diez textos coinciden literalmente con la extracción original y el registro
  normalizado auditado. El constitucional 2 conserva sus 9278 caracteres.
- Los identificadores y la procedencia de la auditoría se conservaron, sin
  corregir ni renumerar incisos.
- SHA-256 del archivo provisional:
  `ced16af809467bef73fe5cf0dfd4db792dbdd7956543427880da2690533e81df`.
- `manifest.json` no declara cotejo oficial ni verificación jurídica de ningún candidato.
- `python -m scripts.pilot_index plan` pasó: valida integridad, calcula la colección
  y la ruta aisladas mediante lectura. No construye `PersistentClient`.
- `python -m unittest discover -q`: **78 pruebas aprobadas**, 62 existentes + 16 nuevas.

Las nuevas pruebas cubren conservación de incisos y espacios, procedencia,
selección penal estricta, candidatos ambiguos, rechazo de alteraciones de texto,
hashes falsificados, aislamiento, negativa a sobrescribir el piloto y necesidad
de ejecución explícita para las mutaciones.

Las pruebas de los adaptadores de indexación y reversión usan únicamente dobles:
**no crean ni eliminan colecciones reales**. Sus fixtures son sintéticos y se
generan en directorios temporales; no se mezclan con los diez candidatos reales.
La integración existente que sí indexa en Chroma no se ejecutó en esta fase.

## No ejecutado y pendiente

No se ejecutó el comando de indexación ni el de reversión. No se creó almacenamiento
Chroma piloto, recibo de indexación ni `data/processed/articles.jsonl`; no se modificó
el índice de producción ni se conectó el piloto a FastAPI/React.

No se cotejaron PDFs oficiales. Tampoco se verificaron completitud, vigencia,
precisión semántica o respuestas RAG del piloto. El procedimiento futuro reutiliza
el indexador existente, pero su escritura real sigue pendiente de autorización.
