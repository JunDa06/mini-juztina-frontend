# Piloto de diez artículos: preparación para cotejo

**Provisional. Ningún candidato está jurídicamente verificado. No se ha indexado.**
Se mantiene sin cambios React, FastAPI, el motor RAG, los originales y las salidas de auditoría.

## Candidatos

- Constitución Política del Perú: **1, 2, 3, 7 y 7-A**. Proceden de las líneas
  1, 2, 3, 7 y 8 de `data/sources/constitucion.jsonl`. Los cinco conservan
  `requiere_revision` de la auditoría y el marcador de borrador OCR original.
- Código Penal peruano: **16, 25, 111, 124 y 288**. Proceden de las líneas
  26, 35, 133, 150 y 347 de `data/sources/codigo_penal_articulos.jsonl`.
  Los cinco pertenecen a los 302 estructuralmente aptos. El texto local menciona,
  respectivamente, tentativa, asistencia dolosa, muerte por culpa, daño corporal
  por culpa y actuación a sabiendas/por culpa. Son motivos de selección del texto
  suministrado, no afirmaciones sobre el contenido oficial completo o vigente.

Los penales II, 11 y 12 serían preferentes para legalidad, dolo y culpa, pero
requieren revisión por posibles títulos arrastrados. Se excluyen para respetar
el requisito de cinco penales estructuralmente aptos. **El piloto no cubre
directamente el principio de legalidad.** No debe suplirse esa ausencia con
conocimiento del modelo o legislación no incluida.

## Archivos y preservación

- `articles_candidates.jsonl`: diez registros con el contrato del motor, IDs
  de auditoría originales y cadenas `texto` copiadas literalmente.
- `manifest.json`: procedencia, líneas, hashes, clasificación previa, incidencias,
  motivos de selección y campos de evidencia oficial sin completar.
- `INDEX_PLAN.json`: plan de aislamiento calculado mediante lectura; no es un índice.
- `TEST_RESULTS.md`: pruebas y comprobaciones observadas.
- Este documento: cotejo e instrucciones de indexación futura.

El artículo constitucional 2 conserva sus **9278 caracteres**, incluidos todos
los incisos extraídos, sus irregularidades OCR, notas y cabeceras. Preservar esta
cadena no demuestra que el extractor haya conservado todos los incisos del PDF.
No se ha añadido, eliminado, reordenado ni reconstruido ninguno.

## Incidencias que necesitan atención

- Los cinco constitucionales son borradores OCR declarados por el origen.
- Constitucional 1: termina en coma. La alerta previa de posible título
  arrastrado es heurística y puede ser un falso positivo; cotejar la puntuación
  completa, sin decidir su corrección por intuición.
- Constitucional 2: contiene cabeceras de página, notas editoriales y numeración
  irregular de incisos. Cotejar la cadena completa, no únicamente los primeros párrafos.
- Constitucional 3: el texto termina con `Capítulo 1 De los derechos sociales y
  económicos`, posible encabezado del bloque siguiente. No se ha recortado.
- Constitucionales 7 y 7-A: confirmar integridad literal; en 7-A aparecen las
  grafías `foma` e `imprescripible` en el registro local. No se han corregido.
- Penales: permanecen comillas editoriales de cierre en las cinco extracciones.
  Comprobar sus límites y si faltan párrafos; la estructura aceptable no prueba integridad.
- Penal 111: registro local breve. Confirmar especialmente que no se haya perdido
  contenido después del primer bloque. No se ha completado con otra fuente.
- Todos tienen `pagina_pdf=null`. Solo hay páginas aproximadas para los
  constitucionales 1 (6), 7 y 7-A (17); permanecen como aproximaciones en el manifiesto,
  nunca como referencias exactas. No hay jerarquía título/capítulo completa.

## Procedimiento de cotejo oficial

1. Definir la edición y fecha de referencia del piloto. El origen constitucional
   declara mayo de 2026; el penal declara actualización al 2 de julio de 2026.
   Son declaraciones de procedencia, no certificaciones de vigencia.
