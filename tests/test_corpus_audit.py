"""Fixtures exclusivamente SINTÉTICOS en temporales; no representan legislación real."""
import json
from pathlib import Path
import tempfile
import unittest

from core.corpus import read_corpus
from scripts.audit_corpus import audit, inspect_sources, sha256


def synthetic(document, article="1", **overrides):
    return {"norma": document, "articulo": article,
            "texto": "PRUEBA SINTÉTICA: este texto de ensayo carece de valor jurídico.",
            "fuente": "PRUEBA NO OFICIAL", **overrides}


class CorpusAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mini-juztina-audit-TEST-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sources = self.root / "sources"
        self.sources.mkdir()
        self.output = self.root / "processed"
        self.const = [synthetic("Constitución Política del Perú")]
        self.penal = [synthetic("Código Penal del Perú", "Artículo 1",
                                texto="PRUEBA SINTÉTICA: otro enunciado sin valor jurídico.")]

    def write_sources(self):
        for name, rows in (("constitucion.jsonl", self.const), ("codigo_penal_articulos.jsonl", self.penal)):
            (self.sources / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")

    def run_audit(self):
        self.write_sources()
        return audit(self.sources, self.output)

    def traces(self):
        return [json.loads(line) for line in (self.output / "audit_records.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_valid_schema_and_document_alias(self):
        report = self.run_audit()
        self.assertEqual(report["estructuralmente_aptos"], 2)
        rows, _ = read_corpus(self.output / "articles_structurally_accepted.jsonl")
        self.assertEqual(len(rows), 2)
        self.assertEqual({a.documento for a in rows.values()}, {"Constitución Política del Perú", "Código Penal peruano"})
        self.assertEqual({a.articulo for a in rows.values()}, {"1"})
        self.assertFalse((self.output / "articles.jsonl").exists())

    def test_literal_text_preserves_accents_spaces_and_newlines(self):
        text = '  PRUEBA SINTÉTICA\n\tcon «tildes», guion- y  espacios dobles.  '
        self.const[0]["texto"] = text
        self.run_audit()
        trace = self.traces()[0]
        self.assertEqual(trace["normalizado_candidato"]["texto"], text)
        self.assertEqual(trace["sha256_texto"], sha256(text.encode("utf-8")))

    def test_source_files_unchanged(self):
        self.write_sources()
        before = {p.name: p.read_bytes() for p in self.sources.iterdir()}
        audit(self.sources, self.output)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.sources.iterdir()})

    def test_empty_and_wrong_type_text_are_quarantined(self):
        for text in ("", " \t", None, 42):
            with self.subTest(text=text):
                self.const[0]["texto"] = text
                self.write_sources()
                records, *_ = inspect_sources(self.sources)
                self.assertEqual(records[0]["clasificacion"], "requiere_revision")

    def test_all_reference_duplicates_are_quarantined(self):
        self.const.append({**self.const[0], "texto": "Otro texto SINTÉTICO de prueba."})
        report = self.run_audit()
        self.assertEqual(report["registros_por_hallazgo"]["referencia_duplicada"], 2)
        self.assertTrue(all(r["clasificacion"] == "requiere_revision" for r in self.traces()[:2]))
        self.assertEqual(len({r["id_auditoria"] for r in self.traces()}), 3)

    def test_identical_text_different_articles_quarantines_both(self):
        self.penal.append({**self.penal[0], "articulo": "Artículo 2"})
        report = self.run_audit()
        self.assertEqual(report["registros_por_hallazgo"]["texto_identico_no_vacio"], 2)
        self.assertEqual(report["estructuralmente_aptos"], 1)

    def test_approximate_page_does_not_become_exact(self):
        self.const[0]["pagina_pdf_aproximada"] = 23
        self.run_audit()
        trace = self.traces()[0]
        self.assertIsNone(trace["normalizado_candidato"]["pagina_pdf"])
        self.assertEqual(trace["original"]["pagina_pdf_aproximada"], 23)

    def test_exact_page_preserved_and_invalid_boolean_rejected(self):
        self.const[0]["pagina_pdf"] = 7
        self.penal[0]["pagina_pdf"] = True
        report = self.run_audit()
        self.assertEqual(self.traces()[0]["normalizado_candidato"]["pagina_pdf"], 7)
        self.assertEqual(report["registros_por_hallazgo"]["pagina_exacta_invalida"], 1)

    def test_draft_marker_and_source_observation_require_review(self):
        self.const[0].update(estado_extraccion="borrador_ocr_requiere_revision",
                             observacion_extraccion="PRUEBA: etiqueta modificada por continuidad, sin cotejo.")
        report = self.run_audit()
        self.assertEqual(report["requieren_revision"], 1)
        self.assertEqual(report["registros_por_hallazgo"]["observacion_del_extractor"], 1)

    def test_ocr_character_signal_not_corrected(self):
        self.const[0]["texto"] = "PRUEBA SINTÉTICA con car\ufffdcter ilegible."
        report = self.run_audit()
        self.assertEqual(report["registros_por_hallazgo"]["codificacion_sospechosa"], 1)
        self.assertEqual(self.traces()[0]["normalizado_candidato"]["texto"], self.const[0]["texto"])

    def test_embedded_article_heading_flagged_but_ordinary_reference_not(self):
        self.const[0]["texto"] = "Artículo 1. PRUEBA SINTÉTICA. Artículo 2. Otro ensayo."
        self.penal[0]["texto"] = "PRUEBA SINTÉTICA que remite al artículo 36 para este ensayo."
        report = self.run_audit()
        self.assertEqual(report["registros_por_hallazgo"]["posible_mezcla_articulos_o_versiones"], 1)
        self.assertEqual(self.traces()[1]["clasificacion"], "estructuralmente_apto")

    def test_header_and_metadata_mismatch(self):
        self.const[0]["texto"] = "Artículo 2. PRUEBA SINTÉTICA de etiqueta discordante."
        report = self.run_audit()
        self.assertEqual(report["registros_por_hallazgo"]["etiqueta_y_cabecera_discrepan"], 1)
        self.assertEqual(self.traces()[0]["normalizado_candidato"]["articulo"], "1")

    def test_numeric_suffix_not_guessed_to_be_a_letter(self):
        self.const[0]["articulo"] = "102-8"
        report = self.run_audit()
        self.assertEqual(report["registros_por_hallazgo"]["etiqueta_articulo_invalida"], 1)
        self.assertEqual(self.traces()[0]["normalizado_candidato"]["articulo"], "102-8")

    def test_roman_and_numeric_labels_remain_distinct(self):
        self.penal.append({**self.penal[0], "articulo": "Artículo I", "texto": "Ensayo SINTÉTICO para una etiqueta romana."})
        self.run_audit()
        rows, _ = read_corpus(self.output / "articles_structurally_accepted.jsonl")
        self.assertEqual({a.articulo for a in rows.values()}, {"1", "I"})

    def test_trailing_heading_with_open_quote_requires_review(self):
        self.const[0]["texto"] = 'PRUEBA SINTÉTICA de oración. “Encabezado de otro ensayo'
        report = self.run_audit()
        self.assertEqual(report["registros_por_hallazgo"]["posible_titulo_arrastrado"], 1)

    def test_section_and_editorial_note_detected(self):
        self.const[0]["texto"] = "PRUEBA SINTÉTICA. SECCIÓN II ENSAYO"
        self.penal[0]["texto"] = "(*) Artículo eliminado en esta PRUEBA SINTÉTICA."
        report = self.run_audit()
        self.assertEqual(report["registros_por_hallazgo"]["encabezado_jerarquico_en_texto"], 1)
        self.assertEqual(report["registros_por_hallazgo"]["nota_editorial_o_sin_contenido"], 1)

    def test_orphan_final_numeral_is_not_completed(self):
        text = "PRUEBA SINTÉTICA de enumeración. 1. Ensayo primero. “2.”"
        self.const[0]["texto"] = text
        report = self.run_audit()
        self.assertEqual(report["registros_por_hallazgo"]["numeral_final_sin_contenido"], 1)
        self.assertEqual(self.traces()[0]["normalizado_candidato"]["texto"], text)

    def test_nominal_heading_can_end_with_period(self):
        self.const[0]["texto"] = "PRUEBA SINTÉTICA de oración. Descripción del ensayo siguiente.”"
        report = self.run_audit()
        self.assertEqual(report["registros_por_hallazgo"]["posible_titulo_nominal_con_punto"], 1)

    def test_null_hierarchy_and_unmapped_metadata_preserved(self):
        self.const[0].update(titulo=None, capitulo=None)
        self.penal[0].update(parte="PRUEBA: Libro", seccion="PRUEBA: Sección")
        self.run_audit()
        for row in self.traces():
            self.assertEqual(row["normalizado_candidato"]["titulo"], "")
            self.assertEqual(row["normalizado_candidato"]["capitulo"], "")
        self.assertEqual(self.traces()[1]["original"]["seccion"], "PRUEBA: Sección")

    def test_json_invalid_and_duplicate_keys_preserve_raw_bytes(self):
        self.write_sources()
        path = self.sources / "constitucion.jsonl"
        for raw in (b'{invalid}\n', b'{"articulo":"1","articulo":"2"}\n', b'\xff\n'):
            path.write_bytes(raw)
            rows, *_ = inspect_sources(self.sources)
            self.assertEqual(rows[0]["clasificacion"], "requiere_revision")
            self.assertEqual(bytes.fromhex(rows[0]["linea_original_hex"]), raw.rstrip(b'\n'))

    def test_unknown_document_and_nonobject_are_not_accepted(self):
        self.const[0]["norma"] = "PRUEBA: documento no admitido"
        self.penal = [42]
        report = self.run_audit()
        self.assertEqual(report["estructuralmente_aptos"], 0)
        self.assertEqual(report["requieren_revision"], 2)

    def test_numbering_anomaly_is_not_repaired_and_gaps_not_filled(self):
        self.const = [synthetic("Constitución Política del Perú", str(n), texto=f"PRUEBA SINTÉTICA número {n}.") for n in (1, 20, 3)]
        report = self.run_audit()
        self.assertEqual(report["registros_por_hallazgo"]["salto_numeracion_local"], 1)
        self.assertEqual(self.traces()[1]["normalizado_candidato"]["articulo"], "20")
        self.assertEqual(report["cobertura_observada"][0]["etiquetas_numericas_no_observadas_entre_1_y_ultima"], [2])

    def test_ids_are_deterministic_and_traceable(self):
        self.write_sources()
        before, *_ = inspect_sources(self.sources)
        after, *_ = inspect_sources(self.sources)
        self.assertEqual(before, after)
        self.assertIn(before[0]["sha256_archivo"], before[0]["id_auditoria"])
        self.assertEqual(before[0]["linea_original"], 1)

    def test_reports_do_not_claim_legal_validation_or_indexing(self):
        report = self.run_audit()
        self.assertFalse(report["cotejo_oficial_realizado"])
        self.assertFalse(report["vigencia_juridica_verificada"])
        self.assertFalse(report["indexacion_chroma_realizada"])
        version = json.loads(self.traces()[0]["normalizado_candidato"]["version_fuente"])
        self.assertFalse(version["cotejo_oficial"])
        self.assertEqual(version["fuente_declarada"], "PRUEBA NO OFICIAL")

    def test_refuses_overwriting_outputs_or_writing_into_sources(self):
        self.run_audit()
        with self.assertRaises(FileExistsError):
            audit(self.sources, self.output)
        with self.assertRaises(ValueError):
            audit(self.sources, self.sources)


if __name__ == "__main__":
    unittest.main()
