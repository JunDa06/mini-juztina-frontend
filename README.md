# Mini-Juztina ⚖️

**Asistente jurídico inteligente local para la consulta de legislación peruana.**

## 1. Descripción del proyecto

Mini-Juztina es un prototipo de aplicación web conversacional orientado a facilitar la consulta de legislación peruana, especialmente de la Constitución Política del Perú y el Código Penal.

El proyecto propone utilizar un sistema de generación aumentada por recuperación (RAG, *Retrieval-Augmented Generation*) para localizar información relevante en documentos jurídicos y utilizarla como fundamento de las respuestas.

La aplicación está planteada para funcionar localmente, priorizando la privacidad de las consultas y el acceso organizado a las fuentes normativas.

Actualmente, el frontend está desarrollado con React y Vite. La integración del backend jurídico y del sistema RAG se encuentra pendiente.

## 2. Objetivo general

Desarrollar un asistente jurídico local que facilite la consulta de normativa peruana mediante una interfaz conversacional y un sistema de recuperación documental que permita identificar las disposiciones legales relevantes para cada consulta.

## 3. Tecnologías del proyecto

### Frontend implementado

- **React:** desarrollo de la interfaz de usuario.
- **Vite:** entorno de desarrollo y herramienta de construcción.
- **JavaScript:** lógica de interacción.
- **CSS:** diseño visual y temas de la aplicación.
- **LocalStorage:** almacenamiento de la preferencia de tema.

### Backend y recuperación documental previstos

- **FastAPI:** API para la comunicación entre el frontend y el backend.
- **Ollama:** ejecución local de un modelo de lenguaje.
- **ChromaDB:** almacenamiento y recuperación vectorial.
- **Embeddings:** representación semántica de los documentos jurídicos.
- **RAG:** recuperación de fragmentos normativos relevantes para fundamentar las respuestas.

Los componentes previstos se integrarán y validarán durante las siguientes etapas del desarrollo.

## 4. Corpus jurídico

El repositorio contiene documentos jurídicos en PDF y sus correspondientes archivos estructurados en formato JSONL.

| Documento | Archivo PDF | Archivo JSONL |
|---|---|---|
| Constitución Política del Perú | `Constitucion-web_2026.pdf` | `constitucion.jsonl` |
| Código Penal | `codigo-penal.pdf` | `codigo_penal_articulos.jsonl` |

Los PDF se utilizan como documentos de referencia, mientras que los archivos JSONL permiten organizar el contenido para su posterior procesamiento y recuperación.

La integridad, exactitud y vigencia de los textos deberán verificarse con las fuentes oficiales correspondientes antes de utilizarlos para generar respuestas jurídicas.

## 5. Estructura del repositorio

```text
Mini-Juztina/
├── README.md
├── corpus-juridico/
│   ├── Constitucion-web_2026.pdf
│   ├── constitucion.jsonl
│   ├── codigo-penal.pdf
│   └── codigo_penal_articulos.jsonl
└── mini-juztina-frontend/
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

## 6. Instalación y ejecución

### Requisitos previos

- Node.js, preferentemente una versión LTS compatible con Vite.
- npm.
- Un navegador web moderno.

Para ejecutar únicamente el frontend no es necesario instalar Python, Ollama ni ChromaDB.

### Clonar el repositorio

```bash
git clone https://github.com/JunDa06/mini-juztina-frontend.git
```

### Acceder al frontend

```bash
cd mini-juztina-frontend
```

### Instalar las dependencias

```bash
npm install
```

### Iniciar la aplicación

```bash
npm run dev
```

Vite mostrará una dirección local, normalmente `http://localhost:5173/`, que podrás abrir en el navegador.

Estas instrucciones permiten ejecutar el frontend. Las consultas jurídicas basadas en recuperación documental estarán disponibles cuando se integre y configure el backend.

## 7. Funcionalidades del frontend

La interfaz desarrollada incluye:

- Interfaz conversacional para consultas.
- Tema claro y oscuro.
- Preferencia visual guardada en el navegador.
- Creación y eliminación de conversaciones.
- Diferenciación visual entre mensajes del usuario y respuestas del asistente.
- Tarjetas de acceso rápido para consultas constitucionales y penales.
- Panel preparado para mostrar fuentes jurídicas.
- Indicadores visuales de conexión y procesamiento.

Las conversaciones se mantienen actualmente en memoria y se pierden al recargar la página. El funcionamiento definitivo de las consultas y la presentación de fuentes dependerá de la integración del backend.

## 8. Arquitectura prevista

El flujo general propuesto es el siguiente:

1. El usuario formula una consulta desde el frontend.
2. El frontend envía la consulta a la API local.
3. El sistema RAG busca fragmentos pertinentes en el corpus jurídico.
4. El modelo de lenguaje utiliza el contexto recuperado para generar una respuesta.
5. El backend devuelve la respuesta y las referencias documentales disponibles.
6. El frontend presenta la respuesta y sus fuentes al usuario.

El endpoint previsto para la comunicación es `POST http://localhost:8000/api/chat`. Su funcionamiento dependerá de la implementación y validación del backend.

## 9. Privacidad y consideraciones técnicas

El proyecto tiene como objetivo ejecutar localmente el procesamiento jurídico para reducir la dependencia de servicios externos.

Sin embargo, la ejecución local del frontend no garantiza por sí sola que todo el procesamiento sea offline. Esta característica deberá verificarse cuando se integren el modelo de lenguaje, los embeddings, la recuperación documental y el backend.

## 10. Estado del proyecto

- [x] Desarrollo inicial del frontend con React y Vite.
- [x] Preparación de documentos jurídicos en PDF.
- [x] Disponibilidad de archivos estructurados en JSONL.
- [x] Organización inicial del repositorio en GitHub.
- [ ] Implementación del backend con FastAPI.
- [ ] Integración del corpus jurídico con el sistema de recuperación.
- [ ] Configuración del modelo de lenguaje local.
- [ ] Integración del pipeline RAG.
- [ ] Presentación de referencias jurídicas recuperadas.
- [ ] Pruebas funcionales y validación de respuestas.

Esta lista deberá actualizarse conforme avance el desarrollo.

## 11. Trabajo colaborativo

El proyecto está organizado en componentes para facilitar el desarrollo y la integración de funcionalidades. Se recomienda utilizar Git y GitHub para el control de versiones, la revisión de cambios y la coordinación entre los integrantes.

## 12. Aviso legal

Mini-Juztina es un prototipo tecnológico de apoyo a la consulta jurídica. Sus respuestas deberán contrastarse con la normativa oficial vigente y no sustituyen la asesoría de un profesional del derecho.

## Licencia

La licencia del proyecto está pendiente de definición. No debe asumirse que el código o los documentos incorporados pueden reutilizarse sin restricciones mientras no se determine la licencia aplicable.
