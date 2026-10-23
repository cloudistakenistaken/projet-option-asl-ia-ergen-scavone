# Projet ASL-IA — Sécurité d'une application LLM

Halil ERGEN et Gabriel SCAVONE — INSA CVL, 2026–2027.
Sujet 10 : attaque et défense d'une application LLM.

Nous travaillons ensemble sur les choix techniques, le code, les tests et la
documentation. Notre première application répond à des questions sur une
entreprise fictive, Novalys, à partir de documents locaux.

## Comment ça marche

Nous utilisons un RAG : l'application cherche des passages dans nos documents,
puis les transmet au modèle pour qu'il rédige une réponse avec des sources.

1. **Ingestion** : Python lit et découpe les documents Markdown.
2. **Embeddings** : E5 transforme les passages et la question en listes de nombres.
3. **Recherche** : Chroma retrouve les passages dont le sens est le plus proche.
4. **Génération** : Ollama fait tourner Qwen localement et reçoit ces passages.
5. **Réponse** : FastAPI renvoie le texte et les extraits utilisés comme contexte.

Notre première version utilise Python 3.12, FastAPI, E5 multilingue small sur
CPU, Chroma sur disque et `qwen2.5:3b` sur Ollama. E5 produit des vecteurs de
384 dimensions ; nous gardons sa révision et les versions des bibliothèques.

**Cette version n'applique pas encore les droits documentaires.** Elle peut
consulter tout le corpus fictif, y compris Aurore. Ranger un fichier dans
`confidentiel` ne le protège pas. Le client ne peut pas fournir un champ `role`
pour se déclarer membre de la direction. Les protections seront ajoutées pour J4.

## Lancer le projet sur notre machine déjà préparée

Vérifier qu'Ollama est démarré, puis ouvrir un terminal à la racine du dépôt :

```bash
make ingest
make serve
```

Dans un deuxième terminal :

```bash
make demo
```

Nous attendons une réponse indiquant 25 jours de congés par an, un délai de
14 jours et la source `public/conges.md`. `make demo` vérifie les deux nombres
et la première source. Le format des citations est aussi vérifié dans les
tests d'intégration. Arrêter l'API avec `Ctrl+C` dans le premier terminal.

## Préparer une machine depuis le début

Nous visons Ubuntu 24.04, Linux x86_64 et Python 3.12. Le projet demande une
machine d'au moins 16 Go de RAM ; le GPU est facultatif. Notre développement
se fait sous WSL2 avec environ 7,6 Gio de RAM visibles et une RTX 4060 Laptop
avec 8 Go de mémoire graphique. Les pics de consommation restent à mesurer.

### 1. Installer les prérequis et récupérer le dépôt

```bash
sudo apt update
sudo apt install -y git make curl python3 python3-venv
git clone https://github.com/cloudistakenistaken/projet-option-asl-ia-ergen-scavone.git
cd projet-option-asl-ia-ergen-scavone
```

### 2. Préparer Ollama

Ollama 0.40.9 est déjà installé chez nous. Sur une machine vierge :

```bash
bash scripts/install_ollama.sh
```

Ce script utilise l'installateur officiel avec une version fixée. Il demande
Internet et peut demander `sudo`. Nous n'avons pas encore testé cette
installation sur une machine vierge.

Si le serveur n'est pas déjà lancé, le démarrer dans un terminal séparé :

```bash
ollama serve
```

Vérifier depuis un autre terminal :

```bash
curl --fail http://localhost:11434/api/tags
```

Si le port est déjà utilisé, vérifier le serveur existant avant d'en lancer un autre.

### 3. Préparer Python et les modèles

```bash
make bootstrap
make models
```

`make bootstrap` crée ou réutilise `.venv`, installe PyTorch CPU et les
dépendances, puis copie `.env.example` vers `.env` si ce fichier n'existe pas.
Le verrou [requirements.lock.txt](requirements.lock.txt) garde toutes les
versions installées. [requirements.txt](requirements.txt) liste nos dépendances
directes. Ce verrou vise notre environnement Linux ; ce n'est pas une image système.

`make models` prépare `qwen2.5:3b`, vérifie son empreinte (`digest`) et télécharge
E5 à la révision indiquée dans [.env.example](.env.example). Une empreinte sert
à repérer un changement de modèle derrière le même nom.
Les téléchargements initiaux demandent Internet. Ensuite, le RAG utilise le
cache local et l'API Ollama sur notre machine, sans API d'inférence externe
ni service payant. La télémétrie anonymisée de Chroma est désactivée.

### 4. Construire l'index, lancer et tester

```bash
make ingest
make test
make integration
make serve
```

Puis `make demo` dans un deuxième terminal. Les trois documents donnent
actuellement trois passages. L'index est conservé dans `.local/chroma`, hors Git.
Après modification du corpus, arrêter l'API et refaire `make ingest` : les
anciens passages sont retirés et les doublons évités. Un corpus vide provoque
une erreur sans supprimer l'index existant.

Cette procédure est écrite et les composants ont été testés. La destruction
et la reconstruction complètes sur une machine propre restent à réaliser pour J5.

## Poser une autre question

Quand `make serve` tourne, l'API est sur `http://127.0.0.1:8000` :

```bash
curl --fail http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Le VPN est-il obligatoire en télétravail ?","top_k":2}'
```

`top_k` règle le nombre de passages récupérés : 3 par défaut, de 1 à 5.
La réponse contient `answer`, `sources` et `latency_ms` (les durées en millisecondes).
Chaque source contient le chemin, la classification, l'extrait et son identifiant.
La liste correspond aux passages donnés au modèle ; elle ne prouve pas que
chaque phrase générée est correcte. Le modèle peut aussi citer une source incorrectement.

