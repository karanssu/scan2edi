#!/bin/sh
set -eu

docker compose ps -a
printf '\nAPI health:\n'
curl -fsS http://localhost:${API_PORT:-8000}/api/health
printf '\n\nOpen http://localhost:${WEB_PORT:-3000}\n'
