# Nos principaux risques

Version du 23 octobre 2026. Nous réévaluerons ces risques au fil des essais.

| Risque | Ce que nous faisons ou prévoyons | Ce qu'il reste à vérifier |
| --- | --- | --- |
| WSL n'est pas accepté pour le rendu. | Confirmer les consignes avec le professeur et prévoir une machine virtuelle Ubuntu si nécessaire. | Acceptation du socle final. |
| La licence de Qwen2.5 3B ne répond pas à la consigne « open source ». | Signaler la licence `qwen-research` et prévoir un modèle sous licence permissive, par exemple Qwen2.5 7B Apache 2.0. | Choix final et mémoire nécessaire ; voir ADR 001. |
| La mémoire disponible est insuffisante. | Garder Qwen quantifié, E5 sur CPU et un seul processus API. Prévoir un essai sans GPU. | Pics de RAM/VRAM et temps de réponse. |
| Le modèle répond faux ou cite mal une source. | Tester séparément la recherche, les faits et les citations. Ajouter des questions hors corpus. | Qualité au-delà des premiers exemples. |
| Une question ou un document piégé détourne le modèle. | Préparer les attaques J3, puis les protections J4. | Aucune résistance aux attaques n'est encore validée. |
| Aurore fuit dans la réponse ou dans les extraits renvoyés. | Utiliser uniquement des données fictives ; ajouter ensuite identité et droits côté serveur, filtrage avant recherche et contrôle des sorties. | La référence actuelle a accès à tout le corpus. |
| Le code ou les modèles changent entre deux essais. | Garder les versions Python, la révision E5, l'empreinte Qwen et les réglages. | Reconstruction complète indépendante et sauvegarde des modèles. |
| L'index ne correspond plus aux documents. | Réingérer après modification, API arrêtée ; refuser les configurations d'index incompatibles. | Pas de mise à jour complète atomique ni d'ingestion concurrente. |
| La comparaison des protections est biaisée. | Fixer le protocole avant J4, garder les demandes légitimes, faire au moins 3 répétitions. | Critères de succès, faux positifs, médiane et dispersion. |
| Nos traces de séance sont incomplètes. | Tenir le journal commun, les carnets et les preuves en fin de séance. | Captures reportées à une prochaine séance et références Git à ajouter. |
