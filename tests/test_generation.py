import json

import httpx
import pytest

from app.config import Settings
from app.generation import GenerationUnavailable, generate
from app.retrieval import Passage


def test_ollama_receives_local_context_and_generation_options():
    def handler(request):
        payload = json.loads(request.content)
        assert request.url == 'http://localhost:11434/api/generate'
        assert payload['stream'] is False
        assert payload['options']['num_ctx'] == 4096
        assert '[S1] public/conges.md' in payload['prompt']
        assert '25 jours' in payload['prompt']
        assert 'Combien ?' in payload['prompt']
        return httpx.Response(200, json={'response': '25 jours [S1]', 'done': True})

    result = generate('Combien ?', [Passage('x', '25 jours', 'public/conges.md', 'public', 0)],
                      Settings(_env_file=None), transport=httpx.MockTransport(handler))
    assert result == '25 jours [S1]'


@pytest.mark.parametrize('payload', [{}, [], {'response': ''},
                                   {'response': 'Texte', 'done': False},
                                   {'response': 42, 'done': True}])
def test_malformed_ollama_response_is_reported(payload):
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=payload))
    with pytest.raises(GenerationUnavailable):
        generate('Question', [], Settings(_env_file=None), transport=transport)


def test_timeout_is_reported():
    def handler(request):
        raise httpx.ReadTimeout('Ollama trop lent', request=request)
    with pytest.raises(GenerationUnavailable):
        generate('Question', [], Settings(_env_file=None), transport=httpx.MockTransport(handler))


def test_missing_model_is_reported():
    transport = httpx.MockTransport(lambda req: httpx.Response(404, json={'error': 'model not found'}))
    with pytest.raises(GenerationUnavailable):
        generate('Question', [], Settings(_env_file=None), transport=transport)
