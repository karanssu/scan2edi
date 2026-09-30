# Extraction contract

Document AI should return observed invoice facts. Scan2EDI converts them into this internal shape.

```json
{
  "vendor": "Red Bull Distribution Company Inc",
  "invoice_number": "2037919435",
  "invoice_date": "09/23/2026",
  "reported_cases": "14",
  "reported_units": "300",
  "invoice_total": "604.70",
  "lines": [
    {
      "vendor_sku": "RB2861",
      "description": "RED BULL 8.4OZ 4PK",
      "printed_upc": "611269108026",
      "case_quantity": "2",
      "units_per_case": "12",
      "direct_quantity": null,
      "price": "45.99",
      "base_amount": null,
      "deposit": "1.20",
      "discount": "7.50",
      "sugar_tax": "0.00",
      "line_total": "79.38"
    }
  ]
}
```

Do not ask the extractor to infer a missing pack size from general knowledge. Missing values remain missing and trigger review unless a saved product mapping resolves them.
