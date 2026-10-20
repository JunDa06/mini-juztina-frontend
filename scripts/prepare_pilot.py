"""Extrae candidatos auditados, sin corregirlos ni indexarlos."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from core.corpus import read_corpus

ROOT = Path(__file__).resolve().parents[1]
CONSTITUTION = "Constitución Política del Perú"
PENAL = "Código Penal peruano"
SELECTION = [(CONSTITUTION, n) for n in ("1", "2", "3", "7", "7-A")] + [
    (PENAL, n) for n in ("16", "25", "111", "124", "288")]
REASONS = {
    (CONSTITUTION, "1"): "Selección expresa del usuario: candidato constitucional a cotejo.",
    (CONSTITUTION, "2"): "Selección expresa del usuario: conservar íntegra la cadena y sus incisos extraídos.",
    (CONSTITUTION, "3"): "Selección expresa del usuario: candidato constitucional a cotejo.",
    (CONSTITUTION, "7"): "Selección expresa del usuario: candidato constitucional a cotejo.",
    (CONSTITUTION, "7-A"): "Selección expresa del usuario: candidato constitucional a cotejo.",
    (PENAL, "16"): "El texto local menciona expresamente tentativa y comienzo de ejecución.",
    (PENAL, "25"): "El texto local menciona auxilio y asistencia dolosa.",
    (PENAL, "111"): "El texto local describe causar la muerte por culpa; verificar integridad de párrafos.",
    (PENAL, "124"): "El texto local describe daño corporal o a la salud por culpa.",
    (PENAL, "288"): "El texto local contiene las expresiones a sabiendas y por culpa.",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def prepare(root=ROOT, output=None):
    root = Path(root).resolve()
    output = Path(output) if output else root / "data/processed/pilot_10_v1"
    if output.exists():
        raise FileExistsError("El piloto ya existe: no se sobrescribe. Use otro directorio para una nueva versión.")
    processed = root / "data/processed"
    trace_path = processed / "audit_records.jsonl"
    accepted_path = processed / "articles_structurally_accepted.jsonl"
    report_path = processed / "audit_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for item in report["archivos_originales"]:
        if Path(item["archivo"]).name != item["archivo"]:
            raise ValueError("Nombre de archivo original inválido")
        if digest(root / "data/sources" / item["archivo"]) != item["sha256"]:
            raise ValueError("Original modificado desde la auditoría")
    for path in (trace_path, accepted_path):
        expected = next(item["sha256"] for item in report["salidas_jsonl"] if item["archivo"] == path.name)
        if digest(path) != expected:
            raise ValueError("Derivado modificado desde la auditoría")
    traces = jsonl(trace_path)
    accepted = {row["id"]: row for row in jsonl(accepted_path)}
    chosen, entries = [], []
    for document, number in SELECTION:
        found = [r for r in traces if r.get("normalizado_candidato") and
                 (r["normalizado_candidato"]["documento"], r["normalizado_candidato"]["articulo"]) == (document, number)]
        if len(found) != 1:
            raise ValueError(f"Candidato ausente o ambiguo: {document} {number}")
        trace = found[0]
        row = trace["normalizado_candidato"]
        if document == PENAL and (trace["clasificacion"] != "estructuralmente_apto" or accepted.get(row["id"]) != row):
            raise ValueError(f"El candidato penal {number} no está entre los estructuralmente aptos")
        source_name = trace["archivo_original"]
        raw = json.loads((root / "data/sources" / source_name).read_text(encoding="utf-8-sig").splitlines()[trace["linea_original"] - 1])
        if row["texto"] != raw["texto"] or row["texto"] != trace["original"]["texto"]:
            raise ValueError("El texto no coincide literalmente con el original")
        chosen.append(row)
        notes = ["Integridad, incisos, vigencia y localización PDF pendientes de cotejo oficial."]
        if document == CONSTITUTION:
            notes.append("Incluido como candidato a cotejo pese a su estado previo requiere_revision; no se reclasifica como apto.")
        if number == "2" and document == CONSTITUTION:
            notes.append("Se conserva todo el texto, incluidas numeración OCR irregular, notas y cabeceras; no se reconstruyen incisos ausentes.")
        if document == PENAL and "”" in row["texto"]:
            notes.append("Comilla editorial de cierre presente en la extracción: conservar y cotejar alcance del fragmento.")
        if document == PENAL and number == "111":
            notes.append("El registro local es breve: no asumir que contiene todos los párrafos o supuestos del artículo.")
        entries.append({
            "id": row["id"], "documento": document, "articulo": number,
            "motivo_seleccion": REASONS[document, number],
            "origen": {"archivo": f"data/sources/{source_name}", "linea": trace["linea_original"],
                       "sha256_archivo": trace["sha256_archivo"], "id_auditoria": trace["id_auditoria"],
                       "archivo_auditoria": "data/processed/audit_records.jsonl",
                       "fuente_declarada": trace["original"].get("fuente"),
                       "documento_fuente_declarado": trace["original"].get("documento_fuente"),
                       "edicion_declarada": trace["original"].get("edicion"),
                       "pagina_pdf_aproximada_original": trace["original"].get("pagina_pdf_aproximada")},
            "sha256_texto": hashlib.sha256(row["texto"].encode("utf-8")).hexdigest(),
            "caracteres_texto": len(row["texto"]), "estado_estructural_previo": trace["clasificacion"],
            "estado_cotejo_oficial": "pendiente", "juridicamente_verificado": False,
            "incidencias_auditoria": trace["hallazgos"], "observaciones_piloto": notes,
            "evidencia_oficial": {"url_documento": None, "sha256_pdf": None, "pagina_pdf": None,
                                  "fecha_edicion": None, "fecha_cotejo": None, "revisor": None,
                                  "integridad_inciso_por_inciso": None, "vigencia_a_fecha": None},
        })
    counts = Counter(row["documento"] for row in chosen)
    if counts != {CONSTITUTION: 5, PENAL: 5}:
        raise ValueError("El piloto debe contener cinco candidatos por documento")
    # Validación del contrato en un temporal: no se publica articles.jsonl.
    import tempfile
    content = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in chosen)
    with tempfile.TemporaryDirectory(prefix="mini-juztina-pilot-contract-") as temp:
        path = Path(temp) / "candidates.jsonl"
        path.write_bytes(content.encode("utf-8"))
        loaded, _ = read_corpus(path)
        if len(loaded) != 10:
            raise ValueError("Contrato piloto inválido")
    manifest = {
        "formato": "mini-juztina-pilot-v1", "estado": "provisional_pendiente_cotejo_y_autorizacion",
        "registros": 10, "indexado": False, "cotejo_oficial_realizado": False,
        "archivo_candidatos": "articles_candidates.jsonl",
        "sha256_candidatos": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "sha256_auditoria": digest(trace_path), "sha256_informe_auditoria": digest(report_path),
        "sha256_aptos": digest(accepted_path),
        "candidatos": entries,
        "preferencias_no_cubiertas": [
            {"documento": PENAL, "articulos": ["II", "11", "12"],
             "motivo": "Preferentes para legalidad/dolo/culpa, pero en revisión por títulos posiblemente arrastrados; se excluyen para mantener cinco penales estructuralmente aptos."}],
        "advertencia": "Copias literales provisionales. Estructura aceptable no certifica integridad, OCR, edición o vigencia. No usar como corpus jurídico validado.",
    }
    output.mkdir(parents=True)
    (output / "articles_candidates.jsonl").write_bytes(content.encode("utf-8"))
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = prepare(output=args.output)
    print(json.dumps({"registros": result["registros"], "sha256_candidatos": result["sha256_candidatos"],
                      "candidatos": [[e["documento"], e["articulo"]] for e in result["candidatos"]]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
