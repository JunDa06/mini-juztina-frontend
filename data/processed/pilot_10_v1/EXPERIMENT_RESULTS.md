# Indexación experimental aislada — 20 de octubre de 2026

**Resultado técnico: indexado y probado. Contenido normativo NO cotejado ni validado.**

## Alcance y aislamiento

Solo se indexaron los diez candidatos autorizados: Constitución 1, 2, 3, 7,
7-A; Código Penal 16, 25, 111, 124, 288. Sus textos y metadatos originales
permanecieron intactos. No se incorporaron fixtures sintéticos al índice real.

Antes de ejecutar se leyeron `INDEX_PLAN.json`, `manifest.json` y
`scripts/pilot_index.py`, y se recalculó el plan. Coincidió con el plan aprobado.
La base y colección son independientes:

- Ruta: `storage/pilots/pilot-10-ced16af809467bef`.
- Colección: `pilot_articles_6c8fe3e916f803a176aee9950c6e9dc62df438a6`.
- Corpus SHA-256: `ced16af809467bef73fe5cf0dfd4db792dbdd7956543427880da2690533e81df`.
- Modelo local de embeddings: `models/multilingual-e5-small`, sin descargas.

El almacenamiento principal `storage/chroma` no existía antes y sigue sin existir.
No se creó `data/processed/articles.jsonl`. No se cambió la configuración
predeterminada del motor ni la implementación de `api.main:app` o React.

## Copia previa

Directorio: `backups/pilot_10_v1_before_index_20261020T153755Z`.
Contiene `backup_manifest.json` y copia de **43 archivos protegidos**: originales,
derivados de auditoría, preparación del piloto, código original core/API/React y
manifiestos de dependencias. Los hashes de las copias se comprobaron al crearlas.

No había base piloto que respaldar. El manifiesto registra expresamente la
ausencia de almacenamiento piloto y principal antes de ejecutar. Se verificó
después que los 43 archivos conservan sus SHA-256 y que el principal no apareció.

## Indexación y persistencia reales

Comando ejecutado, con autorización explícita del usuario:

```powershell
Set-Location 'C:\Users\senat\Desktop\Mini-Juztina'
.\.venv\Scripts\python.exe -u -m scripts.pilot_index index --execute
```

Terminó con código 0. Se almacenaron **10 registros distintos y 14 fragmentos**:
el constitucional 2 produjo cinco fragmentos; cada uno de los otros nueve, uno.
Recibo de ejecución: `index_receipt.json`.

Después de salir del proceso indexador, `python -m scripts.verify_pilot` abrió la
base persistida desde otro proceso. Verificó la colección completa, los diez IDs
de artículos y los 14 IDs/documentos/metadatos frente al particionado reproducido
de los candidatos. La comparación de todos los fragmentos fue exacta.

`manifest.json`, `INDEX_PLAN.json`, `COTEJO.md` y `TEST_RESULTS.md` se conservan como
artefactos de la fase de preparación, que entonces no había indexado. El estado
operativo posterior está en `index_receipt.json` y este informe; no implica cambio
del estado de cotejo oficial, que continúa pendiente.

## Recuperación

Resultados completos: `retrieval_results.json`.

- **10/10 búsquedas exactas** por ID de artículo y por una subcadena literal
  encontraron el registro correcto.
- **8/8 búsquedas semánticas** recuperaron el artículo esperado por tema del
  texto local dentro de los cinco primeros resultados.
- **7/8** lo situaron primero: constitucionales 1, 7 y 7-A; penales 16, 25,
  111 y 288. El penal 124 quedó segundo, detrás del 111, en una pregunta sobre
  daño corporal por culpa. Esta confusión temática queda documentada.

Estas ocho preguntas son un diagnóstico pequeño de recuperación, no una
evaluación de exactitud jurídica ni una calibración suficiente del umbral.

## Generación y HTTP

Se añadió una entrada experimental independiente, `api/pilot.py`, y un cargador
`scripts/pilot_runtime.py`. Este carga únicamente la base ya indexada, exige el
recibo correcto y comprueba que la colección contenga los diez IDs. Inyecta el
store con el nombre piloto en `RAGEngine`; no altera el motor ni sus valores por defecto.

La entrada experimental mantiene el contrato React y CORS para localhost/127.0.0.1
en puerto 5173. Ante cada respuesta añade el aviso visible
`PILOTO EXPERIMENTAL: texto no cotejado oficialmente.`. El texto de las fuentes
no se transforma. No hay memoria conversacional.

La instancia separada de comprobación quedó en `127.0.0.1:8001`. Se realizaron
cuatro POST reales con Ollama `qwen2.5:3b`, todos HTTP 200:

