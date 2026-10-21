# Incident basecamp-payment : erreurs 5xx et latence élevée

Service: basecamp-payment
Gravité: critique, elevee
Detecteur: ml-detector

Symptoms: service basecamp-payment touché, `basecamp-payment__error_count` en forte hausse,
`basecamp-payment__latency_p95` en hausse, `basecamp-payment__success_count` en chute (écart-types négatif).
Logs ERROR et CRITICAL avec status 500, 502, 503 et duration_ms élevée (plusieurs secondes, timeout).
Paiements en échec, erreurs serveur 5xx, indisponibilité du service de paiement.

## Procedure

1. Confirmer l'incident : vérifier que les logs du service basecamp-payment contiennent des status 500, 502 ou 503
   et que error_count dépasse la normale de plusieurs écarts-types.
2. Identifier la cause : status 502 ou 503 avec duration_ms élevée indique une dépendance injoignable
   (passerelle de paiement, base de données) ; status 500 seul indique une erreur applicative.
3. Si la dépendance est injoignable : basculer le trafic sur la passerelle de secours, puis vérifier la base de données.
4. Si l'erreur est applicative et suit un déploiement récent : revenir à la version précédente (rollback).
5. Redémarrer le service basecamp-payment si les erreurs persistent après les étapes 3 ou 4.
6. Vérifier le retour à la normale : success_count remonte, error_count et latency_p95 redescendent,
   plus aucun log ERROR ou CRITICAL.
7. Si la gravité est critique et que le service n'est pas rétabli après 15 minutes : escalader à l'astreinte.
8. Répondre avec cette procédure telle quelle.
