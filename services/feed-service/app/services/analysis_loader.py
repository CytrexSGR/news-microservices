"""
Analysis data loader for feed items - UNIFIED TABLE VERSION.
Reads directly from public.article_analysis (unified table) for 30-40x performance improvement.

✅ MIGRATION COMPLETE (2025-11-08)
==========================================
This module reads from the UNIFIED table (single source of truth):
    public.article_analysis (22,021+ rows, actively written by analysis-consumer)

LEGACY table deprecated and renamed (2025-11-08):
    content_analysis_v2.pipeline_executions_deprecated (22,055 rows, READ-ONLY)
    - No new writes since 2025-11-08 18:10 UTC
    - Scheduled for deletion: 2025-12-08 (30 days retention)
    - Exists only for audit/debugging purposes

PERFORMANCE IMPROVEMENTS:
- Sequential requests: 150-200ms → 4-5ms (30-40x faster) ✅
- Concurrent requests: 175ms → 93ms avg (2x faster) ✅
- Database query execution: 0.145ms
- API hops reduced: 2 (proxy) → 1 (direct DB)

BACKWARD COMPATIBILITY:
- Response format unchanged (frontend expects legacy structure)
- Transformation applied: unified schema → legacy format
- Frontend displays correctly (scores + deep analyses visible)

MIGRATION DETAILS:
- Migrated: 3,698 analyses from legacy table
- Success rate: 99.83% (12 orphaned records filtered)
- Data backup: /tmp/migration_baseline/news_mcp_pre_migration_20251031_173904.dump
- Performance summary: /tmp/migration_baseline/performance_summary.md

Related Files:
- services/feed-service/app/workers/analysis_consumer.py (writes to unified table)
- tests/migration/backfill_unified_table.sql (migration script)

Last Updated: 2025-10-31 Evening
See: POSTMORTEMS.md Incident #8 for full migration details
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


def _empty_analysis_result() -> Dict[str, Any]:
    """Return empty analysis result structure."""
    return {
        "pipeline_execution": None,
        "v3_analysis": None,
    }


def _transform_v3_tier0(tier0_data: Dict[str, Any], metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Transform V3 tier0 (triage) data from database format to frontend format.

    Database stores: priority_score (snake_case)
    Frontend expects: PriorityScore (PascalCase) + cost_usd, tokens_used, model

    This ensures compatibility with ArticleV3AnalysisCard.tsx component.
    """
    if not tier0_data:
        return tier0_data

    # Create transformed copy
    transformed = tier0_data.copy()

    # Rename priority_score → PriorityScore for frontend compatibility
    if "priority_score" in transformed and "PriorityScore" not in transformed:
        transformed["PriorityScore"] = transformed["priority_score"]

    # Ensure cost/token/model fields exist (required by frontend TypeScript types)
    # Use tier0 data if available (new events), otherwise fall back to metrics (old events)
    if "cost_usd" not in transformed and metrics:
        transformed["cost_usd"] = metrics.get("tier0_cost_usd", 0.0)
    if "tokens_used" not in transformed:
        transformed["tokens_used"] = transformed.get("tokens_used", 0)
    if "model" not in transformed:
        transformed["model"] = transformed.get("model", "unknown")

    return transformed


