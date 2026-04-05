"""Add topic_profiles table for semantic category matching.

Revision ID: 023
Revises: 022
Create Date: 2026-01-06

Topic profiles allow defining semantic categories (e.g., "finance", "conflict")
via descriptive text that gets embedded. Clusters are then matched to profiles
by cosine similarity, replacing hardcoded category assignments.
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "topic_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("description_text", sa.Text(), nullable=False),
        sa.Column("embedding_vec", Vector(1536), nullable=True),
        sa.Column("min_similarity", sa.Float(), server_default="0.40", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Index for vector similarity search
    op.execute(
        """
        CREATE INDEX idx_topic_profiles_embedding
        ON topic_profiles
        USING ivfflat (embedding_vec vector_cosine_ops)
        WITH (lists = 10)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_topic_profiles_embedding")
    op.drop_table("topic_profiles")
