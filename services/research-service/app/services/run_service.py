"""Research Run Service for managing batch/scheduled research executions."""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.config import settings
from app.models.research import ResearchRun, ResearchTemplate, CostTracking
from app.services.research import research_service, template_service

logger = logging.getLogger(__name__)


class ResearchRunService:
    """Service for managing research runs (batch/scheduled executions)."""

    async def create_run(
        self,
        db: Session,
        user_id: int,
        template_id: UUID,
        parameters: Dict[str, str],
        model_name: Optional[str] = None,
        depth: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        is_recurring: bool = False,
        recurrence_pattern: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ResearchRun:
        """Create a research run."""

        # Get template
        template = db.query(ResearchTemplate).filter(
            and_(
                ResearchTemplate.id == template_id,
                (ResearchTemplate.user_id == user_id) | (ResearchTemplate.is_public == True)
            )
        ).first()

        if not template:
            raise ValueError("Template not found or access denied")

        # Create run
        run = ResearchRun(
            user_id=user_id,
            template_id=template_id,
            template_name=template.name,
            parameters=parameters,
            model_name=model_name or template.default_model,
            depth=depth or template.default_depth,
            scheduled_at=scheduled_at,
            is_recurring=is_recurring,
            recurrence_pattern=recurrence_pattern,
            status="pending",
            triggered_by="manual" if not scheduled_at else "schedule",
            metadata=metadata or {}
        )

        db.add(run)
        db.commit()
        db.refresh(run)

        # If not scheduled, execute immediately
        if not scheduled_at:
            await self._execute_run(db, run)

        return run

    async def get_run(
        self, db: Session, run_id: UUID, user_id: int
    ) -> Optional[ResearchRun]:
        """Get a research run by ID."""
        return db.query(ResearchRun).filter(
            and_(ResearchRun.id == run_id, ResearchRun.user_id == user_id)
        ).first()

    async def list_runs(
        self,
        db: Session,
        user_id: int,
        status: Optional[str] = None,
        template_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[ResearchRun], int]:
        """List research runs with pagination."""
        query = db.query(ResearchRun).filter(ResearchRun.user_id == user_id)

        if status:
            query = query.filter(ResearchRun.status == status)
        if template_id:
            query = query.filter(ResearchRun.template_id == template_id)

        total = query.count()
        runs = query.order_by(ResearchRun.created_at.desc()).offset(skip).limit(limit).all()

        return runs, total

    async def get_run_status(
        self, db: Session, run_id: UUID, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get detailed status of a research run."""
        run = await self.get_run(db, run_id, user_id)
        if not run:
            return None

        # Calculate progress
        progress = 0.0
        if run.tasks_created > 0:
            progress = ((run.tasks_completed + run.tasks_failed) / run.tasks_created) * 100
        elif run.status == "completed":
            progress = 100.0

        return {
            "id": run.id,
            "status": run.status,
            "progress": progress,
            "tasks_created": run.tasks_created,
            "tasks_completed": run.tasks_completed,
            "tasks_failed": run.tasks_failed,
            "total_tokens_used": run.total_tokens_used,
            "total_cost": run.total_cost,
            "error_message": run.error_message
        }

    async def cancel_run(
        self, db: Session, run_id: UUID, user_id: int
    ) -> bool:
        """Cancel a pending or running research run."""
        run = await self.get_run(db, run_id, user_id)
        if not run:
            return False

        if run.status not in ["pending", "running"]:
            raise ValueError(f"Cannot cancel run with status: {run.status}")

        run.status = "cancelled"
        run.completed_at = datetime.utcnow()
        db.commit()

        return True

    async def _execute_run(self, db: Session, run: ResearchRun):
        """Execute a research run."""
        try:
            run.status = "running"
            run.started_at = datetime.utcnow()
            db.commit()

            # Get template
            template = db.query(ResearchTemplate).filter(
                ResearchTemplate.id == run.template_id
            ).first()

            if not template:
                raise ValueError("Template not found")

            # Apply template with parameters
            rendered_query = await template_service.apply_template(
                db, template, run.parameters
            )

            # Create research task
            task = await research_service.create_research_task(
                db=db,
                user_id=run.user_id,
                query=rendered_query,
                model_name=run.model_name,
                depth=run.depth
            )

            # Link task to run
            task.run_id = run.id
            db.commit()

            # Update run statistics
            run.tasks_created = 1

            if task.status == "completed":
                run.tasks_completed = 1
                run.total_tokens_used = task.tokens_used
                run.total_cost = task.cost
                run.results_summary = {
                    "task_id": task.id,
                    "result": task.result
                }
                run.status = "completed"
            elif task.status == "failed":
                run.tasks_failed = 1
                run.error_message = task.error_message
                run.status = "failed"

            run.completed_at = datetime.utcnow()

            # Track cost
            if settings.ENABLE_COST_TRACKING and task.cost > 0:
                cost_entry = CostTracking(
                    user_id=run.user_id,
                    run_id=run.id,
                    task_id=task.id,
                    model_name=run.model_name,
                    tokens_used=task.tokens_used,
                    cost=task.cost,
                    date=datetime.utcnow()
                )
                db.add(cost_entry)

            db.commit()

        except Exception as e:
            logger.error(f"Research run failed: {e}")
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.commit()


# Global service instance
run_service = ResearchRunService()
