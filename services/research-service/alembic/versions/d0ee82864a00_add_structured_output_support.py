"""add_structured_output_support

Revision ID: d0ee82864a00
Revises: 05b988c45bf9
Create Date: 2025-10-18 12:21:03.247727

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0ee82864a00'
down_revision: Union[str, None] = '05b988c45bf9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add structured output fields to research_tasks
    op.add_column('research_tasks', sa.Column('structured_data', sa.JSON(), nullable=True))
    op.add_column('research_tasks', sa.Column('validation_status', sa.String(length=50), nullable=True))

    # Add research function support to research_templates
    op.add_column('research_templates', sa.Column('research_function', sa.String(length=50), nullable=True))


def downgrade() -> None:
    # Remove research function support from research_templates
    op.drop_column('research_templates', 'research_function')

    # Remove structured output fields from research_tasks
    op.drop_column('research_tasks', 'validation_status')
    op.drop_column('research_tasks', 'structured_data')