- Pregunta constitucional 1: `insufficient_evidence`; el generador declaró
  insuficiencia aunque había fragmentos recuperados. 20.39 segundos, incluida
  carga inicial del proceso.
- Tentativa, artículo penal 16: `answered`, una fuente correcta y cita literal
  validada por el motor. 5.60 segundos.
- Igualdad ante la ley, constitucional 2: `insufficient_evidence`; el generador
  volvió a declarar insuficiencia. 14.26 segundos.
- Artículo penal inexistente 999: `insufficient_evidence`, sin fuentes. 0.04 segundos.

Respuestas y tiempos completos: `http_results.json`. No se cambiaron umbrales ni
prompts para forzar respuestas. Las dos abstenciones constitucionales son una
limitación observada que debe analizarse antes de ampliar el uso del sistema.

## React real y restauración

Para la prueba de navegador, se detuvo temporalmente nuestra instancia normal
del backend, se lanzó `api.pilot:app` en 8000 y se usó el React existente en 5173,
sin editar sus archivos. Pregunta enviada:

> ¿Cuándo comienza la tentativa según el artículo 16 del Código Penal?

React mostró el aviso experimental, la cita del artículo 16 y una fuente
`Código Penal peruano / 16`. Captura: `REACT_PILOT_PROOF.png`.

Después se detuvo la instancia piloto temporal de 8000 y se restauró
`api.main:app` en ese puerto. Se comprobó que el backend normal vuelve a devolver
`No hay corpus local disponible.` y `insufficient_evidence`: no activa el piloto
automáticamente. La instancia experimental en 8001 permanece separada.

## Pruebas

`python -m unittest discover -q`: **87 pruebas aprobadas**, 78 anteriores y 9
nuevas de carga/contrato del runtime piloto. `pip check`: sin incompatibilidades.
Las pruebas nuevas comprueban aviso experimental, validación, abstención,
transformación de fuentes, CORS, ocultación de excepciones, preservación de la
API predeterminada, rechazo de recibos incorrectos y de índices ausentes/incompletos.
Los fixtures sintéticos permanecen en temporales; no se indexaron en esta base.
Los tracebacks de timeout de las pruebas existentes son escenarios negativos esperados.

## Primera consulta desde React

El frontend está fijado a `http://localhost:8000/api/chat`. Para usar el piloto
debe elegirse expresamente la entrada experimental en ese puerto. No basta
con arrancarla en 8001 y dejar React apuntando a la API normal.

1. Detener con Ctrl+C la instancia de backend normal que ocupe 8000. No cerrar
   procesos ajenos. No se necesita detener el frontend si ya sirve en 5173.
2. En una terminal PowerShell, iniciar explícitamente el modo experimental:

```powershell
Set-Location 'C:\Users\senat\Desktop\Mini-Juztina'
.\.venv\Scripts\python.exe -m uvicorn api.pilot:app --host 127.0.0.1 --port 8000 --workers 1
```

3. Si React no está iniciado, en otra terminal:

```powershell
Set-Location 'C:\Users\senat\Desktop\Mini-Juztina\frondend'
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

4. Abrir `http://localhost:5173`, iniciar una consulta y pegar la pregunta de
   tentativa anterior. Esperar la respuesta y comprobar aviso, cita y fuente 16.
   Una respuesta individual puede abstenerse; no se garantiza comportamiento
   idéntico del modelo en ejecuciones futuras.
5. Al terminar, detener con Ctrl+C el backend piloto y restaurar el normal:

```powershell
Set-Location 'C:\Users\senat\Desktop\Mini-Juztina'
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

## Reversión del índice piloto — no ejecutada

Con autorización para retirar el piloto, detener antes las instancias que lo
consulten (8001 o una instancia experimental en 8000), conservando el backend normal.
La reversión está limitada a la colección del recibo:

```powershell
Set-Location 'C:\Users\senat\Desktop\Mini-Juztina'
.\.venv\Scripts\python.exe -m scripts.pilot_index remove --execute
```

No borra recursivamente carpetas ni altera `storage/chroma`; puede dejar archivos
administrativos de la base piloto. Conserva candidatos, recibo histórico y copias.
El estado previo era ausencia de colección, documentado en el respaldo; no había
una base anterior que restaurar. El comando de eliminación no se ejecutó durante
estas comprobaciones y no está autorizado por la orden actual de indexación.

## Límites

No se cotejaron los artículos con PDFs oficiales ni se validaron OCR, integridad,
incisos, edición o vigencia. El éxito técnico no convierte estas extracciones
provisionales en contenido normativo verificado. No se amplió el corpus ni se
corrigió texto jurídico mediante inferencias.
