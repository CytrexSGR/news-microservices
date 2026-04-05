from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.analytics import AnalyticsDashboard
from app.schemas.analytics import DashboardCreate, DashboardUpdate
from app.services.metrics_service import MetricsService


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.metrics_service = MetricsService(db)

    async def create_dashboard(
        self,
        user_id: str,
        dashboard_data: DashboardCreate
    ) -> AnalyticsDashboard:
        """Create a new dashboard"""
        db_dashboard = AnalyticsDashboard(
            user_id=user_id,
            name=dashboard_data.name,
            description=dashboard_data.description,
            config={},
            widgets=[w.model_dump() for w in dashboard_data.widgets],
            is_public=dashboard_data.is_public,
            refresh_interval=dashboard_data.refresh_interval
        )

        self.db.add(db_dashboard)
        self.db.commit()
        self.db.refresh(db_dashboard)

        return db_dashboard

    async def update_dashboard(
        self,
        dashboard_id: int,
        user_id: str,
        dashboard_data: DashboardUpdate
    ) -> Optional[AnalyticsDashboard]:
        """Update an existing dashboard"""
        dashboard = self.db.query(AnalyticsDashboard).filter(
            AnalyticsDashboard.id == dashboard_id,
            AnalyticsDashboard.user_id == user_id
        ).first()

        if not dashboard:
            return None

        if dashboard_data.name is not None:
            dashboard.name = dashboard_data.name
        if dashboard_data.description is not None:
            dashboard.description = dashboard_data.description
        if dashboard_data.widgets is not None:
            dashboard.widgets = [w.model_dump() for w in dashboard_data.widgets]
        if dashboard_data.is_public is not None:
            dashboard.is_public = dashboard_data.is_public
        if dashboard_data.refresh_interval is not None:
            dashboard.refresh_interval = dashboard_data.refresh_interval

        dashboard.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(dashboard)

        return dashboard

    async def get_dashboard(
        self,
        dashboard_id: int,
        user_id: Optional[str] = None
    ) -> Optional[AnalyticsDashboard]:
        """Get a dashboard by ID"""
        query = self.db.query(AnalyticsDashboard).filter(
            AnalyticsDashboard.id == dashboard_id
        )

        if user_id:
            # User can access their own or public dashboards
            query = query.filter(
                (AnalyticsDashboard.user_id == user_id) |
                (AnalyticsDashboard.is_public == True)
            )

        return query.first()

    async def list_dashboards(
        self,
        user_id: Optional[str] = None,
        include_public: bool = True,
        skip: int = 0,
        limit: int = 20
    ) -> List[AnalyticsDashboard]:
        """List dashboards"""
        query = self.db.query(AnalyticsDashboard)

        if user_id:
            if include_public:
                query = query.filter(
                    (AnalyticsDashboard.user_id == user_id) |
                    (AnalyticsDashboard.is_public == True)
                )
            else:
                query = query.filter(AnalyticsDashboard.user_id == user_id)
        elif include_public:
            query = query.filter(AnalyticsDashboard.is_public == True)

        return query.order_by(
            AnalyticsDashboard.updated_at.desc()
        ).offset(skip).limit(limit).all()

    async def delete_dashboard(
        self,
        dashboard_id: int,
        user_id: str
    ) -> bool:
        """Delete a dashboard"""
        dashboard = self.db.query(AnalyticsDashboard).filter(
            AnalyticsDashboard.id == dashboard_id,
            AnalyticsDashboard.user_id == user_id
        ).first()

        if not dashboard:
            return False

        self.db.delete(dashboard)
        self.db.commit()

        return True

    async def get_dashboard_data(
        self,
        dashboard_id: int,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get dashboard with live widget data"""
        dashboard = await self.get_dashboard(dashboard_id, user_id)

        if not dashboard:
            return None

        # Fetch live data for each widget
        widget_data = []
        for widget in dashboard.widgets:
            data = await self._fetch_widget_data(widget)
            widget_data.append({
                **widget,
                "data": data
            })

        return {
            "dashboard": dashboard,
            "widgets": widget_data
        }

    async def _fetch_widget_data(self, widget: Dict[str, Any]) -> Any:
        """Fetch live data for a widget"""
        metric_name = widget.get("metric_name")
        service = widget.get("service")
        widget_type = widget.get("type")

        if not metric_name:
            return None

        # Fetch recent metrics
        metrics = await self.metrics_service.get_service_metrics(
            service_name=service,
            metric_names=[metric_name]
        )

        if widget_type == "stat_card":
            # Return latest value
            if metrics:
                return {
                    "value": metrics[0].value,
                    "unit": metrics[0].unit,
                    "timestamp": metrics[0].timestamp.isoformat()
                }
        elif widget_type in ["line_chart", "bar_chart"]:
            # Return time series data
            return [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "value": m.value
                }
                for m in metrics[:50]  # Limit to 50 data points
            ]

        return None
