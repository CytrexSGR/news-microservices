"""Research service with business logic."""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Type
from uuid import UUID

import redis
from pydantic import BaseModel
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.research import (
    ResearchTask,
    ResearchTemplate,
    ResearchCache,
    CostTracking,
)
from app.services.perplexity import perplexity_client
from app.services.cost_optimizer import cost_optimizer, CostTier

logger = logging.getLogger(__name__)


class ResearchFunction:
    """Base class for specialized research functions."""

    def __init__(
        self,
        name: str,
        description: str,
        model: str = "sonar",
        depth: str = "standard",
        output_schema: Optional[Type[BaseModel]] = None,
    ):
        self.name = name
        self.description = description
        self.model = model
        self.depth = depth
        self.output_schema = output_schema

    def build_prompt(self, **kwargs) -> str:
        """Build the research prompt. Override in subclasses."""
        raise NotImplementedError

    async def execute(
        self,
        db: Session,
        user_id: int,
        cache_enabled: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute the research function."""
        # Extract feed/article IDs from kwargs
        feed_id = kwargs.pop('feed_id', None)
        legacy_feed_id = kwargs.pop('legacy_feed_id', None)
        article_id = kwargs.pop('article_id', None)
        legacy_article_id = kwargs.pop('legacy_article_id', None)

        # Build prompt with remaining kwargs
        prompt = self.build_prompt(**kwargs)

        # Debug: Check output_schema
        logger.info(f"ResearchFunction.execute: self.output_schema = {self.output_schema}, type: {type(self.output_schema) if self.output_schema else 'None'}")

        # Use research service to execute
        service = ResearchService()
        task = await service.create_research_task(
            db=db,
            user_id=user_id,
            query=prompt,
            model_name=self.model,
            depth=self.depth,
            output_schema=self.output_schema,
            cache_enabled=cache_enabled,
            feed_id=feed_id,
            legacy_feed_id=legacy_feed_id,
            article_id=article_id,
            legacy_article_id=legacy_article_id,
        )

        return {
            "function": self.name,
            "task_id": task.id,
            "status": task.status,
            "result": task.result,
            "structured_data": task.structured_data,
            "validation_status": task.validation_status,
            "cost": task.cost,
            "tokens_used": task.tokens_used,
        }


class DeepArticleAnalysis(ResearchFunction):
    """Deep analysis of article content and context."""

    def __init__(self):
        super().__init__(
            name="deep_article_analysis",
            description="Comprehensive analysis of article content, context, and implications",
            model="sonar-pro",
            depth="deep"
        )

    def build_prompt(self, article_title: str, article_content: str, article_url: Optional[str] = None) -> str:
        prompt = f"""Perform a comprehensive deep analysis of the following article:

Title: {article_title}
{f'URL: {article_url}' if article_url else ''}

Content:
{article_content}

Provide a detailed analysis including:
1. Main arguments and claims
2. Evidence quality and credibility
3. Logical structure and coherence
4. Underlying assumptions
5. Potential biases or perspectives
6. Context and background information
7. Implications and consequences
8. Connections to broader themes
9. Credibility assessment
10. Key takeaways

Format as structured JSON with sections for each aspect."""
        return prompt


class FactChecking(ResearchFunction):
    """Verify claims and statements with sources."""

    def __init__(self):
        super().__init__(
            name="fact_checking",
            description="Verify factual claims with authoritative sources",
            model="sonar-reasoning-pro",
            depth="deep"
        )

    def build_prompt(self, claims: List[str], context: Optional[str] = None) -> str:
        claims_text = "\n".join([f"{i+1}. {claim}" for i, claim in enumerate(claims)])

        prompt = f"""Fact-check the following claims with authoritative sources:

{claims_text}

{f'Context: {context}' if context else ''}

For each claim, provide:
1. Verification status (true, false, partially true, unverifiable)
2. Confidence level (0-100%)
3. Supporting evidence with citations
4. Contradicting evidence if any
5. Expert consensus
6. Source reliability assessment
7. Important nuances or context

Return as structured JSON with array of fact-checks."""
        return prompt


class SourceVerification(ResearchFunction):
    """Verify and assess source credibility."""

    def __init__(self):
        super().__init__(
            name="source_verification",
            description="Assess credibility and reliability of information sources",
            model="sonar-pro",
            depth="standard"
        )

    def build_prompt(self, sources: List[str], domain: Optional[str] = None) -> str:
        sources_text = "\n".join([f"- {source}" for source in sources])

        prompt = f"""Verify and assess the credibility of these sources:

{sources_text}

{f'Domain/Topic: {domain}' if domain else ''}

For each source, analyze:
1. Authority and expertise
2. Reputation and track record
3. Bias indicators
4. Transparency and accountability
5. Fact-checking history
6. Editorial standards
7. Funding and ownership
8. Expert opinions
9. Overall credibility score (0-100)
10. Usage recommendations

Return as structured JSON with detailed assessments."""
        return prompt


class TopicExtraction(ResearchFunction):
    """Extract and analyze topics and themes."""

    def __init__(self):
        super().__init__(
            name="topic_extraction",
            description="Extract main topics, themes, and related concepts",
            model="sonar",
            depth="standard"
        )

    def build_prompt(self, content: str, max_topics: int = 10) -> str:
        prompt = f"""Extract and analyze the main topics from this content:

{content}

Identify up to {max_topics} topics including:
1. Primary topics (main subjects)
2. Secondary topics (supporting themes)
3. Related concepts and keywords
4. Topic relationships and connections
5. Topic hierarchy (parent/child topics)
6. Emerging themes
7. Topic relevance scores
8. Domain classification
9. Trending connections
10. Semantic clusters

Return as structured JSON with topic taxonomy."""
        return prompt


class RelatedContentDiscovery(ResearchFunction):
    """Discover related content and articles."""

    def __init__(self):
        super().__init__(
            name="related_content_discovery",
            description="Find related articles, studies, and content",
            model="sonar-pro",
            depth="deep"
        )

    def build_prompt(self, topic: str, keywords: List[str], timeframe: str = "month") -> str:
        keywords_text = ", ".join(keywords)

        prompt = f"""Find related content and articles about:

Topic: {topic}
Keywords: {keywords_text}
Timeframe: Last {timeframe}

Discover and analyze:
1. Recent articles on this topic
2. Academic studies and papers
3. Expert opinions and analyses
4. Statistical data and reports
5. Case studies and examples
6. Debates and controversies
7. Alternative perspectives
8. Related events and developments
9. Key figures and organizations
10. Recommended reading list

Provide URLs, titles, summaries, and relevance scores. Return as structured JSON."""
        return prompt


class TimelineGeneration(ResearchFunction):
    """Generate event timelines and chronologies."""

    def __init__(self):
        super().__init__(
            name="timeline_generation",
            description="Create chronological timelines of events and developments",
            model="sonar-pro",
            depth="deep"
        )

    def build_prompt(self, topic: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        date_range = ""
        if start_date or end_date:
            date_range = f"\nDate range: {start_date or 'earliest'} to {end_date or 'present'}"

        prompt = f"""Create a comprehensive timeline for:

Topic: {topic}{date_range}

Generate a detailed timeline including:
1. Key events in chronological order
2. Dates and timeframes
3. Event descriptions and context
4. Cause-and-effect relationships
5. Turning points and milestones
6. Parallel developments
7. Leading figures and organizations
8. Impact and consequences
9. Related sub-events
10. Sources and citations

Return as structured JSON with timeline array."""
        return prompt


class ExpertIdentification(ResearchFunction):
    """Identify experts and thought leaders."""

    def __init__(self):
        super().__init__(
            name="expert_identification",
            description="Find experts, researchers, and thought leaders in a field",
            model="sonar-pro",
            depth="standard"
        )

    def build_prompt(self, field: str, sub_topics: Optional[List[str]] = None) -> str:
        topics_text = ""
        if sub_topics:
            topics_text = f"\nSpecific topics: {', '.join(sub_topics)}"

        prompt = f"""Identify experts and thought leaders in:

Field: {field}{topics_text}

For each expert, provide:
1. Name and credentials
2. Institutional affiliation
3. Areas of expertise
4. Notable publications and research
5. Citations and impact
6. Social media presence
7. Recent contributions
8. Perspective and approach
9. Credibility indicators
10. Contact information (if public)

Return as structured JSON with expert profiles."""
        return prompt


class StatisticalAnalysis(ResearchFunction):
    """Analyze statistical data and trends."""

    def __init__(self):
        super().__init__(
            name="statistical_analysis",
            description="Analyze statistical data, trends, and patterns",
            model="sonar-reasoning-pro",
            depth="deep"
        )

    def build_prompt(self, topic: str, metrics: Optional[List[str]] = None) -> str:
        metrics_text = ""
        if metrics:
            metrics_text = f"\nSpecific metrics: {', '.join(metrics)}"

        prompt = f"""Perform statistical analysis on:

Topic: {topic}{metrics_text}

Analyze and provide:
1. Current statistics and data points
2. Historical trends and patterns
3. Growth rates and changes
4. Statistical significance
5. Correlations and relationships
6. Outliers and anomalies
7. Comparative analysis (regions, demographics, etc.)
8. Projections and forecasts
9. Data sources and methodology
10. Visualizable data summaries

Return as structured JSON with statistical findings."""
        return prompt


class TrendDetection(ResearchFunction):
    """Detect emerging trends and patterns."""

    def __init__(self):
        super().__init__(
            name="trend_detection",
            description="Identify emerging trends, patterns, and shifts",
            model="sonar-pro",
            depth="deep"
        )

    def build_prompt(self, domain: str, timeframe: str = "6 months") -> str:
        prompt = f"""Detect and analyze emerging trends in:

Domain: {domain}
Analysis period: Last {timeframe}

Identify and analyze:
1. Emerging trends and patterns
2. Trend strength and momentum
3. Early indicators and signals
4. Adoption curves
5. Geographic distribution
6. Demographic patterns
7. Driving forces and factors
8. Potential disruptions
9. Future trajectory predictions
10. Investment and attention metrics

Return as structured JSON with trend analysis."""
        return prompt


class ClaimVerification(ResearchFunction):
    """Verify specific claims with evidence."""

    def __init__(self):
        super().__init__(
            name="claim_verification",
            description="Verify specific claims with authoritative evidence",
            model="sonar-reasoning-pro",
            depth="deep"
        )

    def build_prompt(self, claim: str, context: Optional[str] = None) -> str:
        prompt = f"""Verify this specific claim:

Claim: {claim}

{f'Context: {context}' if context else ''}

Provide comprehensive verification:
1. Truthfulness assessment (true/false/partial/misleading)
2. Confidence level (0-100%)
3. Supporting evidence with citations
4. Contradicting evidence
5. Expert opinions
6. Original source if available
7. Similar claims and their verification
8. Common misconceptions
9. Important context and nuances
10. Verification methodology

Return as structured JSON with verification details."""
        return prompt


class ComparativeAnalysis(ResearchFunction):
    """Compare multiple topics, perspectives, or approaches."""

    def __init__(self):
        super().__init__(
            name="comparative_analysis",
            description="Compare and contrast topics, perspectives, or approaches",
            model="sonar-pro",
            depth="deep"
        )

    def build_prompt(self, items: List[str], comparison_aspects: Optional[List[str]] = None) -> str:
        items_text = "\n".join([f"- {item}" for item in items])
        aspects_text = ""
        if comparison_aspects:
            aspects_text = f"\n\nCompare these aspects:\n" + "\n".join([f"- {aspect}" for aspect in comparison_aspects])

        prompt = f"""Perform a comprehensive comparative analysis of:

{items_text}{aspects_text}

Provide detailed comparison including:
1. Key similarities
2. Important differences
3. Strengths and weaknesses of each
4. Use cases and applications
5. Performance metrics
6. Cost-benefit analysis
7. Expert preferences
8. Historical evolution
9. Future outlook
10. Recommendation matrix

Return as structured JSON with comparison table."""
        return prompt


class ImpactAssessment(ResearchFunction):
    """Assess impact and consequences of events or decisions."""

    def __init__(self):
        super().__init__(
            name="impact_assessment",
            description="Assess impact, consequences, and ripple effects",
            model="sonar-reasoning-pro",
            depth="deep"
        )

    def build_prompt(self, event_or_decision: str, stakeholders: Optional[List[str]] = None) -> str:
        stakeholders_text = ""
        if stakeholders:
            stakeholders_text = f"\n\nStakeholders: {', '.join(stakeholders)}"

        prompt = f"""Assess the impact of:

{event_or_decision}{stakeholders_text}

Analyze impact across:
1. Immediate effects
2. Short-term consequences (weeks/months)
3. Long-term implications (years)
4. Direct impacts
5. Indirect and ripple effects
6. Economic impacts
7. Social and cultural effects
8. Environmental considerations
9. Policy implications
10. Mitigation strategies

Return as structured JSON with impact analysis."""
        return prompt


# Registry of all research functions
RESEARCH_FUNCTIONS = {
    "deep_article_analysis": DeepArticleAnalysis,
    "fact_checking": FactChecking,
    "source_verification": SourceVerification,
    "topic_extraction": TopicExtraction,
    "related_content_discovery": RelatedContentDiscovery,
    "timeline_generation": TimelineGeneration,
    "expert_identification": ExpertIdentification,
    "statistical_analysis": StatisticalAnalysis,
    "trend_detection": TrendDetection,
    "claim_verification": ClaimVerification,
    "comparative_analysis": ComparativeAnalysis,
    "impact_assessment": ImpactAssessment,
}


def get_research_function(function_name: str) -> Optional[ResearchFunction]:
    """Get a research function by name."""
    function_class = RESEARCH_FUNCTIONS.get(function_name)
    if function_class:
        return function_class()
    return None


def list_research_functions() -> List[Dict[str, str]]:
    """List all available research functions."""
    return [
        {
            "name": func_class().name,
            "description": func_class().description,
            "model": func_class().model,
            "depth": func_class().depth
        }
        for func_class in RESEARCH_FUNCTIONS.values()
    ]


class ResearchService:
    """Service for managing research tasks."""
    
    def __init__(self):
        self.redis_client = None
        if settings.CACHE_ENABLED:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL)
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
    
    async def create_research_task(
        self,
        db: Session,
        user_id: int,
        query: str,
        model_name: str = "sonar",
        depth: str = "standard",
        feed_id: Optional[UUID] = None,
        legacy_feed_id: Optional[int] = None,
        article_id: Optional[UUID] = None,
        legacy_article_id: Optional[int] = None,
        optimize_cost: bool = True,
        output_schema: Optional[Type[BaseModel]] = None,
        cache_enabled: bool = True,
    ) -> ResearchTask:
        """Create and execute a research task with cost optimization."""

        # Cost optimization logic
        if optimize_cost and settings.ENABLE_COST_TRACKING:
            # Estimate query complexity
            query_complexity = cost_optimizer.estimate_query_complexity(query)

            # Check cache availability
            cache_key = self._generate_cache_key(query, model_name, depth)
            cache_available = False
            cache_age_seconds = None

            if settings.CACHE_ENABLED and cache_enabled:
                cached_result = await self._get_cached_result(query, model_name, depth)
                if cached_result:
                    cache_available = True
                    # Try to get cache age from Redis
                    try:
                        ttl = self.redis_client.ttl(cache_key)
                        if ttl > 0:
                            cache_age_seconds = settings.CACHE_RESEARCH_RESULTS_TTL - ttl
                    except Exception:
                        cache_age_seconds = 0

            # Get budget status
            predicted_cost = cost_optimizer.predict_cost(
                CostTier(depth),
                len(query),
                use_cache=cache_available
            )
            budget_status = await cost_optimizer.check_budget_limits(
                db, user_id, predicted_cost
            )

            # Select optimal tier
            selected_tier = cost_optimizer.select_tier(
                user_preference=depth,
                query_complexity=query_complexity,
                budget_remaining=budget_status["daily_remaining"],
                cache_available=cache_available
            )

            # Get tier configuration
            tier_config = cost_optimizer.get_tier_config(selected_tier)

            # Decide whether to use cache
            should_use_cache = cost_optimizer.should_use_cache(
                selected_tier,
                cache_age_seconds,
                budget_status["budget_pressure"]
            )

            # Override depth and model based on optimization
            if selected_tier != CostTier(depth):
                logger.info(
                    f"Cost optimizer adjusted tier from {depth} to {selected_tier.value}"
                )
                depth = selected_tier.value
                model_name = tier_config.model

            # Use cache if optimizer recommends
            if should_use_cache and cache_available:
                logger.info(f"Cost optimizer recommends using cache for query: {query[:50]}...")
                return self._create_task_from_cache(
                    db, user_id, query, model_name, depth, cached_result, feed_id, legacy_feed_id, article_id, legacy_article_id
                )

            # Check if can afford after optimization
            if not budget_status["can_afford"]:
                raise ValueError(
                    f"Insufficient budget for research query. "
                    f"Daily: ${budget_status['daily_remaining']:.2f} remaining, "
                    f"Monthly: ${budget_status['monthly_remaining']:.2f} remaining"
                )

        # Original check daily cost limit (fallback if optimization disabled)
        elif settings.ENABLE_COST_TRACKING:
            await self._check_cost_limits(db, user_id)

        # Check cache (original logic if optimization disabled)
        if settings.CACHE_ENABLED and cache_enabled and not optimize_cost:
            cached_result = await self._get_cached_result(query, model_name, depth)
            if cached_result:
                logger.info(f"Cache hit for query: {query[:50]}...")
                return self._create_task_from_cache(
                    db, user_id, query, model_name, depth, cached_result, feed_id, legacy_feed_id, article_id, legacy_article_id
                )
        
        # Serialize output_schema if provided
        schema_data = None
        if output_schema:
            logger.info(f"output_schema provided: {output_schema}, type: {type(output_schema)}")
            try:
                schema_data = output_schema.model_json_schema()
                logger.info(f"Successfully serialized output_schema, result type: {type(schema_data)}, keys: {list(schema_data.keys()) if isinstance(schema_data, dict) else 'N/A'}")
            except Exception as e:
                logger.warning(f"Failed to serialize output_schema: {e}")
        else:
            logger.info("No output_schema provided to create_research_task")

        # Create task
        task = ResearchTask(
            user_id=user_id,
            query=query,
            model_name=model_name,
            depth=depth,
            status="pending",
            feed_id=feed_id,
            legacy_feed_id=legacy_feed_id,
            article_id=article_id,
            legacy_article_id=legacy_article_id,
            output_schema=schema_data
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Dispatch to Celery worker for async processing
        from app.workers.tasks import research_task as celery_research_task

        try:
            celery_result = celery_research_task.delay(str(task.id))
            logger.info(f"Dispatched research task {task.id} to Celery (celery_task_id: {celery_result.id})")
        except Exception as e:
            logger.error(f"Failed to dispatch task to Celery: {e}")
            task.status = "failed"
            task.error_message = f"Failed to dispatch to Celery: {str(e)}"
            db.commit()

        return task
    
    async def get_task(self, db: Session, task_id: int, user_id: int) -> Optional[ResearchTask]:
        """Get a research task by ID."""
        return db.query(ResearchTask).filter(
            and_(ResearchTask.id == task_id, ResearchTask.user_id == user_id)
        ).first()
    
    async def list_tasks(
        self,
        db: Session,
        user_id: int,
        status: Optional[str] = None,
        feed_id: Optional[UUID] = None,
        legacy_feed_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[ResearchTask], int]:
        """List research tasks with pagination."""
        query = db.query(ResearchTask).filter(ResearchTask.user_id == user_id)
        
        if status:
            query = query.filter(ResearchTask.status == status)
        if feed_id:
            query = query.filter(ResearchTask.feed_id == feed_id)
        if legacy_feed_id:
            query = query.filter(ResearchTask.legacy_feed_id == legacy_feed_id)
        
        total = query.count()
        tasks = query.order_by(ResearchTask.created_at.desc()).offset(skip).limit(limit).all()
        
        return tasks, total
    
    async def _check_cost_limits(self, db: Session, user_id: int):
        """Check if user has exceeded cost limits."""
        today = datetime.utcnow().date()
        
        # Check daily limit
        daily_cost = db.query(func.sum(CostTracking.cost)).filter(
            and_(
                CostTracking.user_id == user_id,
                func.date(CostTracking.date) == today
            )
        ).scalar() or 0.0
        
        if daily_cost >= settings.MAX_DAILY_COST:
            raise ValueError(f"Daily cost limit exceeded: ${daily_cost:.2f} / ${settings.MAX_DAILY_COST:.2f}")
        
        # Check monthly limit
        month_start = datetime(today.year, today.month, 1)
        monthly_cost = db.query(func.sum(CostTracking.cost)).filter(
            and_(
                CostTracking.user_id == user_id,
                CostTracking.date >= month_start
            )
        ).scalar() or 0.0
        
        if monthly_cost >= settings.MAX_MONTHLY_COST:
            raise ValueError(f"Monthly cost limit exceeded: ${monthly_cost:.2f} / ${settings.MAX_MONTHLY_COST:.2f}")
        
        # Alert if approaching limit
        if daily_cost >= settings.MAX_DAILY_COST * settings.COST_ALERT_THRESHOLD:
            logger.warning(f"User {user_id} approaching daily cost limit: ${daily_cost:.2f}")
    
    async def _get_cached_result(
        self, query: str, model_name: str, depth: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached research result."""
        if not self.redis_client:
            return None
        
        cache_key = self._generate_cache_key(query, model_name, depth)
        
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
        
        return None
    
    async def _cache_result(
        self, query: str, model_name: str, depth: str, result: Dict[str, Any],
        tokens_used: int, cost: float
    ):
        """Cache research result."""
        if not self.redis_client:
            return
        
        cache_key = self._generate_cache_key(query, model_name, depth)
        cache_data = {
            "result": result,
            "tokens_used": tokens_used,
            "cost": cost,
        }
        
        try:
            self.redis_client.setex(
                cache_key,
                settings.CACHE_RESEARCH_RESULTS_TTL,
                json.dumps(cache_data)
            )
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
    
    def _generate_cache_key(self, query: str, model_name: str, depth: str) -> str:
        """Generate cache key from query parameters."""
        content = f"{query}:{model_name}:{depth}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _create_task_from_cache(
        self,
        db: Session,
        user_id: int,
        query: str,
        model_name: str,
        depth: str,
        cached_data: Dict[str, Any],
        feed_id: Optional[UUID],
        legacy_feed_id: Optional[int],
        article_id: Optional[UUID],
        legacy_article_id: Optional[int],
    ) -> ResearchTask:
        """Create task from cached result."""
        task = ResearchTask(
            user_id=user_id,
            query=query,
            model_name=model_name,
            depth=depth,
            status="completed",
            result=cached_data["result"],
            tokens_used=cached_data.get("tokens_used", 0),
            cost=cached_data.get("cost", 0.0),
            feed_id=feed_id,
            legacy_feed_id=legacy_feed_id,
            article_id=article_id,
            legacy_article_id=legacy_article_id,
            structured_data=cached_data["result"].get("structured_data"),
            validation_status=cached_data["result"].get("validation_status"),
            completed_at=datetime.utcnow(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    def _track_cost(
        self,
        db: Session,
        user_id: int,
        task_id: UUID,
        model_name: str,
        tokens_used: int,
        cost: float,
    ):
        """Track research cost."""
        cost_entry = CostTracking(
            user_id=user_id,
            task_id=task_id,
            model_name=model_name,
            tokens_used=tokens_used,
            cost=cost,
            date=datetime.utcnow()
        )
        db.add(cost_entry)
        db.commit()
    
    async def get_usage_stats(
        self, db: Session, user_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """Get usage statistics for a user."""
        start_date = datetime.utcnow() - timedelta(days=days)

        stats = db.query(
            func.count(CostTracking.id).label("total_requests"),
            func.sum(CostTracking.tokens_used).label("total_tokens"),
            func.sum(CostTracking.cost).label("total_cost")
        ).filter(
            and_(
                CostTracking.user_id == user_id,
                CostTracking.date >= start_date
            )
        ).first()

        # Get stats by model
        model_stats = db.query(
            CostTracking.model_name,
            func.count(CostTracking.id).label("requests"),
            func.sum(CostTracking.cost).label("cost")
        ).filter(
            and_(
                CostTracking.user_id == user_id,
                CostTracking.date >= start_date
            )
        ).group_by(CostTracking.model_name).all()

        requests_by_model = {stat.model_name: stat.requests for stat in model_stats}
        cost_by_model = {stat.model_name: float(stat.cost) for stat in model_stats}

        total_requests = stats.total_requests or 0
        total_tokens = stats.total_tokens or 0
        total_cost = float(stats.total_cost or 0.0)

        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "requests_by_model": requests_by_model,
            "cost_by_model": cost_by_model,
            "avg_tokens_per_request": total_tokens / total_requests if total_requests > 0 else 0,
            "period_start": start_date,
            "period_end": datetime.utcnow()
        }

    async def get_cost_optimization_analytics(
        self, db: Session, user_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """Get cost optimization analytics using the cost optimizer."""
        return await cost_optimizer.get_usage_analytics(db, user_id, days)

    def get_tier_comparison(self) -> Dict[str, Any]:
        """Get comparison of cost tiers for user decision-making."""
        return cost_optimizer.get_tier_comparison()

    def predict_query_cost(
        self, query: str, depth: str = "standard"
    ) -> Dict[str, Any]:
        """Predict cost for a query before execution."""
        tier = CostTier(depth)
        predicted_cost = cost_optimizer.predict_cost(tier, len(query), use_cache=False)
        cached_cost = 0.0

        tier_config = cost_optimizer.get_tier_config(tier)
        query_complexity = cost_optimizer.estimate_query_complexity(query)

        return {
            "query_length": len(query),
            "query_complexity": round(query_complexity, 2),
            "tier": depth,
            "model": tier_config.model,
            "predicted_cost": round(predicted_cost, 4),
            "cached_cost": cached_cost,
            "potential_savings": round(predicted_cost - cached_cost, 4),
            "max_tokens": tier_config.max_tokens,
            "description": tier_config.description
        }

    async def execute_function(
        self,
        db: Session,
        user_id: int,
        function_name: str,
        parameters: Dict[str, Any],
    ) -> ResearchTask:
        """
        Execute a specialised research function and return the resulting task.
        """
        from app.services.function_registry import get_function  # Lazy import to avoid cycle

        function = get_function(function_name)
        result = await function.execute(db=db, user_id=user_id, **parameters)
        task_id = result.get("task_id")

        task = (
            db.query(ResearchTask)
            .filter(and_(ResearchTask.id == task_id, ResearchTask.user_id == user_id))
            .first()
        )
        if not task:
            raise ValueError("Research task could not be retrieved after execution")
        return task


class TemplateService:
    """Service for managing research templates."""
    
    async def create_template(
        self, db: Session, user_id: int, template_data: Dict[str, Any]
    ) -> ResearchTemplate:
        """Create a research template."""
        
        # Check template limit
        count = db.query(func.count(ResearchTemplate.id)).filter(
            and_(ResearchTemplate.user_id == user_id, ResearchTemplate.is_active == True)
        ).scalar()
        
        if count >= settings.MAX_TEMPLATES_PER_USER:
            raise ValueError(f"Maximum templates limit reached: {settings.MAX_TEMPLATES_PER_USER}")
        
        template = ResearchTemplate(**template_data, user_id=user_id)
        db.add(template)
        db.commit()
        db.refresh(template)
        return template
    
    async def get_template(
        self, db: Session, template_id: int, user_id: int
    ) -> Optional[ResearchTemplate]:
        """Get a template by ID."""
        return db.query(ResearchTemplate).filter(
            and_(
                ResearchTemplate.id == template_id,
                (ResearchTemplate.user_id == user_id) | (ResearchTemplate.is_public == True)
            )
        ).first()
    
    async def list_templates(
        self, db: Session, user_id: int, include_public: bool = True
    ) -> List[ResearchTemplate]:
        """List user templates."""
        query = db.query(ResearchTemplate).filter(ResearchTemplate.is_active == True)
        
        if include_public:
            query = query.filter(
                (ResearchTemplate.user_id == user_id) | (ResearchTemplate.is_public == True)
            )
        else:
            query = query.filter(ResearchTemplate.user_id == user_id)
        
        return query.order_by(ResearchTemplate.created_at.desc()).all()
    
    async def apply_template(
        self, db: Session, template: ResearchTemplate, variables: Dict[str, Any]
    ) -> str:
        """Apply variables to template and render query."""
        query = template.query_template
        
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            query = query.replace(placeholder, value)
        
        # Update usage statistics
        template.usage_count += 1
        template.last_used_at = datetime.utcnow()
        db.commit()
        
        return query


# Global service instances
research_service = ResearchService()
template_service = TemplateService()
