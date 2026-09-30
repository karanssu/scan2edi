#!/bin/sh
set -eu
./scripts/preflight.sh
docker compose up -d --build
docker compose ps -a