Nous utilisons un seul processus API pour ne pas charger plusieurs copies d'E5.
Le premier appel charge ce modèle et peut être plus lent.
`/health` indique seulement que FastAPI répond ; `/openapi.json` décrit l'API.
Nous n'avons pas activé d'interface Swagger dépendant d'un téléchargement externe.

## Comprendre les tests

| Commande | Ce que nous vérifions |
| --- | --- |
| `make test` | Stockage et recherche Chroma, réingestion, requêtes invalides et erreurs. E5 et les réponses Ollama sont simulés. |
| `make integration` | Vrai E5, trois recherches françaises, découpage et réponse du vrai Qwen via FastAPI en mémoire. |
| `make demo` | Parcours HTTP complet avec l'API lancée sur le port 8000. |

Pour vérifier le chargement depuis le cache sans accès au Hub Hugging Face :

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 make integration
```

Cela ne coupe pas le réseau de tout le système : Ollama est toujours joint
localement. Nos résultats, les erreurs rencontrées et les preuves sont dans
[docs/validation.md](docs/validation.md). Nous ne confondons pas un appel qui
réussit avec une réponse juste ou une application protégée.

## Configuration et problèmes courants

Les paramètres sont dans `.env`, les chemins relatifs partent de la racine du
dépôt. Redémarrer l'API après un changement. Si nous changeons E5, sa révision
ou le découpage, choisir un nouveau `COLLECTION_NAME` et refaire l'ingestion.
Pour changer Qwen, il faut aussi adapter la cible `models` du Makefile,
`OLLAMA_MODEL` et `OLLAMA_DIGEST`, puis rejouer les essais.

| Problème | Vérification à faire |
| --- | --- |
| Ollama ne répond pas | Tester `/api/tags`, puis vérifier le serveur ou le service existant. |
| HTTP 503 : index absent ou vide | Exécuter `make ingest`. |
| HTTP 503 : E5 indisponible | Vérifier le cache et exécuter `make models`. |
| HTTP 502 | Vérifier le modèle dans `ollama list`, les journaux et le délai `OLLAMA_TIMEOUT`. |
| Réponse fausse | Examiner les passages récupérés, puis ce que le modèle en a fait. |
| Mémoire insuffisante | Garder un seul processus API, fermer les applications lourdes et mesurer la mémoire utilisée. |
| Ollama inaccessible seulement dans le terminal isolé de l'assistant | Vérifier hors de cette isolation avant de conclure à une panne d'Ollama. |

Nous gardons `.env`, `.venv`, `.cache` et `.local` hors Git. Notre corpus ne
contient aucun vrai secret ni document confidentiel réel.

## Nos documents et les points encore ouverts

Nous préparons J1, prévu le 6 novembre 2026 à 18 h, et avons commencé le RAG
pour J2, prévu le 20 novembre à 18 h. Aucun de ces jalons n'est déclaré terminé.

- [Architecture et schéma](docs/architecture/architecture.md).
- [ADR 001 : exécution locale](docs/adr/001-execution-locale.md) et [ADR 002 : recherche](docs/adr/002-recherche-documentaire.md).
- [Risques](docs/risques.md), [calendrier](docs/plan-travail.md) et [checklist J1](docs/jalons/j1.md).
- [Journal commun](docs/journal/2026-10-23.md), [carnet Halil](docs/individuel/halil.md) et [carnet Gabriel](docs/individuel/gabriel.md).

Deux choix restent à confirmer avec le professeur : le socle final WSL ou VM,
et le générateur. La [fiche officielle de Qwen2.5 3B](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
indique la licence `qwen-research` ; nous ne considérons donc pas sa conformité
à l'exigence « open source » comme acquise. Une alternative est présentée dans l'ADR 001.

Nos présences, nos horaires, le journal commun et les deux carnets sont renseignés.
Nous avons reporté les captures à une prochaine séance ; les résultats des tests
et de la démonstration sont déjà conservés. Il reste à sauvegarder les changements
par un commit et un push. Nous créons les tags de jalon après vérification des critères.

## Repères pour l'oral

| Fichier | Son rôle |
| --- | --- |
| `app/config.py` | Charge les paramètres communs. |
| `app/embeddings.py` | Transforme les textes en vecteurs avec E5 sur CPU. |
| `app/ingest.py` | Lit et découpe les documents pour construire l'index. |
| `app/retrieval.py` | Enregistre les passages et retrouve les plus proches. |
| `app/generation.py` | Envoie la question et les passages à Ollama. |
| `app/api.py` | Reçoit les questions et renvoie les réponses avec les sources. |
| `app/security.py` | Contient le prompt et les droits prévus, encore non appliqués. |

## Documentations officielles utilisées

- [Ollama Linux](https://docs.ollama.com/linux), [génération](https://docs.ollama.com/api/generate) et [liste des modèles](https://docs.ollama.com/api/tags).
- [E5 multilingue small](https://huggingface.co/intfloat/multilingual-e5-small?inference_provider=hf-inference).
- [SentenceTransformer](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html).
- [Chroma : client](https://docs.trychroma.com/reference/python/client), [collections](https://docs.trychroma.com/reference/python/collection) et [configuration](https://docs.trychroma.com/docs/collections/configure).
- [FastAPI : tests](https://fastapi.tiangolo.com/tutorial/testing/) et [PyTorch CPU](https://pytorch.org/get-started/locally/).
