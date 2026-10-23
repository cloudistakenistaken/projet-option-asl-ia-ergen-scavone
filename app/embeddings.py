"""E5 sur CPU : téléchargement explicite, puis chargement local uniquement."""

import argparse
import os

from app.config import Settings


class LocalEmbedder:
    def __init__(self, settings: Settings, *, download: bool = False):
        # Téléchargement HTTP standard, compatible avec les réseaux sans accès Xet.
        os.environ.setdefault('HF_HUB_DISABLE_XET', '1')
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(
            settings.embedding_model,
            revision=settings.embedding_revision,
            cache_folder=str(settings.embedding_cache),
            device='cpu',
            trust_remote_code=False,
            local_files_only=not download,
        )

    def passages(self, texts: list[str]) -> list[list[float]]:
        return self._encode(['passage: ' + text for text in texts])

    def question(self, text: str) -> list[list[float]]:
        return self._encode(['query: ' + text])

    def _encode(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(
            texts, normalize_embeddings=True, batch_size=8, show_progress_bar=False
        ).tolist()

    def split(self, text: str, size: int, overlap: int) -> list[str]:
        # Les offsets préservent le texte Markdown original, accents compris.
        offsets = self.model.tokenizer(
            text, add_special_tokens=False, return_offsets_mapping=True,
            truncation=False,
        )['offset_mapping']
        passages = []
        for start in range(0, len(offsets), size - overlap):
            window = offsets[start:start + size]
            passage = text[window[0][0]:window[-1][1]].strip()
            if passage:
                passages.append(passage)
            if start + size >= len(offsets):
                break
        return passages


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true', required=True)
    parser.parse_args()
    settings = Settings()
    embedder = LocalEmbedder(settings, download=True)
    print(f'Modèle prêt : {settings.embedding_model}@{settings.embedding_revision}')
    print(f'Dimension : {len(embedder.question("test")[0])} ; périphérique : CPU')
