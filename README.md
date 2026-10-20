# Mini-Juztina ⚖️

**Asistente jurídico inteligente local para la consulta de legislación peruana.**

## 1. Descripción del proyecto

Mini-Juztina es un proyecto que busca facilitar la consulta de legislación peruana a través de una aplicación web conversacional. Está orientado principalmente a la consulta de la Constitución Política del Perú y el Código Penal.

La idea es que los usuarios puedan realizar preguntas en lenguaje natural y obtener respuestas basadas en información recuperada de documentos jurídicos. Para ello, el proyecto utiliza el enfoque RAG (*Retrieval-Augmented Generation*), que combina la búsqueda de información relevante con la generación de respuestas mediante un modelo de lenguaje.

El sistema está diseñado para funcionar localmente, con el propósito de reducir la dependencia de servicios externos y ofrecer un mayor control sobre el procesamiento de las consultas. La integración y validación de todos sus componentes forman parte del desarrollo del proyecto.

## 2. Objetivo general

Desarrollar un asistente jurídico local que facilite la consulta de legislación peruana mediante una interfaz conversacional y un sistema de recuperación de información que permita encontrar disposiciones legales relacionadas con las preguntas del usuario.

## 3. Arquitectura del proyecto

Mini-Juztina está organizado en varios componentes que cumplen funciones específicas:

| Componente | Función |
|---|---|
| Frontend | Permite al usuario realizar consultas e interactuar con la aplicación. |
| API | Gestiona la comunicación entre la interfaz y los componentes del backend. |
| Motor RAG | Coordina la recuperación de información jurídica y la generación de respuestas. |
| Corpus jurídico | Contiene los documentos legales utilizados como fuentes de consulta. |
| Almacenamiento vectorial | Permite organizar y recuperar información mediante representaciones semánticas. |
| Pruebas | Ayudan a comprobar el funcionamiento de los componentes y detectar posibles errores. |

Estos componentes deben trabajar de manera coordinada para que el sistema pueda responder consultas utilizando información jurídica relevante.

## 4. Tecnologías utilizadas y previstas

### Frontend

- **React:** permite construir la interfaz de usuario.
- **Vite:** facilita el desarrollo y la ejecución de la aplicación web.
- **JavaScript:** gestiona la lógica y las interacciones de la interfaz.
- **CSS:** define los estilos visuales y los temas de la aplicación.
- **LocalStorage:** permite guardar la preferencia de tema en el navegador.

### Backend y sistema RAG

- **Python:** se utiliza para desarrollar los componentes del backend.
- **FastAPI:** está previsto para gestionar las solicitudes a través de una API.
- **Ollama:** está contemplado para ejecutar un modelo de lenguaje localmente.
- **ChromaDB:** está previsto para el almacenamiento y la recuperación vectorial.
- **Embeddings:** permiten representar semánticamente los documentos para facilitar su búsqueda.
- **RAG:** combina la recuperación de información jurídica con la generación de respuestas.

La configuración y disponibilidad de estas tecnologías deben comprobarse en los archivos del proyecto y en las pruebas correspondientes.

## 5. Corpus jurídico

El proyecto incluye documentos de referencia en formato PDF y archivos estructurados en formato JSONL. Estos últimos permiten organizar el contenido jurídico para facilitar su procesamiento posterior.

| Documento | Archivo PDF | Archivo JSONL |
|---|---|---|
| Constitución Política del Perú | `corpus-juridico/Constitucion-web_2026.pdf` | `corpus-juridico/constitucion.jsonl` |
| Código Penal | `corpus-juridico/codigo-penal.pdf` | `corpus-juridico/codigo_penal_articulos.jsonl` |

Los documentos PDF permiten consultar el contenido de referencia, mientras que los archivos JSONL están destinados a facilitar la organización y recuperación de la información.

Antes de utilizar estos datos para responder consultas jurídicas, es importante comprobar que su contenido sea íntegro y coincida con las publicaciones oficiales aplicables.

## 6. Estructura del repositorio

El repositorio reúne el frontend, los componentes del backend, el corpus jurídico y los archivos de apoyo al desarrollo.

```text
Mini-Juztina/
├── README.md
├── .gitignore
├── corpus-juridico/
│   ├── Constitucion-web_2026.pdf
│   ├── constitucion.jsonl
│   ├── codigo-penal.pdf
│   └── codigo_penal_articulos.jsonl
├── api/
│   ├── main.py
│   └── pilot.py
├── core/
│   ├── config.py
│   ├── corpus.py
│   ├── embeddings.py
│   ├── ollama_client.py
│   ├── rag_engine.py
│   └── vector_store.py
├── data/
│   ├── processed/
│   └── sources/
├── tests/
├── scripts/
├── frondend/
├── mini-juztina-frontend/
├── requirements.txt
├── requirements-api.txt
├── requirements-lock.txt
└── requirements-api-lock.txt
```

