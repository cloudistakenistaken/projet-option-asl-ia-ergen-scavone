"""Appel HTTP local à Ollama, avec contexte documentaire et sources numérotées."""

import httpx

from app.config import Settings
from app.retrieval import Passage
from app.security import SYSTEM_PROMPT


class GenerationUnavailable(RuntimeError):
    pass


def generate(question: str, passages: list[Passage], settings: Settings,
             *, transport: httpx.BaseTransport | None = None) -> str:
    context = '\n\n'.join(
        f'[S{i}] {p.source} — passage {p.chunk}\n{p.text}'
        for i, p in enumerate(passages, 1)
    )
    try:
        # Ignore les proxies de l'environnement ; aucune redirection suivie.
        with httpx.Client(timeout=settings.ollama_timeout, trust_env=False,
                          transport=transport) as client:
            response = client.post(settings.ollama_url + '/api/generate', json={
                'model': settings.ollama_model, 'system': SYSTEM_PROMPT,
                'prompt': (f'EXTRAITS DOCUMENTAIRES\n{context}\n\nQUESTION\n{question}'
                           '\n\nRÉPONSE EN FRANÇAIS AVEC LES RÉFÉRENCES DES SOURCES :'),
                'stream': False,
                'options': {'temperature': 0, 'seed': 42,
                            'num_ctx': 4096, 'num_predict': 384},
            })
            response.raise_for_status()
            payload = response.json()
        answer = payload.get('response') if isinstance(payload, dict) else None
        if not isinstance(answer, str) or not answer.strip() or payload.get('done') is not True:
            raise ValueError('Réponse Ollama vide ou incomplète.')
        return answer.strip()
    except (httpx.HTTPError, ValueError) as exc:
        raise GenerationUnavailable(
            'Génération indisponible : vérifier Ollama, le modèle et le délai configuré.'
        ) from exc
