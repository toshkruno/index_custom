#/bin/sh
set -e
git pull origin main
docker build -t tritel-index-base:15.0 -f BaseDockerfile .
docker build -t dennokorir/tritel-index:15.0 .
docker compose down
docker compose up -d
#docker push dennokorir/tritel-index:15.0
docker system prune -f
