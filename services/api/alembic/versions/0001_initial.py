"""initial schema

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("vendor", sa.String(length=255), nullable=True),
        sa.Column("invoice_number", sa.String(length=100), nullable=True),
        sa.Column("invoice_date", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("reported_cases", sa.Numeric(12, 3), nullable=True),
        sa.Column("reported_units", sa.Numeric(12, 3), nullable=True),
        sa.Column("invoice_subtotal", sa.Numeric(12, 2), nullable=True),
        sa.Column("invoice_discount", sa.Numeric(12, 2), nullable=True),
        sa.Column("invoice_deposit", sa.Numeric(12, 2), nullable=True),
        sa.Column("invoice_tax", sa.Numeric(12, 2), nullable=True),
        sa.Column("invoice_total", sa.Numeric(12, 2), nullable=True),
        sa.Column("raw_extraction", sa.JSON(), nullable=True),
        sa.Column("validation", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "invoice_lines",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("invoice_id", sa.String(length=36), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("vendor_sku", sa.String(length=120), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("printed_upc", sa.String(length=32), nullable=True),
        sa.Column("upc", sa.String(length=32), nullable=True),
        sa.Column("case_quantity", sa.Numeric(12, 3), nullable=True),
        sa.Column("units_per_case", sa.Integer(), nullable=True),
        sa.Column("direct_quantity", sa.Numeric(12, 3), nullable=True),
        sa.Column("total_quantity", sa.Numeric(12, 3), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=True),
        sa.Column("base_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("deposit", sa.Numeric(12, 2), nullable=True),
        sa.Column("discount", sa.Numeric(12, 2), nullable=True),
        sa.Column("sugar_tax", sa.Numeric(12, 2), nullable=True),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=True),
        sa.Column("export_total", sa.Numeric(12, 2), nullable=True),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("review_reasons", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_invoice_lines_invoice_id", "invoice_lines", ["invoice_id"])

    op.create_table(
        "vendor_product_mappings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("vendor_sku", sa.String(length=120), nullable=True),
        sa.Column("normalized_description", sa.String(length=500), nullable=False),
        sa.Column("upc", sa.String(length=32), nullable=False),
        sa.Column("units_per_case", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mapping_vendor_sku", "vendor_product_mappings", ["vendor_name", "vendor_sku"])
    op.create_index("ix_mapping_vendor_desc", "vendor_product_mappings", ["vendor_name", "normalized_description"])

    op.create_table(
        "mapping_history",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("mapping_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mapping_history_mapping_id", "mapping_history", ["mapping_id"])


def downgrade() -> None:
    op.drop_table("mapping_history")
    op.drop_table("vendor_product_mappings")
    op.drop_table("invoice_lines")
    op.drop_table("invoices")
