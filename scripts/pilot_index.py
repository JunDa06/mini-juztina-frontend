"""Planificar sin escribir en Chroma. index/remove requieren --execute y autorización humana previa."""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path

from core.config import Config
from core.corpus import read_corpus
from core.vector_store import model_fingerprint
from scripts.prepare_pilot import ROOT, SELECTION, digest, jsonl


def plan(pilot_dir=None, root=ROOT):
    root = Path(root).resolve()
    pilot_dir = Path(pilot_dir) if pilot_dir else root / "data/processed/pilot_10_v1"
    manifest = json.loads((pilot_dir / "manifest.json").read_text(encoding="utf-8"))
    corpus = pilot_dir / "articles_candidates.jsonl"
    if digest(corpus) != manifest["sha256_candidatos"]:
        raise ValueError("Candidatos modificados: preparar una nueva versión del piloto")
    articles, corpus_hash = read_corpus(corpus)
    if len(articles) != 10 or manifest["registros"] != 10:
        raise ValueError("Deben existir exactamente diez registros")
    if {(a.documento, a.articulo) for a in articles.values()} != set(SELECTION):
        raise ValueError("El conjunto de candidatos no coincide con la selección")
    traces_path = root / "data/processed/audit_records.jsonl"
    accepted_path = root / "data/processed/articles_structurally_accepted.jsonl"
    report_path = root / "data/processed/audit_report.json"
    for path, key in ((traces_path, "sha256_auditoria"), (accepted_path, "sha256_aptos"),
                      (report_path, "sha256_informe_auditoria")):
        if digest(path) != manifest[key]:
            raise ValueError("Auditoría modificada: requiere reconstruir el piloto")
    originals = {r["id_auditoria"]: r["normalizado_candidato"] for r in jsonl(traces_path)}
    metadata = {entry["id"]: entry for entry in manifest["candidatos"]}
    if len(metadata) != 10 or set(metadata) != set(articles):
        raise ValueError("El manifiesto no cubre los diez candidatos")
    for row in jsonl(corpus):
        entry = metadata[row["id"]]
        if originals.get(row["id"]) != row or entry["sha256_texto"] != hashlib.sha256(row["texto"].encode("utf-8")).hexdigest():
            raise ValueError("Candidato no idéntico a su normalización auditada")
        origin = entry["origen"]
        expected_name = "constitucion.jsonl" if row["documento"].startswith("Constitución") else "codigo_penal_articulos.jsonl"
        source = root / "data/sources" / expected_name
        if origin["archivo"] != f"data/sources/{expected_name}" or digest(source) != origin["sha256_archivo"]:
            raise ValueError("Original alterado o procedencia inválida")
        if json.loads(source.read_text(encoding="utf-8-sig").splitlines()[origin["linea"] - 1])["texto"] != row["texto"]:
            raise ValueError("El texto ya no coincide con su original")
    # Namespace y directorio derivados del contenido; nunca storage/chroma.
    storage_root = (root / "storage/pilots").resolve()
    storage = storage_root / ("pilot-10-" + corpus_hash[:16])
    if storage.resolve().parent != storage_root or storage.resolve() == (root / "storage/chroma").resolve():
        raise ValueError("Almacenamiento piloto fuera de su directorio aislado")
    model = root / "models/multilingual-e5-small"
    if not model.is_dir():
        raise FileNotFoundError("Falta el modelo local de embeddings")
    embedding_hash = model_fingerprint(model)
    collection = "pilot_articles_" + hashlib.sha256((corpus_hash + embedding_hash + "chunks-v1").encode()).hexdigest()[:40]
    return {"pilot_dir": str(pilot_dir.resolve()), "corpus": str(corpus.resolve()), "corpus_sha256": corpus_hash,
            "storage": str(storage), "collection": collection, "embedding_model": str(model),
            "embedding_sha256": embedding_hash, "registros": 10,
            "juridicamente_verificado": False, "operaciones_chroma_ejecutadas": False}


def index(plan_data, *, execute=False):
    if not execute:
        raise ValueError("Sin --execute no se permite indexar")
    # Revalidar contenido/modelo inmediatamente antes de escribir.
    current = plan(plan_data["pilot_dir"])
    if current != plan_data:
        raise ValueError("El plan cambió antes de indexar")
    from core.embeddings import LocalEmbeddings
    from core.vector_store import VectorStore
    config = replace(Config(), corpus=Path(current["corpus"]), storage=Path(current["storage"]),
                     embedding_model=Path(current["embedding_model"]))
    articles, _ = read_corpus(config.corpus)
    embeddings = LocalEmbeddings(config.embedding_model)
    store = VectorStore(config, current["corpus_sha256"], current["embedding_sha256"])
    # Solo configura esta instancia nueva; no se modifica core ni ninguna colección de producción.
    store.name = current["collection"]
    chunks = store.index(articles, embeddings)
    receipt = {**current, "operaciones_chroma_ejecutadas": True, "chunks": chunks,
               "advertencia": "Piloto técnico no cotejado; no es una validación jurídica."}
    (Path(current["pilot_dir"]) / "index_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def remove(pilot_dir, *, execute=False, root=ROOT):
    if not execute:
        raise ValueError("Sin --execute no se elimina ninguna colección")
    root = Path(root).resolve()
    receipt = json.loads((Path(pilot_dir) / "index_receipt.json").read_text(encoding="utf-8"))
    expected_storage = root / "storage/pilots" / ("pilot-10-" + receipt["corpus_sha256"][:16])
    expected_collection = "pilot_articles_" + hashlib.sha256((receipt["corpus_sha256"] + receipt["embedding_sha256"] + "chunks-v1").encode()).hexdigest()[:40]
    storage = Path(receipt["storage"]).resolve()
    if storage != expected_storage.resolve() or storage.parent != (root / "storage/pilots").resolve() or receipt["collection"] != expected_collection:
        raise ValueError("Recibo fuera del almacenamiento/nombre piloto esperado")
    if not storage.is_dir():
        raise FileNotFoundError("No existe almacenamiento piloto; no se crea para revertir")
    from chromadb import PersistentClient
    from chromadb.config import Settings
    client = PersistentClient(path=str(storage), settings=Settings(anonymized_telemetry=False))
    client.delete_collection(receipt["collection"])
    return {"coleccion_eliminada": receipt["collection"], "storage": str(storage), "archivos_corpus_conservados": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "index", "remove"), nargs="?", default="plan")
    parser.add_argument("--pilot-dir", type=Path, default=ROOT / "data/processed/pilot_10_v1")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.action in {"index", "remove"} and not args.execute:
        parser.error("La mutación requiere --execute y autorización previa del usuario")
    if args.action == "remove":
        result = remove(args.pilot_dir, execute=args.execute)
    else:
        result = plan(args.pilot_dir)
        if args.action == "index":
            result = index(result, execute=args.execute)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
