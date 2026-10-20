"""Preparación inicial CON red; el motor nunca descarga modelos."""
import argparse
from pathlib import Path
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", required=True, help="Commit SHA inmutable de Hugging Face")
    args = parser.parse_args()
    import re
    if not re.fullmatch(r"[0-9a-f]{40}", args.revision):
        parser.error("Se requiere el SHA completo")
    os.environ["HF_HUB_OFFLINE"] = "0"
    os.environ["TRANSFORMERS_OFFLINE"] = "0"
    from sentence_transformers import SentenceTransformer
    target = Path(__file__).resolve().parents[1] / "models/multilingual-e5-small"
    model = SentenceTransformer("intfloat/multilingual-e5-small", revision=args.revision, device="cpu")
    model.save(str(target))
    (target / "REVISION.txt").write_text(args.revision, encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
