# Integración HTTP local de Mini-Juztina

El adaptador está en `api/main.py`. Conserva `core/` y `frondend/` sin cambios.
El nombre `frondend` es intencional y se mantiene.

## Iniciar desde PowerShell

Las dependencias ya están instaladas en `.venv` con Python 3.13.15.
Para reproducir la instalación en ese entorno:

```powershell
Set-Location 'C:\Users\senat\Desktop\Mini-Juztina'
.\.venv\Scripts\python.exe -m pip install -r requirements-api.txt
.\.venv\Scripts\python.exe -m pip check
```

El archivo adicional `requirements-api.txt` incorpora los requirements originales y
aplica `requirements-api-lock.txt`, generado del entorno probado. No sustituye los
archivos originales. Usa este archivo adicional al preparar la API; el instalador
original `scripts/setup.ps1` solo prepara el motor.

Terminal 1, backend:

```powershell
Set-Location 'C:\Users\senat\Desktop\Mini-Juztina'
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Terminal 2, frontend:

```powershell
Set-Location 'C:\Users\senat\Desktop\Mini-Juztina\frondend'
# Solo en una instalación nueva, si falta node_modules:
# npm.cmd ci --ignore-scripts --no-audit --no-fund
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Abrir `http://localhost:5173` o `http://127.0.0.1:5173`. `--strictPort` evita que
Vite cambie silenciosamente a un puerto que CORS no permite. Si estos servidores
siguen activos tras la verificación, no iniciar otras copias. Para detener una
instancia iniciada en una terminal, pulsar Ctrl+C en esa terminal.

Solo se escucha en loopback. Un único worker y un lock serializan el acceso al
motor CPU y su carga inicial. La ruta síncrona se ejecuta en el pool de hilos de
FastAPI; no cambia la lógica de recuperación ni generación del motor.

## Contrato

`POST http://localhost:8000/api/chat`, `Content-Type: application/json`:

```json
{"message":"Pregunta académica","conversation_id":"identificador-del-cliente"}
```

`message` debe ser cadena de 1 a 2000 caracteres, con contenido distinto de espacios.
El máximo coincide con el límite existente del motor. Se conserva el mensaje original
al invocar `core.rag_engine.answer_question(message)`. `conversation_id` debe ser
cadena y se devuelve sin cambios. Campos adicionales se rechazan.

El adaptador mantiene `answer` y `status` del RAG. Transforma cada fuente de esta forma:

- `documento` → `law`
- `articulo` → `article`
- `texto` → `excerpt`
- `pagina_pdf` → `page_pdf`, incluido null

React ya usa `excerpt` y solo usa `text` como alternativa, por lo que no se duplica
el texto. No se inventan `score` ni `url`. La interfaz actual no muestra `page_pdf`,
pero el dato se conserva en JSON para su posterior uso.

**El RAG sigue sin estado conversacional.** `conversation_id` correlaciona la respuesta;
no añade historial a la pregunta ni almacena conversaciones en el servidor.

Los cuatro estados válidos del motor se conservan con HTTP 200, incluido `error` si
lo devuelve el propio motor. Solicitudes inválidas reciben HTTP 422 con mensaje
genérico. Una excepción inesperada o contrato RAG inválido recibe HTTP 500 con
`status=error`, sin fuentes ni detalles internos; el diagnóstico queda en logging local.
El frontend actual presenta cualquier HTTP no exitoso con su mensaje genérico de
conexión. Ese comportamiento preexistente no se modificó.

Solo se autorizan los orígenes CORS `http://localhost:5173` y
`http://127.0.0.1:5173`, método POST y cabecera Content-Type, sin credenciales.
Un origen externo no recibe permiso CORS. No hay autenticación adicional en esta
API de desarrollo local. No se han habilitado Swagger/ReDoc, para evitar sus recursos
remotos; el esquema está disponible localmente en `/openapi.json`.

Abrir `/api/chat` directamente en una pestaña realiza GET y devuelve **405**:
esa ruta requiere POST y un cuerpo JSON.

## Comprobar una solicitud real

Con el backend activo, desde una tercera terminal PowerShell:

```powershell
$payload = @{
    message = '¿Qué dispone el artículo 2 de la Constitución?'
    conversation_id = 'verificacion-local'
} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:8000/api/chat' -Method Post `
    -ContentType 'application/json; charset=utf-8' `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($payload))
```

Mientras falte el corpus, el resultado real es `insufficient_evidence`,
`answer="No hay corpus local disponible."`, `sources=[]` y el mismo identificador.
No se simula una respuesta jurídica.

## Verificación

```powershell
Set-Location 'C:\Users\senat\Desktop\Mini-Juztina'
.\.venv\Scripts\python.exe -m unittest discover -v
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe -u -m tests.integration_local
.\.venv\Scripts\python.exe -m pip check
Set-Location '.\frondend'
npm.cmd run build
```

`tests/test_api.py` usa fixtures identificados como pruebas para comprobar la
transformación y los errores. Incluye además una llamada al RAG real sin mocks
cuando falta el corpus. La integración existente utiliza el modelo, Chroma y Ollama
reales con corpus sintético en una carpeta temporal; nunca lo publica como legislación.

El corpus `data/processed/articles.jsonl` y el índice jurídico definitivo siguen
ausentes. Se necesita integrarlos y evaluar preguntas jurídicas con fuentes esperadas.
Esta integración HTTP no valida calidad jurídica ni calibra el umbral de recuperación.

Referencias técnicas: [CORS de FastAPI](https://fastapi.tiangolo.com/tutorial/cors/)
y [pruebas de FastAPI](https://fastapi.tiangolo.com/tutorial/testing/).
