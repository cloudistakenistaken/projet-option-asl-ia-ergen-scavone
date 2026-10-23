import pytest
from pydantic import ValidationError

from app.config import ROOT, Settings


@pytest.mark.parametrize('url', ['https://api.example.com', 'http://example.com',
                               'http://localhost:11434/path',
                               'http://user:password@localhost:11434',
                               'http://localhost:11434?proxy=external'])
def test_external_or_ambiguous_urls_rejected(url):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ollama_url=url)


def test_paths_are_relative_to_repository_and_overlap_checked():
    assert Settings(_env_file=None, chroma_dir='.local/test').chroma_dir == ROOT / '.local/test'
    with pytest.raises(ValidationError):
        Settings(_env_file=None, chunk_tokens=32, chunk_overlap=32)
