# Business rules

## Export

Current export columns are exactly:

```text
UPC Code, Quantity, Total Amount
```

## Quantity

- When the invoice provides cases and units/case, `Quantity = cases × units/case`.
- When the invoice quantity is already individual selling units, use it directly.
- If the invoice only provides cases and the pack size exists in the saved mapping, use the mapping.
- Never guess an unknown pack size.

## Amount

- Prefer an explicit final product-line total when the vendor format provides one.
- Red Bull / Polar: use the printed final line amount and do not apply deposit/discount a second time.
- BJ's: `base product amount + product deposit - product-specific coupon/discount`.
- A general invoice/receipt-level promotion is ignored for product export amounts.
- Paul Henry returns may have negative quantity and negative amount.

## UPC

- A printed UPC is a suggestion until confirmed/saved as a mapping.
- Saved active mappings are reused for future invoices.
- Mappings can be edited or soft-deleted.
- Mapping history is auditable.
- Historical processed invoice lines keep the UPC snapshot they used.
