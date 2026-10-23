# ADR 001 — Faire tourner le LLM en local

Date : 23 octobre 2026. Statut : choix provisoire pour notre premier prototype.
Une ADR est une fiche qui explique une décision technique, les autres solutions
possibles et ce que nous ferons si le choix ne convient pas.

## Notre besoin

Nous devons utiliser un LLM local de 3 à 8 milliards de paramètres, avec Python,
sans service cloud ni API payante pour l'application. Notre machine dispose de
16 Go de RAM physiques et d'une RTX 4060 Laptop avec 8 Go de mémoire graphique.
Environ 7,6 Gio de RAM sont visibles dans WSL. Ollama et Qwen2.5 3B sont déjà installés.

## Les solutions comparées

| Solution | Avantage | Limite |
| --- | --- | --- |
| Ollama avec Qwen2.5 3B | Le modèle est déjà présent et l'API HTTP est simple à appeler depuis Python. | Nous devons conserver les versions et vérifier la licence du modèle. |
| llama.cpp avec son serveur llama-server | Nous choisissons directement le fichier du modèle et ses réglages. | L'installation et la préparation demandent plus de travail pour notre premier essai. |

## Notre choix

Pour démarrer, nous utilisons Ollama 0.40.9 et `qwen2.5:3b`. Le modèle compte
environ 3,1 milliards de paramètres. Sa quantification Q4_K_M réduit la place
prise par les poids du modèle. Nous appelons Ollama uniquement sur notre
machine, à l'adresse `http://localhost:11434`.

Nous gardons un contexte de 4096 tokens, une sortie de 384 tokens maximum,
une température de 0 et une graine (`seed`) de 42. Un token est une unité de
texte utilisée par le modèle ; ce n'est pas toujours un mot entier.
Ces réglages aident à comparer les essais, sans garantir des réponses identiques
sur toutes les machines. Nous conservons aussi l'empreinte du modèle (`digest`)
pour repérer un changement de version derrière le même nom.

Le choix du générateur final reste ouvert : la [fiche officielle du 3B](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
indique la licence `qwen-research`. Nous devons confirmer son acceptation face
à la consigne « open source ». Une alternative est
[Qwen2.5 7B Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct), sous Apache 2.0,
avec 7,61 milliards de paramètres. Il demandera plus de mémoire ; nous ne l'avons
pas encore téléchargé ni testé.

## Ce que cela implique

Ollama génère les réponses sur le GPU, tandis qu'E5 calcule les embeddings
sur le CPU. Nous gardons les versions, réglages et résultats dans les preuves.
Une réponse HTTP réussie montre que l'appel fonctionne ; nous devons ensuite
vérifier séparément les faits, les sources et la résistance aux attaques.

## Notre plan B

Si le GPU n'est pas disponible, nous essayerons le même modèle sur CPU, en
mesurant le temps de réponse. Si Ollama pose problème sur la machine finale,
nous évaluerons llama-server avec un fichier de modèle compatible, puis nous
adapterons l'appel Python et relancerons les tests.

Si la licence du 3B ne convient pas, nous évaluerons un modèle de la taille
imposée sous licence permissive, dont le 7B cité plus haut. Si WSL n'est pas
accepté pour le rendu, nous préparerons une machine virtuelle Ubuntu selon
les consignes du professeur. Ces solutions de secours restent à tester.

Sources : [installation Ollama](https://docs.ollama.com/linux),
[API de génération](https://docs.ollama.com/api/generate),
[llama.cpp](https://github.com/ggml-org/llama.cpp).
