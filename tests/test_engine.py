"""Datos exclusivamente sintéticos: no representan legislación oficial."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from dataclasses import replace

from core.config import Config
from core.corpus import read_corpus
from core.ollama_client import OllamaClient
from core.rag_engine import RAGEngine, answer_question

SYNTHETIC = {
    "id": "TEST-001", "documento": "PRUEBA SINTÉTICA NO OFICIAL",
    "titulo": "Ensayo", "capitulo": "", "articulo": "TEST-A",
    "texto": "En esta prueba sintética, la biblioteca de ensayo abre a las nueve.",
    "pagina_pdf": None, "version_fuente": "TEST-NO-OFICIAL-v1"
}


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "synthetic.jsonl"
        self.write([SYNTHETIC])
        self.config = Config(corpus=self.path, storage=Path(self.tmp.name) / "chroma")
        self.store = Mock()
        self.store.search.return_value = [(SYNTHETIC["id"], SYNTHETIC["texto"], .95)]
        self.client = Mock()
        self.client.select_evidence.return_value = {
            "sufficient": True, "evidence": [{"id": "S1", "quote": SYNTHETIC["texto"]}]}
        self.engine = RAGEngine(self.config, embeddings=Mock(), store=self.store,
                                client=self.client, allowed_documents={SYNTHETIC["documento"]})

    def write(self, rows):
        self.path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")

    def ask(self):
        return self.engine.answer_question("¿A qué hora abre la biblioteca de ensayo?")

    def test_answer_contract_and_local_metadata(self):
        output = self.ask()
        self.assertEqual(set(output), {"answer", "sources", "status"})
        self.assertEqual(output["status"], "answered")
        self.assertEqual(output["sources"][0]["pagina_pdf"], None)
        self.assertEqual(output["sources"][0]["texto"], SYNTHETIC["texto"])
        self.assertIn("TEST-A", output["answer"])

    def test_unknown_citation_rejected(self):
        self.client.select_evidence.return_value["evidence"][0]["id"] = "S999"
        self.assertEqual(self.ask()["status"], "insufficient_evidence")

    def test_fabricated_quote_rejected(self):
        self.client.select_evidence.return_value["evidence"][0]["quote"] = "La biblioteca abre a las diez."
        self.assertEqual(self.ask()["sources"], [])

    def test_low_similarity_never_calls_llm(self):
        self.store.search.return_value = [(SYNTHETIC["id"], SYNTHETIC["texto"], .3)]
        self.assertEqual(self.ask()["status"], "insufficient_evidence")
        self.client.select_evidence.assert_not_called()

    def test_llm_abstention(self):
        self.client.select_evidence.return_value = {"sufficient": False, "evidence": []}
        self.assertEqual(self.ask()["status"], "insufficient_evidence")

    def test_no_hits(self):
        self.store.search.return_value = []
        self.assertEqual(self.ask()["status"], "insufficient_evidence")

    def test_requested_article_missing(self):
        output = self.engine.answer_question("¿Qué dice el artículo 999?")
        self.assertEqual(output["status"], "insufficient_evidence")
        self.client.select_evidence.assert_not_called()

    def test_wrong_document_rejected(self):
        output = self.engine.answer_question("¿Qué dice la Constitución sobre la biblioteca?")
        self.assertEqual(output["status"], "insufficient_evidence")
        self.client.select_evidence.assert_not_called()

    def test_missing_corpus(self):
        self.path.unlink()
        self.assertEqual(self.ask()["status"], "insufficient_evidence")

    def test_scope(self):
        self.assertEqual(self.engine.answer_question("Explica el Código Civil")["status"], "out_of_scope")
        self.store.search.assert_not_called()

    def test_invalid_questions(self):
        for q in (None, 10, "", " ", "a" * 2001):
            self.assertEqual(self.engine.answer_question(q)["status"], "error")

    def test_ollama_failure(self):
        self.client.select_evidence.side_effect = TimeoutError("test timeout")
        self.assertEqual(self.ask()["status"], "error")

    def test_invalid_model_output(self):
        for selection in ([], {}, {"sufficient": "true"}, {"sufficient": True, "evidence": []}):
            self.client.select_evidence.return_value = selection
            self.assertEqual(self.ask()["status"], "insufficient_evidence")

    def test_stale_text_rejected(self):
        self.store.search.return_value = [(SYNTHETIC["id"], "Texto modificado", .99)]
        self.assertEqual(self.ask()["status"], "insufficient_evidence")

    def test_unknown_article_rejected(self):
        self.store.search.return_value = [("inventado", SYNTHETIC["texto"], .99)]
        self.assertEqual(self.ask()["status"], "insufficient_evidence")

    def test_duplicate_rejected(self):
        self.write([SYNTHETIC, SYNTHETIC])
        with self.assertRaisesRegex(ValueError, "duplicados"):
            read_corpus(self.path, {SYNTHETIC["documento"]})

    def test_invalid_pages(self):
        for value in (True, 0, -1, "2"):
            self.write([{**SYNTHETIC, "pagina_pdf": value}])
            with self.assertRaises(ValueError):
                read_corpus(self.path, {SYNTHETIC["documento"]})

    def test_missing_field(self):
        row = dict(SYNTHETIC)
        del row["version_fuente"]
        self.write([row])
        with self.assertRaises(ValueError):
            read_corpus(self.path, {SYNTHETIC["documento"]})

    def test_test_corpus_rejected_in_production(self):
        with self.assertRaisesRegex(ValueError, "fuera del corpus"):
            read_corpus(self.path)

    def test_hash_changes_when_corpus_changes(self):
        _, before = read_corpus(self.path, {SYNTHETIC["documento"]})
        self.write([{**SYNTHETIC, "version_fuente": "TEST-v2"}])
        _, after = read_corpus(self.path, {SYNTHETIC["documento"]})
        self.assertNotEqual(before, after)

    def test_remote_ollama_rejected(self):
        for url in ("https://example.com", "http://127.0.0.1.evil.com", "http://user@localhost"):
            with self.assertRaises(ValueError):
                OllamaClient(replace(self.config, ollama_url=url))

    def test_public_function(self):
        self.assertEqual(answer_question("")["status"], "error")


if __name__ == "__main__":
    unittest.main()
