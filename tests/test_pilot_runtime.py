"""Fixtures SINTÉTICOS y dobles: no escriben ni borran colecciones reales."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from api.pilot import NOTICE, app
from scripts.pilot_runtime import load_pilot


class PilotAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.payload = {"message": "Consulta SINTÉTICA de ensayo", "conversation_id": "TEST-PILOT"}

    def test_real_contract_with_mocked_engine_and_notice(self):
        engine = Mock()
        engine.answer_question.return_value = {"answer": "Cita SINTÉTICA de prueba.", "status": "answered",
            "sources": [{"documento": "PRUEBA NO OFICIAL", "articulo": "TEST", "texto": "Texto SINTÉTICO.", "pagina_pdf": None}]}
        with patch("api.pilot.pilot_engine", return_value=engine):
            response = self.client.post("/api/chat", json=self.payload)
        self.assertEqual(response.status_code, 200)
        engine.answer_question.assert_called_once_with(self.payload["message"])
        data = response.json()
        self.assertTrue(data["answer"].startswith(NOTICE))
        self.assertEqual(data["status"], "answered")
        self.assertEqual(data["conversation_id"], "TEST-PILOT")
        self.assertEqual(data["sources"], [{"law": "PRUEBA NO OFICIAL", "article": "TEST", "excerpt": "Texto SINTÉTICO.", "page_pdf": None}])

    def test_abstention_not_changed_into_answer(self):
        engine = Mock()
        engine.answer_question.return_value = {"answer": "Sin evidencia de ensayo.", "status": "insufficient_evidence", "sources": []}
        with patch("api.pilot.pilot_engine", return_value=engine):
            response = self.client.post("/api/chat", json=self.payload)
        self.assertEqual(response.json()["status"], "insufficient_evidence")
        self.assertEqual(response.json()["sources"], [])

    def test_validation_before_engine(self):
        with patch("api.pilot.pilot_engine") as engine:
            response = self.client.post("/api/chat", json={**self.payload, "message": "  "})
        self.assertEqual(response.status_code, 422)
        engine.assert_not_called()

    def test_internal_error_not_exposed(self):
        with patch("api.pilot.pilot_engine", side_effect=RuntimeError("SECRET-PILOT-PATH")):
            with self.assertLogs("api.pilot", level="ERROR"):
                response = self.client.post("/api/chat", json=self.payload)
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("SECRET-PILOT-PATH", response.text)
        self.assertEqual(response.json()["status"], "error")

    def test_cors_origins_remain_explicit(self):
        for origin, expected in (("http://localhost:5173", 200), ("http://127.0.0.1:5173", 200), ("https://example.com", 400)):
            response = self.client.options("/api/chat", headers={"Origin": origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
            self.assertEqual(response.status_code, expected)

    def test_default_app_does_not_get_pilot_banner(self):
        from api.main import app as default_app
        with TestClient(default_app) as client:
            with patch("core.rag_engine.answer_question", return_value={"answer": "ENSAYO ORIGINAL", "status": "insufficient_evidence", "sources": []}):
                response = client.post("/api/chat", json=self.payload)
        self.assertEqual(response.json()["answer"], "ENSAYO ORIGINAL")


class PilotRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mini-juztina-runtime-SYNTHETIC-")
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.current = {"storage": str(self.folder / "storage"), "collection": "pilot_articles_TEST",
                        "corpus_sha256": "TESTHASH", "embedding_sha256": "TESTMODEL",
                        "corpus": str(self.folder / "corpus.jsonl"), "embedding_model": str(self.folder / "model")}
        self.receipt = {**self.current, "chunks": 10}
        self.save_receipt()

    def save_receipt(self):
        (self.folder / "index_receipt.json").write_text(json.dumps(self.receipt), encoding="utf-8")

    def test_mismatched_receipt_blocks_storage_access(self):
        self.receipt["collection"] = "OTHER"
        self.save_receipt()
        with patch("scripts.pilot_runtime.plan", return_value=self.current), patch("scripts.pilot_runtime.VectorStore") as store:
            with self.assertRaisesRegex(ValueError, "no coincide"):
                load_pilot(self.folder)
        store.assert_not_called()

    def test_absent_database_is_not_created(self):
        with patch("scripts.pilot_runtime.plan", return_value=self.current), patch("scripts.pilot_runtime.VectorStore") as store:
            with self.assertRaises(FileNotFoundError):
                load_pilot(self.folder)
        store.assert_not_called()
        self.assertFalse(Path(self.current["storage"]).exists())

    def test_partial_collection_rejected(self):
        storage = Path(self.current["storage"])
        storage.mkdir()
        (storage / "chroma.sqlite3").write_bytes(b"SYNTHETIC: NOT A REAL DATABASE")
        with patch("scripts.pilot_runtime.plan", return_value=self.current), patch("scripts.pilot_runtime.VectorStore") as store:
            collection = store.return_value.client.get_collection.return_value
            collection.metadata = {"ready": False}
            with self.assertRaisesRegex(ValueError, "incompleta"):
                load_pilot(self.folder)


if __name__ == "__main__":
    unittest.main()
