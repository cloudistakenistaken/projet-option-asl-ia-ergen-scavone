"""API locale de référence : recherche → génération → sources récupérées."""

from functools import lru_cache
from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import Settings
from app.embeddings import LocalEmbedder
from app.generation import GenerationUnavailable, generate
from app.retrieval import IndexNotReady, Repository
from app.security import BASELINE_MODE

# Pas de Swagger via CDN : l'application reste utilisable sans accès Internet.
app = FastAPI(title='Novalys — RAG local de référence', docs_url=None, redoc_url=None)


class Question(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str = Field(min_length=1, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=5)

    @field_validator('question')
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('La question ne peut pas être vide.')
        return value.strip()


class Source(BaseModel):
    citation: str
    id: str
    source: str
    classification: str
    chunk: int
    text: str
    distance: float


class Answer(BaseModel):
    mode: str
    answer: str
    sources: list[Source]
    latency_ms: dict[str, float]


class RagService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.repository = Repository(settings)
        self.embedder = LocalEmbedder(settings)

    def ask(self, request: Question) -> Answer:
        started = perf_counter()
        passages = self.repository.search(
            self.embedder.question(request.question), request.top_k or self.settings.top_k
        )
        retrieved = perf_counter()
        answer = generate(request.question, passages, self.settings)
        finished = perf_counter()
        return Answer(
            mode=BASELINE_MODE, answer=answer,
            sources=[Source(citation=f'S{i}', **p.to_dict())
                     for i, p in enumerate(passages, 1)],
            latency_ms={'retrieval': round((retrieved - started) * 1000, 2),
                        'generation': round((finished - retrieved) * 1000, 2),
                        'total': round((finished - started) * 1000, 2)},
        )


@lru_cache(maxsize=1)
def get_service() -> RagService:
    try:
        return RagService(Settings())
    except IndexNotReady as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail='Embeddings indisponibles : exécuter make models.') from exc


@app.get('/health')
def health() -> dict:
    # Vivacité de l'API seulement ; ne certifie ni Ollama ni l'index.
    return {'status': 'ok', 'mode': BASELINE_MODE, 'check': 'liveness'}


@app.post('/ask', response_model=Answer)
def ask(request: Question, service: RagService = Depends(get_service)) -> Answer:
    try:
        return service.ask(request)
    except IndexNotReady as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GenerationUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
