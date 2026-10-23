# Carnet individuel — Halil ERGEN

## 23 octobre 2026 — 13 h 40–18 h 00

### Mon travail pendant la séance

J'ai travaillé avec Gabriel sur l'ensemble de la séance. Nous avons avancé
ensemble sur l'environnement, les choix techniques, le corpus, le code, les
tests et la documentation, avec l'aide d'un assistant IA.

Nous avons mis en place notre premier RAG local : lecture des documents,
recherche des passages utiles, génération d'une réponse avec Qwen et affichage
des sources. Nous avons créé les trois documents fictifs de Novalys et préparé
les scripts pour lancer le projet. Nous avons aussi rédigé et relu les documents
pour J1.

Les 35 tests ont réussi et nous avons vérifié la démonstration sur les congés :
25 jours par an, une demande 14 jours avant le départ et une source citée.

### Ce que je retiens

La recherche et la génération sont deux étapes différentes. E5 représente les
textes par des listes de nombres, Chroma retrouve les passages proches de la
question et Ollama fait tourner Qwen pour rédiger la réponse.
Une réponse peut être fausse même si l'appel fonctionne. Il faut donc vérifier
les faits et les sources. Le dossier `confidentiel` ne protège pas encore Aurore.

### Difficultés et suite

Nous avons rencontré des problèmes d'accès à Ollama depuis le terminal isolé,
de téléchargement d'E5 et de citations dans les réponses. Nous les avons traités
ensemble et avons simplifié le prompt pour obtenir une réponse correcte sur
notre exemple.

Je dois encore revoir ces composants pour pouvoir les expliquer à l'oral.
La suite sera de confirmer les choix avec le professeur, tester la reconstruction
complète, puis préparer les attaques et les protections.

Le [journal commun](../journal/2026-10-23.md) détaille notre séance et
[la validation technique](../validation.md) rassemble les résultats.
Les captures sont reportées à une prochaine séance. La référence du commit
sera ajoutée une fois le commit créé.
