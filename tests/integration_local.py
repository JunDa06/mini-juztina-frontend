"""Prueba REAL embeddings + Chroma persistente + Ollama; corpus SINTÉTICO temporal."""
import json
import tempfile
import sys
import subprocess
from dataclasses import replace
from pathlib import Path
from core.config import Config
from core.embeddings import LocalEmbeddings
from core.rag_engine import RAGEngine
from tests.test_engine import SYNTHETIC


def worker(folder, phase):
    # Auditoría de red durante TODA la integración, incluidas cargas de modelos.
    # Fallar si cualquier dependencia intenta conectarse fuera de loopback.
    def audit(event, args):
        if event == "socket.connect":
            address = args[1]
            if isinstance(address, tuple) and address[0] not in {"127.0.0.1", "::1", "localhost"}:
                raise RuntimeError(f"Conexión externa prohibida en prueba offline: {address[0]}")
        if event == "socket.getaddrinfo" and args[0] not in {"127.0.0.1", "::1", "localhost"}:
            raise RuntimeError("DNS externo prohibido en prueba offline")
    sys.addaudithook(audit)
    root = Path(folder)
    corpus = root / "synthetic-NOT-OFFICIAL.jsonl"
    rows = [SYNTHETIC,
            {**SYNTHETIC, "id": "TEST-002", "articulo": "TEST-B",
             "texto": "En esta prueba sintética, las plantas del invernadero se riegan los martes."},
            {**SYNTHETIC, "id": "TEST-003", "articulo": "TEST-C",
             "texto": "En esta prueba sintética, el taller de pintura utiliza pigmentos de color azul."}]
    config = replace(Config(), corpus=corpus, storage=root / "chroma")
    if phase == "--index":
        corpus.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")
        engine = RAGEngine(config, allowed_documents={SYNTHETIC["documento"]})
        indexed = engine.index()
        assert indexed["articles"] == 3 and indexed["chunks"] >= 3, indexed
        assert engine.index() == indexed
        chunks = list(engine._embeddings.chunks(("Texto sintético extenso de ensayo. " * 500) + "MARCADOR_FINAL_TEST"))
        assert len(chunks) > 1 and any("MARCADOR_FINAL_TEST" in c for c in chunks)
        tokenizer = engine._embeddings.model.tokenizer
        assert all(len(tokenizer("passage: " + c)["input_ids"]) <= engine._embeddings.model.max_seq_length for c in chunks)
        print("SYNTHETIC ONLY: indexación idempotente y ventanas sin truncamiento", indexed, flush=True)
        return
    # Proceso nuevo recupera la colección persistida, sin reindexar.
    reader = RAGEngine(config, allowed_documents={SYNTHETIC["documento"]})
    output = reader.answer_question("¿A qué hora abre la biblioteca de ensayo?")
    print(json.dumps(output, ensure_ascii=False, indent=2), flush=True)
    assert output["status"] == "answered", output
    assert output["sources"][0]["texto"] == SYNTHETIC["texto"]
    assert len(output["sources"]) == 1, output
    abstain = reader.answer_question("¿Qué sanción corresponde al robo agravado?")
    print("NO EVIDENCE", json.dumps(abstain, ensure_ascii=False), flush=True)
    assert abstain["status"] == "insufficient_evidence", abstain
    print("PASS: pipeline real con corpus sintético; NO validación jurídica.", flush=True)


def main():
    # El proceso hijo libera los archivos mmap de Chroma antes de limpiar en Windows.
    if len(sys.argv) == 3 and sys.argv[1] in {"--index", "--query"}:
        worker(sys.argv[2], sys.argv[1])
    else:
        with tempfile.TemporaryDirectory(prefix="mini-juztina-TEST-") as folder:
            for phase in ("--index", "--query"):
                subprocess.run([sys.executable, "-u", "-m", "tests.integration_local", phase, folder],
                               check=True, timeout=300)


if __name__ == "__main__":
    main()
