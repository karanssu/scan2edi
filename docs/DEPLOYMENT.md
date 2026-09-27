# On-premise deployment

## Production goals

- Invoice images, extracted text, mappings, and exports stay on the local server.
- PostgreSQL is not published to the LAN.
- The OCR service is an internal application dependency.
- Cloud OCR/LLM APIs are not configured.
- Backups remain local and should be encrypted at rest.

## Before deployment

1. Use a dedicated Linux server account for Scan2EDI.
2. Enable full-disk encryption where operationally practical.
3. Set a strong PostgreSQL password in `.env` and update `DATABASE_URL` to match.
4. Pull/download all required Docker images and local AI model assets while online.
5. Install/download the local Ollama model.
6. Install or import the hardware-appropriate offline PaddleOCR-VL runtime.
7. Test with representative vendor invoices.
8. Block outbound internet access for the production workload/firewall after all local dependencies are available.

## Start

```bash
cp .env.example .env
# edit .env
make up
```

The API container runs `alembic upgrade head` before starting, so database schema changes are versioned.

## Backup

```bash
make backup
```

Encrypt and rotate the resulting database and invoice-file archives according to your retention requirements.

## Do not expose directly to the public internet

Scan2EDI is intended for an on-site/private network. If remote access is later required, put it behind authenticated VPN access and TLS rather than opening the application ports broadly.