2. Obtener el PDF desde el portal oficial y verificar portada, edición y colofón.
   Para Constitución, consultar la [Biblioteca del Congreso](https://www3.congreso.gob.pe/biblioteca/constituciones-peru/)
   y el [portal constitucional del Congreso](https://www.congreso.gob.pe/constitucion-del-peru-y-reglamento/).
   Para Código Penal, usar [Normas Legales Actualizadas de El Peruano](https://diariooficial.elperuano.pe/Normas/normasactualizadas).
   Estos enlaces se localizaron como puntos de partida; **no se cotejaron los artículos**.
   Si la edición disponible es distinta, registrar la diferencia y localizar la
   edición declarada; no intercambiarlas silenciosamente.
3. Guardar la copia oficial como referencia independiente, con URL de descarga,
   fecha, nombre del documento y SHA-256. No sustituir los JSONL originales.
4. Comparar visualmente cada artículo, todos sus párrafos, incisos y subincisos,
   desde el encabezado hasta el siguiente artículo. Distinguir texto normativo de
   notas, títulos, cabeceras y variantes editoriales. Revisar especialmente números,
   negaciones, cuantías, remisiones y condiciones temporales. La extracción de texto
   del PDF por sí sola no sustituye esa comparación.
5. Anotar página PDF real y rango completo cuando atraviese varias páginas,
   distinguiéndolos de la numeración impresa y de aproximaciones del OCR.
6. Registrar diferencias, revisor y fecha. Comprobar separadamente normas
   modificatorias, derogatorias y disposiciones de entrada en vigor respecto de
   la fecha de referencia; coincidencia textual no equivale a vigencia verificada.
7. Completar la evidencia de cada candidato solo cuando exista respaldo documental.
   El manifiesto actual conserva `juridicamente_verificado=false` y todos los campos
   de evidencia oficial vacíos. Encontrar un portal oficial no permite cambiar ese estado.
8. Si hay diferencias, conservar esta versión intacta y preparar una nueva versión
   trazable a la fuente oficial, con autorización para corregir. No parchear el texto
   actual ni inventar incisos faltantes. La comprobación de hashes bloqueará una
   indexación si se alteran candidatos o auditoría sin reconstruir el plan.

## Plan separado de indexación: NO ejecutado

Desde la raíz, solo para comprobar el plan mediante lectura:

```powershell
Set-Location 'C:\Users\senat\Desktop\Mini-Juztina'
.\.venv\Scripts\python.exe -X utf8 -m scripts.pilot_index plan
```

El plan actual identifica:

- Archivo: `data/processed/pilot_10_v1/articles_candidates.jsonl`.
- Chroma aislado: `storage/pilots/pilot-10-ced16af809467bef`.
- Colección: `pilot_articles_6c8fe3e916f803a176aee9950c6e9dc62df438a6`.
- Corpus SHA-256: `ced16af809467bef73fe5cf0dfd4db792dbdd7956543427880da2690533e81df`.

El nombre de colección incorpora corpus, modelo de embeddings y versión del
particionado del motor. Si cambia el modelo, recalcular el plan; no asumir que
la colección sigue siendo la anterior. El prefijo `pilot_articles_` y la ruta
dedicada separan este experimento de cualquier índice de producción.

**Comando preparado para después de autorización explícita; no se ejecutó:**

```powershell
Set-Location 'C:\Users\senat\Desktop\Mini-Juztina'
.\.venv\Scripts\python.exe -X utf8 -m scripts.pilot_index index --execute
```

Si se autoriza antes del cotejo, será únicamente un piloto técnico de extracciones
no verificadas. No podrá presentarse como servicio jurídico validado.

Ese comando revalida hashes, selección e identidad textual, carga embeddings
locales y reutiliza `VectorStore.index` con una instancia apuntada al espacio
piloto. Solo entonces crea Chroma y escribe `index_receipt.json` con la ubicación,
colección y fragmentos. La selección y su manifiesto original permanecen como
evidencia de preparación; el recibo registra la ejecución técnica, sin validar contenido.
No publica `data/processed/articles.jsonl`, no cambia `Config` ni conecta el piloto
automáticamente a FastAPI/React.

Para consultas futuras aisladas, se debe inyectar explícitamente en `RAGEngine`
un `VectorStore` configurado con **el mismo nombre de colección piloto**. Cambiar
solo la ruta de Chroma no basta, porque el nombre por defecto del motor empieza
por `articles_`. Esa conexión no se implementó ni ejecutó en esta preparación.

## Reversión después de una indexación autorizada

Solo si existe el recibo de una ejecución posterior y se autoriza retirar el piloto:

```powershell
Set-Location 'C:\Users\senat\Desktop\Mini-Juztina'
.\.venv\Scripts\python.exe -X utf8 -m scripts.pilot_index remove --execute
```

La reversión valida la ruta y el nombre contra el recibo y elimina únicamente la
colección piloto, sin borrado recursivo de carpetas. Conserva originales,
candidatos, manifiesto y recibo histórico. No toca `storage/chroma`. El piloto
puede reconstruirse posteriormente desde sus datos conservados. Nunca se ejecutó
esta reversión ni se abrió Chroma durante la preparación.
