"""Respuestas extractivas: el LLM selecciona; solo se publica texto verificado localmente."""
import logging
import re
import unicodedata
from functools import lru_cache

from .config import Config
from .corpus import read_corpus
from .embeddings import LocalEmbeddings
from .ollama_client import OllamaClient
from .vector_store import VectorStore, model_fingerprint

logger = logging.getLogger(__name__)


def result(status, answer):
    return {"answer": answer, "sources": [], "status": status}


def outside_scope(question):
    text = unicodedata.normalize("NFKD", question.lower()).encode("ascii", "ignore").decode()
    return bool(re.search(
        r"\b(codigo (civil|tributario|laboral|procesal)|constitucion (de (chile|argentina|colombia|espana)|chilena)|"
        r"legislacion (chilena|argentina|colombiana|espanola)|receta|clima|futbol)\b", text))


def article_number(value):
    return re.sub(r"^art[ií]culo\s*", "", value, flags=re.I).strip().rstrip(".°º").upper()


class RAGEngine:
    def __init__(self, config=None, *, embeddings=None, store=None, client=None, allowed_documents=None):
        self.config = config or Config()
        self._embeddings = embeddings
        self._store = store
        self._client = client
        self.allowed_documents = allowed_documents

    def _load(self):
        kwargs = {} if self.allowed_documents is None else {"allowed_documents": self.allowed_documents}
        articles, digest = read_corpus(self.config.corpus, **kwargs)
        if self._embeddings is None:
            self._embeddings = LocalEmbeddings(self.config.embedding_model)
        store = self._store or VectorStore(self.config, digest, model_fingerprint(self.config.embedding_model))
        return articles, store

    def index(self):
        articles, store = self._load()
        return {"articles": len(articles), "chunks": store.index(articles, self._embeddings)}

    def answer_question(self, question: str) -> dict:
        if not isinstance(question, str) or not question.strip() or len(question) > 2000:
            return result("error", "La pregunta debe contener entre 1 y 2000 caracteres.")
        if outside_scope(question):
            return result("out_of_scope", "El ámbito es la Constitución Política del Perú y el Código Penal peruano proporcionados.")
        if not self.config.corpus.is_file():
            return result("insufficient_evidence", "No hay corpus local disponible.")
        try:
            articles, store = self._load()
            hits = store.search(question, self._embeddings)
            candidates = {}
            for article_id, fragment, score in hits:
                if score < self.config.min_similarity:
                    continue
                if article_id not in articles or fragment not in articles[article_id].texto:
                    raise ValueError("Índice inconsistente con corpus")
                candidates[f"S{len(candidates) + 1}"] = (articles[article_id], fragment)
            requested = {v.upper() for v in re.findall(r"art[ií]culo\s+(\d+(?:-[A-Za-z]+)?)\b", question, re.I)}
            if requested:
                candidates = {key: (a, fragment) for key, (a, fragment) in candidates.items()
                              if article_number(a.articulo) in requested}
            normalized = unicodedata.normalize("NFKD", question.lower()).encode("ascii", "ignore").decode()
            constitution = "constitucion" in normalized
            penal = "codigo penal" in normalized
            if constitution != penal:
                document = "Constitución Política del Perú" if constitution else "Código Penal peruano"
                candidates = {key: (a, fragment) for key, (a, fragment) in candidates.items()
                              if a.documento == document}
            if requested and not requested.issubset({article_number(a.articulo) for a, _ in candidates.values()}):
                return result("insufficient_evidence", "No se recuperaron todos los artículos solicitados con evidencia suficiente.")
            if not candidates:
                return result("insufficient_evidence", "No encontré evidencia local con relevancia suficiente.")
            client = self._client or OllamaClient(self.config)
            selection = client.select_evidence(question, [
                {"id": key, "documento": a.documento, "articulo": a.articulo, "texto": fragment}
                for key, (a, fragment) in candidates.items()])
            if not isinstance(selection, dict) or type(selection.get("sufficient")) is not bool:
                raise ValueError("Respuesta del modelo inválida")
            if selection["sufficient"] is False:
                return result("insufficient_evidence", "Los fragmentos recuperados no bastan para responder la pregunta.")
            evidence = selection.get("evidence")
            if not isinstance(evidence, list) or not 1 <= len(evidence) <= 5:
                raise ValueError("Evidencia inválida")
            sources, lines, seen = [], [], set()
            for item in evidence:
                if not isinstance(item, dict) or item.get("id") not in candidates:
                    raise ValueError("Referencia no recuperada")
                article, fragment = candidates[item["id"]]
                quote = item.get("quote")
                if not isinstance(quote, str) or len(quote.strip()) < 12 or quote not in fragment:
                    raise ValueError("Cita no literal")
                if article.id not in seen:
                    sources.append(article.source())
                    seen.add(article.id)
                page = "" if article.pagina_pdf is None else f", p. PDF {article.pagina_pdf}"
                lines.append(f'«{quote}» [{article.documento}, artículo {article.articulo}{page}]')
            if requested and not requested.issubset({article_number(s["articulo"]) for s in sources}):
                raise ValueError("El modelo omitió artículos solicitados")
            return {"answer": "Evidencia textual del corpus local:\n\n" + "\n\n".join(lines),
                    "sources": sources, "status": "answered"}
        except (ValueError, KeyError, TypeError) as exc:
            logger.warning("Evidencia rechazada: %s", exc)
            return result("insufficient_evidence", "No fue posible validar evidencia y citas suficientes en el corpus local.")
        except Exception:
            logger.exception("Error del motor RAG")
            return result("error", "Error local al consultar el motor. Revise el índice, los modelos y Ollama.")


@lru_cache(maxsize=1)
def _default_engine():
    return RAGEngine()


def answer_question(question: str) -> dict:
    return _default_engine().answer_question(question)
