"""Preparación con fixtures SINTÉTICOS temporales. Ninguna prueba crea índices Chroma."""
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from core.corpus import read_corpus
from scripts.audit_corpus import audit
from scripts.prepare_pilot import CONSTITUTION, PENAL, SELECTION, digest, prepare
from scripts.pilot_index import index, plan, remove


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mini-juztina-pilot-SYNTHETIC-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sources = self.root / "data/sources"
        self.sources.mkdir(parents=True)
        self.output = self.root / "data/processed/pilot_10_v1"
        self.rows = {}
        for document, filename in ((CONSTITUTION, "constitucion.jsonl"), (PENAL, "codigo_penal_articulos.jsonl")):
            rows = []
            for doc, number in SELECTION:
                if doc != document:
                    continue
                row = {"norma": "Código Penal del Perú" if doc == PENAL else doc,
                       "articulo": f"Artículo {number}" if doc == PENAL else number,
                       "texto": f"PRUEBA SINTÉTICA {filename} {number}: contenido sin valor jurídico.",
                       "fuente": "ENSAYO SINTÉTICO NO OFICIAL"}
                if doc == CONSTITUTION:
                    row["estado_extraccion"] = "borrador_ocr_requiere_revision"
                rows.append(row)
            self.rows[filename] = rows
        model = self.root / "models/multilingual-e5-small"
        model.mkdir(parents=True)
        (model / "synthetic-model-fixture.txt").write_bytes(b"TEST ONLY: no actual embedding model")

    def build(self):
        for filename, rows in self.rows.items():
            (self.sources / filename).write_bytes("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8"))
        audit(self.sources, self.root / "data/processed")
        return prepare(self.root)

    def test_ten_candidates_pass_contract_and_preserve_original(self):
        manifest = self.build()
        articles, _ = read_corpus(self.output / "articles_candidates.jsonl")
        self.assertEqual(len(articles), 10)
        self.assertEqual({(a.documento, a.articulo) for a in articles.values()}, set(SELECTION))
        self.assertEqual(manifest["sha256_candidatos"], digest(self.output / "articles_candidates.jsonl"))
        for entry in manifest["candidatos"]:
            row = articles[entry["id"]]
            original = self.rows[Path(entry["origen"]["archivo"]).name][entry["origen"]["linea"] - 1]
            self.assertEqual(row.texto, original["texto"])

    def test_all_incisos_and_whitespace_are_preserved(self):
        text = "  PRUEBA SINTÉTICA\n1. Primer inciso de ensayo.\n2. Segundo inciso de ensayo.  "
        self.rows["constitucion.jsonl"][1]["texto"] = text
        manifest = self.build()
        articles, _ = read_corpus(self.output / "articles_candidates.jsonl")
        entry = next(e for e in manifest["candidatos"] if e["documento"] == CONSTITUTION and e["articulo"] == "2")
        self.assertEqual(articles[entry["id"]].texto, text)
        self.assertEqual(entry["caracteres_texto"], len(text))

    def test_constitution_remains_in_review_and_no_official_claim(self):
        manifest = self.build()
        self.assertFalse(manifest["indexado"])
        self.assertFalse(manifest["cotejo_oficial_realizado"])
        for entry in manifest["candidatos"]:
            self.assertFalse(entry["juridicamente_verificado"])
            self.assertEqual(entry["estado_cotejo_oficial"], "pendiente")
            self.assertTrue(all(v is None for v in entry["evidencia_oficial"].values()))
            expected = "requiere_revision" if entry["documento"] == CONSTITUTION else "estructuralmente_apto"
            self.assertEqual(entry["estado_estructural_previo"], expected)

    def test_penal_in_review_is_not_silently_selected(self):
        self.rows["codigo_penal_articulos.jsonl"][0]["estado_extraccion"] = "requiere_revision"
        with self.assertRaisesRegex(ValueError, "no está entre"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_duplicate_candidate_is_rejected(self):
        duplicate = dict(self.rows["constitucion.jsonl"][0])
        duplicate["texto"] = "PRUEBA SINTÉTICA discordante."
        self.rows["constitucion.jsonl"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "ambiguo"):
            self.build()

    def test_protected_inputs_unchanged_and_no_chroma_created(self):
        self.build()
        protected = list(self.sources.glob("*.jsonl")) + list((self.root / "data/processed").glob("*.json*"))
        before = {p: p.read_bytes() for p in protected}
        result = plan(self.output, self.root)
        self.assertEqual(before, {p: p.read_bytes() for p in protected})
        self.assertFalse((self.root / "storage").exists())
        self.assertFalse((self.root / "data/processed/articles.jsonl").exists())
        self.assertFalse(result["operaciones_chroma_ejecutadas"])

    def test_no_overwriting_pilot(self):
        self.build()
        with self.assertRaises(FileExistsError):
            prepare(self.root)

    def test_original_tampering_prevents_plan(self):
        self.build()
        with (self.sources / "constitucion.jsonl").open("ab") as stream:
            stream.write(b"\n")
        with self.assertRaisesRegex(ValueError, "Original alterado"):
            plan(self.output, self.root)

    def test_candidate_tampering_prevents_plan(self):
        self.build()
        with (self.output / "articles_candidates.jsonl").open("ab") as stream:
            stream.write(b"\n")
        with self.assertRaisesRegex(ValueError, "Candidatos modificados"):
            plan(self.output, self.root)

    def test_forged_manifest_hash_does_not_allow_new_text(self):
        self.build()
        path = self.output / "articles_candidates.jsonl"
        rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]
        rows[0]["texto"] = "PRUEBA SINTÉTICA adulterada."
        path.write_bytes("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8"))
        manifest_path = self.output / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["sha256_candidatos"] = digest(path)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "no idéntico"):
            plan(self.output, self.root)

    def test_plan_has_separate_collection_and_storage(self):
        self.build()
        with patch("core.vector_store.VectorStore") as store:
            result = plan(self.output, self.root)
        store.assert_not_called()
        self.assertTrue(result["collection"].startswith("pilot_articles_"))
        self.assertEqual(Path(result["storage"]).parent, self.root / "storage/pilots")
        self.assertNotEqual(Path(result["storage"]), self.root / "storage/chroma")

    def test_mutations_require_execute(self):
        with self.assertRaisesRegex(ValueError, "execute"):
            index({}, execute=False)
        with self.assertRaisesRegex(ValueError, "execute"):
            remove(self.output, execute=False, root=self.root)

    def test_index_adapter_only_mocked_and_uses_isolated_config(self):
        self.build()
        result = plan(self.output, self.root)
        with patch("scripts.pilot_index.plan", return_value=result), \
             patch("core.embeddings.LocalEmbeddings") as embed, \
             patch("core.vector_store.VectorStore") as store:
            store.return_value.index.return_value = 12
            receipt = index(result, execute=True)
        config = store.call_args.args[0]
        self.assertEqual(config.storage, Path(result["storage"]))
        self.assertEqual(config.corpus, self.output / "articles_candidates.jsonl")
        self.assertEqual(store.return_value.name, result["collection"])
        self.assertEqual(receipt["chunks"], 12)
        self.assertTrue((self.output / "index_receipt.json").is_file())
        self.assertFalse(Path(result["storage"]).exists())  # Solo mocks, ningún índice.

    def test_changed_plan_blocks_write(self):
        self.build()
        result = plan(self.output, self.root)
        with patch("scripts.pilot_index.plan", return_value={**result, "collection": "changed"}), \
             patch("core.vector_store.VectorStore") as store:
            with self.assertRaisesRegex(ValueError, "plan cambió"):
                index(result, execute=True)
        store.assert_not_called()

    def test_rollback_rejects_production_path(self):
        self.build()
        receipt = plan(self.output, self.root)
        receipt["storage"] = str(self.root / "storage/chroma")
        (self.output / "index_receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "fuera del"):
            remove(self.output, execute=True, root=self.root)

    def test_rollback_is_scoped_and_only_mocked(self):
        self.build()
        receipt = plan(self.output, self.root)
        Path(receipt["storage"]).mkdir(parents=True)  # Directorio de ensayo vacío, sin Chroma.
        (self.output / "index_receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
        client = Mock()
        factory = Mock(return_value=client)
        with patch.dict("sys.modules", {"chromadb": SimpleNamespace(PersistentClient=factory),
                                        "chromadb.config": SimpleNamespace(Settings=Mock())}):
            result = remove(self.output, execute=True, root=self.root)
        client.delete_collection.assert_called_once_with(receipt["collection"])
        self.assertEqual(factory.call_args.kwargs["path"], receipt["storage"])
        self.assertTrue(result["archivos_corpus_conservados"])
        self.assertTrue((self.output / "articles_candidates.jsonl").is_file())


if __name__ == "__main__":
    unittest.main()
