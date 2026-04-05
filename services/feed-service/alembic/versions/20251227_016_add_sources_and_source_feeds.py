"""Add sources and source_feeds tables for unified source management

This migration creates the new unified source management architecture:
- sources: Master entity for news sources (one per domain)
- source_feeds: Provider-specific feeds (RSS, MediaStack, etc.)

A Source represents a unique news outlet by domain with:
- Centralized assessment (credibility, bias, trust ratings)
- Centralized scraping config (from source_profiles)
- Scraping metrics

A SourceFeed represents a specific data source:
- RSS feeds (with url, etag, etc.)
- MediaStack sources (with provider_id)
- NewsAPI, GDELT, etc. (future)

Revision ID: 20251227_016
Revises: 017
Create Date: 2025-12-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '20251227_016'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # 1. Create sources table (Master entity)
    # =========================================================================
    op.create_table(
        'sources',
        # === IDENTITY ===
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('domain', sa.String(255), nullable=False, unique=True, index=True,
                  comment='Unique domain identifier (e.g., heise.de)'),
        sa.Column('canonical_name', sa.String(200), nullable=False,
                  comment='Display name (e.g., Heise Online)'),
        sa.Column('organization_name', sa.String(200), nullable=True,
                  comment='Parent organization (e.g., Heise Medien)'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('homepage_url', sa.String(500), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),

        # === STATUS ===
        sa.Column('status', sa.String(20), nullable=False, server_default='active',
                  comment='active, inactive, blocked'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),

        # === CATEGORIZATION ===
        sa.Column('category', sa.String(50), nullable=True,
                  comment='Primary category (general, business, tech, etc.)'),
        sa.Column('country', sa.String(5), nullable=True,
                  comment='ISO country code (de, us, gb)'),
        sa.Column('language', sa.String(5), nullable=True,
                  comment='ISO language code (de, en)'),

        # === ASSESSMENT (from Research Service) ===
        sa.Column('assessment_status', sa.String(50), nullable=True,
                  comment='pending, completed, failed'),
        sa.Column('assessment_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('credibility_tier', sa.String(20), nullable=True,
                  comment='tier_1, tier_2, tier_3'),
        sa.Column('reputation_score', sa.Integer, nullable=True,
                  comment='0-100 overall reputation score'),
        sa.Column('political_bias', sa.String(50), nullable=True,
                  comment='left, center-left, center, center-right, right'),
        sa.Column('founded_year', sa.Integer, nullable=True),
        sa.Column('organization_type', sa.String(100), nullable=True,
                  comment='news_agency, newspaper, broadcaster, etc.'),
        sa.Column('editorial_standards', JSONB, nullable=True,
                  comment='fact_checking_level, corrections_policy, etc.'),
        sa.Column('trust_ratings', JSONB, nullable=True,
                  comment='media_bias_fact_check, newsguard_score, etc.'),
        sa.Column('assessment_summary', sa.Text, nullable=True,
                  comment='Human-readable assessment summary'),

        # === SCRAPING CONFIG (migrated from source_profiles) ===
        sa.Column('scrape_method', sa.String(50), nullable=False, server_default='newspaper4k',
                  comment='newspaper4k, trafilatura, playwright, httpx'),
        sa.Column('fallback_methods', JSONB, nullable=True,
                  comment='Ordered list of fallback methods'),
        sa.Column('scrape_status', sa.String(50), nullable=False, server_default='unknown',
                  comment='working, degraded, blocked, unsupported, unknown'),
        sa.Column('paywall_type', sa.String(50), nullable=False, server_default='none',
                  comment='none, soft, hard, metered, registration'),
        sa.Column('paywall_bypass_method', sa.String(100), nullable=True,
                  comment='Method to bypass paywall if applicable'),
        sa.Column('rate_limit_per_minute', sa.Integer, nullable=False, server_default='10'),
        sa.Column('requires_stealth', sa.Boolean, nullable=False, server_default='false',
                  comment='Needs browser fingerprinting evasion'),
        sa.Column('requires_proxy', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('custom_headers', JSONB, nullable=True,
                  comment='Custom HTTP headers for requests'),

        # === SCRAPING METRICS ===
        sa.Column('scrape_success_rate', sa.Float, nullable=False, server_default='0.0',
                  comment='Rolling success rate 0.0-1.0'),
        sa.Column('scrape_avg_response_ms', sa.Integer, nullable=False, server_default='0'),
        sa.Column('scrape_total_attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('scrape_avg_word_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('scrape_avg_quality', sa.Float, nullable=False, server_default='0.0',
                  comment='Average content quality 0.0-1.0'),
        sa.Column('scrape_last_success', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scrape_last_failure', sa.DateTime(timezone=True), nullable=True),

        # === META ===
        sa.Column('notes', sa.Text, nullable=True,
                  comment='Internal notes about the source'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, onupdate=sa.func.now()),
    )

    # Additional indexes for sources
    op.create_index('idx_sources_status', 'sources', ['status'])
    op.create_index('idx_sources_category', 'sources', ['category'])
    op.create_index('idx_sources_country', 'sources', ['country'])
    op.create_index('idx_sources_credibility_tier', 'sources', ['credibility_tier'])
    op.create_index('idx_sources_is_active', 'sources', ['is_active'])

    # =========================================================================
    # 2. Create source_feeds table (Provider-specific feeds)
    # =========================================================================
    op.create_table(
        'source_feeds',
        # === IDENTITY ===
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_id', UUID(as_uuid=True), sa.ForeignKey('sources.id', ondelete='CASCADE'),
                  nullable=False, index=True),

        # === PROVIDER ===
        sa.Column('provider_type', sa.String(50), nullable=False, index=True,
                  comment='rss, mediastack, newsapi, gdelt, manual'),
        sa.Column('provider_id', sa.String(100), nullable=True,
                  comment='External provider ID (e.g., MediaStack source ID)'),
        sa.Column('channel_name', sa.String(100), nullable=True,
                  comment='Sub-channel name (e.g., Developer, Security for heise.de)'),

        # === RSS-SPECIFIC ===
        sa.Column('feed_url', sa.String(500), nullable=True, unique=True,
                  comment='RSS/Atom feed URL (only for provider_type=rss)'),
        sa.Column('etag', sa.String(100), nullable=True,
                  comment='HTTP ETag for conditional requests'),
        sa.Column('last_modified', sa.String(100), nullable=True,
                  comment='HTTP Last-Modified header'),
        sa.Column('fetch_interval', sa.Integer, nullable=False, server_default='60',
                  comment='Fetch interval in minutes'),

        # === STATUS ===
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('health_score', sa.Integer, nullable=False, server_default='100',
                  comment='Feed health score 0-100'),
        sa.Column('consecutive_failures', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_fetched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text, nullable=True),

        # === ANALYSIS CONFIG ===
        sa.Column('enable_analysis', sa.Boolean, nullable=False, server_default='true',
                  comment='Enable content analysis for this feed'),

        # === STATISTICS ===
        sa.Column('total_items', sa.Integer, nullable=False, server_default='0'),
        sa.Column('items_last_24h', sa.Integer, nullable=False, server_default='0'),

        # === META ===
        sa.Column('discovered_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(),
                  comment='When this feed was first discovered'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, onupdate=sa.func.now()),
    )

    # Unique constraint for source + provider combination
    op.create_unique_constraint(
        'uq_source_provider',
        'source_feeds',
        ['source_id', 'provider_type', 'provider_id']
    )

    # Additional indexes
    op.create_index('idx_source_feeds_provider_type', 'source_feeds', ['provider_type'])
    op.create_index('idx_source_feeds_is_active', 'source_feeds', ['is_active'])
    op.create_index('idx_source_feeds_health_score', 'source_feeds', ['health_score'])
    op.create_index('idx_source_feeds_last_fetched', 'source_feeds', ['last_fetched_at'])

    # =========================================================================
    # 3. Create source_assessment_history table
    # =========================================================================
    op.create_table(
        'source_assessment_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_id', UUID(as_uuid=True), sa.ForeignKey('sources.id', ondelete='CASCADE'),
                  nullable=False, index=True),

        # Assessment data
        sa.Column('assessment_status', sa.String(50), nullable=False),
        sa.Column('assessment_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('credibility_tier', sa.String(20), nullable=True),
        sa.Column('reputation_score', sa.Integer, nullable=True),
        sa.Column('political_bias', sa.String(50), nullable=True),
        sa.Column('founded_year', sa.Integer, nullable=True),
        sa.Column('organization_type', sa.String(100), nullable=True),
        sa.Column('editorial_standards', JSONB, nullable=True),
        sa.Column('trust_ratings', JSONB, nullable=True),
        sa.Column('assessment_summary', sa.Text, nullable=True),

        # Raw response for debugging
        sa.Column('raw_response', JSONB, nullable=True,
                  comment='Full raw response from research service'),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index('idx_source_assessment_history_date', 'source_assessment_history',
                    ['source_id', 'assessment_date'])

    # =========================================================================
    # 4. Add comments
    # =========================================================================
    op.execute("""
        COMMENT ON TABLE sources IS
        'Master entity for news sources. One entry per domain with centralized assessment and scraping config.'
    """)

    op.execute("""
        COMMENT ON TABLE source_feeds IS
        'Provider-specific feeds linked to sources. Supports RSS, MediaStack, NewsAPI, etc.'
    """)

    op.execute("""
        COMMENT ON TABLE source_assessment_history IS
        'Historical record of source assessments from research service.'
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('source_assessment_history')
    op.drop_table('source_feeds')
    op.drop_table('sources')
