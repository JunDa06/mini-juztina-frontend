# Demostración académica — 3 a 5 minutos

## Preparación

Seguir el README: Ollama con `qwen2.5:3b`, API `api.pilot:app` en 8000 y React en 5173.
Tras extraer el ZIP, completar el rebase del recibo antes de arrancar la API.
No descargar modelos, reindexar ni editar datos durante la exposición.

## Guion

1. Presentar: «MVP académico local con diez artículos provisionales; no certificamos
   OCR, integridad ni vigencia. La coincidencia literal no es una validación jurídica».
2. Abrir http://localhost:5173 y preguntar:

   **¿Cuándo comienza la tentativa según el artículo 16 del Código Penal?**

   Esperar sin reenviar. Mostrar el aviso experimental, la cita y la tarjeta de fuente 16.
   Comparar el texto con `data/processed/pilot_10_v1/articles_candidates.jsonl`.
3. Mostrar abstención con:

   **¿Qué dispone el artículo 999 del Código Penal?**

   Explicar que no se inventan artículos ni se añaden fuentes cuando falta evidencia.
4. Explicar React → FastAPI → embeddings/Chroma → Ollama → validación literal.
   No existe memoria conversacional en el motor.
5. Indicar el alcance offline: se ejecutó con conexiones externas bloqueadas dentro
   de Python, sin desconectar físicamente el equipo ni bloquear el proceso Ollama.
6. Cerrar: el siguiente trabajo es cotejo oficial, revisión OCR y evaluación mayor.

## Contingencias

- Conexión: comprobar backend 8000 y Ollama 11434; no confundir error con ausencia de evidencia.
- Recibo/ruta tras extraer: detener API y completar el paso de rebase del README.
- Carga inicial lenta: esperar; no enviar la misma pregunta repetidamente.
- Abstención: informarla honestamente. La evidencia guardada en `release/SMOKE_RESULT.json`
  y `release/UI_PROOF.png` puede mostrarse como EJECUCIÓN PREVIA, nunca como una respuesta
  que acaba de producirse en vivo.
- No cambiar puertos al azar: React y CORS usan direcciones fijas.
