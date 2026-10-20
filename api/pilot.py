"""Entrada ASGI opcional para el piloto experimental. api.main:app permanece intacta."""
from functools import lru_cache
import logging
from threading import Lock

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.main import ChatRequest, ChatResponse, ChatSource, RAGResult, invalid_request
from scripts.pilot_runtime import load_pilot

NOTICE = "PILOTO EXPERIMENTAL: texto no cotejado oficialmente.\n\n"
logger = logging.getLogger(__name__)
_lock = Lock()


@lru_cache(maxsize=1)
def pilot_engine():
    return load_pilot()


app = FastAPI(title="Mini-Juztina — piloto experimental no cotejado", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware,
                   allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["POST"], allow_headers=["Content-Type"], allow_credentials=False)
app.add_exception_handler(RequestValidationError, invalid_request)


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    try:
        with _lock:
            result = RAGResult.model_validate(pilot_engine().answer_question(payload.message))
        return ChatResponse(answer=NOTICE + result.answer, status=result.status,
                            conversation_id=payload.conversation_id,
                            sources=[ChatSource(law=s.documento, article=s.articulo,
                                                excerpt=s.texto, page_pdf=s.pagina_pdf) for s in result.sources])
    except Exception:
        logger.exception("Fallo interno del piloto experimental")
        return JSONResponse(status_code=500, content={
            "answer": NOTICE + "No fue posible consultar el índice piloto local.",
            "status": "error", "sources": [], "conversation_id": payload.conversation_id})
