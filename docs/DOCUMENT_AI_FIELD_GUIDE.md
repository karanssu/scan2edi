# Document AI field labeling guide

Use these meanings consistently when configuring and labeling the Custom Extractor.

| Field | Meaning |
|---|---|
| `vendor` | Seller/distributor name, not the customer/store name. |
| `invoice_number` | Vendor invoice/receipt identifier. |
| `invoice_date` | Invoice/receipt date. |
| `reported_cases` | Vendor-printed invoice-level case count, when present. |
| `reported_units` | Vendor-printed invoice-level selling-unit count, when present. |
| `invoice_subtotal` | Invoice-level subtotal. |
| `invoice_discount` | **Only a general invoice/receipt-level promotion not assigned to a product.** Do not put product coupons here. |
| `invoice_deposit` | Invoice-level deposit summary. This is informational if product line totals already include deposits. |
| `invoice_tax` | Invoice-level tax. |
| `invoice_total` | Invoice amount used for reconciliation, before/after payment depending on the vendor's invoice semantics. Do not use a payment/tender value as the invoice total. |
| `line_item/vendor_sku` | Vendor item/product ID. This is not necessarily a UPC. |
| `line_item/description` | Printed product description. |
| `line_item/printed_upc` | UPC/barcode printed for that product. Leave blank when the printed code is not confidently a UPC. |
| `line_item/case_quantity` | Number of cases/packages whose contents must be expanded by `units_per_case`. |
| `line_item/units_per_case` | Number of selling units in each case/package when explicitly printed. |
| `line_item/direct_quantity` | Quantity already expressed in final selling units; do not multiply it by pack size. |
| `line_item/price` | Printed unit/case price used for audit. |
| `line_item/base_amount` | Product amount before a separately printed product deposit/coupon. Important for BJ's. |
| `line_item/deposit` | Deposit associated with this product line. |
| `line_item/discount` | Discount/coupon associated with this product line. Store it as a positive magnitude when possible; Scan2EDI subtracts it where required. |
| `line_item/sugar_tax` | Product-specific sugar tax when printed separately. |
| `line_item/line_total` | Explicit final product-line amount after product-specific adjustments when the vendor prints one. |

## Vendor-specific labeling

### Red Bull

- `QTY` -> `case_quantity`
- `UNITS` -> `units_per_case`
- UPC printed under the product -> `printed_upc`
- `TOTAL` -> `line_total`
- `DEP`, `DISC`, `SUGAR` stay as audit fields; do not recalculate `line_total` in Document AI.
- Bottom `DISCOUNT` and `DEPOSIT` are summary fields, not additional line adjustments.

### Polar

- Case/package count -> `case_quantity`
- Printed pack/selling-unit count -> `units_per_case`
- `EXT`/final extended amount -> `line_total`

### BJ's

A receipt product such as `MONSTER 24PK` is a package/case for Scan2EDI quantity purposes.

- If one package is purchased, label `case_quantity = 1` even when the receipt omits an explicit `1`.
- If the receipt prints a multiplier, use that package count as `case_quantity`.
- Do **not** infer `units_per_case` from the words `24PK` as the authoritative value; the saved product mapping should supply it unless the invoice explicitly provides the pack count in a trustworthy field.
- Product price -> `base_amount`
- Product `DEPOSIT` child line -> `deposit`
- `ECPN-...` product coupon -> `discount`
- Scan2EDI computes `base_amount + deposit - discount`.
- A receipt-wide promotion belongs in `invoice_discount`, not any product line.

### Market Basket

- Quantity already shown as purchased consumer items -> `direct_quantity`.
- Final product/extended amount -> `line_total`.

### Paul Henry Foods

- Quantity -> `direct_quantity` when it already represents selling units.
- Returns remain negative (`direct_quantity < 0`, `line_total < 0`).

### GL Distribution

- Package/case count -> `case_quantity`.
- If selling units per package are not printed, leave `units_per_case` blank; Scan2EDI resolves it from the saved product mapping.
- Printed total -> `line_total`.

### Coca-Cola

- Case/package count -> `case_quantity`.
- Explicit pack/units field -> `units_per_case`.
- Prefer a printed final/extended line amount as `line_total`.
- If there is no printed final amount but product-specific adjustments exist, use `base_amount`, `deposit`, and `discount` and let Scan2EDI calculate the export amount.
