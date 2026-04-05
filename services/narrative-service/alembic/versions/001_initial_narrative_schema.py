"""Initial narrative schema

Revision ID: 001
Revises:
Create Date: 2025-11-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Narrative Frames table - individual frame instances
    op.create_table(
        'narrative_frames',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('frame_type', sa.String(50), nullable=False, index=True),  # victim, hero, threat, etc.
        sa.Column('confidence', sa.Float, nullable=False),  # 0-1 confidence score
        sa.Column('text_excerpt', sa.Text, nullable=True),  # supporting text
        sa.Column('entities', postgresql.JSONB, nullable=True),  # related entities
        sa.Column('frame_metadata', postgresql.JSONB, nullable=True),  # additional metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )

    # Narrative Clusters table - grouped narrative frames
    op.create_table(
        'narrative_clusters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('dominant_frame', sa.String(50), nullable=False),  # primary frame type
        sa.Column('frame_count', sa.Integer, default=0),
        sa.Column('bias_score', sa.Float, nullable=True),  # -1 (left) to +1 (right)
        sa.Column('keywords', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('entities', postgresql.JSONB, nullable=True),
        sa.Column('sentiment', sa.Float, nullable=True),  # -1 (negative) to +1 (positive)
        sa.Column('perspectives', postgresql.JSONB, nullable=True),  # different viewpoints
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )

    # Bias Analysis table - source/article bias scores
    op.create_table(
        'bias_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('source', sa.String(255), nullable=True),
        sa.Column('bias_score', sa.Float, nullable=False),  # -1 (left) to +1 (right)
        sa.Column('bias_label', sa.String(20), nullable=True),  # left, center-left, center, center-right, right
        sa.Column('sentiment', sa.Float, nullable=False),  # -1 (negative) to +1 (positive)
        sa.Column('language_indicators', postgresql.JSONB, nullable=True),  # emotional words, loaded language
        sa.Column('perspective', sa.String(50), nullable=True),  # pro, con, neutral
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )

    # Add foreign key to narrative_frames
    op.create_table(
        'narrative_frame_clusters',
        sa.Column('frame_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_frames.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('cluster_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_clusters.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Indexes for performance
    op.create_index('idx_narrative_frames_event_id', 'narrative_frames', ['event_id'])
    op.create_index('idx_narrative_frames_frame_type', 'narrative_frames', ['frame_type'])
    op.create_index('idx_narrative_frames_created_at', 'narrative_frames', ['created_at'])
    op.create_index('idx_narrative_clusters_dominant_frame', 'narrative_clusters', ['dominant_frame'])
    op.create_index('idx_bias_analysis_event_id', 'bias_analysis', ['event_id'])
    op.create_index('idx_bias_analysis_bias_label', 'bias_analysis', ['bias_label'])


def downgrade():
    op.drop_table('narrative_frame_clusters')
    op.drop_table('bias_analysis')
    op.drop_table('narrative_clusters')
    op.drop_table('narrative_frames')
