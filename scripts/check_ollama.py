"""Vérifie la présence et le digest du générateur de référence."""

import json

import httpx

from app.config import Settings

settings = Settings()
with httpx.Client(timeout=15, trust_env=False) as client:
    response = client.get(settings.ollama_url + '/api/tags')
    response.raise_for_status()
    matches = [m for m in response.json()['models'] if m['name'] == settings.ollama_model]
    if not matches:
        raise SystemExit(f'Modèle absent : {settings.ollama_model}')
    model = matches[0]
    if model['digest'] != settings.ollama_digest:
        raise SystemExit('Digest Qwen différent : comparer avec la référence avant de continuer.')
    print(json.dumps(model, ensure_ascii=False, indent=2))
