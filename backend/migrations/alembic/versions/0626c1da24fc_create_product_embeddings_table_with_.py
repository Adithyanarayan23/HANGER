"""Create product_embeddings table with pgvector

Revision ID: 0626c1da24fc
Revises: ca4ea65e3542
Create Date: 2026-11-15 23:13:05.022234

"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0626c1da24fc"
down_revision: Union[str, Sequence[str], None] = "ca4ea65e3542"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "product_embeddings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=False),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_embeddings_content_hash"), "product_embeddings", ["content_hash"], unique=False)
    op.create_index(
        "ix_product_embeddings_embedding_hnsw",
        "product_embeddings",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(op.f("ix_product_embeddings_id"), "product_embeddings", ["id"], unique=False)
    op.create_index(op.f("ix_product_embeddings_product_id"), "product_embeddings", ["product_id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_product_embeddings_product_id"), table_name="product_embeddings")
    op.drop_index(op.f("ix_product_embeddings_id"), table_name="product_embeddings")
    op.drop_index(
        "ix_product_embeddings_embedding_hnsw",
        table_name="product_embeddings",
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.drop_index(op.f("ix_product_embeddings_content_hash"), table_name="product_embeddings")
    op.drop_table("product_embeddings")
