# Adding the final EDI format

The exact receiving-system EDI specification has not yet been provided. Scan2EDI therefore does not guess an X12 transaction set or proprietary record layout.

The current reviewed output is exactly:

```text
UPC Code,Quantity,Total Amount
```

The export layer is isolated in `services/api/app/services/exporters.py`. Once the receiving system's specification is available, implement another `InvoiceExporter` using the already validated fields:

- `line.upc`
- `line.total_quantity`
- `line.export_total`

Do not repeat invoice parsing or financial calculations in the EDI formatter. The formatter should only serialize already-reviewed normalized values.

Before implementing it, obtain at least one of:

- an EDI implementation guide,
- sample accepted EDI files,
- a field/record specification from the receiving system,
- or the exact X12 transaction/version and partner requirements.
