import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

DOCUMENTS = {"Constitución Política del Perú", "Código Penal peruano"}


@dataclass(frozen=True)
class Article:
    id: str
    documento: str
    titulo: str
    capitulo: str
    articulo: str
    texto: str
    pagina_pdf: int | None
    version_fuente: str

    def source(self):
        return {k: getattr(self, k) for k in ("documento", "articulo", "texto", "pagina_pdf")}


def read_corpus(path: Path, allowed_documents=DOCUMENTS):
    raw = path.read_bytes()
    articles = {}
    references = set()
    for line_number, line in enumerate(raw.decode("utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            for key in Article.__dataclass_fields__:
                if key not in row:
                    raise ValueError(f"Falta {key}")
            for key in ("id", "documento", "articulo", "texto", "version_fuente"):
                if not isinstance(row[key], str) or not row[key].strip():
                    raise ValueError(f"{key} debe ser texto no vacío")
            for key in ("titulo", "capitulo"):
                if not isinstance(row[key], str):
                    raise ValueError(f"{key} debe ser texto (puede ser vacío)")
            page = row["pagina_pdf"]
            if page is not None and (type(page) is not int or page < 1):
                raise ValueError("pagina_pdf debe ser entero positivo o null")
            if row["documento"] not in allowed_documents:
                raise ValueError("Documento fuera del corpus permitido")
            article = Article(**{k: row[k] for k in Article.__dataclass_fields__})
            reference = (article.documento, article.articulo)
            if article.id in articles or reference in references:
                raise ValueError("ID o referencia duplicados; resolver versiones antes de indexar")
            articles[article.id] = article
            references.add(reference)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Línea {line_number}: {exc}") from exc
    if not articles:
        raise ValueError("Corpus vacío")
    return articles, hashlib.sha256(raw).hexdigest()
