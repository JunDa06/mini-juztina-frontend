"""Empaquetado académico por lista explícita, sin tocar el índice ni los originales."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, str):
        yield value


def relative_operational_paths(value):
    if isinstance(value, dict):
        return {key: relative_operational_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [relative_operational_paths(item) for item in value]
    if isinstance(value, str) and (value.startswith(str(ROOT)) or value.startswith(ROOT.as_posix())):
        return Path(value).relative_to(ROOT).as_posix()
    return value


def package():
    from scripts.pilot_index import plan
    current = plan()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stage = ROOT / ".cache" / ("release-stage-" + stamp) / "Mini-Juztina"
    stage.mkdir(parents=True, exist_ok=False)
    output_dir = ROOT / "deliverables"
    output_dir.mkdir(exist_ok=True)
    target = output_dir / "Mini-Juztina-MVP-Academico-2026-10-20.zip"
    if target.exists():
        raise FileExistsError("No se sobrescribe un entregable existente")

    selected = set()
    for name in ("README.md", "DEMO_ACADEMICA.md", "requirements.txt", "requirements-lock.txt",
                 "requirements-api.txt", "requirements-api-lock.txt"):
        selected.add(ROOT / name)
    for directory in ("core", "api", "scripts", "tests"):
        selected.update((ROOT / directory).glob("*.py"))
        selected.update((ROOT / directory).glob("*.ps1"))
    frontend = ROOT / "frondend"
    for name in ("package.json", "package-lock.json", "index.html", "vite.config.js", "eslint.config.js"):
        selected.add(frontend / name)
    for directory in ("src", "public", "dist"):
        selected.update(p for p in (frontend / directory).rglob("*") if p.is_file())
    selected.update((ROOT / "data/sources").glob("*.jsonl"))
    selected.update(p for p in (ROOT / "data/processed").glob("*") if p.is_file() and p.suffix in {".json", ".jsonl", ".md"})
    pilot = ROOT / "data/processed/pilot_10_v1"
    for name in ("articles_candidates.jsonl", "manifest.json", "index_receipt.json", "INDEX_PLAN.json",
                 "COTEJO.md", "EXPERIMENT_RESULTS.md", "TEST_RESULTS.md", "retrieval_results.json", "http_results.json"):
        selected.add(pilot / name)
    selected.update(p for p in (ROOT / "models/multilingual-e5-small").rglob("*") if p.is_file())
    selected.update(p for p in (ROOT / "release").glob("*") if p.is_file() and p.suffix in {".md", ".json", ".png"})

    roots = (str(ROOT), ROOT.as_posix())
    for source in sorted(selected):
        if not source.is_file():
            raise FileNotFoundError(source.relative_to(ROOT))
        relative = source.relative_to(ROOT)
        if any(part in {".venv", ".venv312", ".runtime", "node_modules", "__pycache__", ".git", ".aws"} for part in relative.parts):
            raise ValueError("Archivo excluido en la selección")
        dest = stage / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if source.name in {"index_receipt.json", "INDEX_PLAN.json", "retrieval_results.json"}:
            data = relative_operational_paths(json.loads(source.read_text(encoding="utf-8")))
            dest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        elif source.suffix == ".md" and "models" not in relative.parts:
            # Solo documentación; los JSONL jurídicos y archivos del modelo se copian byte a byte.
            content = source.read_text(encoding="utf-8")
            for private_root in roots:
                content = content.replace(private_root, ".")
            dest.write_text(content, encoding="utf-8")
        else:
            shutil.copy2(source, dest)

    storage = Path(current["storage"])
    snapshot = stage / storage.relative_to(ROOT)
    snapshot.mkdir(parents=True)
    native_before = {p.relative_to(storage).as_posix(): sha(p) for p in storage.rglob("*.bin")}
    for rel in native_before:
        src, dst = storage / rel, snapshot / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    uri = (storage / "chroma.sqlite3").as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as src, sqlite3.connect(snapshot / "chroma.sqlite3") as dst:
        src.backup(dst)
        assert dst.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    if native_before != {p.relative_to(storage).as_posix(): sha(p) for p in storage.rglob("*.bin")}:
        raise RuntimeError("El índice HNSW cambió durante la copia; no se publica")

    required = {"README.md", "DEMO_ACADEMICA.md", "core/rag_engine.py", "core/corpus.py", "core/vector_store.py",
                "api/main.py", "api/pilot.py", "scripts/pilot_runtime.py", "scripts/pilot_index.py",
                "scripts/release_smoke.py", "requirements-api.txt", "requirements-api-lock.txt",
                "requirements.txt", "requirements-lock.txt", "frondend/package.json", "frondend/package-lock.json",
                "frondend/src/App.jsx", "frondend/src/main.jsx", "frondend/index.html", "frondend/vite.config.js",
                "frondend/dist/index.html", "data/sources/constitucion.jsonl", "data/sources/codigo_penal_articulos.jsonl",
                "data/processed/audit_records.jsonl", "data/processed/audit_report.json",
                "data/processed/articles_structurally_accepted.jsonl", "data/processed/pilot_10_v1/articles_candidates.jsonl",
                "data/processed/pilot_10_v1/manifest.json", "data/processed/pilot_10_v1/index_receipt.json",
                "models/multilingual-e5-small/model.safetensors", "models/multilingual-e5-small/tokenizer.json",
                "models/multilingual-e5-small/1_Pooling/config.json", "models/multilingual-e5-small/modules.json",
                "release/SMOKE_RESULT.json", "release/UI_CHECK.json", "release/UI_PROOF.png"}
    names = {p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()}
    assert required <= names, sorted(required - names)
    secret_pattern = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?<![A-Za-z0-9_])sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}|hf_[A-Za-z0-9]{25,}|AKIA[A-Z0-9]{16}")
    for path in stage.rglob("*"):
        if path.is_file() and path.suffix in {".json", ".jsonl", ".py", ".js", ".jsx", ".md", ".txt", ".ps1", ".html", ".css"}:
            raw = path.read_bytes()
            if any(private_root.encode() in raw for private_root in roots):
                raise ValueError("Ruta personal detectada en " + path.relative_to(stage).as_posix())
            if path.suffix in {".json", ".jsonl"}:
                objects = [json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()] if path.suffix == ".jsonl" else [json.loads(raw)]
                if any(private_root in text for obj in objects for text in strings(obj) for private_root in roots):
                    raise ValueError("Ruta personal en JSON decodificado: " + path.relative_to(stage).as_posix())
            if secret_pattern.search(raw):
                raise ValueError("Posible credencial detectada en " + path.relative_to(stage).as_posix())

    manifest = {p.relative_to(stage).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p)}
                for p in sorted(stage.rglob("*")) if p.is_file()}
    (stage / "FILE_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as archive:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                archive.write(path, "Mini-Juztina/" + path.relative_to(stage).as_posix())
    print("ZIP CREADO. Verificando contenido, CRC y SHA-256...", flush=True)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        actual = {name.removeprefix("Mini-Juztina/") for name in archive.namelist()}
        assert actual == set(manifest) | {"FILE_MANIFEST.json"}
        for name, details in manifest.items():
            h = hashlib.sha256()
            with archive.open("Mini-Juztina/" + name) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(block)
            assert h.hexdigest() == details["sha256"], name
    checksum = sha(target)
    (output_dir / (target.name + ".sha256")).write_text(checksum + "  " + target.name + "\n", encoding="ascii")
    check = {"zip": target.name, "bytes": target.stat().st_size, "sha256": checksum,
             "archivos": len(manifest) + 1, "crc_correcto": True, "hashes_archivos_correctos": True,
             "indispensables_verificados": sorted(required), "credenciales_conocidas_detectadas": False,
             "rutas_personales_detectadas": False, "modelo_embeddings_incluido": True,
             "indice_piloto_incluido": True, "rebase_recibo_requerido_tras_extraer": True}
    (output_dir / "PACKAGE_CHECK.json").write_text(json.dumps(check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(check, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    package()
