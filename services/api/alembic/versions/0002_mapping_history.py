"""Add editable/deletable mapping history.

Revision ID: 0002_mapping_history
Revises: 0001_initial
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_mapping_history"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "vendor_product_mappings",
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.execute(
        "UPDATE vendor_product_mappings SET updated_at = created_at WHERE updated_at IS NULL"
    )
    op.alter_column("vendor_product_mappings", "updated_at", nullable=False)

    op.create_table(
        "mapping_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("mapping_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("old_upc", sa.String(length=32), nullable=True),
        sa.Column("new_upc", sa.String(length=32), nullable=True),
        sa.Column("old_units_per_case", sa.Integer(), nullable=True),
        sa.Column("new_units_per_case", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["mapping_id"], ["vendor_product_mappings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mapping_history_mapping_id", "mapping_history", ["mapping_id"])
    op.create_index("ix_mapping_history_action", "mapping_history", ["action"])


def downgrade() -> None:
    op.drop_index("ix_mapping_history_action", table_name="mapping_history")
    op.drop_index("ix_mapping_history_mapping_id", table_name="mapping_history")
    op.drop_table("mapping_history")
    op.drop_column("vendor_product_mappings", "updated_at")
