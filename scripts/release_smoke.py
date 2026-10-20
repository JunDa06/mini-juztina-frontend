"""Prueba real de release con red externa bloqueada para este proceso Python."""
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import socket
import sys
import time


def main():
    denied = []
    allowed = []

    class OfflineBlocked(RuntimeError):
        pass

    def is_local(host):
        if host == "localhost":
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False

    def audit(event, args):
        if event == "socket.getaddrinfo" and not is_local(args[0]):
            denied.append({"evento": event, "destino": str(args[0])})
            raise OfflineBlocked("DNS externo bloqueado por prueba offline de proceso")
        if event == "socket.connect":
            address = args[1]
            if isinstance(address, tuple):
                if not is_local(address[0]):
                    denied.append({"evento": event, "destino": str(address[0])})
                    raise OfflineBlocked("Socket externo bloqueado por prueba offline de proceso")
                allowed.append({"host": str(address[0]), "puerto": address[1]})

    sys.addaudithook(audit)
    for probe in (lambda: socket.getaddrinfo("example.com", 443),
                  lambda: socket.socket().connect(("192.0.2.1", 443))):
        try:
            probe()
        except OfflineBlocked:
            pass
        else:
            raise AssertionError("La prueba no consiguió bloquear el acceso externo")

    # Se importa y carga TODO el pipeline bajo el bloqueo, sin reutilizar el backend ya iniciado.
    from fastapi.testclient import TestClient
    from api.pilot import app, NOTICE
    from core.corpus import read_corpus
    from scripts.prepare_pilot import ROOT

    folder = ROOT / "data/processed/pilot_10_v1"
    articles, _ = read_corpus(folder / "articles_candidates.jsonl")
    question = "¿Cuándo comienza la tentativa según el artículo 16 del Código Penal?"
    start = time.monotonic()
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": question, "conversation_id": "release-offline-real"},
                               headers={"Origin": "http://localhost:5173"})
        data = response.json()
        assert response.status_code == 200, data
        assert data["status"] == "answered", data
        assert data["answer"].startswith(NOTICE), data
        assert data["conversation_id"] == "release-offline-real"
        assert len(data["sources"]) == 1, data
        source = data["sources"][0]
        article = next(a for a in articles.values() if a.documento == source["law"] and a.articulo == source["article"])
        assert article.articulo == "16" and article.documento == "Código Penal peruano"
        assert source["excerpt"] == article.texto
        quotes = re.findall(r"«(.*?)»", data["answer"], flags=re.S)
        assert quotes and all(q in article.texto for q in quotes)
        missing = client.post("/api/chat", json={"message": "¿Qué dispone el artículo 999 del Código Penal?",
                                                 "conversation_id": "release-abstention"})
        assert missing.json()["status"] == "insufficient_evidence", missing.json()
        assert missing.json()["sources"] == []
    record = {
        "fecha_local": "2026-10-20", "prueba": "FastAPI + Chroma persistente + embeddings + Ollama reales",
        "http": response.status_code, "status": data["status"], "pregunta": question,
        "respuesta": data, "cita_literal_verificada": True, "fuente_completa_identica": True,
        "sha256_texto_fuente": hashlib.sha256(article.texto.encode()).hexdigest(),
        "duracion_segundos": round(time.monotonic() - start, 2),
        "abstencion_articulo_999": missing.json(),
        "modo_offline": "Audit hook Python: deniega DNS/sockets externos en este proceso y permite loopback",
        "pruebas_bloqueo_externo": denied, "conexiones_loopback": allowed,
        "limitacion_offline": "No se deshabilitaron adaptadores de red. El bloqueo no se extiende a otros procesos, incluido Ollama.",
        "corpus_juridicamente_verificado": False,
    }
    target = ROOT / "release/SMOKE_RESULT.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k != "respuesta"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
