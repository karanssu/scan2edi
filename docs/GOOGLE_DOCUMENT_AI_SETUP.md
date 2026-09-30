# Google Cloud Document AI setup

Scan2EDI expects a **Custom Extractor** processor. Google Document AI supports custom entity extraction and online processing through the `ProcessDocument` API.

## 1. Create a processor

In Google Cloud Console:

1. Enable Document AI API.
2. Create a **Custom Extractor** processor.
3. Use the same region you place in `GCP_LOCATION` (for example `us`).
4. Deploy a processor version, or leave the processor's default version deployed.

## 2. Recommended schema

Create these top-level entities:

```text
vendor
invoice_number
invoice_date
reported_cases
reported_units
invoice_subtotal
invoice_discount
invoice_deposit
invoice_tax
invoice_total
line_item (repeated parent entity)
```

Create these nested fields under repeated `line_item`:

```text
vendor_sku
description
printed_upc
case_quantity
units_per_case
direct_quantity
price
base_amount
deposit
discount
sugar_tax
line_total
```

The extraction model should **read facts from the invoice**, not calculate final EDI fields. Scan2EDI performs the arithmetic.

## 3. Label examples

Use representative examples from each recurring vendor and include difficult cases:

- Red Bull table invoices
- Polar table invoices
- BJ's receipts with deposit and ECPN product coupon child lines
- Market Basket receipts
- Paul Henry Foods invoices including returns
- GL Distribution invoices
- Coca-Cola distributor invoices

For BJ's, label the product price as `base_amount`, the associated bottle/can deposit as `deposit`, and its product-specific coupon as `discount`. Do not label a receipt-wide promotion as a product discount.

## 4. Credentials

Create a service account and grant it the least-privilege **Document AI API User** role (`roles/documentai.apiUser`), which includes online document-processing permissions. Download its JSON key locally as:

```text
secrets/gcp-service-account.json
```

The `secrets/` directory is ignored by Git.

Set in `.env`:

```env
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us
DOCUMENT_AI_PROCESSOR_ID=your-processor-id
DOCUMENT_AI_PROCESSOR_VERSION_ID=
GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/gcp-service-account.json
```

If you specify `DOCUMENT_AI_PROCESSOR_VERSION_ID`, Scan2EDI calls that exact version. Otherwise it calls the processor and Google uses its deployed default version.
