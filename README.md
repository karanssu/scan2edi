# Scan2EDI

Private, on-premise AI invoice processing and EDI/CSV generation.

## Current MVP

- Vendors and vendor-specific product mappings
- UPC mappings saved locally
- Total-unit quantity calculation (`cases × units per case`)
- Product-level discount handling
- General invoice-level discounts stored but ignored in product export
- Deterministic CSV export: `UPC Code, Quantity, Total Amount`
- Local OCR service boundary for PaddleOCR-VL
- Local schema extraction through Ollama structured output
- PostgreSQL production database / SQLite-friendly application code for tests
- Next.js review UI

## Architecture

```text
Browser -> Next.js -> FastAPI -> PostgreSQL
                        |
                        +-> Local OCR service -> PaddleOCR-VL -> Local Ollama
```

Invoice content is designed to remain on the on-premise network.

## Quick start

1. Copy environment config:

```bash
cp .env.example .env
```

2. Change `POSTGRES_PASSWORD` and `DATABASE_URL` in `.env`.

3. Start PostgreSQL/API/web first:

```bash
docker compose up --build postgres api web
```

4. Open:

- Web: http://localhost:3000
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/api/health

## OCR setup

PaddleOCR-VL has hardware-specific PaddlePaddle dependencies, so the base OCR image deliberately does not choose CPU vs NVIDIA for you. Follow `docs/OCR_SETUP.md`, then rebuild the OCR container.

Ollama must be available locally and the selected model must already be downloaded before the server is isolated from the internet.

## Tests

```bash
cd services/api
PYTHONPATH=. pytest -q
```

See `docs/BUSINESS_RULES.md` for the exact financial/export rules.

## Production notes

- Database schema is managed with Alembic migrations.
- The OCR service is not published to the LAN by the default Compose file.
- General invoice discounts never alter exported product totals.
- See `docs/DEPLOYMENT.md` before putting real confidential invoices through the system.
