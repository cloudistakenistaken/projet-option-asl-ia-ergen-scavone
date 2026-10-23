"""Configuration commune à l'API et aux scripts, relative au dépôt."""

from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / '.env', env_file_encoding='utf-8', extra='forbid'
    )

    ollama_url: str = 'http://localhost:11434'
    ollama_model: str = 'qwen2.5:3b'
    ollama_digest: str = '357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b'
    ollama_timeout: float = Field(default=120, gt=0)
    embedding_model: str = 'intfloat/multilingual-e5-small'
    embedding_revision: str = '614241f622f53c4eeff9890bdc4f31cfecc418b3'
    embedding_cache: Path = ROOT / '.cache/embeddings'
    corpus_dir: Path = ROOT / 'data/corpus'
    chroma_dir: Path = ROOT / '.local/chroma'
    collection_name: str = 'novalys-baseline'
    chunk_tokens: int = Field(default=220, ge=32, le=400)
    chunk_overlap: int = Field(default=32, ge=0)
    top_k: int = Field(default=3, ge=1, le=5)

    @field_validator('embedding_cache', 'corpus_dir', 'chroma_dir')
    @classmethod
    def resolve_path(cls, value: Path) -> Path:
        return (ROOT / value).resolve()

    @field_validator('ollama_url')
    @classmethod
    def local_ollama_only(cls, value: str) -> str:
        url = urlsplit(value)
        if (url.scheme != 'http' or url.hostname not in {'localhost', '127.0.0.1', '::1'}
                or url.username or url.password or url.path not in {'', '/'}
                or url.query or url.fragment):
            raise ValueError('OLLAMA_URL doit désigner une API HTTP sur la boucle locale.')
        return value.rstrip('/')

    @model_validator(mode='after')
    def check_overlap(self) -> 'Settings':
        if self.chunk_overlap >= self.chunk_tokens:
            raise ValueError('CHUNK_OVERLAP doit être inférieur à CHUNK_TOKENS.')
        return self

    @property
    def index_metadata(self) -> dict[str, str | int]:
        return {
            'embedding_model': self.embedding_model,
            'embedding_revision': self.embedding_revision,
            'chunk_tokens': self.chunk_tokens,
            'chunk_overlap': self.chunk_overlap,
            'schema_version': 1,
        }
