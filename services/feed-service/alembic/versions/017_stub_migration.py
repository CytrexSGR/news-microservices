"""Stub migration to fix revision chain

This is a stub migration created to fix a broken revision chain.
The database was at revision '017' but the file was missing.

Revision ID: 017
Revises: 20251226_015
Create Date: 2025-12-27 (retroactive fix)
"""
from alembic import op

# revision identifiers
revision = '017'
down_revision = '20251226_015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Stub - no operations needed
    pass


def downgrade() -> None:
    # Stub - no operations needed
    pass
