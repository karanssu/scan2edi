"""Initial Scan2EDI schema.

Revision ID: 0001_initial
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_vendors_name", "vendors", ["name"])

    op.create_table(
        "products",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("upc", sa.String(length=32), nullable=False),
        sa.Column("canonical_name", sa.String(length=250), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("upc"),
    )
    op.create_index("ix_products_upc", "products", ["upc"])

    op.create_table(
        "invoices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("vendor_id", sa.String(length=36), nullable=False),
        sa.Column("invoice_number", sa.String(length=120), nullable=True),
        sa.Column("source_filename", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=True),
        sa.Column("invoice_level_discount", sa.Numeric(14, 2), nullable=True),
        sa.Column("invoice_total", sa.Numeric(14, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoices_vendor_id", "invoices", ["vendor_id"])
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"])

    op.create_table(
        "vendor_product_mappings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("vendor_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("vendor_sku", sa.String(length=100), nullable=True),
        sa.Column("vendor_description", sa.String(length=500), nullable=False),
        sa.Column("normalized_description", sa.String(length=500), nullable=False),
        sa.Column("units_per_case", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vendor_id", "normalized_description", "units_per_case", name="uq_vendor_description_pack"),
    )
    op.create_index("ix_vendor_product_mappings_vendor_id", "vendor_product_mappings", ["vendor_id"])
    op.create_index("ix_vendor_product_mappings_product_id", "vendor_product_mappings", ["product_id"])
    op.create_index("ix_vendor_product_mappings_vendor_sku", "vendor_product_mappings", ["vendor_sku"])
    op.create_index("ix_vendor_product_mappings_normalized_description", "vendor_product_mappings", ["normalized_description"])

    op.create_table(
        "invoice_lines",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("vendor_sku", sa.String(length=100), nullable=True),
        sa.Column("product_id", sa.String(length=36), nullable=True),
        sa.Column("case_quantity", sa.Numeric(12, 3), nullable=True),
        sa.Column("units_per_case", sa.Integer(), nullable=True),
        sa.Column("explicit_unit_quantity", sa.Numeric(12, 3), nullable=True),
        sa.Column("total_quantity", sa.Numeric(12, 3), nullable=True),
        sa.Column("case_price", sa.Numeric(14, 2), nullable=True),
        sa.Column("gross_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("product_discount", sa.Numeric(14, 2), nullable=True),
        sa.Column("explicit_net_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("export_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoice_lines_invoice_id", "invoice_lines", ["invoice_id"])
    op.create_index("ix_invoice_lines_product_id", "invoice_lines", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_invoice_lines_product_id", table_name="invoice_lines")
    op.drop_index("ix_invoice_lines_invoice_id", table_name="invoice_lines")
    op.drop_table("invoice_lines")
    op.drop_index("ix_vendor_product_mappings_normalized_description", table_name="vendor_product_mappings")
    op.drop_index("ix_vendor_product_mappings_vendor_sku", table_name="vendor_product_mappings")
    op.drop_index("ix_vendor_product_mappings_product_id", table_name="vendor_product_mappings")
    op.drop_index("ix_vendor_product_mappings_vendor_id", table_name="vendor_product_mappings")
    op.drop_table("vendor_product_mappings")
    op.drop_index("ix_invoices_invoice_number", table_name="invoices")
    op.drop_index("ix_invoices_vendor_id", table_name="invoices")
    op.drop_table("invoices")
    op.drop_index("ix_products_upc", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_vendors_name", table_name="vendors")
    op.drop_table("vendors")
