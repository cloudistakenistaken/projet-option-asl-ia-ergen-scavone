"""Mesure reproductible de la latence HTTP de l'API RAG locale."""

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.config import Settings


QUESTIONS = [
    "Combien de jours de congés par an et quel délai pour les demander ?",
    "Le VPN est-il obligatoire en télétravail ?",
    "Quel est le budget du projet Aurore ?",
    "Combien de jours de télétravail sont autorisés par semaine ?",
    "Qui doit valider une demande de congés ?",
]


def corpus_catalog() -> dict[str, object]:
    root = Path(__file__).resolve().parents[1] / "data" / "corpus"
    groups: dict[str, object] = {}
    for classification in ("public", "confidentiel"):
        files = []
        for path in sorted((root / classification).glob("*.md")):
            content = path.read_text(encoding="utf-8")
            files.append(
                {
                    "path": str(path.relative_to(root)),
                    "title": content.splitlines()[0].removeprefix("# "),
                    "bytes": len(content.encode("utf-8")),
                    "words": len(content.split()),
                    "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "topics": {
                        "conges.md": ["25 jours/an", "délai de 14 jours", "report de 5 jours", "portail RH"],
                        "teletravail.md": ["2 jours/semaine", "VPN obligatoire", "prévenance de 3 jours", "authentification multifacteur"],
                        "aurore.md": ["projet Aurore", "15 mars 2027", "budget 420 000 euros", "équipe pilote", "phase pilote de 6 semaines"],
                    }.get(path.name, []),
                }
            )
        groups[classification] = {"document_count": len(files), "documents": files}
    return {
        "root": "data/corpus",
        "classification_note": "Le répertoire confidentiel correspond aux données privées fictives du scénario.",
        "total_document_count": sum(group["document_count"] for group in groups.values()),
        "groups": groups,
    }


def quartiles(values: list[float]) -> tuple[float, float]:
    values = sorted(values)
    return statistics.quantiles(values, n=4, method="inclusive")[0], statistics.quantiles(
        values, n=4, method="inclusive"
    )[2]


def machine() -> dict[str, str]:
    result = {
        "hostname": platform.node(),
        "os": platform.platform(),
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
    }
    try:
        result["cpu"] = subprocess.run(
            ["bash", "-lc", "lscpu | sed -n 's/^Model name:[[:space:]]*//p' | head -1"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        result["cpu"] = "non renseigné"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repetitions < 3:
        parser.error("--repetitions doit être au moins égal à 3")

    settings = Settings()
    records: list[dict[str, object]] = []
    with httpx.Client(base_url=args.url, timeout=180, trust_env=False) as client:
        client.get("/health").raise_for_status()
        benchmark_user = os.getenv("AUTH_BENCHMARK_USER", "user_a")
        benchmark_password = (settings.auth_password_user_b
                              if benchmark_user == "user_b"
                              else settings.auth_password_user_a)
        login = client.post("/auth/login", json={
            "username": benchmark_user,
            "password": benchmark_password,
        })
        login.raise_for_status()
        for question in QUESTIONS:
            client.post("/ask", json={"question": question, "top_k": 2}).raise_for_status()
            for repetition in range(1, args.repetitions + 1):
                started = time.perf_counter()
                response = client.post(
                    "/ask", json={"question": question, "top_k": 2}
                )
                elapsed_ms = (time.perf_counter() - started) * 1000
                response.raise_for_status()
                payload = response.json()
                records.append(
                    {
                        "question": question,
                        "repetition": repetition,
                        "http_total_ms": round(elapsed_ms, 2),
                        "service_total_ms": payload["latency_ms"]["total"],
                        "retrieval_ms": payload["latency_ms"]["retrieval"],
                        "generation_ms": payload["latency_ms"]["generation"],
                    }
                )

    values = [float(record["http_total_ms"]) for record in records]
    q1, q3 = quartiles(values)
    summary = {
        "metric": "HTTP POST /ask, temps aller-retour, échauffement exclu",
        "question_count": len(QUESTIONS),
        "repetitions_per_question": args.repetitions,
        "measured_executions": len(records),
        "median_ms": round(statistics.median(values), 2),
        "mean_ms": round(statistics.mean(values), 2),
        "min_ms": round(min(values), 2),
        "max_ms": round(max(values), 2),
        "q1_ms": round(q1, 2),
        "q3_ms": round(q3, 2),
        "iqr_ms": round(q3 - q1, 2),
    }
    output = {
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "endpoint": args.url + "/ask",
        "machine": machine(),
        "model": "qwen2.5:3b",
        "protocol": {
            "questions": QUESTIONS,
            "warmup_per_question": 1,
            "top_k": 2,
            "temperature": 0,
            "seed": 42,
        },
        "corpus": corpus_catalog(),
        "summary": summary,
        "measurements": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
