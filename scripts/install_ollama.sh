#!/usr/bin/env bash
# À exécuter explicitement sur une machine vierge ; peut demander sudo.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .cache/ollama
curl --fail --show-error --location https://ollama.com/install.sh -o .cache/ollama/install.sh
OLLAMA_VERSION=0.40.9 sh .cache/ollama/install.sh
ollama --version
