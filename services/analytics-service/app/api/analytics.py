from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.analytics import (
    MetricCreate, MetricResponse, OverviewResponse,
    TrendResponse
)
from app.services.metrics_service import MetricsService
from app.services.trend_service import TrendService

router = APIRouter()


@router.get("/overview", response_model=OverviewResponse)
async def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get system-wide analytics overview"""
    service = MetricsService(db)
    return await service.get_overview()


@router.get("/trends", response_model=TrendResponse)
async def get_trend_analysis(
    service: str = Query(..., description="Service name"),
    metric_name: str = Query(..., description="Metric name to analyze"),
    hours: int = Query(24, ge=1, le=168, description="Time range in hours"),
    interval_minutes: int = Query(60, ge=5, le=1440, description="Aggregation interval"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get trend analysis for a specific metric"""
    trend_service = TrendService(db)
    return await trend_service.analyze_trend(
        service=service,
        metric_name=metric_name,
        hours=hours,
        interval_minutes=interval_minutes
    )


@router.get("/service/{service_name}", response_model=List[MetricResponse])
async def get_service_metrics(
    service_name: str,
    metric_names: Optional[List[str]] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get metrics for a specific service"""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(hours=24)
    if not end_date:
        end_date = datetime.utcnow()

    service = MetricsService(db)
    metrics = await service.get_service_metrics(
        service_name=service_name,
        start_date=start_date,
        end_date=end_date,
        metric_names=metric_names
    )

    return metrics


@router.post("/metrics", response_model=MetricResponse, status_code=201)
async def create_metric(
    metric: MetricCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Store a new metric (for internal service use)"""
    service = MetricsService(db)
    return await service.store_metric(metric)
