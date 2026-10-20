import os

# No descarga de modelos ni telemetría durante el funcionamiento.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"


class LocalEmbeddings:
    def __init__(self, path):
        if not path.is_dir():
            raise FileNotFoundError("Embeddings locales ausentes: ejecutar scripts/prepare_model.py")
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(str(path), device="cpu", local_files_only=True)

    def encode(self, texts, query=False):
        prefix = "query: " if query else "passage: "
        return self.model.encode([prefix + t for t in texts], normalize_embeddings=True,
                                 batch_size=16, show_progress_bar=False).tolist()

    def chunks(self, text):
        # Los offsets conservan exactamente el texto original y evitan truncamiento silencioso.
        offsets = self.model.tokenizer(text, add_special_tokens=False,
                                       truncation=False, verbose=False,
                                       return_offsets_mapping=True)["offset_mapping"]
        size = min(self.model.max_seq_length - 16, 460)
        if size < 32:
            raise ValueError("Ventana del modelo insuficiente")
        for start in range(0, len(offsets), size - 32):
            part = offsets[start:start + size]
            if part:
                yield text[part[0][0]:part[-1][1]]
