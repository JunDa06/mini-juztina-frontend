import hashlib
import json
from pathlib import Path


def model_fingerprint(path: Path):
    digest = hashlib.sha256()
    for file in sorted(path.rglob("*")):
        if file.is_file():
            digest.update(file.relative_to(path).as_posix().encode())
            with file.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
    return digest.hexdigest()


class VectorStore:
    def __init__(self, config, corpus_hash, embedding_hash):
        from chromadb import PersistentClient
        from chromadb.config import Settings
        self.client = PersistentClient(path=str(config.storage),
                                       settings=Settings(anonymized_telemetry=False))
        self.name = "articles_" + hashlib.sha256(
            (corpus_hash + embedding_hash + "chunks-v1").encode()).hexdigest()[:40]
        self.config = config

    def index(self, articles, embeddings):
        # Publicar solo después de terminar. Una interrupción deja ready=False.
        collection = self.client.get_or_create_collection(
            self.name, embedding_function=None,
            metadata={"hnsw:space": "cosine", "ready": False})
        if collection.metadata.get("ready"):
            return collection.count()
        batch = []
        count = 0
        for article in articles.values():
            for number, chunk in enumerate(embeddings.chunks(article.texto)):
                batch.append((f"{article.id}:{number}", chunk, {"article_id": article.id}))
                if len(batch) == 64:
                    self._write(collection, batch, embeddings)
                    count += len(batch)
                    batch = []
        if batch:
            self._write(collection, batch, embeddings)
            count += len(batch)
        # Chroma rechaza hnsw:space en modify, incluso si el valor no cambia.
        collection.modify(metadata={"ready": True})
        return count

    @staticmethod
    def _write(collection, batch, embeddings):
        collection.upsert(ids=[r[0] for r in batch], documents=[r[1] for r in batch],
                          metadatas=[r[2] for r in batch],
                          embeddings=embeddings.encode([r[1] for r in batch]))

    def search(self, question, embeddings):
        try:
            collection = self.client.get_collection(self.name, embedding_function=None)
        except Exception as exc:
            raise RuntimeError("Índice ausente: ejecutar python -m core.cli index") from exc
        if not collection.metadata.get("ready") or not collection.count():
            raise RuntimeError("Índice incompleto")
        result = collection.query(query_embeddings=embeddings.encode([question], query=True),
                                  n_results=min(self.config.top_k, collection.count()),
                                  include=["documents", "metadatas", "distances"])
        return [(meta["article_id"], text, 1 - distance) for meta, text, distance in zip(
            result["metadatas"][0], result["documents"][0], result["distances"][0])]
