# Scan2EDI

Scan2EDI converts invoice images/PDFs into reviewed product lines and exports the fields your downstream system needs:

- `UPC Code`
- `Quantity`
- `Total Amount`

This repository is a clean rewrite. It uses **Google Cloud Document AI** for document extraction and keeps UPC mapping, quantity math, deposit/discount rules, validation, review, and export inside Scan2EDI.

## Architecture

```text
Invoice image / PDF
        |
        v
Google Document AI Custom Extractor
        |
        v
Normalized invoice JSON
        |
        v
Scan2EDI vendor rule engine
        |
        +--> UPC / pack mapping database
        |
        +--> deterministic quantity + amount calculations
        |
        +--> validation / review
        v
CSV export (and pluggable future EDI exporter)
```

No local PaddleOCR/Ollama service is used in this rewrite.

## Vendor rules included

- Red Bull: `QTY × UNITS`; use printed final `TOTAL`.
- Polar: case quantity × units/case; use printed final `EXT`/line total.
- BJ's: product amount + product deposit - product-specific coupon/discount. General receipt discounts are not allocated to products.
- Market Basket: direct item quantity; use final item/extended amount.
- Paul Henry Foods: direct quantity; negative quantity/amount is allowed for returns.
- GL Distribution: use mapped pack size when quantity is case/package quantity.
- Coca-Cola: prefer explicit final line total; otherwise base amount + product deposit - product-specific discount.
- Unknown vendors: conservative generic rules and review when quantity/UPC cannot be resolved.

## Important EDI note

The exact target EDI specification has not been supplied, so this repository **does not invent X12 810 or another standard**. It ships a production-ready CSV exporter containing exactly the current required fields and an `InvoiceExporter` interface where the final EDI format can be added once its specification is known. See `docs/ADD_EDI_FORMAT.md`.

## Quick start

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Create a Google Cloud Document AI Custom Extractor and put its project/location/processor IDs in `.env`. See `docs/GOOGLE_DOCUMENT_AI_SETUP.md` and `docs/DOCUMENT_AI_FIELD_GUIDE.md`.

3. Put the service-account key at:

```text
secrets/gcp-service-account.json
```

4. Start everything:

```bash
docker compose up -d --build
```

5. Verify:

```bash
./scripts/check.sh
```

Or manually:

```bash
docker compose ps -a
curl http://localhost:8000/api/health
```

6. Open:

```text
http://localhost:3000
```

## Before replacing your existing GitHub repository

Keep the old repository history on a backup branch first:

```bash
git checkout -b backup/local-ocr-version
git push origin backup/local-ocr-version
```

Then replace the working tree with this project, preserving only `.git/`, and commit the rewrite. Exact commands are in `docs/REPLACE_EXISTING_REPO.md`.
