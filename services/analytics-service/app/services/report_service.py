import os
import json
import csv
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from app.core.config import settings
from app.models.analytics import AnalyticsReport, AnalyticsMetric
from app.schemas.analytics import ReportCreate
from app.services.metrics_service import MetricsService


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.metrics_service = MetricsService(db)
        self.template_env = Environment(
            loader=FileSystemLoader('templates')
        )
        os.makedirs(settings.REPORTS_STORAGE_PATH, exist_ok=True)

    async def create_report(self, user_id: str, report_data: ReportCreate) -> AnalyticsReport:
        """Create a new analytics report"""
        db_report = AnalyticsReport(
            user_id=user_id,
            name=report_data.name,
            description=report_data.description,
            config=report_data.config.model_dump(),
            format=report_data.format,
            status="pending"
        )

        self.db.add(db_report)
        self.db.commit()
        self.db.refresh(db_report)

        return db_report

    async def generate_report(self, report_id: int) -> AnalyticsReport:
        """Generate the actual report file"""
        report = self.db.query(AnalyticsReport).filter(
            AnalyticsReport.id == report_id
        ).first()

        if not report:
            raise ValueError(f"Report {report_id} not found")

        try:
            report.status = "processing"
            self.db.commit()

            # Collect data
            data = await self._collect_report_data(report.config)

            # Generate based on format
            if report.format == "csv":
                file_path = await self._generate_csv_report(report, data)
            elif report.format == "json":
                file_path = await self._generate_json_report(report, data)
            elif report.format == "md":
                file_path = await self._generate_markdown_report(report, data)
            else:
                raise ValueError(f"Unsupported format: {report.format}")

            # Update report
            report.status = "completed"
            report.file_path = file_path
            report.file_size_bytes = os.path.getsize(file_path)
            report.completed_at = datetime.utcnow()

        except Exception as e:
            report.status = "failed"
            report.error_message = str(e)

        self.db.commit()
        self.db.refresh(report)
        return report

    async def _collect_report_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect metrics data for the report"""
        data = {
            "services": {},
            "summary": {},
            "charts": []
        }

        for service in config.get("services", []):
            metrics = await self.metrics_service.get_service_metrics(
                service_name=service,
                start_date=datetime.fromisoformat(config["start_date"]),
                end_date=datetime.fromisoformat(config["end_date"]),
                metric_names=config.get("metrics")
            )

            # Organize metrics by name
            service_data = {}
            for metric in metrics:
                if metric.metric_name not in service_data:
                    service_data[metric.metric_name] = []

                service_data[metric.metric_name].append({
                    "timestamp": metric.timestamp.isoformat(),
                    "value": metric.value,
                    "unit": metric.unit
                })

            data["services"][service] = service_data

        return data

    async def _generate_csv_report(self, report: AnalyticsReport, data: Dict[str, Any]) -> str:
        """Generate CSV report"""
        file_path = os.path.join(
            settings.REPORTS_STORAGE_PATH,
            f"report_{report.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Service', 'Metric', 'Timestamp', 'Value', 'Unit'])

            for service, metrics in data["services"].items():
                for metric_name, values in metrics.items():
                    for value_data in values:
                        writer.writerow([
                            service,
                            metric_name,
                            value_data["timestamp"],
                            value_data["value"],
                            value_data.get("unit", "")
                        ])

        return file_path

    async def _generate_json_report(self, report: AnalyticsReport, data: Dict[str, Any]) -> str:
        """Generate JSON report"""
        file_path = os.path.join(
            settings.REPORTS_STORAGE_PATH,
            f"report_{report.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(file_path, 'w') as jsonfile:
            json.dump({
                "report_id": report.id,
                "name": report.name,
                "generated_at": datetime.utcnow().isoformat(),
                "config": report.config,
                "data": data
            }, jsonfile, indent=2)

        return file_path

    async def _generate_markdown_report(self, report: AnalyticsReport, data: Dict[str, Any]) -> str:
        """Generate Markdown report"""
        file_path = os.path.join(
            settings.REPORTS_STORAGE_PATH,
            f"report_{report.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
        )

        with open(file_path, 'w') as mdfile:
            # Header
            mdfile.write(f"# {report.name}\n\n")
            if report.description:
                mdfile.write(f"_{report.description}_\n\n")

            mdfile.write(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
            mdfile.write(f"**Report ID:** {report.id}\n\n")

            # Configuration
            mdfile.write("## Configuration\n\n")
            mdfile.write(f"- **Time Range:** {report.config.get('start_date', 'N/A')} to {report.config.get('end_date', 'N/A')}\n")
            mdfile.write(f"- **Aggregation:** {report.config.get('aggregation', 'N/A')}\n")
            mdfile.write(f"- **Services:** {', '.join(report.config.get('services', []))}\n")
            mdfile.write(f"- **Metrics:** {', '.join(report.config.get('metrics', []))}\n\n")

            # Data by Service
            mdfile.write("## Metrics Data\n\n")

            if not data["services"]:
                mdfile.write("_No data available for the selected time range._\n")
            else:
                for service, metrics in data["services"].items():
                    mdfile.write(f"### {service}\n\n")

                    if not metrics:
                        mdfile.write("_No metrics data available._\n\n")
                        continue

                    for metric_name, values in metrics.items():
                        mdfile.write(f"#### {metric_name}\n\n")

                        if not values:
                            mdfile.write("_No data points._\n\n")
                            continue

                        # Table format
                        mdfile.write("| Timestamp | Value | Unit |\n")
                        mdfile.write("|-----------|-------|------|\n")

                        for value_data in values[:50]:  # Limit to first 50 data points
                            timestamp = value_data.get("timestamp", "N/A")
                            value = value_data.get("value", "N/A")
                            unit = value_data.get("unit", "")
                            mdfile.write(f"| {timestamp} | {value} | {unit} |\n")

                        if len(values) > 50:
                            mdfile.write(f"\n_... and {len(values) - 50} more data points._\n\n")
                        else:
                            mdfile.write("\n")

            # Footer
            mdfile.write("---\n\n")
            mdfile.write("_Generated by Analytics Service_\n")

        return file_path

    async def _generate_charts(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate base64-encoded charts for embedding in reports"""
        charts = {}

        for service, metrics in data["services"].items():
            for metric_name, values in metrics.items():
                if not values:
                    continue

                # Create line chart
                fig, ax = plt.subplots(figsize=(10, 6))

                timestamps = [datetime.fromisoformat(v["timestamp"]) for v in values]
                metric_values = [v["value"] for v in values]

                ax.plot(timestamps, metric_values, marker='o')
                ax.set_xlabel('Time')
                ax.set_ylabel(f'{metric_name} ({values[0].get("unit", "")})')
                ax.set_title(f'{service} - {metric_name}')
                ax.grid(True)
                plt.xticks(rotation=45)
                plt.tight_layout()

                # Convert to base64
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=100)
                buffer.seek(0)
                chart_base64 = base64.b64encode(buffer.read()).decode()
                plt.close()

                charts[f"{service}_{metric_name}"] = f"data:image/png;base64,{chart_base64}"

        return charts

    async def get_report(self, report_id: int, user_id: str) -> AnalyticsReport:
        """Get a specific report"""
        return self.db.query(AnalyticsReport).filter(
            AnalyticsReport.id == report_id,
            AnalyticsReport.user_id == user_id
        ).first()

    async def list_reports(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[AnalyticsReport]:
        """List user's reports"""
        return self.db.query(AnalyticsReport).filter(
            AnalyticsReport.user_id == user_id
        ).order_by(
            AnalyticsReport.created_at.desc()
        ).offset(skip).limit(limit).all()
