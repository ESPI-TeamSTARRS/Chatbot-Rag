# Incident basecamp-shop : chute du trafic (req_count) sans erreur

Service: basecamp-shop
Gravité: critique
Detecteur: ml-detector

Symptoms: service basecamp-shop touché, `basecamp-shop__req_count` en chute (écart-types négatif),
`basecamp-shop__denied_count` et `basecamp-shop__non_success_count` légèrement en baisse (écart-types négatif).
Les logs sont uniquement de niveau INFO, aucun log ERROR ou CRITICAL, aucun status 5xx.
Intensité élevée (plusieurs écarts-types) : le nombre de requêtes reçues par la boutique s'effondre,
le trafic n'arrive plus, volume de logs très faible, service silencieux, boutique inaccessible ou isolée,
panne de routage, de proxy, de load balancer ou de DNS, ou service arrêté sans erreur applicative.

## Procedure

1. Confirmer l'incident : vérifier que `basecamp-shop__req_count` est sous la normale de plusieurs écarts-types
   et que les logs de basecamp-shop sont rares et tous en INFO (pas d'erreur, donc pas un problème applicatif).

2. Vérifier que le service basecamp-shop est démarré et répond au health check ; le redémarrer s'il est arrêté.

3. Si le service répond mais ne reçoit plus de requêtes : vérifier en amont le proxy, le load balancer,
   la configuration DNS et les règles de routage ou de pare-feu vers basecamp-shop.

4. Vérifier si un déploiement ou un changement de configuration récent coïncide avec le début de la chute :
   si oui, revenir à la version précédente (rollback).

5. Vérifier le retour à la normale : req_count remonte vers sa valeur habituelle et le volume de logs reprend.

6. Si la gravité est critique et que le trafic n'est pas rétabli après 15 minutes : escalader à l'astreinte.

7. Répondre avec cette procédure telle quelle.
