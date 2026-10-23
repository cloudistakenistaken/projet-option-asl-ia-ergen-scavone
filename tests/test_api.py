import httpx
import pytest
from fastapi.testclient import TestClient

import app.api as api
from app.config import Settings
from app.generation import GenerationUnavailable, generate
from app.retrieval import IndexNotReady, Passage, Repository


@pytest.fixture
def service(tmp_path, monkeypatch):
    settings = Settings(_env_file=None, chroma_dir=tmp_path / 'index')
    service = api.RagService.__new__(api.RagService)
    service.settings = settings
    service.repository = Repository(settings, create=True)
    service.repository.synchronize([
        Passage('conges', '25 jours', 'public/conges.md', 'public', 0)
    ], [[1., 0.]])

    class Embedder:
        def question(self, text):
            return [[1., 0.]]

    service.embedder = Embedder()
    transport = httpx.MockTransport(lambda req: httpx.Response(
        200, json={'response': '25 jours [S1]', 'done': True}
    ))
    monkeypatch.setattr(api, 'generate', lambda q, p, s: generate(q, p, s, transport=transport))
    api.app.dependency_overrides[api.get_service] = lambda: service
    yield service
    api.app.dependency_overrides.clear()


def test_ask_runs_retrieval_and_returns_sources(service):
    with TestClient(api.app) as client:
        response = client.post('/ask', json={'question': 'Combien de jours ?', 'top_k': 2})
    assert response.status_code == 200
    result = response.json()
    assert result['mode'] == 'baseline'
    assert result['answer'] == '25 jours [S1]'
    assert result['sources'][0]['citation'] == 'S1'
    assert result['sources'][0]['source'] == 'public/conges.md'
    assert result['sources'][0]['text'] == '25 jours'
    assert result['latency_ms']['total'] >= 0


@pytest.mark.parametrize('payload', [
    {'question': ''}, {'question': '   '}, {'question': 'x' * 1001},
    {'question': 'Congés ?', 'top_k': 0}, {'question': 'Congés ?', 'top_k': 6},
    {'question': 'Budget ?', 'role': 'direction'},
])
def test_invalid_requests_and_client_supplied_roles_rejected(service, payload):
    with TestClient(api.app) as client:
        assert client.post('/ask', json=payload).status_code == 422


@pytest.mark.parametrize('error,status', [(IndexNotReady('Index vide'), 503),
                                        (GenerationUnavailable('Ollama absent'), 502)])
def test_service_errors_become_http_errors(service, monkeypatch, error, status):
    def fail(request):
        raise error
    monkeypatch.setattr(service, 'ask', fail)
    with TestClient(api.app) as client:
        assert client.post('/ask', json={'question': 'Congés ?'}).status_code == status


def test_health_only_checks_api_liveness():
    with TestClient(api.app) as client:
        assert client.get('/health').json()['check'] == 'liveness'


def test_missing_index_before_service_initialization(tmp_path, monkeypatch):
    monkeypatch.setattr(api, 'Settings', lambda: Settings(_env_file=None, chroma_dir=tmp_path))
    api.get_service.cache_clear()
    with TestClient(api.app) as client:
        response = client.post('/ask', json={'question': 'Congés ?'})
    assert response.status_code == 503
    assert 'make ingest' in response.json()['detail']
    api.get_service.cache_clear()
