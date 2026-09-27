#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT/backups}"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cd "$ROOT"
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-scan2edi}" "${POSTGRES_DB:-scan2edi}" | gzip > "$BACKUP_DIR/db-$STAMP.sql.gz"
tar -czf "$BACKUP_DIR/files-$STAMP.tar.gz" storage/invoices storage/exports
printf 'Created %s and %s\n' "$BACKUP_DIR/db-$STAMP.sql.gz" "$BACKUP_DIR/files-$STAMP.tar.gz"
