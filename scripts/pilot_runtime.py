"""Consulta solo la colección piloto ya indexada, sin activar el corpus de producción."""
from dataclasses import replace
import json
from pathlib import Path

from core.config import Config
from core.corpus import read_corpus
from core.embeddings import LocalEmbeddings
from core.rag_engine import RAGEngine
from core.vector_store import VectorStore
from scripts.pilot_index import plan
from scripts.prepare_pilot import ROOT


def load_pilot(pilot_dir=None):
    pilot_dir = Path(pilot_dir) if pilot_dir else ROOT / "data/processed/pilot_10_v1"
    current = plan(pilot_dir)
    receipt = json.loads((pilot_dir / "index_receipt.json").read_text(encoding="utf-8"))
    for key in ("storage", "collection", "corpus_sha256", "embedding_sha256"):
        if receipt[key] != current[key]:
            raise ValueError("El índice piloto no coincide con los candidatos/modelo actuales")
    storage = Path(current["storage"])
    # Evitar que abrir un piloto ausente cree accidentalmente un almacenamiento vacío.
    if not (storage / "chroma.sqlite3").is_file():
        raise FileNotFoundError("No existe la base piloto persistida")
    config = replace(Config(), corpus=Path(current["corpus"]), storage=storage,
                     embedding_model=Path(current["embedding_model"]))
    store = VectorStore(config, current["corpus_sha256"], current["embedding_sha256"])
    store.name = current["collection"]
    collection = store.client.get_collection(store.name, embedding_function=None)
    if not collection.metadata.get("ready") or collection.count() != receipt["chunks"]:
        raise ValueError("La colección piloto está incompleta o cambió desde la indexación")
    articles, _ = read_corpus(config.corpus)
    existing = collection.get(include=["metadatas"])
    if {m["article_id"] for m in existing["metadatas"]} != set(articles):
        raise ValueError("La colección piloto no contiene exactamente los diez candidatos")
    return RAGEngine(config, embeddings=LocalEmbeddings(config.embedding_model), store=store)
