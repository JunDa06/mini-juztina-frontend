# Resultados observados — 20 de octubre de 2026

## Entorno verificado

- Windows x64; `.venv` usa Python **3.13.15** instalado localmente en `.runtime`.
- Ollama HTTP local: **0.40.6**; modelo disponible: **qwen2.5:3b**.
- ChromaDB **1.5.9**, sentence-transformers **5.3.0**, PyTorch **2.14.1**,
  transformers **5.20.2**. Versiones completas en `requirements-lock.txt`.
- Embeddings CPU: `intfloat/multilingual-e5-small`, revisión
  `614241f622f53c4eeff9890bdc4f31cfecc418b3`, guardado en `models/multilingual-e5-small`.

## Pruebas ejecutadas

- `python -m unittest discover -q`: **22 pruebas pasaron** en Python 3.13.15.
  Incluyen contrato, metadatos locales, página null, referencias y citas inventadas,
  evidencia débil, abstención del modelo, corpus ausente, pregunta inválida,
  timeout, JSON inesperado, índice inconsistente, IDs y referencias duplicados,
  páginas inválidas, campos ausentes, ámbito, documento/artículo incorrectos,
  rechazo del corpus sintético en configuración de producción y Ollama remoto.
  Los mensajes de rechazo y traceback del timeout son escenarios negativos esperados.
- `python -m pip check`: **No broken requirements found**.
- `python -m compileall -q core scripts tests`: salida correcta, código 0.
- CLI pública sin corpus: `status=insufficient_evidence`, `sources=[]`.
- `python -u -m tests.integration_local`: **pasó**, código 0.
  Tres registros **SINTÉTICOS NO OFICIALES**, creados solo en carpeta temporal.
  Indexación real con Sentence Transformers y Chroma: 3 artículos / 3 fragmentos;
  segunda indexación idempotente; tokenización de texto extenso sin perder el final
  y fragmentos de tamaño admitido por el modelo.
  Un proceso nuevo abrió el índice persistido y consultó Ollama real.
  «¿A qué hora abre la biblioteca de ensayo?» produjo `answered`, una única fuente
  `TEST-A` y la cita literal «En esta prueba sintética, la biblioteca de ensayo abre a las nueve.».
  «¿Qué sanción corresponde al robo agravado?» produjo `insufficient_evidence`, sin fuentes.
  Durante indexación y consulta un audit hook rechazaba DNS y sockets externos;
  solo se permitía loopback. No se activó ninguna conexión externa.

## Pendiente para validar el sistema jurídico

No existe `data/processed/articles.jsonl`. No se indexaron ni se probaron la
Constitución ni el Código Penal reales. No se ha medido precisión, cobertura,
calidad de OCR, vigencia o fidelidad a PDFs. El umbral 0.82 es provisional.
Al recibir el corpus: validar nombres y versiones, indexarlo y evaluar preguntas
con fuentes esperadas y casos de abstención etiquetados por el equipo.

La verificación literal impide publicar citas generadas que no estén en el corpus;
no prueba que una cita sea jurídicamente pertinente o suficiente. Las respuestas
son extractivas, sin conclusiones jurídicas libres del modelo.

No se crearon ni modificaron `frontend/`, `ingestion/` o `docs/`.
