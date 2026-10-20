# Resultados de integración — 20 de octubre de 2026

## Resultado

**React → FastAPI → motor RAG verdadero verificado en el navegador.**
React mostró «No hay corpus local disponible.» al enviar una pregunta constitucional.
Evidencia visual: `INTEGRATION_PROOF.png`. No se reemplazó el motor por simulaciones.

## Archivos nuevos

- `api/__init__.py`, `api/main.py`: API, validación, adaptación y CORS.
- `tests/test_api.py`: 15 pruebas adicionales del adaptador.
- `requirements-api.txt`, `requirements-api-lock.txt`: dependencias adicionales y versiones probadas.
- `INTEGRATION.md`: contrato, comandos PowerShell, pruebas y límites.
- `INTEGRATION_RESULTS.md`: este informe.
- `INTEGRATION_PROOF.png`: captura del navegador después del intercambio real.

No se editaron ni eliminaron archivos fuente existentes. Se compararon SHA-256
antes y después para todos los módulos `core/*.py`, fuentes `frondend/src/*.*`,
`frondend/package.json`, `frondend/package-lock.json`, `frondend/vite.config.js`,
requirements originales y `scripts/setup.ps1`: **sin cambios**.
La instalación/compilación generó `frondend/node_modules/`, `frondend/dist/`,
caché local `.cache/npm/` y bytecode de Python, sin sustituir fuentes ni manifiestos.

## Resultados observados

- Python **3.13.15**, FastAPI **0.135.1**, Starlette **1.9.0**, Pydantic **2.14.1**,
  Uvicorn **0.54.0**, HTTPX **0.28.1**. `pip check`: **No broken requirements found**.
- `python -m unittest discover -v`: **37 pruebas aprobadas**, 22 existentes + 15 nuevas.
  Incluyen cadenas vacías, espacios, tipos incorrectos, campos ausentes, JSON
  inválido, alias de fuentes, página null, conservación de estados y respuesta,
  ausencia de memoria, CORS permitido/prohibido y ocultación de errores internos.
- `python -u -m tests.integration_local`: **pasó** (código 0). Modelo de embeddings,
  Chroma persistente y Ollama reales; 3 artículos explícitamente sintéticos en
  carpeta temporal, reapertura desde otro proceso, respuesta con cita literal y
  abstención sin evidencia. No se creó índice jurídico real.
- Node **24.20.0**, npm **11.19.0**; `npm ci` instaló 143 paquetes desde el lock
  existente, sin modificarlo.
- `npm run build`: **pasó** con Vite **8.3.4**, 17 módulos transformados,
  compilación de Vite en 1.42 segundos. Salida en `frondend/dist/`.
- Uvicorn iniciado en `127.0.0.1:8000`; Vite en `127.0.0.1:5173`.
- POST HTTP real a `http://localhost:8000/api/chat`: **200**, con:
  `answer="No hay corpus local disponible."`, `status="insufficient_evidence"`,
  `sources=[]`, `conversation_id="verificacion-http-real"`.
  Cabecera CORS del origen local conservada.
- POST HTTP real con mensaje en blanco: **422**, respuesta genérica sin traceback.
- Preflight real: ambos orígenes locales **200** con origen exacto autorizado;
  origen externo rechazado sin permiso CORS (también cubierto por prueba automatizada).
- Navegador en `http://localhost:5173`: se introdujo y envió
  «¿Qué dispone el artículo 2 de la Constitución Política del Perú?» mediante los
  controles existentes. React mostró la respuesta real del motor, sin error de conexión.

## Límites pendientes

No existe el corpus real ni el índice definitivo en las rutas configuradas.
No se ha validado al asistente para consultas jurídicas reales. No hay memoria
conversacional en RAG: el identificador solo se devuelve para correlación.
`page_pdf` se conserva en el intercambio, pero React no lo muestra actualmente.
El frontend conserva su manejo genérico de HTTP 422/500 como error de conexión.
Esas funcionalidades existentes no se reescribieron.

La instalación inicial encontró restricciones de red del entorno aislado; las
descargas se completaron después con el permiso de red correspondiente. No quedan
fallos observados de pruebas, dependencias o compilación.
