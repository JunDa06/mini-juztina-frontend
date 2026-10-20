"""Auditoría estructural reproducible. No corrige texto jurídico ni utiliza Chroma.

Los hallazgos de OCR/mezcla son heurísticos: exigen cotejo humano, no prueban errores.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import tempfile

from core.corpus import read_corpus

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    "constitucion.jsonl": ("Constitución Política del Perú", "constitucion"),
    "codigo_penal_articulos.jsonl": ("Código Penal peruano", "codigo-penal"),
}
DOCUMENT_ALIASES = {
    "Constitución Política del Perú": "Constitución Política del Perú",
    "Código Penal del Perú": "Código Penal peruano",
    "Código Penal peruano": "Código Penal peruano",
}
OUTPUTS = ("articles_structurally_accepted.jsonl", "review_required.jsonl",
           "audit_records.jsonl", "audit_report.json", "AUDIT_REPORT.md")
LABEL = re.compile(r"(?:[1-9]\d*(?:-[A-Z])?|[IVXLCDM]+)\Z")
HEADER = re.compile(r"\bArt[íi]culo\s+(\d+(?:-[A-Za-z0-9]+)?|[IVXLCDM]+)\s*[.,:º°—-]")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def label(value):
    if not isinstance(value, str):
        return None
    # Solo cambia la etiqueta de metadatos, nunca el texto normativo.
    return re.sub(r"^art[ií]culo\s+", "", value.strip(), flags=re.I).upper()


def issue(record, code, detail, evidence=None, severity="review"):
    finding = {"codigo": code, "severidad": severity, "detalle": detail}
    if evidence is not None:
        finding["evidencia"] = evidence
    record["hallazgos"].append(finding)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Clave JSON duplicada: {key}")
        result[key] = value
    return result


def inspect_row(record, expected_document):
    row = record["original"]
    if not isinstance(row, dict):
        issue(record, "registro_no_objeto", "El registro JSON no es un objeto.")
        return
    document = DOCUMENT_ALIASES.get(row.get("norma")) if isinstance(row.get("norma"), str) else None
    if document != expected_document:
        issue(record, "norma_incompatible", "Norma no reconocida o incompatible con el archivo.", row.get("norma"))
    article = label(row.get("articulo"))
    if not article or not LABEL.fullmatch(article):
        issue(record, "etiqueta_articulo_invalida", "Etiqueta ambigua: no se infiere ni corrige su numeración.", row.get("articulo"))
    text = row.get("texto")
    if not isinstance(text, str):
        issue(record, "texto_no_cadena", "texto debe ser cadena; no se convierte automáticamente.")
    elif not text.strip():
        issue(record, "texto_vacio", "Texto vacío: no se deduce si corresponde a derogación u omisión.")
    else:
        record["sha256_texto"] = sha256(text.encode("utf-8"))
        if "\ufffd" in text or re.search(r"Ã[\u0080-\u00bf]|Â[\u0080-\u00bf]|â€", text):
            issue(record, "codificacion_sospechosa", "Posible pérdida de caracteres o mojibake.")
        if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text):
            issue(record, "caracteres_control", "Caracteres de control distintos de espacios/saltos habituales.")
        if re.search(r"\bCONSTITUCI[ÓO]N\s+[^|]{0,60}\|", text):
            issue(record, "cabecera_pagina_en_texto", "Posible encabezado/paginación incrustado. Se conserva literalmente.")
        if re.search(r"[A-ZÁÉÍÓÚÑ]{18,}|[a-záéíóúñ]0[a-záéíóúñ]", text):
            issue(record, "ocr_sospechoso", "Palabra con cero interno o mayúsculas largas concatenadas; señal heurística.")
        if re.search(r"(?i)\bimprenta del congreso\b", text):
            issue(record, "colofon_en_texto", "Posible colofón editorial incrustado.")
        headers = list(HEADER.finditer(text))
        first = HEADER.match(text.lstrip())
        if first and label(first.group(1)) != article:
            issue(record, "etiqueta_y_cabecera_discrepan", "Etiqueta original y encabezado del texto no coinciden.", first.group(0))
        # Referencias 'el artículo 36' no se tratan como nuevos artículos.
        embedded = [h for h in headers if h.start() > 0 and
                    (h.group(1).upper() == article or
                     re.search(r"[.!?”“]\s*$", text[:h.start()]))]
        if embedded:
            issue(record, "posible_mezcla_articulos_o_versiones",
                  "Encabezado repetido o de otro artículo en límite de oración. No se divide automáticamente.",
                  [h.group(0) for h in embedded])
        if re.search(r"\b(?:CAP[ÍI]TULO|T[ÍI]TULO|LIBRO|SECCI[ÓO]N)\s+(?:[IVXLCDM]+|\d+)\b", text):
            issue(record, "encabezado_jerarquico_en_texto", "Posible mezcla con títulos/capítulos editoriales; también puede ser una cita legítima.")
        # No se elimina el sufijo: puede ser título del artículo siguiente o texto legítimo.
        tail = re.search(r"[.!?][”\"]?\s+[“\"]?([A-ZÁÉÍÓÚÑ][^.!?]{3,180})$", text)
        if tail and len(tail.group(1).split()) <= 24:
            issue(record, "posible_titulo_arrastrado", "Frase final sin cierre tras una oración; posible título del artículo siguiente.", tail.group(1))
        nominal_tail = re.search(r"[.!?][”\"]?\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]*(?:ción|sión) (?:de|del|a|para|por) [^.!?]{3,180})\.[”\"]?\s*$", text)
        if nominal_tail:
            issue(record, "posible_titulo_nominal_con_punto", "Frase nominal final tras una oración, incluso con punto; posible encabezado arrastrado, sin corregir.", nominal_tail.group(1))
        orphan = re.search(r"(?:^|[.!?]\s+)[“\"]?\d{1,3}[.)][”\"]?\s*$", text)
        if orphan:
            issue(record, "numeral_final_sin_contenido", "Enumeración termina en un numeral aislado: posible corte de extracción. No se completa.", orphan.group(0))
        if re.search(r"(?i)\b(?:artículo sin contenido|texto anterior|fe de erratas|artículo derogado|artículo eliminado)\b", text):
            issue(record, "nota_editorial_o_sin_contenido", "El texto contiene una nota editorial o de ausencia de contenido; no prueba vigencia.")
    if row.get("tipo_registro", "articulo") != "articulo":
        issue(record, "tipo_registro_incompatible", "No se identifica como registro de artículo.")
    state = row.get("estado_extraccion")
    if state and re.search(r"(?i)borrador|ocr|revisi[oó]n|revision|pendiente", str(state)):
        issue(record, "origen_marcado_para_revision", "El propio archivo declara extracción pendiente de revisión.", state)
    if row.get("observacion_extraccion"):
        issue(record, "observacion_del_extractor", "La observación original debe cotejarse, sin adoptar su corrección como validada.", row["observacion_extraccion"])
    for key in ("titulo", "capitulo"):
        if row.get(key) is not None and not isinstance(row[key], str):
            issue(record, "jerarquia_tipo_incompatible", f"{key} no es cadena ni null; no se fuerza su conversión.")
    for key in ("titulo_numero", "capitulo_numero"):
        value = row.get(key)
        if value is not None and (not isinstance(value, str) or not re.fullmatch(r"[IVXLCDM]+(?:-[A-Z])?|\d+", value)):
            issue(record, "numeracion_jerarquica_sospechosa", f"{key}: etiqueta no reconocida, sin corregir.", value)
    for key in ("titulo", "capitulo"):
        if isinstance(row.get(key), str) and "?" in row[key]:
            issue(record, "jerarquia_con_interrogacion", f"{key} contiene interrogación; posible duda del extractor.", row[key])
    if not isinstance(row.get("fuente"), str) or not row["fuente"].strip():
        issue(record, "fuente_no_declarada", "No hay fuente declarada utilizable como procedencia.")
    page = row.get("pagina_pdf")
    if page is not None and (type(page) is not int or page < 1):
        issue(record, "pagina_exacta_invalida", "pagina_pdf no es entero positivo ni null.")
        page = None
    if row.get("pagina_pdf_aproximada") is not None:
        issue(record, "pagina_solo_aproximada", "Página aproximada conservada solo en trazabilidad; no se convierte en página exacta.",
              row["pagina_pdf_aproximada"], severity="info")
    if page is None:
        issue(record, "sin_pagina_pdf_exacta", "Se utiliza pagina_pdf=null, sin inventar localizador.", severity="info")
    if not row.get("titulo") or not row.get("capitulo"):
        issue(record, "jerarquia_parcial", "Jerarquía ausente/null se convierte en cadena vacía. parte/seccion se conservan en el original, sin equipararlos a capítulos.", severity="info")
    if document and article and isinstance(text, str):
        version = {"archivo": record["archivo_original"], "sha256": record["sha256_archivo"],
                   "fuente_declarada": row.get("fuente"), "edicion_declarada": row.get("edicion"),
                   "documento_fuente_declarado": row.get("documento_fuente"), "cotejo_oficial": False}
        record["normalizado_candidato"] = {
            "id": record["id_auditoria"], "documento": document,
            "titulo": row.get("titulo") if isinstance(row.get("titulo"), str) else "",
            "capitulo": row.get("capitulo") if isinstance(row.get("capitulo"), str) else "",
            "articulo": article, "texto": text, "pagina_pdf": page,
            "version_fuente": json_text(version),
        }


def inspect_sources(source_dir):
    records, files = [], []
    for filename, (expected, slug) in INPUTS.items():
        path = source_dir / filename
        raw = path.read_bytes()
        digest = sha256(raw)
        nonblank, blank = 0, []
        for number, line in enumerate(raw.splitlines(), 1):
            if not line.strip():
                blank.append(number)
                continue
            nonblank += 1
            record = {"id_auditoria": f"{slug}:{digest}:{number}", "archivo_original": filename,
                      "linea_original": number, "sha256_archivo": digest,
                      "sha256_linea_original": sha256(line), "original": None,
                      "normalizado_candidato": None, "hallazgos": []}
            try:
                row_text = line.decode("utf-8-sig" if number == 1 else "utf-8")
                record["original"] = json.loads(row_text, object_pairs_hook=unique_object)
            except (UnicodeDecodeError, ValueError) as exc:
                record["linea_original_hex"] = line.hex()
                issue(record, "json_o_utf8_invalido", "No se reconstruye automáticamente un registro inválido.", str(exc))
            else:
                inspect_row(record, expected)
            records.append(record)
        files.append({"archivo": filename, "sha256": digest, "bytes": len(raw),
                      "registros": nonblank, "lineas_vacias": blank})
    references, texts = defaultdict(list), defaultdict(list)
    for record in records:
        candidate = record["normalizado_candidato"]
        if candidate:
            references[candidate["documento"], candidate["articulo"]].append(record)
            if candidate["texto"].strip():
                texts[candidate["texto"]].append(record)
    duplicate_groups = []
    for groups, code in ((references, "referencia_duplicada"), (texts, "texto_identico_no_vacio")):
        for group in groups.values():
            if len(group) < 2:
                continue
            locations = [{"archivo": r["archivo_original"], "linea": r["linea_original"],
                          "articulo": r["normalizado_candidato"]["articulo"]} for r in group]
            duplicate_groups.append({"codigo": code, "registros": locations})
            for record in group:
                issue(record, code, "Se retienen todos los registros implicados para cotejo; no se elige uno ni se deduplican textos jurídicos por suposición.", locations)
    coverage = []
    for file in files:
        subset = [r for r in records if r["archivo_original"] == file["archivo"] and r["normalizado_candidato"]]
        numeric = [(r, int(r["normalizado_candidato"]["articulo"])) for r in subset
                   if r["normalizado_candidato"]["articulo"].isdigit()]
        for (previous, a), (current, b), (following, c) in zip(numeric, numeric[1:], numeric[2:]):
            if c == a + 2 and b != a + 1:
                issue(current, "salto_numeracion_local", "Etiqueta intermedia incompatible con la continuidad de sus vecinas. No se propone una corrección jurídica.", [a, b, c])
        # Hasta la última etiqueta numérica LEÍDA, no un número legal esperado.
        end = numeric[-1][1] if numeric else 0
        seen = {n for _, n in numeric}
        coverage.append({"archivo": file["archivo"], "ultima_etiqueta_numerica_leida": end,
                         "etiquetas_numericas_no_observadas_entre_1_y_ultima": [n for n in range(1, end + 1) if n not in seen],
                         "advertencia": "Huecos observados, no prueba de artículos vigentes faltantes ni catálogo legal completo; no se rellenan."})
    for record in records:
        record["clasificacion"] = "requiere_revision" if any(i["severidad"] == "review" for i in record["hallazgos"]) else "estructuralmente_apto"
    return records, files, duplicate_groups, coverage


def validate_accepted(accepted):
    if not accepted:
        return 0
    with tempfile.TemporaryDirectory(prefix="mini-juztina-contract-audit-") as folder:
        path = Path(folder) / "accepted.jsonl"
        path.write_text("\n".join(json_text(row) for row in accepted), encoding="utf-8")
        articles, _ = read_corpus(path)
    return len(articles)


def audit(source_dir, output_dir):
    if source_dir.resolve() == output_dir.resolve() or source_dir.resolve() in output_dir.resolve().parents:
        raise ValueError("La salida no puede escribirse en el directorio de originales")
    if any((output_dir / name).exists() for name in OUTPUTS):
        raise FileExistsError("Ya existen resultados: use otro directorio de salida; no se sobrescriben")
    records, files, duplicates, coverage = inspect_sources(source_dir)
    accepted = [r["normalizado_candidato"] for r in records if r["clasificacion"] == "estructuralmente_apto"]
    reviewed = [r for r in records if r["clasificacion"] == "requiere_revision"]
    assert validate_accepted(accepted) == len(accepted)
    assert len({r["id_auditoria"] for r in records}) == len(records)
    for record in records:
        candidate = record["normalizado_candidato"]
        if candidate:
            assert candidate["texto"] == record["original"]["texto"]
    for file in files:
        if sha256((source_dir / file["archivo"]).read_bytes()) != file["sha256"]:
            raise RuntimeError("El original cambió durante la auditoría; se cancela la exportación")
    report = {
        "version_reglas": "1.2", "cotejo_oficial_realizado": False, "vigencia_juridica_verificada": False,
        "indexacion_chroma_realizada": False,
        "criterio_aptitud": "Pasa el contrato real y no presenta señales bloqueantes de esta auditoría automática. No certifica contenido, OCR, completitud o vigencia.",
        "total_registros": len(records), "estructuralmente_aptos": len(accepted), "requieren_revision": len(reviewed),
        "archivos_originales": files,
        "por_archivo": [{"archivo": f["archivo"], "registros": f["registros"],
                         "aptos": sum(r["archivo_original"] == f["archivo"] and r["clasificacion"] == "estructuralmente_apto" for r in records),
                         "revision": sum(r["archivo_original"] == f["archivo"] and r["clasificacion"] == "requiere_revision" for r in records)} for f in files],
        "registros_por_hallazgo": dict(sorted(Counter(code for r in records for code in {i["codigo"] for i in r["hallazgos"]}).items())),
        "duplicados": duplicates, "cobertura_observada": coverage,
        "mapeo": {"norma": "Alias controlados a documento", "articulo": "Quitar prefijo Artículo y mayúsculas solo de etiqueta; conservar números romanos y sufijos válidos",
                  "titulo_capitulo": "null/ausencia a cadena vacía; no inferir desde parte/seccion",
                  "texto": "Identidad literal de la cadena Unicode, sin strip, corrección, recorte o recomposición",
                  "pagina_pdf": "Solo campo exacto explícito; las páginas aproximadas permanecen en trazabilidad",
                  "version_fuente": "Procedencia declarada y SHA-256 del archivo; no certifica edición oficial",
                  "id": "Corpus + SHA-256 de archivo + número de línea original, único por ocurrencia"},
        "siguientes_pasos": ["Cotejar con PDFs oficiales, incluidos límites, títulos arrastrados y notas de versiones.",
                             "Resolver duplicados, etiquetas sospechosas, páginas y huecos sin inferir texto.",
                             "Calibrar recuperación y abstención después de resolver el corpus.",
                             "Esperar autorización explícita antes de publicar articles.jsonl o indexar en ChromaDB."],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    def write_lines(name, rows):
        (output_dir / name).write_text("".join(json_text(r) + "\n" for r in rows), encoding="utf-8")
    write_lines(OUTPUTS[0], accepted)
    write_lines(OUTPUTS[1], reviewed)
    write_lines(OUTPUTS[2], records)
    report["salidas_jsonl"] = [{"archivo": name, "sha256": sha256((output_dir / name).read_bytes())} for name in OUTPUTS[:3]]
    (output_dir / OUTPUTS[3]).write_text(json_text(report) + "\n", encoding="utf-8")
    lines = ["# Auditoría estructural de corpus de Mini-Juztina", "",
             f"Reglas {report['version_reglas']}. {len(records)} registros: **{len(accepted)} estructuralmente aptos** y **{len(reviewed)} requieren revisión**.", "",
             "No se realizó cotejo oficial ni verificación de vigencia. No se indexó en ChromaDB. La aptitud es estructural y heurística, no jurídica.", "",
             "## Por archivo", ""]
    lines += [f"- `{r['archivo']}`: {r['registros']} registros, {r['aptos']} aptos, {r['revision']} en revisión." for r in report["por_archivo"]]
    lines += ["", "## Hallazgos", "", "Los conteos se superponen: un registro puede presentar varios hallazgos. Las detecciones de mezclas, títulos y OCR son indicios para cotejo, no errores jurídicos demostrados.", ""]
    lines += [f"- `{key}`: {value} registros." for key, value in report["registros_por_hallazgo"].items()]
    lines += ["", "## Casos concretos para cotejar", ""]
    for group in duplicates:
        locations = "; ".join(f"{r['archivo']}, línea {r['linea']}, etiqueta {r['articulo']}" for r in group["registros"])
        lines.append(f"- `{group['codigo']}`: {locations}. No se determina automáticamente si son errores o coincidencias legítimas.")
    for record in records:
        important = [i for i in record["hallazgos"] if i["codigo"] in {
            "texto_vacio", "etiqueta_articulo_invalida", "etiqueta_y_cabecera_discrepan",
            "salto_numeracion_local", "numeral_final_sin_contenido", "observacion_del_extractor"}]
        if important:
            original = record["original"] if isinstance(record["original"], dict) else {}
            lines.append(f"- `{record['archivo_original']}`, línea {record['linea_original']}, etiqueta `{original.get('articulo')}`: " + "; ".join(i["codigo"] for i in important) + ".")
    lines += ["", "## Cobertura observada, sin inferir catálogo vigente", ""]
    for group in coverage:
        gaps = group["etiquetas_numericas_no_observadas_entre_1_y_ultima"]
        lines.append(f"- `{group['archivo']}`: {len(gaps)} etiquetas numéricas no observadas entre 1 y la última etiqueta numérica leída ({group['ultima_etiqueta_numerica_leida']}): " + ", ".join(map(str, gaps)) + ".")
    lines.append("Estos huecos no demuestran derogaciones ni omisiones jurídicas: también pueden obedecer a extracción o etiquetas erróneas. No se generan artículos para rellenarlos.")
    lines += ["", "## Preservación y normalización", "",
              "Las cadenas `texto` se exportan literalmente. No se eliminan encabezados, notas, títulos ni errores sospechosos; los registros se ponen en revisión. Se conserva el registro original completo y su procedencia en `audit_records.jsonl` y, para rechazados, `review_required.jsonl`.", "",
              "Los duplicados se ponen TODOS en revisión, sin seleccionar una supuesta versión correcta. Un texto vacío no se interpreta como artículo derogado. Las páginas aproximadas no se convierten en localizadores exactos. `pagina_pdf` queda null cuando no hay página exacta declarada.", "",
              "Los campos `parte` y `seccion` del Código Penal permanecen en el original de trazabilidad; no se equiparan a título/capítulo. `version_fuente` identifica el archivo y su fuente declarada, sin afirmar autenticidad o vigencia.", "",
              "## Archivos", "",
              "- `articles_structurally_accepted.jsonl`: únicamente aptos, verificados con `core.corpus.read_corpus`, sin indexar.",
              "- `review_required.jsonl`: cada registro pendiente, original completo, candidato normalizado y motivos.",
              "- `audit_records.jsonl`: trazabilidad de TODOS los registros, incluidos los aceptados.",
              "- `audit_report.json`: estadísticas, duplicados, huecos observados, SHA-256 y mapeos.", "",
              "No se crea `articles.jsonl`: evita activar el corpus de producción antes de su revisión y autorización.", "",
              "## Siguientes pasos", ""]
    lines += [f"- {step}" for step in report["siguientes_pasos"]]
    (output_dir / OUTPUTS[4]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=ROOT / "data/sources")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed")
    args = parser.parse_args()
    report = audit(args.sources, args.output)
    print(json_text({key: report[key] for key in ("total_registros", "estructuralmente_aptos", "requieren_revision", "por_archivo")}))


if __name__ == "__main__":
    main()
