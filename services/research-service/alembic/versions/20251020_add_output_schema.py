"""Add output_schema column to research_tasks

Revision ID: add_output_schema
Revises:
Create Date: 2025-10-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'add_output_schema'
down_revision = None  # Will be set based on existing migrations
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add output_schema column to store Pydantic schema for structured output
    op.add_column(
        'research_tasks',
        sa.Column('output_schema', JSONB, nullable=True)
    )

    # Add index for queries that filter by output_schema presence
    op.create_index(
        'ix_research_tasks_has_output_schema',
        'research_tasks',
        [sa.text('(output_schema IS NOT NULL)')],
        postgresql_where=sa.text('output_schema IS NOT NULL')
    )


def downgrade() -> None:
    op.drop_index('ix_research_tasks_has_output_schema', table_name='research_tasks')
    op.drop_column('research_tasks', 'output_schema')
