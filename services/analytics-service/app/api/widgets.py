from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any
from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.widget_service import WidgetDataService
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/widgets/{widget_id}/data")
async def get_widget_data(
    widget_id: str,
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get data for a specific widget based on its configuration.

    Args:
        widget_id: The widget's unique ID
        dashboard_id: The dashboard containing the widget

    Returns:
        Widget data formatted for the widget type
    """
    # Get dashboard to find widget config
    dashboard_service = DashboardService(db)
    dashboard = await dashboard_service.get_dashboard(
        dashboard_id=dashboard_id,
        user_id=current_user["user_id"]
    )

    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    # Find widget in dashboard
    widget_config = None
    for widget in dashboard.widgets:
        if widget.get("id") == widget_id:
            widget_config = widget
            break

    if not widget_config:
        raise HTTPException(status_code=404, detail="Widget not found in dashboard")

    # Get widget data based on configuration
    widget_service = WidgetDataService(db)
    widget_data = await widget_service.get_widget_data(widget_config)

    return widget_data


@router.get("/dashboards/{dashboard_id}/widgets/data")
async def get_all_widget_data(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Dict[str, Any]]:
    """
    Get data for all widgets in a dashboard.

    Returns:
        Dictionary mapping widget IDs to their data
    """
    # Get dashboard
    dashboard_service = DashboardService(db)
    dashboard = await dashboard_service.get_dashboard(
        dashboard_id=dashboard_id,
        user_id=current_user["user_id"]
    )

    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    # Get data for all widgets
    widget_service = WidgetDataService(db)
    all_data = {}

    for widget in dashboard.widgets:
        widget_id = widget.get("id")
        if widget_id:
            try:
                widget_data = await widget_service.get_widget_data(widget)
                all_data[widget_id] = widget_data
            except Exception as e:
                # Log error but don't fail entire request
                print(f"Error loading widget {widget_id}: {e}")
                all_data[widget_id] = {"error": str(e)}

    return all_data
