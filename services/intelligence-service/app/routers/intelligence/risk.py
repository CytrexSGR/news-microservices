"""
Intelligence Risk Calculation Endpoints
Risk scoring and analysis
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.cluster import IntelligenceCluster
from app.schemas.intelligence import (
    RiskCalculateRequest,
    RiskCalculateResponse,
    RiskFactor,
)
from app.services.event_detection import event_detection_service
from app.services.risk_scoring import risk_scoring_service
from .utils import normalize_risk_score, get_risk_level

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/risk/calculate", response_model=RiskCalculateResponse)
async def calculate_risk(
    request: RiskCalculateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate risk score for a cluster, entities, or text

    Supports three modes:
    1. **Cluster mode**: Provide cluster_id to get risk score for existing cluster
    2. **Entity mode**: Provide list of entity names to calculate risk
    3. **Text mode**: Provide text to analyze and calculate risk

    Risk score ranges from 0-100:
    - 0-24: Low risk
    - 25-49: Medium risk
    - 50-74: High risk
    - 75-100: Critical risk

    Example request (cluster mode):
    ```json
    {
        "cluster_id": "550e8400-e29b-41d4-a716-446655440000",
        "include_factors": true
    }
    ```

    Example request (text mode):
    ```json
    {
        "text": "Breaking: Major cyberattack on government systems...",
        "include_factors": true
    }
    ```
    """
    try:
        factors = []
        risk_score = 0.0
        risk_delta = None
        cluster_id = request.cluster_id

        # Mode 1: Calculate risk for existing cluster
        if request.cluster_id:
            cluster_result = await db.execute(
                select(IntelligenceCluster).where(IntelligenceCluster.id == request.cluster_id)
            )
            cluster = cluster_result.scalar_one_or_none()

            if not cluster:
                raise HTTPException(status_code=404, detail=f"Cluster {request.cluster_id} not found")

            # Get last week's metrics for delta calculation
            last_metrics = await risk_scoring_service.get_last_week_metrics(db, request.cluster_id)

            # Calculate current metrics
            current_metrics = await risk_scoring_service.calculate_current_metrics(db, request.cluster_id)

            # Calculate risk score
            risk_data = risk_scoring_service.calculate_risk_score(current_metrics, last_metrics)
            risk_score = normalize_risk_score(risk_data["risk_score"])
            risk_delta = risk_data["risk_delta"]

            if request.include_factors:
                factors = [
                    RiskFactor(
                        name="Article Volume",
                        value=current_metrics["article_count"],
                        weight=0.4,
                        contribution=min(current_metrics["article_count"] / 100.0, 1.0) * 40
                    ),
                    RiskFactor(
                        name="Sentiment",
                        value=current_metrics["avg_sentiment"],
                        weight=0.4,
                        contribution=((1.0 - current_metrics["avg_sentiment"]) / 2.0) * 40
                    ),
                    RiskFactor(
                        name="Source Diversity",
                        value=current_metrics["unique_sources"],
                        weight=0.2,
                        contribution=min(current_metrics["unique_sources"] / 10.0, 1.0) * 20
                    ),
                ]

        # Mode 2: Calculate risk for entities
        elif request.entities:
            high_risk_keywords = ["attack", "war", "crisis", "threat", "hack", "breach", "explosion"]
            entity_text = " ".join(request.entities).lower()

            keyword_hits = sum(1 for kw in high_risk_keywords if kw in entity_text)
            entity_count = len(request.entities)

            entity_factor = min(entity_count / 10.0, 1.0) * 30
            keyword_factor = min(keyword_hits / 3.0, 1.0) * 50
            base_risk = 20

            risk_score = min(base_risk + entity_factor + keyword_factor, 100)

            if request.include_factors:
                factors = [
                    RiskFactor(
                        name="Entity Count",
                        value=entity_count,
                        weight=0.3,
                        contribution=entity_factor
                    ),
                    RiskFactor(
                        name="High-Risk Keywords",
                        value=keyword_hits,
                        weight=0.5,
                        contribution=keyword_factor
                    ),
                    RiskFactor(
                        name="Base Risk",
                        value=1.0,
                        weight=0.2,
                        contribution=base_risk
                    ),
                ]

        # Mode 3: Calculate risk from text
        elif request.text:
            entities = event_detection_service.extract_entities(request.text)
            keywords = event_detection_service.extract_keywords(request.text, max_keywords=20)

            total_entities = sum(len(v) for v in entities.values())

            high_risk_keywords = [
                "attack", "war", "crisis", "threat", "hack", "breach",
                "explosion", "terror", "conflict", "emergency", "death",
                "crash", "collapse", "scandal", "fraud", "investigation"
            ]
            text_lower = request.text.lower()
            keyword_hits = sum(1 for kw in high_risk_keywords if kw in text_lower)

            negative_words = ["not", "fail", "bad", "worse", "worst", "danger", "risk", "loss"]
            negative_count = sum(1 for word in negative_words if word in text_lower)

            entity_factor = min(total_entities / 15.0, 1.0) * 25
            keyword_factor = min(keyword_hits / 5.0, 1.0) * 40
            sentiment_factor = min(negative_count / 5.0, 1.0) * 25
            length_factor = min(len(request.text) / 5000.0, 1.0) * 10

            risk_score = min(entity_factor + keyword_factor + sentiment_factor + length_factor, 100)

            if request.include_factors:
                factors = [
                    RiskFactor(
                        name="Entity Density",
                        value=total_entities,
                        weight=0.25,
                        contribution=entity_factor
                    ),
                    RiskFactor(
                        name="Risk Keywords",
                        value=keyword_hits,
                        weight=0.40,
                        contribution=keyword_factor
                    ),
                    RiskFactor(
                        name="Negative Sentiment",
                        value=negative_count,
                        weight=0.25,
                        contribution=sentiment_factor
                    ),
                    RiskFactor(
                        name="Content Length",
                        value=len(request.text),
                        weight=0.10,
                        contribution=length_factor
                    ),
                ]

        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either cluster_id, entities, or text"
            )

        return RiskCalculateResponse(
            risk_score=round(risk_score, 2),
            risk_level=get_risk_level(risk_score),
            risk_delta=risk_delta,
            factors=factors if request.include_factors else [],
            cluster_id=cluster_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Risk calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Risk calculation failed: {str(e)}")