Esta estructura es orientativa. Algunas carpetas contienen archivos adicionales y pueden reorganizarse a medida que avance el desarrollo. El directorio `frondend/` conserva ese nombre en la rama integrada.

## 7. Requisitos e instalación del frontend

Para ejecutar el frontend se necesita:

- Node.js, preferentemente una versión LTS compatible con Vite.
- npm, incluido normalmente con Node.js.
- Un navegador web moderno.

### Clonar el repositorio

```bash
git clone https://github.com/JunDa06/mini-juztina-frontend.git
```

### Acceder a la carpeta del frontend

```bash
cd mini-juztina-frontend/mini-juztina-frontend
```

### Instalar las dependencias

```bash
npm install
```

### Iniciar la aplicación

```bash
npm run dev
```

Vite mostrará en la terminal una dirección local, normalmente `http://localhost:5173/`. Abre esa dirección en el navegador para visualizar la aplicación.

Estas instrucciones corresponden al frontend ubicado en `mini-juztina-frontend/mini-juztina-frontend`. El repositorio también contiene otra carpeta de frontend procedente de la rama integrada, por lo que conviene confirmar cuál se utilizará como versión principal.

## 8. Backend y recuperación de información

Los componentes del backend se encuentran principalmente en las carpetas `api/` y `core/`.

Entre los archivos relevantes se encuentran:

- `api/main.py`: archivo principal de la API.
- `api/pilot.py`: componente relacionado con las pruebas piloto.
- `core/corpus.py`: gestión del corpus documental.
- `core/embeddings.py`: procesamiento de representaciones semánticas.
- `core/ollama_client.py`: componente para la comunicación con Ollama.
- `core/rag_engine.py`: lógica del motor RAG.
- `core/vector_store.py`: gestión del almacenamiento vectorial.
- `core/config.py`: configuración del sistema.

Para preparar el entorno del backend, deben revisarse los archivos de dependencias y la documentación técnica incluida en `INTEGRATION.md`.

La forma de iniciar el backend dependerá de la configuración efectiva de la API y de los servicios que requiera. Por ello, es necesario verificar el procedimiento de ejecución antes de considerarlo definitivo.

## 9. Pruebas y evaluación

El repositorio incluye pruebas y documentos destinados a evaluar diferentes componentes del sistema.

Entre los archivos de prueba se encuentran:

- `tests/test_api.py`
- `tests/test_engine.py`
- `tests/test_corpus_audit.py`
- `tests/test_pilot.py`
- `tests/integration_local.py`

También se incluyen documentos como `TEST_RESULTS.md`, `INTEGRATION_RESULTS.md` e `INTEGRATION.md`, que sirven como referencia para revisar los procedimientos y resultados registrados.

Estos archivos ayudan a documentar el desarrollo y la evaluación del proyecto. Sin embargo, sus resultados deben comprobarse en el entorno actual para confirmar que las pruebas siguen siendo válidas después de combinar las ramas.

## 10. Privacidad y consideraciones legales

Mini-Juztina está pensado para funcionar localmente, con el objetivo de mantener un mayor control sobre las consultas realizadas y reducir la dependencia de servicios externos.

No obstante, que la interfaz se ejecute en el equipo del usuario no garantiza por sí solo que todo el procesamiento sea local. Para confirmar esta característica, será necesario comprobar que el modelo de lenguaje, los embeddings, la recuperación documental y la generación de respuestas no envíen información a servicios externos.

En el ámbito jurídico, las respuestas deberán contrastarse con fuentes oficiales y con la normativa vigente. Mini-Juztina es una herramienta tecnológica de apoyo a la consulta y no sustituye la asesoría de un profesional del derecho.

## 11. Colaboración

El proyecto se desarrolla de manera colaborativa y utiliza Git y GitHub para mantener el código organizado y facilitar la integración de los aportes de sus integrantes.

Se recomienda revisar los cambios antes de combinarlos, mantener actualizadas las instrucciones de instalación y documentar las modificaciones importantes. Esto facilita el mantenimiento del proyecto y ayuda a que todos los integrantes trabajen sobre una estructura común.

## Licencia

La licencia del proyecto está pendiente de definición. Hasta que se establezca una licencia aplicable, no debe asumirse que el código o los documentos incorporados pueden reutilizarse sin restricciones.
