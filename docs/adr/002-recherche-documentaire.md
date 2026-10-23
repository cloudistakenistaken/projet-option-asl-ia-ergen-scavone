# ADR 002 — Retrouver les bons passages dans nos documents

Date : 23 octobre 2026. Statut : choix pour notre premier prototype.

## Notre besoin

Notre corpus, c'est-à-dire l'ensemble de nos documents, est petit et écrit en
français. Nous voulons retrouver les passages utiles à une question sans
appeler de service externe, puis garder le lien vers chaque source.

## Les solutions comparées

| Solution | Avantage | Limite |
| --- | --- | --- |
| E5 multilingue small avec Chroma | Recherche par le sens, français pris en charge, index conservé sur disque. | Un modèle doit être téléchargé et plusieurs bibliothèques sont nécessaires. |
| MiniLM multilingue avec NumPy | Modèle multilingue et index simple pour un petit corpus. | Nous devons gérer nous-mêmes le stockage et les informations sur les sources. |
| BM25 | Recherche par mots, légère et sans modèle à télécharger. | Les reformulations avec des mots différents peuvent être moins bien retrouvées. |

## Notre choix

Nous utilisons `intfloat/multilingual-e5-small` avec Sentence Transformers.
Ce modèle transforme un texte en un vecteur, c'est-à-dire une liste de 384
nombres. Nous comparons les vecteurs pour rechercher des passages proches du
sens de la question. Nous faisons ce calcul sur CPU pour laisser le GPU à Qwen.

La [fiche E5](https://huggingface.co/intfloat/multilingual-e5-small?inference_provider=hf-inference)
indique une limite de 512 tokens et demande les préfixes `passage:` pour les
documents et `query:` pour les questions. Nous respectons ces préfixes et
utilisons la même version d'E5 des deux côtés.

Nous découpons les documents en passages de 220 tokens avec un recouvrement
de 32 tokens : la fin d'un passage est reprise au début du suivant pour limiter
les coupures de contexte. Chaque passage garde un identifiant, le chemin du
document, son numéro et sa classification (`public` ou `confidentiel`).

Chroma enregistre les textes et les vecteurs dans `.local/chroma`. La recherche
utilise la distance cosinus, une mesure de proximité entre vecteurs, et renvoie
les trois passages les plus proches par défaut. Nous n'avons pas encore fixé
de seuil pour refuser un passage trop peu pertinent.

## Ce que cela implique

Nous devons télécharger E5 une première fois ; ensuite, le code le charge depuis
le cache local. La révision du modèle est fixée dans `.env.example`. Si nous
changeons de modèle, de révision ou de découpage, nous devons reconstruire un
index compatible. Une distance faible indique une proximité, pas la certitude
que le passage suffit à répondre.

Nous avons testé le classement sur trois questions françaises. Cela ne suffit
pas à évaluer tous les cas. Chroma ne protège pas non plus un document parce
qu'il est rangé dans `confidentiel` : les droits seront une étape séparée.

## Notre plan B

Si Chroma pose un problème d'installation, nous garderons E5 et évaluerons
un petit index NumPy avec les sources enregistrées en JSON. Si la mémoire
utilisée est trop importante, nous évaluerons un encodeur multilingue quantifié
avec ONNX. BM25 reste une solution de secours par mots-clés, à présenter comme
telle. Après tout changement, nous relancerons les tests. Ces plans B ne sont
pas encore validés.

Sources : [E5](https://huggingface.co/intfloat/multilingual-e5-small?inference_provider=hf-inference),
[SentenceTransformer](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html),
[Chroma](https://docs.trychroma.com/reference/python/client).
