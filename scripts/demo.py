"""Démonstration HTTP sur l'API démarrée par make serve."""

import argparse
import json
from pathlib import Path

import httpx

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, help='Conserver la réponse JSON comme preuve.')
args = parser.parse_args()

with httpx.Client(base_url='http://127.0.0.1:8000', timeout=180, trust_env=False) as client:
    response = client.post('/ask', json={
        'question': 'Combien de jours de congés par an et quel délai pour les demander ?',
        'top_k': 2,
    })
    response.raise_for_status()
    result = response.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not result['sources'] or result['sources'][0]['source'] != 'public/conges.md':
        raise SystemExit('Échec : la première source attendue est public/conges.md.')
    if not all(term in result['answer'] for term in ('25', '14')):
        raise SystemExit('Réponse à vérifier : les valeurs attendues sont 25 et 14.')
    print('Démonstration réussie pour cette question ; la qualité générale reste à évaluer.')
