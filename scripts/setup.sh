#!/usr/bin/env bash
# Prépare une machine et vérifie une reconstruction complète du projet.
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

OLLAMA_PID=""

usage() {
    cat <<'EOF'
Usage: bash scripts/setup.sh

Prépare l'environnement Python, vérifie Ollama, télécharge les modèles,
reconstruit l'index, puis lance les tests unitaires et d'intégration.

Le serveur Ollama est démarré temporairement s'il ne répond pas déjà sur son
adresse configurée. Il n'est pas arrêté s'il était déjà lancé par l'utilisateur.
EOF
}

log() {
    printf '\n==> %s\n' "$1"
}

cleanup() {
    if [[ -n "$OLLAMA_PID" ]] && kill -0 "$OLLAMA_PID" 2>/dev/null; then
        log "Arrêt du serveur Ollama démarré par le script"
        kill "$OLLAMA_PID" 2>/dev/null || true
        wait "$OLLAMA_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi
if [[ $# -ne 0 ]]; then
    echo "Option inconnue : $1" >&2
    usage >&2
    exit 2
fi

for command_name in make curl; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "Commande requise absente : $command_name" >&2
        echo "Voir la section des prérequis dans README.md." >&2
        exit 1
    fi
done

log "Installation des dépendances Python"
make bootstrap

if ! command -v ollama >/dev/null 2>&1; then
    log "Installation d'Ollama"
    bash scripts/install_ollama.sh
fi

OLLAMA_URL="$(.venv/bin/python -c 'from app.config import Settings; print(Settings().ollama_url)')"
OLLAMA_LOG="$ROOT_DIR/.cache/ollama/server.log"

if ! curl --fail --silent --show-error --max-time 3 "$OLLAMA_URL/api/tags" >/dev/null; then
    log "Démarrage temporaire d'Ollama"
    mkdir -p "$(dirname "$OLLAMA_LOG")"
    ollama serve >"$OLLAMA_LOG" 2>&1 &
    OLLAMA_PID=$!

    for _ in $(seq 1 60); do
        if curl --fail --silent --show-error --max-time 3 "$OLLAMA_URL/api/tags" >/dev/null; then
            break
        fi
        sleep 1
    done
    if ! curl --fail --silent --show-error --max-time 3 "$OLLAMA_URL/api/tags" >/dev/null; then
        echo "Ollama ne répond pas sur $OLLAMA_URL." >&2
        echo "Journal : $OLLAMA_LOG" >&2
        exit 1
    fi
fi

log "Téléchargement et vérification des modèles"
make models

log "Création de l'index Chroma"
make ingest

log "Tests unitaires"
make test

log "Tests d'intégration"
make integration

log "Préparation terminée avec succès"
cat <<'EOF'
L'API va maintenant démarrer sur http://127.0.0.1:8000.
Dans un autre terminal, vous pourrez envoyer une requête avec :

curl --fail http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Le VPN est-il obligatoire en télétravail ?","top_k":2}' \
  | python3 -m json.tool

Arrêtez le serveur avec Ctrl+C.
EOF

make serve
