"""Pruebas del adaptador. Las respuestas inyectadas son fixtures SINTÉTICOS, no legislación."""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from core.config import Config


class APITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.payload = {"message": "Consulta de prueba sintética", "conversation_id": "prueba-123"}

    def test_maps_verified_source_contract(self):
        fixture = {
            "answer": "Cita de PRUEBA SINTÉTICA NO OFICIAL.", "status": "answered",
            "sources": [{"documento": "PRUEBA SINTÉTICA NO OFICIAL", "articulo": "TEST-A",
                         "texto": "Texto de ensayo, sin valor jurídico.", "pagina_pdf": 7}],
        }
        with patch("core.rag_engine.answer_question", return_value=fixture) as rag:
            response = self.client.post("/api/chat", json=self.payload)
        self.assertEqual(response.status_code, 200)
        rag.assert_called_once_with(self.payload["message"])
        data = response.json()
        self.assertEqual(data["answer"], fixture["answer"])
        self.assertEqual(data["status"], fixture["status"])
        self.assertEqual(data["conversation_id"], self.payload["conversation_id"])
        self.assertEqual(data["sources"], [{"law": "PRUEBA SINTÉTICA NO OFICIAL", "article": "TEST-A",
                                            "excerpt": "Texto de ensayo, sin valor jurídico.", "page_pdf": 7}])
        self.assertNotIn("text", data["sources"][0])  # React ya consume excerpt.

    def test_nullable_pdf_page(self):
        fixture = {"answer": "PRUEBA", "status": "answered", "sources": [
            {"documento": "PRUEBA", "articulo": "TEST", "texto": "Texto de prueba", "pagina_pdf": None}]}
        with patch("core.rag_engine.answer_question", return_value=fixture):
            response = self.client.post("/api/chat", json=self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["sources"][0]["page_pdf"])

    def test_preserves_every_rag_status_and_answer(self):
        for status in ("answered", "out_of_scope", "insufficient_evidence", "error"):
            with self.subTest(status=status):
                fixture = {"answer": f"Mensaje de ensayo: {status}", "status": status, "sources": []}
                with patch("core.rag_engine.answer_question", return_value=fixture):
                    response = self.client.post("/api/chat", json=self.payload)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {**fixture, "conversation_id": "prueba-123"})

    def test_rejects_invalid_message_without_calling_rag(self):
        for message in ("", " \n\t", 42, False, None, [], {}, "a" * 2001):
            with self.subTest(message_type=type(message).__name__):
                with patch("core.rag_engine.answer_question") as rag:
                    response = self.client.post("/api/chat", json={**self.payload, "message": message})
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["status"], "error")
                rag.assert_not_called()

    def test_rejects_missing_fields_and_nonstring_conversation_id(self):
        for payload in ({}, {"message": "Hola"}, {"conversation_id": "1"},
                        {**self.payload, "conversation_id": 123}, {**self.payload, "conversation_id": None}):
            with self.subTest(payload=payload):
                with patch("core.rag_engine.answer_question") as rag:
                    response = self.client.post("/api/chat", json=payload)
                self.assertEqual(response.status_code, 422)
                rag.assert_not_called()

    def test_rejects_malformed_json(self):
        with patch("core.rag_engine.answer_question") as rag:
            response = self.client.post("/api/chat", content='{broken', headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("broken", response.text)
        rag.assert_not_called()

    def test_passes_original_message_without_rewriting(self):
        message = "  Pregunta sintética con tildes: ¿sí?  "
        with patch("core.rag_engine.answer_question", return_value={"answer": "PRUEBA", "status": "insufficient_evidence", "sources": []}) as rag:
            response = self.client.post("/api/chat", json={**self.payload, "message": message})
        self.assertEqual(response.status_code, 200)
        rag.assert_called_once_with(message)

    def test_no_conversation_memory(self):
        fixture = {"answer": "PRUEBA", "status": "insufficient_evidence", "sources": []}
        with patch("core.rag_engine.answer_question", return_value=fixture) as rag:
            self.client.post("/api/chat", json=self.payload)
            second = self.client.post("/api/chat", json={**self.payload, "message": "Segunda pregunta"})
        self.assertEqual(rag.call_count, 2)
        self.assertEqual(rag.call_args.args, ("Segunda pregunta",))
        self.assertEqual(second.json()["conversation_id"], "prueba-123")

    def test_unexpected_exception_is_not_exposed(self):
        with patch("core.rag_engine.answer_question", side_effect=RuntimeError("SECRET-INTERNAL-PATH")):
            with self.assertLogs("api.main", level="ERROR"):
                response = self.client.post("/api/chat", json=self.payload)
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("SECRET-INTERNAL-PATH", response.text)
        self.assertEqual(response.json()["status"], "error")
        self.assertEqual(response.json()["sources"], [])
        self.assertEqual(response.json()["conversation_id"], "prueba-123")

    def test_invalid_rag_contract_does_not_invent_answer(self):
        for fixture in ({}, {"answer": "PRUEBA", "status": "unknown", "sources": []},
                        {"answer": "PRUEBA", "status": "answered", "sources": [{}]}):
            with patch("core.rag_engine.answer_question", return_value=fixture):
                with self.assertLogs("api.main", level="ERROR"):
                    response = self.client.post("/api/chat", json=self.payload)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json()["status"], "error")
            self.assertEqual(response.json()["sources"], [])

    def test_cors_allowed_preflight(self):
        for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
            response = self.client.options("/api/chat", headers={
                "Origin": origin, "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["access-control-allow-origin"], origin)
            self.assertEqual(response.headers["access-control-allow-methods"], "POST")

    def test_cors_disallowed_origins(self):
        for origin in ("https://example.com", "http://localhost:5174", "http://localhost:5173.evil.com", "null"):
            response = self.client.options("/api/chat", headers={
                "Origin": origin, "Access-Control-Request-Method": "POST"})
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("access-control-allow-origin", response.headers)

    def test_cors_header_on_actual_response(self):
        with patch("core.rag_engine.answer_question", return_value={"answer": "PRUEBA", "sources": [], "status": "insufficient_evidence"}):
            response = self.client.post("/api/chat", json=self.payload, headers={"Origin": "http://localhost:5173"})
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5173")

    def test_get_is_not_chat(self):
        self.assertEqual(self.client.get("/api/chat").status_code, 405)

    @unittest.skipIf(Config().corpus.is_file(), "El caso sin corpus solo corresponde cuando el archivo está ausente")
    def test_real_rag_without_corpus_no_mock(self):
        response = self.client.post("/api/chat", json={**self.payload, "message": "¿Qué dispone el artículo 2 de la Constitución?"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "insufficient_evidence")
        self.assertEqual(response.json()["answer"], "No hay corpus local disponible.")
        self.assertEqual(response.json()["sources"], [])


if __name__ == "__main__":
    unittest.main()
