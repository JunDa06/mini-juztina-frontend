# Mini-Juztina — Frontend ⚖️

**Asistente jurídico inteligente local**

## Descripción

Mini-Juztina es un prototipo de aplicación web conversacional orientado a la consulta de legislación peruana. Su objetivo es facilitar la consulta de la Constitución Política del Perú y el Código Penal mediante un sistema RAG (*Retrieval-Augmented Generation*) ejecutado localmente.

Actualmente, el proyecto cuenta con el frontend desarrollado en React y Vite. La integración con el backend jurídico todavía está pendiente.

## 1. Tecnologías utilizadas

- **React:** desarrollo de la interfaz de usuario.
- **Vite:** servidor de desarrollo y herramienta de construcción.
- **JavaScript:** lógica de la aplicación.
- **CSS:** diseño adaptable y temas visuales.
- **LocalStorage:** almacenamiento de la preferencia de tema.

## 2. Requisitos previos

Antes de iniciar el proyecto, asegúrate de tener instalado:

- [Node.js](https://nodejs.org/), preferentemente una versión LTS compatible con Vite.
- npm, incluido normalmente con Node.js.
- [Visual Studio Code](https://code.visualstudio.com/) (recomendado como editor).

No es necesario tener Python ni Ollama instalados para ejecutar únicamente el frontend.

## 3. Instalación

Clona o descarga el repositorio y abre la carpeta `mini-juztina-frontend` en Visual Studio Code.

Abre una terminal en esa carpeta, donde se encuentra el archivo `package.json`, y ejecuta:

```bash
npm install
```

Este comando instala las dependencias necesarias para ejecutar el frontend.

## 4. Iniciar la aplicación

En la terminal, ejecuta:

```bash
npm run dev
```

Vite mostrará una dirección local similar a esta:

```text
http://localhost:5173/
```

Abre esa dirección en tu navegador para utilizar Mini-Juztina.

Para detener el servidor, pulsa `Ctrl + C` en la terminal.

## 5. Funcionalidades implementadas

- Interfaz de asistente jurídico con diseño adaptable.
- Modo oscuro y modo claro con tonos rosa pastel.
- Preferencia de tema guardada en el navegador.
- Creación y eliminación de conversaciones.
- Mensajes del usuario a la derecha y respuestas del asistente a la izquierda.
- Tarjetas de acceso rápido para consultas constitucionales y penales.
- Panel de transparencia preparado para mostrar fuentes jurídicas.
- Indicadores visuales de conexión y procesamiento.

### Limitaciones actuales

Las conversaciones se mantienen únicamente en memoria y se pierden al recargar la página. El panel de fuentes todavía no recibe información real del motor RAG.

Estas limitaciones deberán actualizarse cuando se implementen las funcionalidades correspondientes.

## 6. Estructura principal

```text
mini-juztina-frontend/
├── public/
├── src/
│   ├── assets/
│   ├── App.jsx
│   ├── App.css
│   ├── index.css
│   └── main.jsx
├── index.html
├── package.json
├── package-lock.json
├── vite.config.js
└── README.md
```

La estructura puede variar ligeramente según la configuración del proyecto.

## 7. Integración pendiente

En las siguientes etapas se prevé desarrollar e integrar el backend local con los siguientes componentes:

- **FastAPI:** API para recibir consultas del frontend.
- **Ollama:** ejecución local del modelo de lenguaje.
- **ChromaDB:** almacenamiento y recuperación vectorial.
- **Embeddings:** representación semántica de los documentos jurídicos.
- **Pipeline RAG:** recuperación de artículos relevantes y generación de respuestas fundamentadas.

La interfaz contempla la futura comunicación con el endpoint local:

```http
POST http://localhost:8000/api/chat
```

Este endpoint es una referencia de integración prevista; no se considera operativo hasta que el backend correspondiente esté implementado y probado.

El backend deberá devolver la respuesta jurídica y las fuentes recuperadas. Hasta entonces, las consultas no producirán respuestas jurídicas reales basadas en el corpus.

## 8. Consideraciones de privacidad

Que el frontend se ejecute en el equipo local no garantiza, por sí solo, que todo el procesamiento sea offline.

La arquitectura final deberá verificar que el modelo, los embeddings, la recuperación documental y la generación de respuestas se ejecuten localmente, sin enviar consultas a servicios externos.

## 9. Información del proyecto

- **Proyecto integrador:** Desarrollo de un Asistente Legal Inteligente 100 % Local (Mini-Juztina).
- **Estado:** frontend desarrollado; backend RAG pendiente de integración.
- **Entorno de desarrollo:** Visual Studio Code en Windows.

## Aviso legal

Mini-Juztina es un prototipo informativo. Sus respuestas deberán fundamentarse en fuentes jurídicas oficiales y no sustituyen la asesoría de un profesional del derecho.

