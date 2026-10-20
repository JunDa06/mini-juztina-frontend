"""Sin memoria conversacional: conversation_id solo se devuelve al cliente."""
import logging
from threading import Lock
from typing import Annotated, Literal

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from core import rag_engine

logger = logging.getLogger(__name__)
_rag_lock = Lock()
Status = Literal["answered", "out_of_scope", "insufficient_evidence", "error"]


class ChatRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    message: Annotated[str, Field(min_length=1, max_length=2000)]
    conversation_id: str

    @field_validator("message")
    @classmethod
    def non_blank_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("El mensaje no puede estar vacío")
        return value


class RAGSource(BaseModel):
    model_config = ConfigDict(strict=True)
    documento: str
    articulo: str
    texto: str
    pagina_pdf: Annotated[int, Field(ge=1)] | None


class RAGResult(BaseModel):
    model_config = ConfigDict(strict=True)
    answer: str
    sources: list[RAGSource]
    status: Status


class ChatSource(BaseModel):
    law: str
    article: str
    excerpt: str
    page_pdf: int | None


class ChatResponse(BaseModel):
    answer: str
    status: Status
    sources: list[ChatSource]
    conversation_id: str


app = FastAPI(
    title="Mini-Juztina API local",
    description="Adaptador sin estado conversacional del RAG local. No añade historial a las consultas.",
    docs_url=None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def invalid_request(_request, _exception):
    # No devolver el cuerpo recibido ni los detalles internos de Pydantic.
    return JSONResponse(status_code=422, content={
        "answer": "Solicitud inválida: message debe ser una cadena no vacía de hasta 2000 caracteres y conversation_id una cadena.",
        "status": "error", "sources": [],
    })


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    try:
        # El RAG es síncrono. FastAPI ejecuta esta ruta en su pool de hilos;
        # serializar evita carreras en la carga del modelo y la inferencia CPU.
        with _rag_lock:
            result = RAGResult.model_validate(rag_engine.answer_question(payload.message))
        return ChatResponse(
            answer=result.answer,
            status=result.status,
            conversation_id=payload.conversation_id,
            sources=[ChatSource(law=s.documento, article=s.articulo,
                                excerpt=s.texto, page_pdf=s.pagina_pdf)
                     for s in result.sources],
        )
    except Exception:
        logger.exception("Fallo interno al atender /api/chat")
        return JSONResponse(status_code=500, content={
            "answer": "No fue posible procesar la consulta en el motor local.",
            "status": "error", "sources": [], "conversation_id": payload.conversation_id,
        })
