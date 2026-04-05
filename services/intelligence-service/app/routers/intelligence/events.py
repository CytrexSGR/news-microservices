"""
Intelligence Event Endpoints
Event retrieval and detection
"""
import logging
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.cluster import IntelligenceCluster
from app.models.event import IntelligenceEvent
from app.schemas.intelligence import (
    EventDetectRequest,
    EventDetectResponse,
)
from app.services.event_detection import event_detection_service
from .utils import normalize_risk_score

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/events/latest")
async def get_latest_events(
    hours: int = Query(4, ge=1, le=48, description="Hours to look back"),
    limit: int = Query(20, ge=1, le=100, description="Maximum events to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get latest events across all clusters

    Returns most recent events from the last N hours, sorted by published_at DESC.
    Includes cluster information and risk scores.
    """
    try:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)

        events_result = await db.execute(
            select(IntelligenceEvent)
            .join(IntelligenceCluster, IntelligenceEvent.cluster_id == IntelligenceCluster.id)
            .where(IntelligenceEvent.published_at >= time_threshold)
            .order_by(IntelligenceEvent.published_at.desc())
            .limit(limit)
            .options(selectinload(IntelligenceEvent.cluster))
        )
        events = events_result.scalars().all()

        formatted_events = []
        for event in events:
            persons = []
            organizations = []
            locations = []

            if event.entities:
                if isinstance(event.entities, list):
                    for entity in event.entities:
                        if isinstance(entity, dict) and entity.get("name"):
                            entity_type = entity.get("type", "").upper()
                            if entity_type == "PERSON":
                                persons.append(entity["name"])
                            elif entity_type == "ORGANIZATION":
                                organizations.append(entity["name"])
                            elif entity_type == "LOCATION":
                                locations.append(entity["name"])
                elif isinstance(event.entities, dict):
                    persons = event.entities.get("persons", [])
                    organizations = event.entities.get("organizations", [])
                    locations = event.entities.get("locations", [])

            formatted_events.append({
                "id": str(event.id),
                "title": event.title,
                "description": event.description,
                "source": event.source,
                "source_url": event.source_url,
                "published_at": event.published_at.isoformat(),
                "entities": {
                    "persons": persons,
                    "organizations": organizations,
                    "locations": locations
                },
                "keywords": event.keywords or [],
                "sentiment": event.sentiment,
                "bias_score": event.bias_score,
                "confidence": event.confidence,
                "cluster": {
                    "id": str(event.cluster.id),
                    "name": event.cluster.name,
                    "risk_score": normalize_risk_score(float(event.cluster.risk_score))
                } if event.cluster else None
            })

        return {
            "events": formatted_events,
            "total": len(formatted_events),
            "hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get latest events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/detect", response_model=EventDetectResponse)
async def detect_events(
    request: EventDetectRequest,
):
    """
    Detect events and extract entities from text

    Analyzes the provided text to:
    - Extract named entities (persons, organizations, locations)
    - Extract keywords using NLP
    - Provide structured event detection results

    This endpoint is useful for:
    - Testing text analysis before ingestion
    - Ad-hoc analysis of news articles
    - Validating entity extraction quality

    Example request:
    ```json
    {
        "text": "The Federal Reserve announced interest rate changes...",
        "include_keywords": true,
        "max_keywords": 10
    }
    ```
    """
    start_time = time.time()

    try:
        # Extract entities using the event detection service
        entities = event_detection_service.extract_entities(request.text)

        # Extract keywords if requested
        keywords = []
        if request.include_keywords:
            keywords = event_detection_service.extract_keywords(
                request.text,
                max_keywords=request.max_keywords
            )

        # Calculate total entity count
        entity_count = sum(len(v) for v in entities.values())

        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        return EventDetectResponse(
            entities=entities,
            keywords=keywords,
            entity_count=entity_count,
            text_length=len(request.text),
            processing_time_ms=round(processing_time, 2)
        )

    except Exception as e:
        logger.error(f"Event detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Event detection failed: {str(e)}")
