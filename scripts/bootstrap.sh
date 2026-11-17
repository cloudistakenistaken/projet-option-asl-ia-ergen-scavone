#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Le verrou a été validé avec Python 3.12, mais les distributions récentes
# peuvent fournir une autre version comme Python système. Utiliser celle-ci
# après vérification de la présence du module venv.
PYTHON_BIN=python3

if ! "$PYTHON_BIN" -c 'import ensurepip' >/dev/null 2>&1; then
    echo "Impossible de créer .venv : le module venv manque pour $PYTHON_BIN." >&2
    echo "Ubuntu/Debian : installez python3-venv, puis relancez make bootstrap." >&2
    exit 1
fi

"$PYTHON_BIN" -m venv .venv
export PIP_CACHE_DIR="$PWD/.cache/pip"
.venv/bin/python -m pip install --index-url https://download.pytorch.org/whl/cpu 'torch==2.9.0+cpu'
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
