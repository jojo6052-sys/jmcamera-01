"""scoring knowledge rules

Revision ID: 0003_scoring_rules
Revises: 0002_competitor_research
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_scoring_rules"
down_revision = "0002_competitor_research"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "scoring_rules" not in existing_tables:
        op.create_table(
            "scoring_rules",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("match_type", sa.String(length=32), nullable=False),
            sa.Column("pattern", sa.String(length=255), nullable=False),
            sa.Column("score_adjustment", sa.Numeric(5, 2), nullable=False),
            sa.Column("max_bid_adjustment_pct", sa.Numeric(6, 2), nullable=False),
            sa.Column("risk_level", sa.String(length=32), nullable=False),
            sa.Column("reason", sa.Text()),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_scoring_rules_pattern", "scoring_rules", ["pattern"])
        op.create_index("ix_scoring_rules_enabled", "scoring_rules", ["enabled"])


def downgrade() -> None:
    op.drop_table("scoring_rules")
