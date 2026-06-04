"""competitor research tables

Revision ID: 0002_competitor_research
Revises: 0001_initial
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_competitor_research"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "competitor_sellers" not in existing_tables:
        op.create_table(
            "competitor_sellers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("marketplace", sa.String(length=32), nullable=False),
            sa.Column("seller_username", sa.String(length=128), nullable=False),
            sa.Column("seller_url", sa.String(length=1024), nullable=False),
            sa.Column("fetch_status", sa.String(length=32), nullable=False),
            sa.Column("last_error", sa.Text()),
            sa.Column("active_count", sa.Integer(), nullable=False),
            sa.Column("sold_count", sa.Integer(), nullable=False),
            sa.Column("avg_active_price", sa.Numeric(12, 2)),
            sa.Column("avg_sold_price", sa.Numeric(12, 2)),
            sa.Column("last_analyzed_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("marketplace", "seller_username", name="uq_competitor_seller_marketplace_username"),
        )
        op.create_index("ix_competitor_sellers_marketplace", "competitor_sellers", ["marketplace"])
        op.create_index("ix_competitor_sellers_seller_username", "competitor_sellers", ["seller_username"])

    if "competitor_items" not in existing_tables:
        op.create_table(
            "competitor_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("seller_id", sa.Integer(), sa.ForeignKey("competitor_sellers.id", ondelete="CASCADE"), nullable=False),
            sa.Column("marketplace", sa.String(length=32), nullable=False),
            sa.Column("external_item_id", sa.String(length=128), nullable=False),
            sa.Column("title", sa.String(length=512), nullable=False),
            sa.Column("normalized_title", sa.String(length=512)),
            sa.Column("item_url", sa.String(length=1024), nullable=False),
            sa.Column("image_url", sa.String(length=1024)),
            sa.Column("price", sa.Numeric(12, 2)),
            sa.Column("currency", sa.String(length=8)),
            sa.Column("item_status", sa.String(length=32), nullable=False),
            sa.Column("sold_at", sa.DateTime(timezone=True)),
            sa.Column("source_url", sa.String(length=1024), nullable=False),
            sa.Column("raw", sa.JSON(), nullable=False),
            sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("seller_id", "external_item_id", "item_status", name="uq_competitor_item_seller_external_status"),
        )
        op.create_index("ix_competitor_items_seller_id", "competitor_items", ["seller_id"])
        op.create_index("ix_competitor_items_marketplace", "competitor_items", ["marketplace"])
        op.create_index("ix_competitor_items_external_item_id", "competitor_items", ["external_item_id"])
        op.create_index("ix_competitor_items_title", "competitor_items", ["title"])
        op.create_index("ix_competitor_items_normalized_title", "competitor_items", ["normalized_title"])
        op.create_index("ix_competitor_items_item_status", "competitor_items", ["item_status"])


def downgrade() -> None:
    op.drop_table("competitor_items")
    op.drop_table("competitor_sellers")
