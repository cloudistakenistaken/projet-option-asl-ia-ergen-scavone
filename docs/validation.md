# Nos vérifications — 23 octobre 2026

Nous regroupons ici ce que nous avons réellement testé, les résultats et leurs
limites. Halil et Gabriel ont travaillé ensemble sur l'ensemble de la séance,
avec l'aide d'un assistant IA. Le [journal commun](journal/2026-10-23.md)
décrit le déroulement et indique nos horaires de séance.

## Notre point de départ

Le dépôt était sur `main`, liée à `origin/main`. Le README, le `.gitignore`
et la présentation de l'équipe étaient renseignés. La plupart des autres
fichiers étaient vides : nous n'avions pas encore de RAG dans le dépôt.

Python 3.12.3, `.venv`, Ollama 0.40.9 et `qwen2.5:3b` étaient présents.
Nous avons confirmé le modèle Q4_K_M de 3,1 milliards de paramètres par
l'API locale. Son empreinte est dans [ollama-tags.json](preuves/2026-10-23/ollama-tags.json).
La RTX 4060 Laptop était reconnue, avec 8 188 Mio de mémoire graphique.
Le système indiquait environ 7,61 Gio de RAM visibles dans WSL ; les 16 Go
physiques viennent de notre configuration connue, pas d'une mesure Windows
réalisée pendant ces essais.

## Ce qui a fonctionné

| Vérification | Résultat | Ce que cela montre |
| --- | --- | --- |
| Préparation Python et contrôle des dépendances | Installation réussie ; `pip check` sans conflit. | Les versions de `requirements.lock.txt` fonctionnent dans notre environnement. |
| Relance du script de préparation | Réussie sur le même `.venv`. | Le script peut être relancé ; ce n'est pas encore une reconstruction propre. |
| Chargement E5 | Vecteurs de 384 dimensions sur CPU. | Le modèle est téléchargé et utilisable localement. |
| `make ingest` | 3 documents et 3 passages enregistrés. | Le corpus fictif est indexé dans Chroma. |
| `make test` | 30 tests réussis. | Stockage, classement, réingestion et erreurs vérifiés avec des vecteurs et réponses simulés. |
| `make integration` | 5 tests réels réussis. | Vrai E5, trois recherches françaises, découpage et génération avec Qwen. |
| Intégration avec Hugging Face forcé hors ligne | 5 tests réussis. | Le cache E5 suffit ; Ollama est toujours appelé localement. |
| Essai HTTP avec l'API lancée | Réponse correcte pour les congés, avec une source. | Le premier parcours complet fonctionne sur cette question. |
| État Ollama après génération | Taille chargée entièrement en VRAM, contexte 4096. | Le modèle utilise la mémoire graphique lors de cet essai. |

Les recherches réelles ont placé le bon document en première position pour :

- Les jours de congés : `public/conges.md`.
- L'obligation du VPN : `public/teletravail.md`.
- Le budget d'Aurore : `confidentiel/aurore.md`.

Lors de la relecture, nous avons relancé les 35 tests ensemble : **35 réussites**
en 38,14 secondes. Le [compte rendu XML](preuves/2026-10-23/tests-relecture.xml)
conserve le résultat. `pip check` et la vérification syntaxique des scripts shell
ont également réussi. Les tests émettent un avertissement de dépréciation de
Starlette/AnyIO, sans échec.

Nous avons aussi rejoué `make demo` avec l'API lancée : la commande a réussi.
La [sortie complète](preuves/2026-10-23/demo-relecture.txt) conserve les valeurs
25 et 14, la validation par le responsable et la citation `[S1]`.
Cet appel a pris environ 11,17 secondes dans le service, contre environ
1,75 seconde pour l'appel précédent. Nous n'en tirons pas de conclusion de
performance : ces appels ne suivent pas encore un protocole de mesure fixé.

## Les problèmes que nous avons rencontrés

Le terminal isolé de l'assistant ne pouvait pas joindre Ollama et bloquait le
client de test FastAPI. Les essais hors de cette isolation ont fonctionné.
Nous distinguons donc cette restriction de l'environnement d'une panne du RAG.

Le téléchargement E5 a échoué avec le transfert Xet de Hugging Face. Le
transfert HTTP standard a fonctionné ; le code utilise ce mode par défaut.

Le premier prompt donnait les bonnes valeurs sur les congés, mais sans la
citation `[S1]` demandée. Nous avons ensuite essayé un exemple de forme :
le modèle a recopié « Information extraite. [S1] » au lieu de répondre.
Nous avons retiré cet exemple et simplifié le prompt. Les tests sur les faits
et les citations ont alors réussi. Nous conservons
[la réponse en échec](preuves/2026-10-23/demo-echec-exemple-prompt.json)
pour garder une trace de ce problème.

## Ce que prouvent les fichiers conservés

La [première réponse HTTP réussie](preuves/2026-10-23/demo.json) contient bien
25 jours, un délai de 14 jours et `[S1] public/conges.md`. Elle donne environ
1,75 seconde pour la recherche et la génération sur cet appel. Le chargement
initial d'E5 et les frais HTTP ne sont pas inclus dans ce temps interne.
Ce n'est pas une moyenne ni la mesure comparative prévue pour J4.
Le modèle répète aussi la question en début de réponse : la présentation peut
encore être améliorée.

Nous avons ajusté le prompt sur cette question connue. Sa réussite ne prouve
ni la qualité générale du modèle ni sa résistance aux attaques.

Nos preuves sont :

- [Tests rapides](preuves/2026-10-23/tests-rapides.xml), [tests d'intégration](preuves/2026-10-23/tests-integration.xml) et [nouvelle vérification des 35 tests](preuves/2026-10-23/tests-relecture.xml).
- [Réponse réussie](preuves/2026-10-23/demo.json), [nouveau make demo](preuves/2026-10-23/demo-relecture.txt) et [échec de prompt](preuves/2026-10-23/demo-echec-exemple-prompt.json).
- [Modèle disponible](preuves/2026-10-23/ollama-tags.json) et [modèle chargé](preuves/2026-10-23/ollama-ps.json).

## Ce que nous devons encore vérifier

Nous devons tester davantage de questions et les demandes hors corpus, mesurer
les pics de RAM/VRAM et reconstruire tout le projet sur un environnement propre.
L'installation d'Ollama sur une machine vierge et le téléchargement Qwen depuis
zéro n'ont pas encore été testés. Nos essais hors ligne concernent le chargement
E5, pas une observation de tous les échanges réseau du système.

Nous n'avons pas encore développé l'identité des utilisateurs, les droits
documentaires, les attaques et les protections. La comparaison avant/après,
avec au moins trois répétitions, médiane, dispersion, latence et faux positifs,
reste à préparer pour J4.

Nous devons confirmer le socle final et la licence du modèle avec le professeur.
Les preuves ne sont pas encore rattachées à un nouveau commit. Aucun commit,
push ou tag de jalon n'a été créé pour ces changements. Nous avançons vers
J1 et J2 sans les déclarer validés.
