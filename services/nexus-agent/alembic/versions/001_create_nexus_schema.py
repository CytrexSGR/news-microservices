"""Create nexus schema and tables

Revision ID: 001_nexus_schema
Revises:
Create Date: 2025-12-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = '001_nexus_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create schema
    op.execute('CREATE SCHEMA IF NOT EXISTS nexus')

    # Conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_id', sa.String(100), nullable=False, index=True),
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('message_count', sa.Integer(), default=0),
        sa.Column('metadata', JSONB, default={}),
        schema='nexus'
    )

    # Messages table (embedding added via raw SQL for pgvector)
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('nexus.conversations.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),  # 'user' | 'assistant' | 'system'
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(50)),
        sa.Column('tool_calls', JSONB),
        sa.Column('tokens_used', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema='nexus'
    )
    # Add vector column via raw SQL
    op.execute('ALTER TABLE nexus.messages ADD COLUMN embedding vector(1536)')

    op.create_index('ix_nexus_messages_conversation_id', 'messages', ['conversation_id'], schema='nexus')
    op.create_index('ix_nexus_messages_created_at', 'messages', ['created_at'], schema='nexus')

    # Learned facts table
    op.create_table(
        'learned_facts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('fact_type', sa.String(50), nullable=False),  # 'preference' | 'entity' | 'relationship'
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source_message_id', sa.Integer(), sa.ForeignKey('nexus.messages.id')),
        sa.Column('confidence', sa.Float(), default=0.5),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_used', sa.DateTime(timezone=True)),
        sa.Column('use_count', sa.Integer(), default=0),
        schema='nexus'
    )
    # Add vector column via raw SQL
    op.execute('ALTER TABLE nexus.learned_facts ADD COLUMN embedding vector(1536)')

    # Plans table (persistent plan storage)
    op.create_table(
        'plans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_id', sa.String(100), nullable=False, index=True),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('goal', sa.Text(), nullable=False),
        sa.Column('steps', JSONB, nullable=False),
        sa.Column('status', sa.String(20), default='pending'),  # pending | confirmed | running | completed | cancelled
        sa.Column('current_step', sa.Integer(), default=0),
        sa.Column('step_results', JSONB, default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        schema='nexus'
    )

    # Reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('nexus.plans.id')),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content_markdown', sa.Text(), nullable=False),
        sa.Column('file_path', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema='nexus'
    )

    # Create indexes for vector similarity search
    op.execute('''
        CREATE INDEX ix_nexus_messages_embedding
        ON nexus.messages USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    ''')
    op.execute('''
        CREATE INDEX ix_nexus_learned_facts_embedding
        ON nexus.learned_facts USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    ''')


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS nexus.ix_nexus_learned_facts_embedding')
    op.execute('DROP INDEX IF EXISTS nexus.ix_nexus_messages_embedding')
    op.drop_table('reports', schema='nexus')
    op.drop_table('plans', schema='nexus')
    op.drop_table('learned_facts', schema='nexus')
    op.drop_table('messages', schema='nexus')
    op.drop_table('conversations', schema='nexus')
    op.execute('DROP SCHEMA IF EXISTS nexus')
