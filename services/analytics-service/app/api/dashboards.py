from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
import json
from datetime import datetime
from app.core.database import get_db
from app.core.auth import get_current_user, get_optional_user
from app.schemas.analytics import (
    DashboardCreate, DashboardUpdate, DashboardResponse
)
from app.services.dashboard_service import DashboardService
from app.services.data_aggregator import (
    aggregate_stat_card_data,
    aggregate_timeseries_data,
    aggregate_bar_chart_data,
    aggregate_pie_chart_data
)

router = APIRouter()


@router.post("/dashboards", response_model=DashboardResponse, status_code=201)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new dashboard"""
    service = DashboardService(db)
    return await service.create_dashboard(
        user_id=current_user["user_id"],
        dashboard_data=dashboard_data
    )


@router.get("/dashboards", response_model=List[DashboardResponse])
async def list_dashboards(
    include_public: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_user)
):
    """List dashboards (user's own + public if requested)"""
    service = DashboardService(db)
    user_id = current_user["user_id"] if current_user else None

    return await service.list_dashboards(
        user_id=user_id,
        include_public=include_public,
        skip=skip,
        limit=limit
    )


@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_user)
):
    """Get a specific dashboard"""
    service = DashboardService(db)
    user_id = current_user["user_id"] if current_user else None

    dashboard = await service.get_dashboard(
        dashboard_id=dashboard_id,
        user_id=user_id
    )

    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return dashboard


@router.get("/dashboards/{dashboard_id}/data")
async def get_dashboard_data(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_optional_user)
):
    """Get dashboard with live widget data"""
    service = DashboardService(db)
    user_id = current_user["user_id"] if current_user else None

    data = await service.get_dashboard_data(
        dashboard_id=dashboard_id,
        user_id=user_id
    )

    if not data:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return data


@router.put("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: int,
    dashboard_data: DashboardUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a dashboard"""
    service = DashboardService(db)

    dashboard = await service.update_dashboard(
        dashboard_id=dashboard_id,
        user_id=current_user["user_id"],
        dashboard_data=dashboard_data
    )

    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return dashboard


@router.delete("/dashboards/{dashboard_id}", status_code=204)
async def delete_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a dashboard"""
    service = DashboardService(db)

    success = await service.delete_dashboard(
        dashboard_id=dashboard_id,
        user_id=current_user["user_id"]
    )

    if not success:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return None


# WebSocket helper function for data aggregation
def generate_widget_data(widget_type: str, widget_config: dict, db: Session) -> dict:
    """Generate widget data using real aggregated metrics"""
    try:
        if widget_type == "stat_card":
            return aggregate_stat_card_data(db, widget_config)
        elif widget_type == "line_chart":
            return aggregate_timeseries_data(db, widget_config)
        elif widget_type == "bar_chart":
            return aggregate_bar_chart_data(db, widget_config)
        elif widget_type == "pie_chart":
            return aggregate_pie_chart_data(db, widget_config)
        else:
            return {"value": 0}
    except Exception as e:
        print(f"Error aggregating data for widget type {widget_type}: {str(e)}")
        # Return empty data structure on error
        if widget_type == "stat_card":
            return {"value": 0, "change": 0, "trend": "neutral"}
        else:
            return {"series": []}


@router.websocket("/dashboards/{dashboard_id}/ws")
async def dashboard_websocket(websocket: WebSocket, dashboard_id: int):
    """
    WebSocket endpoint for real-time dashboard data updates
    Sends mock data to widgets every 3 seconds
    """
    await websocket.accept()

    try:
        # Get dashboard configuration from database
        db = next(get_db())
        service = DashboardService(db)

        try:
            dashboard = await service.get_dashboard(dashboard_id=dashboard_id, user_id=None)
        except Exception:
            dashboard = None

        if not dashboard:
            await websocket.send_json({"error": "Dashboard not found"})
            await websocket.close()
            return

        # Extract widgets from dashboard (convert to dict if Pydantic model)
        if hasattr(dashboard, 'dict'):
            dashboard_dict = dashboard.dict()
        elif hasattr(dashboard, 'model_dump'):
            dashboard_dict = dashboard.model_dump()
        elif isinstance(dashboard, dict):
            dashboard_dict = dashboard
        else:
            dashboard_dict = {"widgets": getattr(dashboard, 'widgets', [])}

        widgets = dashboard_dict.get("widgets", [])

        # Send initial data for all widgets
        for widget in widgets:
            widget_id = widget["id"]
            widget_type = widget["type"]
            data = generate_widget_data(widget_type, widget, db)

            await websocket.send_json({
                "widget_id": widget_id,
                "data": data
            })

        # Continuous update loop
        while True:
            # Wait 3 seconds between updates
            await asyncio.sleep(3)

            # Send updated data for all widgets
            for widget in widgets:
                widget_id = widget["id"]
                widget_type = widget["type"]
                data = generate_widget_data(widget_type, widget, db)

                try:
                    await websocket.send_json({
                        "widget_id": widget_id,
                        "data": data
                    })
                except Exception as e:
                    print(f"Error sending data: {e}")
                    break

    except WebSocketDisconnect:
        print(f"Client disconnected from dashboard {dashboard_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
