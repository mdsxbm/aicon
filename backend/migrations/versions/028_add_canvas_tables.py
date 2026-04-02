"""add canvas tables

Revision ID: 028
Revises: 027
Create Date: 2026-04-01 21:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "028"
down_revision = "027"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "canvas_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_canvas_documents_user_id", "canvas_documents", ["user_id"])

    op.create_table(
        "canvas_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("position_x", sa.Float(), nullable=False),
        sa.Column("position_y", sa.Float(), nullable=False),
        sa.Column("width", sa.Float(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.Column("content_json", sa.JSON(), nullable=False),
        sa.Column("generation_config_json", sa.JSON(), nullable=False),
        sa.Column("last_run_status", sa.String(length=20), nullable=False),
        sa.Column("last_run_error", sa.Text(), nullable=True),
        sa.Column("last_output_json", sa.JSON(), nullable=False),
        sa.Column("z_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["canvas_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_canvas_items_document_id", "canvas_items", ["document_id"])
    op.create_index("ix_canvas_items_item_type", "canvas_items", ["item_type"])

    op.create_table(
        "canvas_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_handle", sa.String(length=20), nullable=False),
        sa.Column("target_handle", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["canvas_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_item_id"], ["canvas_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_item_id"], ["canvas_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_canvas_connections_document_id", "canvas_connections", ["document_id"])
    op.create_index("ix_canvas_connections_source_item_id", "canvas_connections", ["source_item_id"])
    op.create_index("ix_canvas_connections_target_item_id", "canvas_connections", ["target_item_id"])

    op.create_table(
        "canvas_item_generations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("generation_type", sa.String(length=20), nullable=False),
        sa.Column("request_payload_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("result_payload_json", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["item_id"], ["canvas_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["canvas_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_canvas_item_generations_item_id", "canvas_item_generations", ["item_id"])
    op.create_index("ix_canvas_item_generations_document_id", "canvas_item_generations", ["document_id"])
    op.create_index("ix_canvas_item_generations_user_id", "canvas_item_generations", ["user_id"])
    op.create_index("ix_canvas_item_generations_generation_type", "canvas_item_generations", ["generation_type"])


def downgrade():
    op.drop_index("ix_canvas_item_generations_generation_type", table_name="canvas_item_generations")
    op.drop_index("ix_canvas_item_generations_user_id", table_name="canvas_item_generations")
    op.drop_index("ix_canvas_item_generations_document_id", table_name="canvas_item_generations")
    op.drop_index("ix_canvas_item_generations_item_id", table_name="canvas_item_generations")
    op.drop_table("canvas_item_generations")

    op.drop_index("ix_canvas_connections_target_item_id", table_name="canvas_connections")
    op.drop_index("ix_canvas_connections_source_item_id", table_name="canvas_connections")
    op.drop_index("ix_canvas_connections_document_id", table_name="canvas_connections")
    op.drop_table("canvas_connections")

    op.drop_index("ix_canvas_items_item_type", table_name="canvas_items")
    op.drop_index("ix_canvas_items_document_id", table_name="canvas_items")
    op.drop_table("canvas_items")

    op.drop_index("ix_canvas_documents_user_id", table_name="canvas_documents")
    op.drop_table("canvas_documents")
