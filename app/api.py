"""API locale de référence : recherche → génération → sources récupérées."""

from functools import lru_cache
from pathlib import Path
from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import Settings
from app.embeddings import LocalEmbedder
from app.generation import GenerationUnavailable, generate
from app.retrieval import IndexNotReady, Repository
from app.security import Authenticator, BASELINE_MODE, SESSION_COOKIE, User

# Pas de Swagger via CDN : l'application reste utilisable sans accès Internet.
app = FastAPI(title='Novalys — RAG local de référence', docs_url=None, redoc_url=None)
WEB_ROOT = Path(__file__).with_name('static')


@app.get('/', include_in_schema=False)
def web_app() -> FileResponse:
    """Page locale pour poser une question sans utiliser curl."""
    return FileResponse(WEB_ROOT / 'index.html', media_type='text/html')


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


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    username: str


class Source(BaseModel):
    citation: str
    id: str
    source: str
    classification: str
    chunk: int
    text: str
    distance: float
    owner: str | None = None


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

    def ask(self, request: Question, user: User) -> Answer:
        started = perf_counter()
        passages = self.repository.search(
            self.embedder.question(request.question),
            request.top_k or self.settings.top_k,
            username=user.username,
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


@lru_cache(maxsize=1)
def get_authenticator() -> Authenticator:
    settings = Settings()
    return Authenticator(settings.auth_password_user_a,
                         settings.auth_password_user_b,
                         settings.auth_session_ttl)


def current_user(request: Request,
                 authenticator: Authenticator = Depends(get_authenticator)) -> User:
    user = authenticator.user_from_token(request.cookies.get(SESSION_COOKIE))
    if user is None:
        raise HTTPException(status_code=401, detail='Connexion requise.')
    return user


@app.post('/auth/login', response_model=UserResponse)
def login(request: LoginRequest, response: Response,
          authenticator: Authenticator = Depends(get_authenticator)) -> UserResponse:
    user = authenticator.authenticate(request.username.strip(), request.password)
    if user is None:
        raise HTTPException(status_code=401, detail='Identifiants invalides.')
    response.set_cookie(
        SESSION_COOKIE, authenticator.create_session(user), httponly=True,
        samesite='lax', max_age=authenticator.session_ttl,
    )
    return UserResponse(username=user.username)


@app.get('/auth/me', response_model=UserResponse)
def me(user: User = Depends(current_user)) -> UserResponse:
    return UserResponse(username=user.username)


@app.post('/auth/logout', status_code=204)
def logout(request: Request, response: Response,
           authenticator: Authenticator = Depends(get_authenticator)) -> None:
    authenticator.revoke(request.cookies.get(SESSION_COOKIE))
    response.delete_cookie(SESSION_COOKIE)


@app.get('/health')
def health() -> dict:
    # Vivacité de l'API seulement ; ne certifie ni Ollama ni l'index.
    return {'status': 'ok', 'mode': BASELINE_MODE, 'check': 'liveness'}


@app.post('/ask', response_model=Answer)
def ask(request: Question, user: User = Depends(current_user),
        service: RagService = Depends(get_service)) -> Answer:
    try:
        return service.ask(request, user)
    except IndexNotReady as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GenerationUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
