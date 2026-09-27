#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../services/api"
export PYTHONPATH=.
export DATABASE_URL="${DATABASE_URL:-sqlite:///./scan2edi.db}"
alembic upgrade head
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
