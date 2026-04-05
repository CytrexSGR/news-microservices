"""Template-based research automation engine."""

import logging
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.research import ResearchTemplate, ResearchTask
from app.services.research import research_service, ResearchService
from app.services.perplexity import perplexity_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class TemplateValidationError(Exception):
    """Exception raised for template validation errors."""
    pass


class TemplateEngine:
    """
    Template engine for automated research with variable substitution.

    Features:
    - Variable substitution with {{variable}} syntax
    - Required and optional parameters
    - Conditional logic (if/else)
    - Batch processing
    - Scheduled execution
    - Result aggregation
    - Template usage tracking
    """

    # Regular expressions for template parsing
    VARIABLE_PATTERN = re.compile(r'\{\{(\w+)\}\}')
    CONDITIONAL_PATTERN = re.compile(r'\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}', re.DOTALL)
    ELSE_PATTERN = re.compile(r'\{\{else\}\}')

    def __init__(self):
        self.research_service = research_service

    def parse_template(self, template_text: str) -> Dict[str, Any]:
        """
        Parse template and extract metadata.

        Args:
            template_text: Template string with {{variables}}

        Returns:
            Dictionary with variables, conditionals, and validation info
        """
        # Extract all variables
        variables = set(self.VARIABLE_PATTERN.findall(template_text))

        # Extract conditionals
        conditionals = []
        for match in self.CONDITIONAL_PATTERN.finditer(template_text):
            var_name = match.group(1)
            content = match.group(2)
            conditionals.append({
                "variable": var_name,
                "content": content,
                "has_else": bool(self.ELSE_PATTERN.search(content))
            })

        # Determine required vs optional variables
        required_vars = variables.copy()
        optional_vars = set()

        for cond in conditionals:
            # Variables in conditionals are optional
            if cond["variable"] in required_vars:
                required_vars.remove(cond["variable"])
                optional_vars.add(cond["variable"])

        return {
            "variables": list(variables),
            "required_variables": list(required_vars),
            "optional_variables": list(optional_vars),
            "conditionals": conditionals,
            "has_conditionals": len(conditionals) > 0
        }

    def validate_parameters(
        self,
        template: ResearchTemplate,
        variables: Dict[str, str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that all required parameters are provided.

        Args:
            template: ResearchTemplate instance
            variables: Variable substitution dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        metadata = self.parse_template(template.query_template)
        required = set(metadata["required_variables"])
        provided = set(variables.keys())

        # Check for missing required variables
        missing = required - provided
        if missing:
            return False, f"Missing required variables: {', '.join(sorted(missing))}"

        # Check for undefined variables
        allowed = set(metadata["variables"])
        undefined = provided - allowed
        if undefined:
            logger.warning(f"Undefined variables provided: {', '.join(sorted(undefined))}")

        return True, None

    def substitute_variables(
        self,
        template_text: str,
        variables: Dict[str, str]
    ) -> str:
        """
        Substitute variables in template.

        Args:
            template_text: Template string
            variables: Variable values

        Returns:
            Rendered template string
        """
        result = template_text

        # First, process conditionals
        result = self._process_conditionals(result, variables)

        # Then, substitute simple variables
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, str(var_value))

        return result

    def _process_conditionals(self, text: str, variables: Dict[str, str]) -> str:
        """Process if/else conditional blocks."""
        def replace_conditional(match):
            var_name = match.group(1)
            content = match.group(2)

            # Check if variable exists and is truthy
            var_value = variables.get(var_name, "")
            is_truthy = bool(var_value and var_value.lower() not in ["false", "0", "no", "none"])

            # Split on {{else}} if present
            else_match = self.ELSE_PATTERN.search(content)
            if else_match:
                if_content = content[:else_match.start()]
                else_content = content[else_match.end():]
                return if_content if is_truthy else else_content
            else:
                return content if is_truthy else ""

        return self.CONDITIONAL_PATTERN.sub(replace_conditional, text)

    async def render_query(
        self,
        db: Session,
        template: ResearchTemplate,
        variables: Dict[str, str]
    ) -> str:
        """
        Render template with variables and update usage stats.

        Args:
            db: Database session
            template: ResearchTemplate instance
            variables: Variable substitution dictionary

        Returns:
            Rendered query string

        Raises:
            TemplateValidationError: If validation fails
        """
        # Validate parameters
        is_valid, error = self.validate_parameters(template, variables)
        if not is_valid:
            raise TemplateValidationError(error)

        # Substitute variables
        query = self.substitute_variables(template.query_template, variables)

        # Update usage statistics
        template.usage_count += 1
        template.last_used_at = datetime.utcnow()
        db.commit()

        return query

    async def execute_template(
        self,
        db: Session,
        user_id: int,
        template: ResearchTemplate,
        variables: Dict[str, str],
        model_name: Optional[str] = None,
        depth: Optional[str] = None,
        feed_id: Optional[UUID] = None,
        legacy_feed_id: Optional[int] = None,
        article_id: Optional[UUID] = None,
        legacy_article_id: Optional[int] = None
    ) -> ResearchTask:
        """
        Execute research with rendered template.

        Args:
            db: Database session
            user_id: User ID
            template: ResearchTemplate instance
            variables: Variable substitution dictionary
            model_name: Override template's default model
            depth: Override template's default depth
            feed_id: Associated feed ID
            article_id: Associated article ID

        Returns:
            ResearchTask instance
        """
        # Render query
        query = await self.render_query(db, template, variables)

        # Use template defaults if not overridden
        if model_name is None:
            model_name = template.default_model
        if depth is None:
            depth = template.default_depth

        # Execute research
        task = await self.research_service.create_research_task(
            db=db,
            user_id=user_id,
            query=query,
            model_name=model_name,
            depth=depth,
            feed_id=feed_id,
            legacy_feed_id=legacy_feed_id,
            article_id=article_id,
            legacy_article_id=legacy_article_id,
        )

        return task

    async def batch_execute(
        self,
        db: Session,
        user_id: int,
        template: ResearchTemplate,
        variable_sets: List[Dict[str, str]],
        model_name: Optional[str] = None,
        depth: Optional[str] = None
    ) -> List[ResearchTask]:
        """
        Execute template with multiple variable sets in batch.

        Args:
            db: Database session
            user_id: User ID
            template: ResearchTemplate instance
            variable_sets: List of variable dictionaries
            model_name: Override template's default model
            depth: Override template's default depth

        Returns:
            List of ResearchTask instances
        """
        tasks = []

        for variables in variable_sets:
            try:
                task = await self.execute_template(
                    db=db,
                    user_id=user_id,
                    template=template,
                    variables=variables,
                    model_name=model_name,
                    depth=depth
                )
                tasks.append(task)
            except Exception as e:
                logger.error(f"Batch execution failed for variables {variables}: {e}")
                # Continue with other items

        return tasks

    async def schedule_execution(
        self,
        db: Session,
        user_id: int,
        template: ResearchTemplate,
        variables: Dict[str, str],
        schedule_at: datetime,
        model_name: Optional[str] = None,
        depth: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule template execution for future time.

        Args:
            db: Database session
            user_id: User ID
            template: ResearchTemplate instance
            variables: Variable substitution dictionary
            schedule_at: Scheduled execution time
            model_name: Override template's default model
            depth: Override template's default depth

        Returns:
            Scheduling information
        """
        from app.workers.tasks import process_template_execution

        # Validate parameters first
        is_valid, error = self.validate_parameters(template, variables)
        if not is_valid:
            raise TemplateValidationError(error)

        # Schedule Celery task
        eta = schedule_at if schedule_at > datetime.utcnow() else None

        task = process_template_execution.apply_async(
            kwargs={
                "user_id": user_id,
                "template_id": template.id,
                "variables": variables,
                "model_name": model_name or template.default_model,
                "depth": depth or template.default_depth
            },
            eta=eta
        )

        return {
            "celery_task_id": task.id,
            "scheduled_at": schedule_at,
            "template_id": template.id,
            "status": "scheduled"
        }

    async def aggregate_results(
        self,
        db: Session,
        task_ids: List[int],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple template executions.

        Args:
            db: Database session
            task_ids: List of ResearchTask IDs
            user_id: User ID (for access control)

        Returns:
            Aggregated results and statistics
        """
        # Fetch tasks
        tasks = db.query(ResearchTask).filter(
            and_(
                ResearchTask.id.in_(task_ids),
                ResearchTask.user_id == user_id
            )
        ).all()

        if not tasks:
            return {
                "tasks": [],
                "total": 0,
                "completed": 0,
                "failed": 0,
                "pending": 0
            }

        # Aggregate statistics
        completed_tasks = [t for t in tasks if t.status == "completed"]
        failed_tasks = [t for t in tasks if t.status == "failed"]
        pending_tasks = [t for t in tasks if t.status in ["pending", "processing"]]

        total_tokens = sum(t.tokens_used for t in completed_tasks)
        total_cost = sum(t.cost for t in completed_tasks)

        # Extract all citations and sources
        all_citations = []
        all_sources = []
        seen_sources = set()

        for task in completed_tasks:
            if task.result:
                citations = task.result.get("citations", [])
                sources = task.result.get("sources", [])

                all_citations.extend(citations)

                for source in sources:
                    url = source.get("url")
                    if url and url not in seen_sources:
                        all_sources.append(source)
                        seen_sources.add(url)

        # Create consolidated content
        consolidated_content = "\n\n".join([
            f"Query: {t.query}\n{t.result.get('content', '')}"
            for t in completed_tasks if t.result
        ])

        return {
            "total": len(tasks),
            "completed": len(completed_tasks),
            "failed": len(failed_tasks),
            "pending": len(pending_tasks),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "unique_sources": len(all_sources),
            "tasks": [
                {
                    "id": t.id,
                    "query": t.query,
                    "status": t.status,
                    "result": t.result,
                    "tokens_used": t.tokens_used,
                    "cost": t.cost,
                    "created_at": t.created_at,
                    "completed_at": t.completed_at
                }
                for t in tasks
            ],
            "aggregated_content": consolidated_content,
            "all_citations": all_citations,
            "unique_sources": all_sources
        }

    async def track_template_usage(
        self,
        db: Session,
        template_id: int,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Track template usage statistics.

        Args:
            db: Database session
            template_id: ResearchTemplate ID
            user_id: User ID (for access control)
            days: Number of days to analyze

        Returns:
            Usage statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get template
        template = db.query(ResearchTemplate).filter(
            ResearchTemplate.id == template_id
        ).first()

        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Count tasks using this template (we need to track this separately)
        # For now, we'll use the template's usage_count

        return {
            "template_id": template.id,
            "template_name": template.name,
            "total_usage": template.usage_count,
            "last_used": template.last_used_at,
            "created_at": template.created_at,
            "is_active": template.is_active,
            "is_public": template.is_public
        }

    def preview_template(
        self,
        template: ResearchTemplate,
        variables: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Preview rendered template without executing.

        Args:
            template: ResearchTemplate instance
            variables: Variable substitution dictionary

        Returns:
            Preview information
        """
        # Validate
        is_valid, error = self.validate_parameters(template, variables)

        rendered_query = None
        if is_valid:
            try:
                rendered_query = self.substitute_variables(
                    template.query_template,
                    variables
                )
            except Exception as e:
                error = str(e)
                is_valid = False

        # Estimate cost
        estimated_tokens = len(rendered_query.split()) * 1.3 if rendered_query else 0
        estimated_cost = settings.calculate_cost(
            int(estimated_tokens),
            template.default_model
        )

        return {
            "template_id": template.id,
            "template_name": template.name,
            "is_valid": is_valid,
            "error": error,
            "rendered_query": rendered_query,
            "estimated_tokens": int(estimated_tokens),
            "estimated_cost": estimated_cost,
            "model": template.default_model,
            "depth": template.default_depth
        }

    async def create_from_pattern(
        self,
        db: Session,
        user_id: int,
        pattern_name: str,
        context: Dict[str, str]
    ) -> ResearchTemplate:
        """
        Create template from predefined patterns.

        Common patterns:
        - feed_analysis: Analyze RSS feed for topics
        - article_summary: Deep dive into article
        - trend_detection: Detect trends in topic
        - fact_check: Verify claims with sources

        Args:
            db: Database session
            user_id: User ID
            pattern_name: Name of predefined pattern
            context: Pattern-specific context

        Returns:
            Created ResearchTemplate
        """
        patterns = {
            "feed_analysis": {
                "name": f"Feed Analysis: {context.get('topic', 'General')}",
                "description": "Analyze RSS feed articles for key themes and insights",
                "query_template": "Analyze recent articles about {{topic}} from {{feed_name}}. "
                                  "Identify key themes, emerging trends, and notable insights. "
                                  "{{#if time_range}}Focus on articles from {{time_range}}.{{/if}}",
                "parameters": {
                    "topic": "Main topic or keyword",
                    "feed_name": "RSS feed name",
                    "time_range": "(Optional) Time range to analyze"
                }
            },
            "article_summary": {
                "name": f"Article Deep Dive: {context.get('article_title', 'Unknown')}",
                "description": "Deep research into article topic with multiple sources",
                "query_template": "Provide comprehensive research on: {{article_title}}. "
                                  "Include context, expert opinions, and related developments. "
                                  "{{#if specific_aspect}}Focus particularly on {{specific_aspect}}.{{/if}}",
                "parameters": {
                    "article_title": "Article title or main topic",
                    "specific_aspect": "(Optional) Specific aspect to focus on"
                }
            },
            "trend_detection": {
                "name": f"Trend Analysis: {context.get('domain', 'General')}",
                "description": "Detect and analyze emerging trends",
                "query_template": "Identify emerging trends in {{domain}} over the past {{timeframe}}. "
                                  "Analyze growth patterns, key drivers, and future implications.",
                "parameters": {
                    "domain": "Domain or industry",
                    "timeframe": "Time period (e.g., 'month', 'quarter')"
                }
            },
            "fact_check": {
                "name": f"Fact Check: {context.get('claim', 'Claim')}",
                "description": "Verify claims with authoritative sources",
                "query_template": "Fact-check the following claim: {{claim}}. "
                                  "Provide evidence from authoritative sources, "
                                  "noting any context or nuance. "
                                  "{{#if claimant}}The claim was made by {{claimant}}.{{/if}}",
                "parameters": {
                    "claim": "Claim to verify",
                    "claimant": "(Optional) Person/organization making the claim"
                }
            }
        }

        pattern = patterns.get(pattern_name)
        if not pattern:
            raise ValueError(f"Unknown pattern: {pattern_name}")

        template = ResearchTemplate(
            user_id=user_id,
            name=pattern["name"],
            description=pattern["description"],
            query_template=pattern["query_template"],
            parameters=pattern["parameters"],
            default_model="sonar",
            default_depth="standard"
        )

        db.add(template)
        db.commit()
        db.refresh(template)

        return template


# Global template engine instance
template_engine = TemplateEngine()
