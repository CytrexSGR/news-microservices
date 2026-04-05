"""
Clustering Admin API
Provides endpoints for manual clustering triggers and configuration
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

from app.tasks.clustering import run_clustering_pipeline
from app.services.clustering import ClusteringService
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/clustering", tags=["clustering-admin"])


class ClusteringTriggerRequest(BaseModel):
    """Request model for manual clustering trigger"""
    hours: int = Field(default=24, ge=1, le=168, description="Process events from last N hours")
    min_samples: int = Field(default=3, ge=2, le=50, description="Minimum events for cluster formation")
    eps: float = Field(default=0.55, ge=0.1, le=1.0, description="DBSCAN epsilon parameter (cosine distance)")


class ClusteringStatusResponse(BaseModel):
    """Response model for clustering status"""
    current_config: Dict[str, Any]
    last_run: Optional[str]
    scheduled_interval: str
    available_parameters: Dict[str, Dict[str, Any]]


class ClusteringTriggerResponse(BaseModel):
    """Response model for clustering trigger"""
    task_id: str
    status: str
    message: str
    parameters: Dict[str, Any]


@router.post("/trigger", response_model=ClusteringTriggerResponse)
async def trigger_clustering(
    request: ClusteringTriggerRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Manually trigger clustering pipeline with custom parameters

    Requires admin role
    """
    # Check if user is admin
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Trigger Celery task
    task = run_clustering_pipeline.delay(
        hours=request.hours,
        min_samples=request.min_samples,
        eps=request.eps
    )

    return ClusteringTriggerResponse(
        task_id=task.id,
        status="started",
        message=f"Clustering pipeline started with custom parameters",
        parameters={
            "hours": request.hours,
            "min_samples": request.min_samples,
            "eps": request.eps,
        }
    )


@router.get("/status", response_model=ClusteringStatusResponse)
async def get_clustering_status(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get current clustering configuration and status

    Returns default parameters and parameter constraints
    """
    return ClusteringStatusResponse(
        current_config={
            "default_hours": 24,
            "default_min_samples": 3,
            "default_eps": 0.55,
            "metric": "cosine",
            "algorithm": "DBSCAN",
        },
        last_run=None,  # TODO: Track last run timestamp
        scheduled_interval="Every 15 minutes (Celery Beat)",
        available_parameters={
            "hours": {
                "min": 1,
                "max": 168,
                "default": 24,
                "description": "Process events from last N hours (1-168)",
            },
            "min_samples": {
                "min": 2,
                "max": 50,
                "default": 3,
                "description": "Minimum events required to form a cluster (2-50)",
            },
            "eps": {
                "min": 0.1,
                "max": 1.0,
                "default": 0.55,
                "description": "DBSCAN epsilon parameter for cosine distance (0.1-1.0). Lower = stricter clustering.",
            },
        }
    )


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get status of a clustering task
    """
    from app.celery_app import celery_app

    task = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None,
    }
