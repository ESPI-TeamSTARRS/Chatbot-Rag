#!/usr/bin/env bash
# Deploie la version du chatbot decrite par deploy/manifest.json (image par digest, ecrite par la CI).
#   ./deploy.sh            pull + up -d
# Equivalent a `docker compose -f docker-compose-prod.yml up -d` avec APP_IMAGE pris dans le manifeste.
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

APP_IMAGE="$(jq -er '.services.app.image' deploy/manifest.json)"
[[ "$APP_IMAGE" =~ @sha256:[0-9a-f]{64}$ ]] || { echo "image sans digest : $APP_IMAGE" >&2; exit 1; }
export APP_IMAGE
echo "Deploiement de $(jq -r '.services.app.version' deploy/manifest.json) : $APP_IMAGE"

docker compose -f docker-compose-prod.yml pull
docker compose -f docker-compose-prod.yml up -d