def _transform_to_legacy_format(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform unified table row to legacy format for backward compatibility.

    Frontend expects (based on ArticleV2AnalysisCard.tsx):
    - triage_decision.PriorityScore (note: capital P!)
    - tier1_summary, tier2_summary, tier3_summary (not tier1_results!)

    Unified table has: triage_results, tier1_results, tier2_results, tier3_results
    """
    # Get tier results
    triage = row.get("triage_results") or {}
    tier1 = row.get("tier1_results") or {}
    tier2 = row.get("tier2_results") or {}
    tier3 = row.get("tier3_results") or {}
    metrics = row.get("metrics") or {}

    # Normalize triage_decision keys for frontend compatibility
    # Frontend expects PriorityScore (capital P), but DB has priority_score
    if triage and "priority_score" in triage and "PriorityScore" not in triage:
        triage["PriorityScore"] = triage["priority_score"]

    # Extract metrics for frontend compatibility (v2_analysis expects these at top level)
    # DB stores: metrics.total_cost_usd, metrics.total_time_ms
    # Frontend expects: total_cost, execution_time_seconds
    total_cost = metrics.get("total_cost_usd")
    total_time_ms = metrics.get("total_time_ms")
    execution_time_seconds = (total_time_ms / 1000.0) if total_time_ms is not None else None

    # Legacy format response
    return {
        "article_id": str(row["article_id"]),
        "pipeline_version": row.get("pipeline_version"),
        "success": row.get("success", False),

        # Triage (direct mapping)
        "triage_decision": triage,

        # Frontend expects tierX_summary, not tierX_results!
        "tier1_summary": tier1,
        "tier2_summary": tier2,
        "tier3_summary": tier3,

        # Metadata
        "relevance_score": float(row["relevance_score"]) if row.get("relevance_score") else None,
        "score_breakdown": row.get("score_breakdown"),
        "metrics": metrics,  # Keep original metrics for backward compatibility

        # Frontend v2_analysis compatibility: extract cost and time to top level
        "total_cost": total_cost,
        "execution_time_seconds": execution_time_seconds,

        "error_message": row.get("error_message"),
        "failed_agents": row.get("failed_agents", []),
        "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
        "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
    }


async def load_analysis_data(
    db,  # SQLAlchemy AsyncSession
    item_id: UUID
) -> Dict[str, Any]:
    """
    Load analysis data for a feed item from unified table.

    Returns a dict with both V2 (legacy) and V3 (active) analysis data.
    Returns empty structure if no analysis exists.

    Performance: ~50-80ms (vs 150-200ms with proxy)
    """
    try:
        # Load V2 analysis (pipeline_version = '2.0')
        v2_query = text("""
            SELECT
                article_id,
                pipeline_version,
                success,
                triage_results,
                tier1_results,
                tier2_results,
                tier3_results,
                relevance_score,
                score_breakdown,
                metrics,
                error_message,
                failed_agents,
                created_at,
                updated_at
            FROM public.article_analysis
            WHERE article_id = :article_id AND pipeline_version = '2.0'
        """)

        v2_result = await db.execute(v2_query, {"article_id": str(item_id)})
        v2_row = v2_result.fetchone()

        # Load V3 analysis (pipeline_version = '3.0')
        v3_query = text("""
            SELECT
                article_id,
                pipeline_version,
                success,
                triage_results,
                tier1_results,
                tier2_results,
                tier3_results,
                relevance_score,
                score_breakdown,
                metrics,
                error_message,
                failed_agents,
                created_at,
                updated_at
            FROM public.article_analysis
            WHERE article_id = :article_id AND pipeline_version = '3.0'
        """)

        v3_result = await db.execute(v3_query, {"article_id": str(item_id)})
        v3_row = v3_result.fetchone()

        # Build response with both V2 and V3 data
        response = {}

        # V2 data (legacy format)
        if v2_row:
            v2_dict = dict(v2_row._mapping)
            legacy_data = _transform_to_legacy_format(v2_dict)
            response["pipeline_execution"] = legacy_data
        else:
            response["pipeline_execution"] = None

        # V3 data (transform tier0 for frontend compatibility)
        if v3_row:
            v3_dict = dict(v3_row._mapping)

            # If analysis failed (success=False) or tier0 is missing, return null
            # This prevents frontend errors when trying to render incomplete data
            if not v3_dict.get("success", False) or not v3_dict.get("triage_results"):
                response["v3_analysis"] = None
            else:
                # Transform tier0 (priority_score → PriorityScore + add cost/token data)
                tier0_transformed = _transform_v3_tier0(
                    v3_dict.get("triage_results"),
                    v3_dict.get("metrics")
                )

                # Transform tier1 (scores: flat → nested object for frontend compatibility)
                # CRITICAL: Frontend expects scores in nested 'scores' object!
                # Database stores: { impact_score: 7.0, credibility_score: 8.0, urgency_score: 4.0 }
                # Frontend needs: { scores: { impact_score: 7.0, ... } }
                # See: POSTMORTEMS.md Incident #23 (2025-11-23)
                tier1_raw = v3_dict.get("tier1_results")
                tier1_transformed = None
                if tier1_raw:
                    # Extract scores from top-level into nested 'scores' object
                    tier1_transformed = {
                        "entities": tier1_raw.get("entities", []),
                        "relations": tier1_raw.get("relations", []),
                        "topics": tier1_raw.get("topics", []),
                        "scores": {  # ← IMPORTANT: Scores must be nested here
                            "impact_score": tier1_raw.get("impact_score"),
                            "credibility_score": tier1_raw.get("credibility_score"),
                            "urgency_score": tier1_raw.get("urgency_score"),
                        },
                        "tokens_used": tier1_raw.get("tokens_used"),
                        "cost_usd": tier1_raw.get("cost_usd"),
                        "model": tier1_raw.get("model"),
                    }

                response["v3_analysis"] = {
                    "article_id": str(v3_dict["article_id"]),
                    "pipeline_version": v3_dict.get("pipeline_version"),
                    "success": v3_dict.get("success", False),
                    "tier0": tier0_transformed,  # Transformed for frontend
                    "tier1": tier1_transformed,  # Transformed (scores nested)
                    "tier2": v3_dict.get("tier2_results"),
                    "tier3": v3_dict.get("tier3_results"),
                    "relevance_score": float(v3_dict["relevance_score"]) if v3_dict.get("relevance_score") else None,
                    "score_breakdown": v3_dict.get("score_breakdown"),
                    "metrics": v3_dict.get("metrics"),
                    "error_message": v3_dict.get("error_message"),
                    "failed_agents": v3_dict.get("failed_agents", []),
                    "created_at": v3_dict.get("created_at").isoformat() if v3_dict.get("created_at") else None,
                    "updated_at": v3_dict.get("updated_at").isoformat() if v3_dict.get("updated_at") else None,
                }
        else:
            response["v3_analysis"] = None

        return response

    except Exception as e:
        logger.error(f"Failed to load analysis for {item_id}: {e}")
        return _empty_analysis_result()


async def load_analysis_data_batch(
    db,  # SQLAlchemy AsyncSession
    item_ids: List[UUID]
) -> Dict[UUID, Dict[str, Any]]:
    """
    Load analysis data for multiple feed items from unified table.

    Returns both V2 (legacy) and V3 (active) analysis data for each item.
    Uses batch query with IN clause for efficiency.

    Performance: ~300-400ms for 20 items (vs 800-1000ms with proxy)
    """
    if not item_ids:
        return {}

    try:
        # Convert UUIDs to strings for query
        item_ids_str = [str(item_id) for item_id in item_ids]

        # Load both V2 and V3 analyses in one query
        query = text("""
            SELECT
                article_id,
                pipeline_version,
                success,
                triage_results,
                tier1_results,
                tier2_results,
                tier3_results,
                relevance_score,
                score_breakdown,
                metrics,
                error_message,
                failed_agents,
                created_at,
                updated_at
            FROM public.article_analysis
            WHERE article_id = ANY(:article_ids)
              AND pipeline_version IN ('2.0', '3.0')
        """)

        result = await db.execute(query, {"article_ids": item_ids_str})
        rows = result.fetchall()

        # Build results dict - separate V2 and V3 by pipeline_version
        results = {}
        v2_data = {}
        v3_data = {}

        for row in rows:
            row_dict = dict(row._mapping)
            article_id = row_dict["article_id"]
            pipeline_version = row_dict.get("pipeline_version")

            if pipeline_version == "2.0":
                # Transform to legacy format for V2
                v2_data[article_id] = _transform_to_legacy_format(row_dict)
            elif pipeline_version == "3.0":
                # Only include V3 data if analysis succeeded and tier0 exists
                # Failed analyses are excluded (v3_analysis = null in response)
                if row_dict.get("success", False) and row_dict.get("triage_results"):
                    # Transform V3 data for frontend compatibility
                    tier0_transformed = _transform_v3_tier0(
                        row_dict.get("triage_results"),
                        row_dict.get("metrics")
                    )

                    # Transform tier1 (scores: flat → nested object for frontend compatibility)
                    # Frontend expects nested 'scores' object (see POSTMORTEMS.md Incident #23)
                    tier1_raw = row_dict.get("tier1_results")
                    tier1_transformed = None
                    if tier1_raw:
                        tier1_transformed = {
                            "entities": tier1_raw.get("entities", []),
                            "relations": tier1_raw.get("relations", []),
                            "topics": tier1_raw.get("topics", []),
                            "scores": {  # ← IMPORTANT: Must be nested
                                "impact_score": tier1_raw.get("impact_score"),
                                "credibility_score": tier1_raw.get("credibility_score"),
                                "urgency_score": tier1_raw.get("urgency_score"),
                            },
                            "tokens_used": tier1_raw.get("tokens_used"),
                            "cost_usd": tier1_raw.get("cost_usd"),
                            "model": tier1_raw.get("model"),
                        }

                    v3_data[article_id] = {
                        "article_id": str(row_dict["article_id"]),
                        "pipeline_version": row_dict.get("pipeline_version"),
                        "success": row_dict.get("success", False),
                        "tier0": tier0_transformed,  # Transformed for frontend
                        "tier1": tier1_transformed,  # Transformed (scores nested)
                        "tier2": row_dict.get("tier2_results"),
                        "tier3": row_dict.get("tier3_results"),
                        "relevance_score": float(row_dict["relevance_score"]) if row_dict.get("relevance_score") else None,
                        "score_breakdown": row_dict.get("score_breakdown"),
                        "metrics": row_dict.get("metrics"),
                        "error_message": row_dict.get("error_message"),
                        "failed_agents": row_dict.get("failed_agents", []),
                        "created_at": row_dict.get("created_at").isoformat() if row_dict.get("created_at") else None,
                        "updated_at": row_dict.get("updated_at").isoformat() if row_dict.get("updated_at") else None,
                    }
                # else: Skip failed analyses (will result in v3_analysis = null)

        # Combine V2 and V3 data for each item
        for item_id in item_ids:
            results[item_id] = {
                "pipeline_execution": v2_data.get(item_id),
                "v3_analysis": v3_data.get(item_id),
            }

        return results

    except Exception as e:
        logger.error(f"Failed to load batch analysis: {e}")
        return {item_id: _empty_analysis_result() for item_id in item_ids}
