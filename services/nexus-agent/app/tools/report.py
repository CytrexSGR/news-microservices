"""Report generation tool for NEXUS agent."""

from typing import Dict, Any, Optional
from datetime import datetime
import os

from app.tools.base import BaseTool
from app.core.logging import get_logger

logger = get_logger(__name__)

REPORT_TEMPLATE = """
# {title}

**Erstellt:** {date}
**Erstellt von:** NEXUS AI Co-Pilot

---

## Zusammenfassung

{summary}

---

## Details

{details}

---

## Datenquellen

{sources}

---

*Dieser Report wurde automatisch von NEXUS generiert.*
"""


class ReportTool(BaseTool):
    """Tool for generating Markdown reports."""

    name = "generate_report"
    description = "Generiert einen Markdown-Report aus Analyseergebnissen und speichert ihn als Datei."

    async def execute(
        self,
        title: str,
        summary: str,
        details: str,
        sources: Optional[list] = None,
        save_to_file: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a Markdown report.

        Args:
            title: Report title
            summary: Executive summary
            details: Detailed findings
            sources: List of data sources used
            save_to_file: Whether to save as file

        Returns:
            Report metadata including file path if saved
        """
        try:
            # Format sources
            sources_text = "\n".join([f"- {s}" for s in (sources or ["Interne Datenbank"])])

            # Generate report content
            content = REPORT_TEMPLATE.format(
                title=title,
                date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                summary=summary,
                details=details,
                sources=sources_text,
            )

            result = {
                "title": title,
                "content_preview": content[:500] + "...",
                "content_length": len(content),
            }

            if save_to_file:
                # Generate file path
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_title = "".join(c if c.isalnum() else "_" for c in title[:30])
                file_dir = "/app/reports"
                file_path = f"{file_dir}/{timestamp}_{safe_title}.md"

                # Ensure directory exists
                os.makedirs(file_dir, exist_ok=True)

                # Write file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                result["file_path"] = file_path
                result["saved"] = True
                logger.info("report_generated", path=file_path)

            return result

        except Exception as e:
            logger.error("report_generation_error", error=str(e))
            return {"error": str(e), "saved": False}
