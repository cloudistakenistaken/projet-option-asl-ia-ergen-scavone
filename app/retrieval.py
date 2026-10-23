"""Chroma persistant ; les embeddings sont toujours calculés par notre code."""

from dataclasses import asdict, dataclass

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.errors import NotFoundError

from app.config import Settings


class IndexNotReady(RuntimeError):
    pass


@dataclass(frozen=True)
class Passage:
    id: str
    text: str
    source: str
    classification: str
    chunk: int
    distance: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class Repository:
    def __init__(self, settings: Settings, *, create: bool = False):
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        try:
            if create:
                self.collection = self.client.get_or_create_collection(
                    name=settings.collection_name,
                    embedding_function=None,
                    metadata=settings.index_metadata,
                    configuration={'hnsw': {'space': 'cosine'}},
                )
            else:
                self.collection = self.client.get_collection(
                    name=settings.collection_name, embedding_function=None
                )
        except NotFoundError as exc:
            raise IndexNotReady('Index absent : exécuter make ingest.') from exc
        if self.collection.metadata != settings.index_metadata:
            raise IndexNotReady(
                'Configuration différente de celle de l’index. Choisir un nouveau '
                'COLLECTION_NAME puis exécuter make ingest.'
            )

    def synchronize(self, passages: list[Passage], vectors: list[list[float]]) -> None:
        if not passages:
            raise ValueError('Corpus vide : index existant conservé.')
        # Mise à jour avant suppression ; ingestion à effectuer API arrêtée.
        self.collection.upsert(
            ids=[p.id for p in passages], embeddings=vectors,
            documents=[p.text for p in passages],
            metadatas=[{'source': p.source, 'classification': p.classification,
                        'chunk': p.chunk} for p in passages],
        )
        current_ids = {p.id for p in passages}
        stale = set(self.collection.get(include=[])['ids']) - current_ids
        if stale:
            self.collection.delete(ids=sorted(stale))

    def search(self, vector: list[list[float]], top_k: int) -> list[Passage]:
        count = self.collection.count()
        if not count:
            raise IndexNotReady('Index vide : exécuter make ingest.')
        result = self.collection.query(
            query_embeddings=vector, n_results=min(top_k, count),
            include=['documents', 'metadatas', 'distances'],
        )
        return [
            Passage(id=id_, text=text, source=meta['source'],
                    classification=meta['classification'], chunk=meta['chunk'],
                    distance=float(distance))
            for id_, text, meta, distance in zip(
                result['ids'][0], result['documents'][0],
                result['metadatas'][0], result['distances'][0], strict=True
            )
        ]
