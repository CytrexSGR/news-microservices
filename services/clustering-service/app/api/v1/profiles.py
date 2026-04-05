# services/clustering-service/app/api/v1/profiles.py
"""Topic Profile API endpoints for semantic category management.

This module provides CRUD operations for topic profiles and cluster matching.
Topic profiles define semantic categories via descriptive text that gets embedded,
enabling mathematical cluster matching via cosine similarity.

Endpoints:
- GET    /profiles              - List all topic profiles
- POST   /profiles              - Create a new profile
- GET    /profiles/{name}       - Get profile details
- PUT    /profiles/{name}       - Update a profile
- DELETE /profiles/{name}       - Delete a profile
- GET    /profiles/{name}/matches - Get clusters matching a profile
- GET    /profiles/matches/all  - Get all profile matches (for SITREP)
- POST   /profiles/embed        - Embed all profiles without embeddings
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.db.session import get_db
from app.schemas.profile import (
    AllProfileMatchesResponse,
    ClusterMatch,
    EmbedProfilesResponse,
    ProfileCreate,
    ProfileDetail,
    ProfileListResponse,
    ProfileMatchesResponse,
    ProfileSummary,
    ProfileUpdate,
)
from app.services.embedding_service import get_embedding_service
from app.services.profile_service import ProfileService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_profile_service(db: AsyncSession = Depends(get_db)) -> ProfileService:
    """Dependency for ProfileService."""
    embedding_service = get_embedding_service()
    return ProfileService(db, embedding_service)


@router.get("", response_model=ProfileListResponse)
async def list_profiles(
    active_only: bool = Query(True, description="Only return active profiles"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    List all topic profiles.

    Returns profiles sorted by priority (highest first).

    Examples:
        GET /profiles
        GET /profiles?active_only=false
    """
    service = get_profile_service(db)
    profiles = await service.list_profiles(active_only=active_only)

    # Check which profiles have embeddings via raw SQL
    from sqlalchemy import text

    result = await db.execute(
        text("SELECT id FROM topic_profiles WHERE embedding_vec IS NOT NULL")
    )
    embedded_ids = {row.id for row in result.fetchall()}

    summaries = [
        ProfileSummary(
            id=p.id,
            name=p.name,
            display_name=p.display_name,
            min_similarity=p.min_similarity,
            priority=p.priority,
            is_active=p.is_active,
            has_embedding=p.id in embedded_ids,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in profiles
    ]

    return ProfileListResponse(profiles=summaries, total=len(summaries))


@router.post("", response_model=ProfileDetail, status_code=201)
async def create_profile(
    data: ProfileCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Create a new topic profile.

    The profile's description_text will be embedded immediately.

    Example:
        POST /profiles
        {
            "name": "finance",
            "display_name": "Financial Markets",
            "description_text": "Stocks, bonds, ETFs, Federal Reserve...",
            "min_similarity": 0.40,
            "priority": 10
        }
    """
    service = get_profile_service(db)

    try:
        profile = await service.create_profile(
            name=data.name,
            description_text=data.description_text,
            display_name=data.display_name,
            min_similarity=data.min_similarity,
            priority=data.priority,
            embed_now=True,
        )

        await db.commit()

        return ProfileDetail(
            id=profile.id,
            name=profile.name,
            display_name=profile.display_name,
            description_text=profile.description_text,
            min_similarity=profile.min_similarity,
            priority=profile.priority,
            is_active=profile.is_active,
            has_embedding=True,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/matches/all", response_model=AllProfileMatchesResponse)
async def get_all_profile_matches(
    batch_id: Optional[str] = Query(None, description="Specific batch ID"),
    limit_per_profile: int = Query(10, ge=1, le=50, description="Max clusters per profile"),
    hours: Optional[int] = Query(
        None, ge=1, le=168, description="Filter to clusters from last N hours (max 7 days)"
    ),
    since: Optional[str] = Query(
        None, description="Filter to clusters since ISO datetime (e.g. 2026-01-06T00:00:00Z)"
    ),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get matching clusters for all active profiles.

    Useful for generating category-based views or SITREP summaries.

    Time Filters (mutually exclusive with batch_id):
    - hours: Get clusters from batches completed in the last N hours
    - since: Get clusters from batches completed after the given datetime

    Examples:
        GET /profiles/matches/all?limit_per_profile=5
        GET /profiles/matches/all?hours=24&limit_per_profile=10
    """
    from datetime import datetime

    service = get_profile_service(db)

    # Parse since datetime if provided
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid datetime format: {since}. Use ISO format (e.g. 2026-01-06T00:00:00Z)"
            )

    all_matches = await service.get_all_profile_matches(
        batch_id=batch_id,
        limit_per_profile=limit_per_profile,
        hours=hours,
        since=since_dt,
    )

    # Convert to response format
    profiles_dict = {
        name: [ClusterMatch(**m) for m in matches]
        for name, matches in all_matches.items()
    }

    return AllProfileMatchesResponse(profiles=profiles_dict)


@router.get("/{name}", response_model=ProfileDetail)
async def get_profile(
    name: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get details of a specific profile.

    Args:
        name: Profile name (unique identifier)
    """
    service = get_profile_service(db)
    profile = await service.get_profile_by_name(name)

    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")

    # Check if profile has embedding
    from sqlalchemy import text

    result = await db.execute(
        text("SELECT 1 FROM topic_profiles WHERE id = :id AND embedding_vec IS NOT NULL"),
        {"id": profile.id},
    )
    has_embedding = result.scalar_one_or_none() is not None

    return ProfileDetail(
        id=profile.id,
        name=profile.name,
        display_name=profile.display_name,
        description_text=profile.description_text,
        min_similarity=profile.min_similarity,
        priority=profile.priority,
        is_active=profile.is_active,
        has_embedding=has_embedding,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.put("/{name}", response_model=ProfileDetail)
async def update_profile(
    name: str,
    data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Update a topic profile.

    If description_text is changed, the embedding will be regenerated.
    """
    service = get_profile_service(db)

    profile = await service.get_profile_by_name(name)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")

    profile = await service.update_profile(
        profile_id=profile.id,
        description_text=data.description_text,
        display_name=data.display_name,
        min_similarity=data.min_similarity,
        priority=data.priority,
        is_active=data.is_active,
        re_embed=True,
    )

    await db.commit()

    # Check if profile has embedding
    from sqlalchemy import text

    result = await db.execute(
        text("SELECT 1 FROM topic_profiles WHERE id = :id AND embedding_vec IS NOT NULL"),
        {"id": profile.id},
    )
    has_embedding = result.scalar_one_or_none() is not None

    return ProfileDetail(
        id=profile.id,
        name=profile.name,
        display_name=profile.display_name,
        description_text=profile.description_text,
        min_similarity=profile.min_similarity,
        priority=profile.priority,
        is_active=profile.is_active,
        has_embedding=has_embedding,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.delete("/{name}", status_code=204)
async def delete_profile(
    name: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Delete a topic profile.

    Warning: This permanently removes the profile.
    """
    service = get_profile_service(db)

    profile = await service.get_profile_by_name(name)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")

    await service.delete_profile(profile.id)
    await db.commit()


@router.get("/{name}/matches", response_model=ProfileMatchesResponse)
async def get_profile_matches(
    name: str,
    batch_id: Optional[str] = Query(None, description="Specific batch ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum clusters to return"),
    min_similarity: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Override profile threshold"
    ),
    hours: Optional[int] = Query(
        None, ge=1, le=168, description="Filter to clusters from last N hours (max 7 days)"
    ),
    since: Optional[str] = Query(
        None, description="Filter to clusters since ISO datetime (e.g. 2026-01-06T00:00:00Z)"
    ),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get clusters matching a profile by embedding similarity.

    Returns clusters sorted by similarity (highest first).
    Only returns clusters above the profile's min_similarity threshold.

    Time Filters (mutually exclusive with batch_id):
    - hours: Get clusters from batches completed in the last N hours
    - since: Get clusters from batches completed after the given datetime

    Examples:
        GET /profiles/finance/matches
        GET /profiles/finance/matches?limit=50&min_similarity=0.35
        GET /profiles/conflict/matches?hours=24
        GET /profiles/conflict/matches?since=2026-01-06T00:00:00Z
    """
    from datetime import datetime

    service = get_profile_service(db)

    profile = await service.get_profile_by_name(name)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")

    # Parse since datetime if provided
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid datetime format: {since}. Use ISO format (e.g. 2026-01-06T00:00:00Z)"
            )

    matches = await service.find_matching_clusters(
        profile_name=name,
        batch_id=batch_id,
        limit=limit,
        min_similarity=min_similarity,
        hours=hours,
        since=since_dt,
    )

    return ProfileMatchesResponse(
        profile_name=name,
        profile_display_name=profile.display_name,
        min_similarity=min_similarity or profile.min_similarity,
        matches=[ClusterMatch(**m) for m in matches],
        total_matches=len(matches),
    )


@router.post("/embed", response_model=EmbedProfilesResponse)
async def embed_all_profiles(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Generate embeddings for all profiles without embeddings.

    Use this after bulk creating profiles or to fix missing embeddings.
    """
    service = get_profile_service(db)
    results = await service.embed_all_profiles()

    await db.commit()

    success_count = sum(1 for v in results.values() if v)
    failed_count = sum(1 for v in results.values() if not v)

    return EmbedProfilesResponse(
        embedded=results,
        total_success=success_count,
        total_failed=failed_count,
    )
