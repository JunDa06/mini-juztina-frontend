"""Comprobación real de persistencia y recuperación; no añade ni modifica registros."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from core.corpus import read_corpus
from scripts.pilot_runtime import load_pilot
from scripts.prepare_pilot import ROOT, CONSTITUTION, PENAL

QUERIES = [
    ("¿Cómo se protege la dignidad de la persona humana?", CONSTITUTION, "1"),
    ("¿Qué protección tiene la salud de la familia y la comunidad?", CONSTITUTION, "7"),
    ("¿Qué se reconoce sobre el acceso al agua potable?", CONSTITUTION, "7-A"),
    ("¿Cuándo comienza la ejecución de un delito sin que llegue a consumarse?", PENAL, "16"),
    ("¿Qué ocurre si alguien presta auxilio dolosamente para realizar un hecho punible?", PENAL, "25"),
    ("¿Qué se señala sobre ocasionar la muerte de una persona por culpa?", PENAL, "111"),
    ("¿Qué se indica sobre causar por culpa un daño en el cuerpo o la salud?", PENAL, "124"),
    ("¿Qué se menciona sobre vender alimentos contaminados a sabiendas o actuar por culpa?", PENAL, "288"),
]


def verify():
    engine = load_pilot()
    articles, corpus_hash = read_corpus(engine.config.corpus)
    store = engine._store
    collection = store.client.get_collection(store.name, embedding_function=None)
    loaded = collection.get(include=["documents", "metadatas"])
    counts = Counter(meta["article_id"] for meta in loaded["metadatas"])
    expected = {}
    for article in articles.values():
        for number, chunk in enumerate(engine._embeddings.chunks(article.texto)):
            expected[f"{article.id}:{number}"] = (article.id, chunk)
    actual = {chunk_id: (meta["article_id"], text) for chunk_id, meta, text in zip(
        loaded["ids"], loaded["metadatas"], loaded["documents"])}
    if actual != expected:
        raise ValueError("IDs, fragmentos o metadatos persistidos difieren del particionado de los diez originales")
    exact = []
    for article in articles.values():
        hits = collection.get(where={"article_id": article.id}, include=["documents", "metadatas"])
        phrase = next(iter(engine._embeddings.chunks(article.texto)))[:48]
        literal = collection.get(where={"article_id": article.id}, where_document={"$contains": phrase}, include=["metadatas"])
        if not hits["ids"] or not literal["ids"]:
            raise ValueError("Búsqueda exacta por artículo/texto sin resultados")
        exact.append({"documento": article.documento, "articulo": article.articulo,
                      "fragmentos": len(hits["ids"]), "literal_encontrado": phrase, "ok": True})
    semantic = []
    for question, document, number in QUERIES:
        hits = store.search(question, engine._embeddings)
        ranked = [{"documento": articles[article_id].documento, "articulo": articles[article_id].articulo,
                   "similitud_coseno": score, "supera_umbral_motor": score >= engine.config.min_similarity,
                   "texto_fragmento": text} for article_id, text, score in hits]
        rank = next((i for i, row in enumerate(ranked, 1) if (row["documento"], row["articulo"]) == (document, number)), None)
        semantic.append({"pregunta": question, "esperado_por_tema_del_texto_local": [document, number],
                         "rango_en_top_5": rank, "resultados": ranked})
    output = {"modo": "experimental_no_cotejado", "proceso_nuevo_abre_indice_persistido": True,
              "corpus_sha256": corpus_hash, "collection": store.name, "storage": str(engine.config.storage),
              "registros": len(counts), "fragmentos": collection.count(), "identidad_fragmentos_originales": True,
              "busquedas_exactas": exact, "busquedas_semanticas": semantic,
              "recuperaciones_esperadas_en_top_5": sum(r["rango_en_top_5"] is not None for r in semantic),
              "juridicamente_verificado": False}
    target = ROOT / "data/processed/pilot_10_v1/retrieval_results.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items() if k not in {"busquedas_exactas", "busquedas_semanticas"}}, ensure_ascii=False, indent=2))
    for r in semantic:
        first = r["resultados"][0]
        print(json.dumps({"esperado": r["esperado_por_tema_del_texto_local"], "rango": r["rango_en_top_5"],
                          "primero": [first["documento"], first["articulo"]], "similitud": first["similitud_coseno"]}, ensure_ascii=False))


if __name__ == "__main__":
    verify()
