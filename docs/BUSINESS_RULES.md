# Scan2EDI Business Rules

## Export columns

The initial export contains exactly:

1. UPC Code
2. Quantity
3. Total Amount

## Quantity

`Quantity` always means total individual units.

- 2 cases × 24 units/case = 48 quantity.
- If an invoice directly states individual unit quantity, use it.
- If pack size is missing, use the saved vendor-product mapping when available.
- If total units cannot be determined, require human review. Never guess.

## Total Amount

`Total Amount` means the final amount attributable to that specific product line.

Priority:
1. Explicit line net/final amount if printed.
2. Otherwise line gross amount minus product-specific discount.
3. Otherwise cases × price-per-case, minus product-specific discount.

A discount immediately associated with a product line is a product-specific discount and must reduce that product's total amount.

A general invoice-level discount (for example, a promo discount shown only in the invoice summary) must be recorded for audit but MUST NOT be allocated to products and MUST NOT reduce exported product totals.

## UPC mapping

The AI must never invent a UPC. Unknown products require manual mapping. The saved mapping is scoped to the vendor and should use vendor SKU first when available, then normalized description and pack size.
