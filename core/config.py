from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Config:
    corpus: Path = ROOT / "data/processed/articles.jsonl"
    storage: Path = ROOT / "storage/chroma"
    embedding_model: Path = ROOT / "models/multilingual-e5-small"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:3b"
    timeout: float = 180
    top_k: int = 5
    min_similarity: float = 0.82

    def __post_init__(self):
        if not 0 <= self.min_similarity <= 1 or self.top_k < 1:
            raise ValueError("Configuración de recuperación inválida")
