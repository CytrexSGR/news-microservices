from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import numpy as np
from app.models.analytics import AnalyticsMetric
from app.schemas.analytics import TrendResponse, TrendDataPoint


class TrendService:
    def __init__(self, db: Session):
        self.db = db

    async def analyze_trend(
        self,
        service: str,
        metric_name: str,
        hours: int = 24,
        interval_minutes: int = 60
    ) -> TrendResponse:
        """Analyze metric trends over time"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Single query: fetch all metrics in range, then bucket in Python
        # This replaces N loop queries (one per interval) with 1 query
        all_metrics = self.db.query(
            AnalyticsMetric.timestamp,
            AnalyticsMetric.value
        ).filter(
            and_(
                AnalyticsMetric.service == service,
                AnalyticsMetric.metric_name == metric_name,
                AnalyticsMetric.timestamp >= start_time,
                AnalyticsMetric.timestamp < end_time
            )
        ).order_by(AnalyticsMetric.timestamp).all()

        # Bucket by interval
        data_points = []
        if all_metrics:
            buckets = {}
            for row in all_metrics:
                # Calculate bucket start time
                elapsed = (row.timestamp - start_time).total_seconds()
                bucket_idx = int(elapsed // (interval_minutes * 60))
                bucket_time = start_time + timedelta(minutes=bucket_idx * interval_minutes)

                if bucket_time not in buckets:
                    buckets[bucket_time] = []
                buckets[bucket_time].append(row.value)

            for bucket_time in sorted(buckets.keys()):
                values = buckets[bucket_time]
                avg_value = sum(values) / len(values)
                data_points.append(TrendDataPoint(
                    timestamp=bucket_time,
                    value=float(avg_value)
                ))

        if not data_points:
            return TrendResponse(
                metric_name=metric_name,
                service=service,
                data_points=[],
                trend="stable",
                change_percent=0.0,
                anomalies=[]
            )

        # Calculate trend direction
        values = [dp.value for dp in data_points]
        trend_direction = self._calculate_trend_direction(values)
        change_percent = self._calculate_change_percent(values)

        # Detect anomalies using z-score
        anomalies = self._detect_anomalies(data_points, threshold=2.5)

        return TrendResponse(
            metric_name=metric_name,
            service=service,
            data_points=data_points,
            trend=trend_direction,
            change_percent=change_percent,
            anomalies=anomalies
        )

    def _calculate_trend_direction(self, values: List[float]) -> str:
        """Calculate overall trend direction"""
        if len(values) < 2:
            return "stable"

        # Linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        # Determine direction based on slope
        if abs(slope) < 0.01:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"

    def _calculate_change_percent(self, values: List[float]) -> float:
        """Calculate percentage change from start to end"""
        if len(values) < 2 or values[0] == 0:
            return 0.0

        return ((values[-1] - values[0]) / values[0]) * 100

    def _detect_anomalies(
        self,
        data_points: List[TrendDataPoint],
        threshold: float = 2.5
    ) -> List[datetime]:
        """Detect anomalies using z-score method"""
        if len(data_points) < 3:
            return []

        values = np.array([dp.value for dp in data_points])
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return []

        # Calculate z-scores
        z_scores = np.abs((values - mean) / std)

        # Find anomalies
        anomaly_indices = np.where(z_scores > threshold)[0]

        return [data_points[i].timestamp for i in anomaly_indices]

    async def get_moving_average(
        self,
        service: str,
        metric_name: str,
        window_size: int = 5,
        hours: int = 24
    ) -> List[TrendDataPoint]:
        """Calculate moving average for smoothing"""
        trend_data = await self.analyze_trend(service, metric_name, hours)

        if len(trend_data.data_points) < window_size:
            return trend_data.data_points

        values = np.array([dp.value for dp in trend_data.data_points])
        moving_avg = np.convolve(values, np.ones(window_size)/window_size, mode='valid')

        # Adjust timestamps to match moving average length
        adjusted_points = []
        for i, avg_value in enumerate(moving_avg):
            idx = i + window_size - 1
            adjusted_points.append(TrendDataPoint(
                timestamp=trend_data.data_points[idx].timestamp,
                value=float(avg_value)
            ))

        return adjusted_points
