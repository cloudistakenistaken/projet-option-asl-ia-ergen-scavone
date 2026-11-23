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


## 6 novembre 2026 — finalisation du cadrage J1

### Mon travail pendant la séance

J'ai travaillé avec Gabriel sur l'ensemble de cette séance. Nous avons tout
fait ensemble le 6 novembre, sans séparation des tâches. Nous avions oublié
de pousser les changements ; ils figurent dans le commit `88ce053` daté du
15 novembre 2026.

Nous avons relu les six attendus de J1 et complété la checklist avec les preuves.
Nous avons raccourci et clarifié l'architecture, conservé le schéma et préparé
le PDF de trois pages. Nous avons ajouté le script d'export, sa dépendance
ReportLab et l'exclusion de l'environnement documentaire dans Git.

Nous avons aussi précisé nos responsabilités partagées dans le document
d'équipe et mis à jour le README, le calendrier et la validation technique.
Nous avons vérifié le PDF et les liens locaux. Les tests applicatifs n'ont pas
été rejoués pendant cette revue documentaire.

### Ce que je retiens

Chaque attendu du jalon doit être relié à une preuve dans le dépôt. Le script
d'export permet de reconstruire le PDF depuis le Markdown. Je retiens aussi
qu'il faut distinguer la date du travail de celle du commit et penser à pousser
les changements pour que le suivi soit visible.

### Difficultés et suite

L'oubli du push a créé un décalage entre notre séance et l'historique Git.
La revue du contenu ne vaut pas validation du professeur. Nous devons encore
vérifier la clôture Git et le tag J1, confirmer le socle et la licence du modèle,
puis mesurer la mémoire et préparer la reconstruction complète pour J2.

Le [journal commun du 6 novembre](../journal/2026-11-06.md) détaille le travail
réalisé ensemble et [la checklist J1](../jalons/j1.md) regroupe les preuves.

## 17 novembre 2026 — automatisation de la reconstruction

### Mon travail pendant la séance

J'ai travaillé avec Gabriel sur l'ensemble de cette séance, avec l'aide d'un
assistant IA. Nous avons relu les instructions du README et décidé de réunir
les étapes d'installation, de téléchargement des modèles, d'indexation et de
tests dans un script unique.

Nous avons créé `scripts/setup.sh`. Le script prépare l'environnement Python,
installe Ollama si nécessaire, vérifie que son serveur répond, télécharge et
contrôle les modèles, reconstruit l'index Chroma et exécute les tests unitaires
et d'intégration. Nous avons également ajouté `make setup` dans le Makefile et
expliqué cette nouvelle procédure dans le README.

Nous avons ensuite amélioré le parcours utilisateur : après une préparation
réussie, le script affiche un exemple de commande `curl`, puis démarre l'API
avec `make serve`. Nous avons lancé l'API et vérifié une requête sur le VPN en
télétravail ; la source et la réponse obtenues étaient cohérentes. La sortie
JSON peut être rendue lisible avec `python3 -m json.tool`.

### Ce que je retiens

L'automatisation permet de limiter les oublis entre les dépendances, les modèles
et l'index. Le serveur Ollama peut être réutilisé s'il est déjà actif ou démarré
temporairement par le script, tandis que le serveur FastAPI reste lancé pour
permettre les requêtes de démonstration.

### Difficultés et suite

Nous avons validé la syntaxe du script et le format des modifications. Les tests
unitaires ont été lancés, mais n'ont pas produit de résultat dans le délai de
l'environnement ; ils devront être rejoués complètement dans des conditions
stables. Nous devrons aussi réaliser la reconstruction complète sur une machine
propre.

Le [journal commun du 17 novembre](../journal/2026-11-17.md) détaille notre
travail réalisé ensemble.

## 18 novembre 2026 — enrichissement des données et mesure J2

### Mon travail pendant la séance

J'ai travaillé avec Gabriel sur l'ensemble de cette séance. Nous avons réalisé
ensemble, sans séparation des tâches, les modifications du corpus et de la
documentation J2.

Nous avons enrichi les deux documents publics sur les congés et le télétravail
avec des informations fictives supplémentaires : report des jours, portail RH,
fermetures collectives, prévenance, jours de présence et authentification
multifacteur. Nous avons aussi complété le document confidentiel Aurore avec
son objectif, l'équipe pilote, la ventilation du budget et la durée de la phase
pilote. Nous avons réingéré les trois documents dans Chroma.

Nous avons ajouté un inventaire du corpus dans la preuve de latence : deux
documents publics et un document confidentiel, avec leurs titres, tailles,
nombres de mots, empreintes SHA-256 et thèmes. Nous avons enfin relancé la
mesure sur cinq questions fixes, avec cinq exécutions par question après un
échauffement, soit 25 exécutions mesurées.

### Ce que je retiens

Une mesure de temps de réponse doit conserver le jeu de questions, la
configuration du modèle, la machine et les données utilisées. Après
l'enrichissement, la médiane mesurée est de 1 877,51 ms et l'IQR de 2 162,23 ms.
La moyenne est influencée par des valeurs plus élevées ; la médiane et l'IQR
sont donc les indicateurs les plus lisibles pour cette série.

### Difficultés et suite

La première régénération de la preuve n'avait pas encore remplacé les anciennes
métadonnées du corpus. Nous avons vérifié le processus de benchmark, relancé la
mesure avec l'API locale, puis contrôlé le JSON, la syntaxe Python et le format
Git. Il reste à intégrer ces changements dans le commit et à déplacer le tag
J2 comme prévu.

Le [journal commun du 18 novembre](../journal/2026-11-18.md) détaille ce travail
réalisé ensemble, et la [preuve de latence](../preuves/2026-11-18/j2-latence.json)
conserve les données et les mesures.

## 22 novembre 2026 — interface web locale

### Mon travail pendant la séance

J'ai travaillé avec Gabriel sur l'ensemble de cette séance. Nous avons fait à
deux la conception, le code, les tests et la documentation de la page web.
L'utilisateur peut maintenant ouvrir l'adresse locale, poser sa question et
voir la réponse avec les passages utilisés, au lieu de préparer une commande
`curl` dans le terminal.

Nous avons prévu les états de chargement et d'erreur, un affichage responsive et
un rendu en texte brut avec `textContent`. Nous avons également mis à jour la
fiche J3 pour que le scénario LLM05 soit maintenant testable sur cette interface.

### Ce que je retiens

Le navigateur simplifie la démonstration, mais il ne change pas le rôle de
FastAPI : la page appelle toujours `/ask` et l'API conserve ses contrôles de
taille et ses erreurs explicites.

Le [journal commun du 22 novembre](../journal/2026-11-22.md) détaille notre
travail réalisé ensemble.
