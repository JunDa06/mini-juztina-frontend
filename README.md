# Mini-Juztina — MVP académico experimental

React + Vite, FastAPI, Sentence Transformers, ChromaDB y Ollama `qwen2.5:3b`.
**Corpus provisional: no se certifican integridad normativa, OCR ni vigencia. No es asesoría legal.**

## Alcance y arquitectura

Piloto aislado: Constitución 1, 2, 3, 7 y 7-A; Código Penal 16, 25, 111, 124 y 288.
Diez registros, catorce fragmentos; el constitucional 2 produce cinco fragmentos.
La auditoría de origen comprende 779 registros: 302 estructuralmente aptos y 477 en revisión.
Los cinco constitucionales del piloto siguen pendientes de revisión.

React (`frondend/`, nombre conservado) → POST `localhost:8000/api/chat` →
FastAPI experimental `api.pilot:app` → embeddings CPU y colección Chroma piloto →
Ollama local selecciona evidencia → motor valida citas literales → React muestra respuesta y fuentes.

El motor conserva `answer_question(question: str) -> dict` y los estados `answered`,
`out_of_scope`, `insufficient_evidence`, `error`. La API transforma `documento/articulo/texto/pagina_pdf`
a `law/article/excerpt/page_pdf`. `conversation_id` solo correlaciona: no hay memoria RAG.
La API normal `api.main:app` permanece intacta y no activa el piloto automáticamente.
CORS solo permite localhost y 127.0.0.1 en el puerto 5173.

## Instalación en Windows

Probado con Python 3.13.15, Node 24.20.0, npm 11.19.0, Ollama 0.40.6 y 32 GB RAM.
Extraer TODO el ZIP y abrir PowerShell en la carpeta raíz extraída.
`python` debe resolver a Python 3.13; sustituirlo por la ruta completa del intérprete si es necesario.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-api.txt
.\.venv\Scripts\python.exe -m pip check
Push-Location .\frondend
npm.cmd ci --ignore-scripts --no-audit --no-fund
Pop-Location
ollama pull qwen2.5:3b
```

Si Ollama no está iniciado, ejecutar `ollama serve` en otra terminal. Si ya responde
en `127.0.0.1:11434`, no iniciar otra instancia.

El ZIP incluye embeddings y una instantánea del índice piloto; excluye Python, Node,
Ollama, `.venv`, `node_modules`, cachés y backups de la máquina. La instalación inicial
de dependencias y del modelo Ollama requiere Internet.

**Después de extraer en otra ruta, recrear el recibo con las rutas locales:**

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.pilot_index plan
.\.venv\Scripts\python.exe -X utf8 -m scripts.pilot_index index --execute
```

Con el modelo incluido, la operación es idempotente: abre la colección lista y conserva
los catorce fragmentos; genera el recibo local. Solo usa los diez candidatos y
`storage/pilots/pilot-10-ced16af809467bef`. No ejecutar `core.cli index` para esta demo.
Los JSON operativos del ZIP tienen rutas relativas por privacidad y necesitan este paso.

No editar archivos de `models/multilingual-e5-small`: todos participan en su fingerprint.
Si se pierde esa carpeta, preparar de nuevo con Internet y la revisión fija:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_model.py --revision 614241f622f53c4eeff9890bdc4f31cfecc418b3
.\.venv\Scripts\python.exe -m scripts.pilot_index index --execute
```

Un modelo reconstruido puede tener otro fingerprint y producir otra colección piloto,
sin borrar la anterior. El ZIP completo conserva el modelo de las pruebas.

## Ejecutar el piloto

Terminal 1, desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.pilot:app --host 127.0.0.1 --port 8000 --workers 1
```

Terminal 2, inicialmente desde la raíz:

```powershell
Set-Location .\frondend
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Abrir http://localhost:5173/. Si 8000 está ocupado por la API normal, detener esa
instancia propia con Ctrl+C. React apunta a 8000; una API en 8001 no lo conecta.
Debe aparecer el aviso `PILOTO EXPERIMENTAL: texto no cotejado oficialmente.`.

Consulta principal: **¿Cuándo comienza la tentativa según el artículo 16 del Código Penal?**
Abstención: **¿Qué dispone el artículo 999 del Código Penal?**
La generación puede abstenerse incluso con evidencia recuperada. Ver `DEMO_ACADEMICA.md`.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -X utf8 -m scripts.release_smoke
Push-Location .\frondend
npm.cmd run build
Pop-Location
```

`release_smoke` usa FastAPI, Chroma persistente, embeddings y Ollama reales. Bloquea
DNS y sockets externos EN SU PROCESO Python, permite loopback y comprueba cita/fuente
literal del artículo 16 y abstención para el 999. No desconecta la red del equipo
ni bloquea otros procesos, incluido Ollama. No equivale a una prueba del equipo
físicamente desconectado. Evidencia: `release/SMOKE_RESULT.json`.

Las pruebas unitarias usan fixtures sintéticos en temporales, sin mezclarlos con el
piloto. `tests.integration_local` es una integración antigua con corpus sintético temporal.
Resumen vigente de release: `release/RELEASE_REPORT.md`.

## Datos y reversión

Originales intactos en `data/sources/`; auditoría y candidatos en `data/processed/`.
No se corrigió texto jurídico mediante inferencias. Las páginas aproximadas no son
citas exactas: `pagina_pdf` sigue null. Ver `data/processed/AUDIT_REPORT.md`.

El ZIP usa una selección explícita de archivos y excluye credenciales y configuración
privada. `FILE_MANIFEST.json` contiene tamaños y SHA-256 de sus archivos.
Se conservan el model card y los recursos del modelo local.

No eliminar el piloto para instalar o demostrar. Si posteriormente se autoriza retirarlo,
detener sus consultas y ejecutar `.\.venv\Scripts\python.exe -m scripts.pilot_index remove --execute`.
Solo elimina la colección del recibo, sin borrado recursivo ni cambios en el principal.
No ejecutar esa reversión durante la demostración.

## Limitaciones

- Cotejo oficial, revisión OCR, integridad de incisos y vigencia pendientes.
- Umbral 0.82 provisional; muestra de recuperación pequeña.
- Abstenciones observadas en consultas constitucionales pese a recuperar fragmentos.
- Sin memoria RAG; conversaciones React solo en memoria del navegador.
- La interfaz no muestra actualmente `page_pdf`.
- Solo uso académico local, sin autenticación ni preparación para exposición pública.
- La instalación inicial requiere Internet y tiempo; preparar antes de la presentación.
- No se verificó una instalación limpia en otro equipo físico.
