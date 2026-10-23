PYTHON := .venv/bin/python

.PHONY: bootstrap models ingest serve test integration demo

bootstrap:
	bash scripts/bootstrap.sh

# Téléchargements initiaux explicites ; Ollama doit déjà être démarré.
models:
	ollama pull qwen2.5:3b
	$(PYTHON) -m scripts.check_ollama
	$(PYTHON) -m app.embeddings --download

ingest:
	$(PYTHON) -m app.ingest

serve:
	$(PYTHON) -m uvicorn app.api:app --host 127.0.0.1 --port 8000 --workers 1

test:
	$(PYTHON) -m pytest -m 'not integration' -q

integration:
	$(PYTHON) -m pytest -m integration -v

# Nécessite make serve dans un autre terminal.
demo:
	$(PYTHON) scripts/demo.py
