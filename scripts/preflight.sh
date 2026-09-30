#!/bin/sh
set -eu

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed or not on PATH" >&2
  exit 1
fi

if [ ! -f .env ]; then
  echo "ERROR: .env is missing. Run: cp .env.example .env" >&2
  exit 1
fi

if [ ! -f secrets/gcp-service-account.json ]; then
  echo "ERROR: secrets/gcp-service-account.json is missing" >&2
  exit 1
fi

if ! grep -Eq '^GCP_PROJECT_ID=.+$' .env; then
  echo "ERROR: GCP_PROJECT_ID is empty in .env" >&2
  exit 1
fi

if ! grep -Eq '^DOCUMENT_AI_PROCESSOR_ID=.+$' .env; then
  echo "ERROR: DOCUMENT_AI_PROCESSOR_ID is empty in .env" >&2
  exit 1
fi

docker compose config >/dev/null
echo "Preflight OK"
