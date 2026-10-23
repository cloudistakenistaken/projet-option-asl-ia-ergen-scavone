"""Tests réels explicites : make integration, après téléchargement des modèles."""

import re

import pytest
from fastapi.testclient import TestClient

from app.api import RagService, app, get_service
from app.config import ROOT, Settings
from app.embeddings import LocalEmbedder
from app.ingest import ingest
from app.retrieval import Repository

pytestmark = pytest.mark.integration


@pytest.fixture(scope='module')
def real_rag(tmp_path_factory):
    settings = Settings(_env_file=None, chroma_dir=tmp_path_factory.mktemp('real-rag'),
                        corpus_dir=ROOT / 'data/corpus')
    embedder = LocalEmbedder(settings)
    report = ingest(settings, embedder)
    assert report['documents'] == 3
    service = RagService.__new__(RagService)
    service.settings = settings
    service.embedder = embedder
    service.repository = Repository(settings)
    return service


@pytest.mark.parametrize('question,source', [
    ('Combien de jours de congés par an ?', 'public/conges.md'),
    ('Le VPN est-il obligatoire en télétravail ?', 'public/teletravail.md'),
    ('Quel est le budget du projet Aurore ?', 'confidentiel/aurore.md'),
])
def test_real_french_semantic_retrieval(real_rag, question, source):
    vector = real_rag.embedder.question(question)
    assert len(vector[0]) == 384
    assert real_rag.repository.search(vector, 1)[0].source == source


def test_real_token_chunking_preserves_unicode_and_token_budget(real_rag):
    text = 'Les salariés déposent leurs congés auprès du responsable. ' * 50
    chunks = real_rag.embedder.split(text, 64, 12)
    assert len(chunks) > 1
    assert chunks[0].startswith('Les salariés')
    assert chunks[-1].endswith('responsable.')
    assert all(len(real_rag.embedder.model.tokenizer.encode(
        c, add_special_tokens=False)) <= 64 for c in chunks)


def test_real_api_with_ollama_returns_facts_and_citations(real_rag):
    app.dependency_overrides[get_service] = lambda: real_rag
    try:
        with TestClient(app) as client:
            response = client.post('/ask', json={
                'question': 'Combien de jours de congés par an et quel délai pour les demander ?',
                'top_k': 2,
            })
        assert response.status_code == 200, response.text
        result = response.json()
        assert result['sources'][0]['source'] == 'public/conges.md'
        assert '25' in result['answer'] and '14' in result['answer']
        assert re.search(r'\[S[12]\]', result['answer']), result['answer']
    finally:
        app.dependency_overrides.clear()
