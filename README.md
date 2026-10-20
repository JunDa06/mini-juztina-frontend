# Mini-Juztina ⚖️

**Asistente jurídico basado en inteligencia artificial para la consulta de normativa peruana.**

## 📌 Descripción del proyecto

Mini-Juztina es un proyecto orientado al desarrollo de un asistente jurídico que facilite la consulta y comprensión de la legislación peruana mediante una interfaz conversacional.

La propuesta busca utilizar técnicas de recuperación de información aumentada por generación (RAG, *Retrieval-Augmented Generation*) para responder consultas utilizando documentos jurídicos como fuentes de referencia, permitiendo relacionar las respuestas con la normativa correspondiente.

El proyecto prioriza el uso de fuentes documentales identificables y la transparencia de las respuestas, con el objetivo de facilitar la consulta de información legal.

## 🎯 Objetivo

Desarrollar un asistente jurídico que permita consultar normativa peruana de manera sencilla, utilizando un corpus documental organizado y un sistema de recuperación de información que facilite la identificación de las disposiciones legales relevantes.

## 📚 Corpus jurídico

El repositorio incluye documentos normativos en formato PDF y archivos estructurados en JSONL para su procesamiento.

| Documento | Archivo PDF | Archivo estructurado |
|---|---|---|
| Constitución Política del Perú | `Constitucion-web_2026.pdf` | `constitucion.jsonl` |
| Código Penal | `codigo-penal.pdf` | `codigo_penal_articulos.jsonl` |

Los documentos PDF sirven como referencia documental, mientras que los archivos JSONL contienen información estructurada para facilitar su procesamiento e incorporación al sistema de recuperación.

> **Nota:** La exactitud, integridad y vigencia de los textos legales deben verificarse con las publicaciones oficiales correspondientes. Las respuestas del asistente no sustituyen la asesoría de un profesional del derecho.

## 🛠️ Tecnologías

### Frontend

- **React:** desarrollo de la interfaz de usuario.
- **Vite:** entorno de desarrollo y herramienta de construcción.
- **JavaScript y CSS:** lógica de interacción y presentación visual.

### Componentes previstos

- Procesamiento y recuperación de información jurídica mediante RAG.
- Integración de un modelo de lenguaje.
- Presentación de respuestas vinculadas con fuentes documentales.

Los componentes de backend, recuperación documental y modelo de lenguaje se encuentran sujetos al avance de la implementación.

## 📁 Estructura del repositorio

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
    └── vite.config.js
```

## 🚀 Instalación y ejecución del frontend

### Requisitos previos

- [Node.js](https://nodejs.org/) instalado.
- npm, incluido normalmente con Node.js.
- Git, si deseas clonar el repositorio.

### 1. Clonar el repositorio

```bash
git clone https://github.com/JunDa06/mini-juztina-frontend.git
```

### 2. Entrar en la carpeta del frontend

```bash
cd mini-juztina-frontend
```

### 3. Instalar dependencias

```bash
npm install
```

### 4. Ejecutar el entorno de desarrollo

```bash
npm run dev
```

Vite mostrará en la terminal la dirección local donde podrás abrir la aplicación desde tu navegador.

> Estos pasos permiten ejecutar el frontend. La disponibilidad de respuestas jurídicas automatizadas dependerá de la integración y configuración del backend y del sistema RAG.

## 🔎 Enfoque del proyecto

Mini-Juztina busca orientar su desarrollo hacia los siguientes aspectos:

- **Consulta accesible:** facilitar la interacción con información jurídica mediante lenguaje natural.
- **Recuperación documental:** localizar fragmentos pertinentes dentro del corpus normativo.
- **Trazabilidad:** facilitar la identificación de los documentos utilizados como referencia.
- **Organización de la información:** mantener separados el código de la aplicación y los documentos jurídicos.
- **Transparencia:** distinguir la información respaldada por fuentes de las limitaciones del sistema.

## 📈 Estado del proyecto

El proyecto se encuentra en desarrollo.

- [x] Creación de la estructura inicial del frontend.
- [x] Preparación del corpus jurídico en PDF y JSONL.
- [x] Publicación del código y los documentos en GitHub.
- [ ] Implementación e integración del backend.
- [ ] Integración del sistema RAG con el corpus jurídico.
- [ ] Integración del modelo de lenguaje.
- [ ] Verificación de respuestas y referencias normativas.
- [ ] Pruebas funcionales del sistema completo.

Esta lista deberá actualizarse conforme se completen las distintas etapas.

## 👥 Colaboración

El proyecto se desarrolla mediante trabajo colaborativo. Se recomienda utilizar ramas de Git para desarrollar funcionalidades y realizar revisiones antes de incorporar cambios a la rama principal.

## ⚖️ Aviso legal

Mini-Juztina es un proyecto tecnológico de apoyo a la consulta jurídica. La información generada debe contrastarse con las normas oficiales vigentes y no debe considerarse asesoría legal personalizada ni sustituir la evaluación de un abogado.

## 📄 Licencia

La licencia del proyecto está pendiente de definición. Hasta que se establezca una licencia, no debe asumirse que el código o los documentos incorporados pueden reutilizarse sin restricciones.
