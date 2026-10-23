#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
export PIP_CACHE_DIR="$PWD/.cache/pip"
.venv/bin/python -m pip install --index-url https://download.pytorch.org/whl/cpu 'torch==2.8.0+cpu'
requirements_file=requirements.txt
if [[ -f requirements.lock.txt ]]; then
    requirements_file=requirements.lock.txt
fi
.venv/bin/python -m pip install -r "$requirements_file"
.venv/bin/python -m pip check
if [[ ! -f .env ]]; then
    cp .env.example .env
fi
echo 'Dépendances prêtes. Étape suivante : make models, puis make ingest.'
