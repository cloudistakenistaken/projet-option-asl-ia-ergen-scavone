"""Lecture du corpus fictif, découpage et synchronisation de l'index."""

from hashlib import sha256
import json

from app.config import Settings
from app.embeddings import LocalEmbedder
from app.retrieval import Passage, Repository


def read_passages(settings: Settings, embedder: LocalEmbedder) -> list[Passage]:
    passages = []
    for path in sorted(settings.corpus_dir.rglob('*.md')):
        relative = path.relative_to(settings.corpus_dir)
        if len(relative.parts) < 2 or relative.parts[0] not in {'public', 'confidentiel'}:
            raise ValueError(f'Classification inconnue : {relative}')
        if path.is_symlink() or not path.resolve().is_relative_to(settings.corpus_dir):
            raise ValueError(f'Lien hors corpus ou symbolique interdit : {relative}')
        text = path.read_text(encoding='utf-8').strip()
        for number, chunk in enumerate(embedder.split(
            text, settings.chunk_tokens, settings.chunk_overlap
        )):
            source = relative.as_posix()
            id_ = sha256(f'{source}\0{number}\0{chunk}'.encode()).hexdigest()
            passages.append(Passage(id_, chunk, source, relative.parts[0], number))
    if not passages:
        raise ValueError('Aucun document non vide dans le corpus ; index conservé.')
    return passages


def ingest(settings: Settings, embedder: LocalEmbedder) -> dict:
    passages = read_passages(settings, embedder)
    repository = Repository(settings, create=True)
    vectors = embedder.passages([p.text for p in passages])
    repository.synchronize(passages, vectors)
    return {'documents': len({p.source for p in passages}),
            'passages': len(passages), 'index': str(settings.chroma_dir),
            'collection': settings.collection_name}


if __name__ == '__main__':
    settings = Settings()
    print(json.dumps(ingest(settings, LocalEmbedder(settings)), ensure_ascii=False, indent=2))
