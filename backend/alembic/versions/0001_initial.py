"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("products", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("es_number", sa.String(length=64)), sa.Column("title", sa.String(length=512), nullable=False), sa.Column("normalized_title", sa.String(length=512)), sa.Column("brand", sa.String(length=128)), sa.Column("model", sa.String(length=128)), sa.Column("category", sa.String(length=128)), sa.Column("mount", sa.String(length=128)), sa.Column("condition_rank", sa.String(length=32)), sa.Column("purchase_price_jpy", sa.Numeric(12,2)), sa.Column("sale_price_usd", sa.Numeric(12,2)), sa.Column("sale_price_jpy", sa.Numeric(12,2)), sa.Column("gross_profit_jpy", sa.Numeric(12,2)), sa.Column("final_profit_jpy", sa.Numeric(12,2)), sa.Column("profit_margin", sa.Numeric(5,2)), sa.Column("purchased_at", sa.DateTime(timezone=True)), sa.Column("listed_at", sa.DateTime(timezone=True)), sa.Column("sold_at", sa.DateTime(timezone=True)), sa.Column("days_to_sell", sa.Integer()), sa.Column("sales_channel", sa.String(length=64)), sa.Column("buyer_country", sa.String(length=64)), sa.Column("returned", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("complaint", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("repair_required", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("seller_id", sa.String(length=128)), sa.Column("source_platform", sa.String(length=64)), sa.Column("source_url", sa.String(length=1024)), sa.Column("notes", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))

    op.create_table("sellers", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("platform", sa.String(length=32), nullable=False), sa.Column("seller_id", sa.String(length=128), nullable=False, unique=True), sa.Column("seller_name", sa.String(length=255)), sa.Column("rating", sa.Numeric(5,2)), sa.Column("total_purchases", sa.Integer(), nullable=False, server_default="0"), sa.Column("successful_purchases", sa.Integer(), nullable=False, server_default="0"), sa.Column("failed_purchases", sa.Integer(), nullable=False, server_default="0"), sa.Column("average_profit_jpy", sa.Numeric(12,2)), sa.Column("return_rate", sa.Numeric(5,2)), sa.Column("repair_rate", sa.Numeric(5,2)), sa.Column("description_mismatch_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("is_blacklisted", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("is_whitelisted", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("risk_score", sa.Numeric(5,2)), sa.Column("notes", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))

    op.create_table("search_keywords", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("keyword", sa.String(length=255), nullable=False, unique=True), sa.Column("category", sa.String(length=128)), sa.Column("brand", sa.String(length=128)), sa.Column("model_group", sa.String(length=128)), sa.Column("priority", sa.Integer(), nullable=False, server_default="100"), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))

    op.create_table("yahoo_auction_candidates", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("auction_id", sa.String(length=128), nullable=False, unique=True), sa.Column("title", sa.String(length=512), nullable=False), sa.Column("normalized_title", sa.String(length=512)), sa.Column("url", sa.String(length=1024), nullable=False), sa.Column("current_price_jpy", sa.Numeric(12,2)), sa.Column("buyout_price_jpy", sa.Numeric(12,2)), sa.Column("bid_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("end_time", sa.DateTime(timezone=True)), sa.Column("seller_id", sa.String(length=128)), sa.Column("seller_rating", sa.Numeric(5,2)), sa.Column("description", sa.Text()), sa.Column("image_urls", sa.JSON(), nullable=False), sa.Column("search_keyword", sa.String(length=255)), sa.Column("status", sa.String(length=32), nullable=False, server_default="new"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))

    op.create_table("recommendation_scores", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("yahoo_auction_candidates.id", ondelete="CASCADE"), nullable=False), sa.Column("similarity_score", sa.Numeric(5,2)), sa.Column("expected_sale_price_usd", sa.Numeric(12,2)), sa.Column("expected_sale_price_jpy", sa.Numeric(12,2)), sa.Column("expected_profit_jpy", sa.Numeric(12,2)), sa.Column("expected_profit_margin", sa.Numeric(5,2)), sa.Column("recommended_max_bid_jpy", sa.Numeric(12,2)), sa.Column("seller_risk_score", sa.Numeric(5,2)), sa.Column("description_risk_score", sa.Numeric(5,2)), sa.Column("image_risk_score", sa.Numeric(5,2)), sa.Column("total_score", sa.Numeric(5,2)), sa.Column("rank", sa.String(length=8)), sa.Column("reason", sa.Text()), sa.Column("caution", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))

    op.create_table("feedbacks", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("yahoo_auction_candidates.id", ondelete="CASCADE"), nullable=False), sa.Column("user_decision", sa.String(length=32), nullable=False), sa.Column("purchased", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("actual_purchase_price_jpy", sa.Numeric(12,2)), sa.Column("actual_condition", sa.String(length=64)), sa.Column("inspection_result", sa.Text()), sa.Column("sold", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("actual_sale_price_jpy", sa.Numeric(12,2)), sa.Column("actual_profit_jpy", sa.Numeric(12,2)), sa.Column("returned", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("complaint", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("repair_required", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("ai_prediction_was_correct", sa.Boolean()), sa.Column("notes", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))


def downgrade() -> None:
    op.drop_table("feedbacks")
    op.drop_table("recommendation_scores")
    op.drop_table("yahoo_auction_candidates")
    op.drop_table("search_keywords")
    op.drop_table("sellers")
    op.drop_table("products")
