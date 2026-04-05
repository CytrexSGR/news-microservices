"""
Source Registry Service

Central intelligence hub for scraping decisions.
Tracks per-source capabilities and performance.

Now with database persistence for profiles across restarts.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_profile import (
    SourceProfile,
    SourceProfileDB,
    SourceProfileCreate,
    SourceProfileUpdate,
    SourceProfileMetricsUpdate,
    ScrapeMethodEnum,
    ScrapeStatusEnum,
    PaywallTypeEnum
)

logger = logging.getLogger(__name__)


class SourceRegistry:
    """
    Source Registry - Intelligence layer for scraping decisions.

    Responsibilities:
    - Track scraping success/failure per domain
    - Select optimal extraction method
    - Record paywall status
    - Adapt strategy based on historical data
    - Persist profiles to database

    Uses in-memory cache for fast reads, with async DB persistence.
    """

    def __init__(self):
        """Initialize Source Registry with in-memory cache."""
        self._cache: Dict[str, SourceProfile] = {}
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._db_session_factory = None
        self._initialized = False

    async def initialize(self, session_factory) -> None:
        """
        Initialize registry and load profiles from database.

        Args:
            session_factory: AsyncSessionLocal factory for database access
        """
        self._db_session_factory = session_factory
        await self._load_profiles_from_db()
        self._initialized = True
        logger.info(f"Source Registry initialized with {len(self._cache)} profiles from database")

    async def _load_profiles_from_db(self) -> None:
        """Load all source profiles from database into cache."""
        if not self._db_session_factory:
            return

        try:
            async with self._db_session_factory() as session:
                result = await session.execute(select(SourceProfileDB))
                db_profiles = result.scalars().all()

                for db_profile in db_profiles:
                    profile = self._db_to_pydantic(db_profile)
                    self._cache[profile.domain] = profile
                    self._metrics[profile.domain] = {
                        "attempts": profile.total_attempts,
                        "successes": profile.total_successes,
                        "failures": profile.total_failures,
                        "total_response_time": profile.avg_response_time_ms * max(1, profile.total_attempts),
                        "total_word_count": profile.avg_word_count * max(1, profile.total_successes),
                        "total_quality": profile.avg_extraction_quality * max(1, profile.total_successes)
                    }

                logger.info(f"Loaded {len(db_profiles)} source profiles from database")

        except Exception as e:
            logger.error(f"Failed to load profiles from database: {e}")

    def _db_to_pydantic(self, db_profile: SourceProfileDB) -> SourceProfile:
        """Convert database model to Pydantic model."""
        return SourceProfile(
            id=db_profile.id,
            domain=db_profile.domain,
            scrape_method=ScrapeMethodEnum(db_profile.scrape_method),
            fallback_methods=[ScrapeMethodEnum(m) for m in (db_profile.fallback_methods or [])],
            scrape_status=ScrapeStatusEnum(db_profile.scrape_status),
            paywall_type=PaywallTypeEnum(db_profile.paywall_type),
            success_rate=db_profile.success_rate or 0.0,
            avg_response_time_ms=db_profile.avg_response_time_ms or 0,
            total_attempts=db_profile.total_attempts or 0,
            total_successes=db_profile.total_successes or 0,
            total_failures=db_profile.total_failures or 0,
            avg_word_count=db_profile.avg_word_count or 0,
            avg_extraction_quality=db_profile.avg_extraction_quality or 0.0,
            rate_limit_per_minute=db_profile.rate_limit_per_minute or 10,
            requires_ua_rotation=db_profile.requires_ua_rotation,
            requires_stealth=db_profile.requires_stealth,
            requires_proxy=db_profile.requires_proxy,
            custom_headers=db_profile.custom_headers or {},
            notes=db_profile.notes,
            last_successful_scrape=db_profile.last_successful_scrape,
            last_failed_scrape=db_profile.last_failed_scrape,
            created_at=db_profile.created_at,
            updated_at=db_profile.updated_at
        )

    async def _save_profile_to_db(self, profile: SourceProfile) -> None:
        """Save or update profile in database."""
        if not self._db_session_factory:
            return

        try:
            async with self._db_session_factory() as session:
                # Check if profile exists
                result = await session.execute(
                    select(SourceProfileDB).where(SourceProfileDB.domain == profile.domain)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing profile
                    existing.scrape_method = profile.scrape_method.value
                    existing.fallback_methods = [m.value for m in profile.fallback_methods]
                    existing.scrape_status = profile.scrape_status.value
                    existing.paywall_type = profile.paywall_type.value
                    existing.success_rate = profile.success_rate
                    existing.avg_response_time_ms = profile.avg_response_time_ms
                    existing.total_attempts = profile.total_attempts
                    existing.total_successes = profile.total_successes
                    existing.total_failures = profile.total_failures
                    existing.avg_word_count = profile.avg_word_count
                    existing.avg_extraction_quality = profile.avg_extraction_quality
                    existing.rate_limit_per_minute = profile.rate_limit_per_minute
                    existing.requires_ua_rotation = profile.requires_ua_rotation
                    existing.requires_stealth = profile.requires_stealth
                    existing.requires_proxy = profile.requires_proxy
                    existing.custom_headers = profile.custom_headers
                    existing.notes = profile.notes
                    existing.last_successful_scrape = profile.last_successful_scrape
                    existing.last_failed_scrape = profile.last_failed_scrape
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new profile
                    db_profile = SourceProfileDB(
                        domain=profile.domain,
                        scrape_method=profile.scrape_method.value,
                        fallback_methods=[m.value for m in profile.fallback_methods],
                        scrape_status=profile.scrape_status.value,
                        paywall_type=profile.paywall_type.value,
                        success_rate=profile.success_rate,
                        avg_response_time_ms=profile.avg_response_time_ms,
                        total_attempts=profile.total_attempts,
                        total_successes=profile.total_successes,
                        total_failures=profile.total_failures,
                        avg_word_count=profile.avg_word_count,
                        avg_extraction_quality=profile.avg_extraction_quality,
                        rate_limit_per_minute=profile.rate_limit_per_minute,
                        requires_ua_rotation=profile.requires_ua_rotation,
                        requires_stealth=profile.requires_stealth,
                        requires_proxy=profile.requires_proxy,
                        custom_headers=profile.custom_headers,
                        notes=profile.notes,
                        last_successful_scrape=profile.last_successful_scrape,
                        last_failed_scrape=profile.last_failed_scrape,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(db_profile)

                await session.commit()
                logger.debug(f"Saved profile to database: {profile.domain}")

        except Exception as e:
            logger.error(f"Failed to save profile to database: {e}")

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL (removes www. prefix)"""
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain

    def get_profile(self, url: str) -> Optional[SourceProfile]:
        """Get source profile for URL's domain"""
        domain = self._extract_domain(url)
        return self._cache.get(domain)

    async def get_or_create_profile(self, url: str) -> SourceProfile:
        """Get existing profile or create new one with defaults"""
        profile = self.get_profile(url)

        if profile:
            return profile

        # Create new profile with intelligent defaults
        domain = self._extract_domain(url)

        new_profile = SourceProfile(
            id=len(self._cache) + 1,
            domain=domain,
            scrape_method=ScrapeMethodEnum.NEWSPAPER4K,
            fallback_methods=[ScrapeMethodEnum.TRAFILATURA, ScrapeMethodEnum.PLAYWRIGHT],
            scrape_status=ScrapeStatusEnum.UNKNOWN,
            paywall_type=PaywallTypeEnum.UNKNOWN,
            requires_ua_rotation=True,
            requires_stealth=False,
            requires_proxy=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self._cache[domain] = new_profile
        self._metrics[domain] = {
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "total_response_time": 0,
            "total_word_count": 0,
            "total_quality": 0.0
        }

        # Save to database
        await self._save_profile_to_db(new_profile)

        logger.info(f"Created new source profile for domain: {domain}")
        return new_profile

    async def update_metrics(self, url: str, metrics: SourceProfileMetricsUpdate) -> SourceProfile:
        """Update source profile metrics after scrape attempt"""
        domain = self._extract_domain(url)

        # Ensure profile exists
        profile = await self.get_or_create_profile(url)

        # Update metrics tracking
        domain_metrics = self._metrics.get(domain, {
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "total_response_time": 0,
            "total_word_count": 0,
            "total_quality": 0.0
        })

        domain_metrics["attempts"] += 1

        if metrics.success:
            domain_metrics["successes"] += 1
            domain_metrics["total_word_count"] += metrics.word_count
            domain_metrics["total_quality"] += metrics.extraction_quality
        else:
            domain_metrics["failures"] += 1

        domain_metrics["total_response_time"] += metrics.response_time_ms
        self._metrics[domain] = domain_metrics

        # Calculate updated profile values
        n = domain_metrics["attempts"]
        n_success = domain_metrics["successes"]

        updated_profile = SourceProfile(
            id=profile.id,
            domain=domain,
            scrape_method=profile.scrape_method,
            fallback_methods=profile.fallback_methods,
            paywall_type=profile.paywall_type,
            scrape_status=self._determine_status(n, n_success),
            success_rate=self._calculate_success_rate(
                domain_metrics["successes"],
                domain_metrics["attempts"],
                metrics.success
            ),
            avg_response_time_ms=int(domain_metrics["total_response_time"] / n),
            total_attempts=n,
            total_successes=n_success,
            total_failures=domain_metrics["failures"],
            avg_word_count=int(domain_metrics["total_word_count"] / n_success) if n_success > 0 else 0,
            avg_extraction_quality=domain_metrics["total_quality"] / n_success if n_success > 0 else 0.0,
            requires_ua_rotation=profile.requires_ua_rotation,
            requires_stealth=profile.requires_stealth,
            requires_proxy=profile.requires_proxy,
            custom_headers=profile.custom_headers,
            last_successful_scrape=datetime.utcnow() if metrics.success else profile.last_successful_scrape,
            last_failed_scrape=datetime.utcnow() if not metrics.success else profile.last_failed_scrape,
            created_at=profile.created_at,
            updated_at=datetime.utcnow()
        )

        self._cache[domain] = updated_profile

        # Save to database
        await self._save_profile_to_db(updated_profile)

        return updated_profile

    def _calculate_success_rate(
        self,
        current_successes: int,
        current_attempts: int,
        success: bool
    ) -> float:
        """Calculate success rate (already includes this attempt)"""
        if current_attempts == 0:
            return 0.0
        return current_successes / current_attempts

    def _determine_status(self, total_attempts: int, total_successes: int) -> ScrapeStatusEnum:
        """Determine scrape status based on metrics"""
        if total_attempts < 5:
            return ScrapeStatusEnum.UNKNOWN

        success_rate = total_successes / total_attempts

        if success_rate >= 0.8:
            return ScrapeStatusEnum.WORKING
        elif success_rate >= 0.5:
            return ScrapeStatusEnum.DEGRADED
        else:
            return ScrapeStatusEnum.BLOCKED

    def _select_best_method(self, profile: Optional[SourceProfile]) -> ScrapeMethodEnum:
        """Select best scraping method based on profile"""
        if not profile:
            return ScrapeMethodEnum.NEWSPAPER4K

        # If current method is working well, keep it
        if profile.scrape_status == ScrapeStatusEnum.WORKING:
            return profile.scrape_method

        # If degraded or blocked, try fallback methods
        if profile.scrape_status in [ScrapeStatusEnum.DEGRADED, ScrapeStatusEnum.BLOCKED]:
            if profile.fallback_methods:
                for fallback in profile.fallback_methods:
                    if fallback != profile.scrape_method:
                        logger.info(
                            f"Domain {profile.domain} status={profile.scrape_status.value}, "
                            f"switching from {profile.scrape_method.value} to {fallback.value}"
                        )
                        return fallback

        # If blocked and no fallbacks work, try stealth
        if profile.scrape_status == ScrapeStatusEnum.BLOCKED:
            if not profile.requires_stealth:
                logger.info(f"Domain {profile.domain} blocked, escalating to playwright_stealth")
                return ScrapeMethodEnum.PLAYWRIGHT_STEALTH

        return profile.scrape_method

    def get_scrape_config(self, url: str) -> Dict[str, Any]:
        """Get complete scraping configuration for URL"""
        profile = self._cache.get(self._extract_domain(url))
        if not profile:
            # Return defaults for unknown domain
            return {
                "method": ScrapeMethodEnum.NEWSPAPER4K,
                "fallback_methods": [ScrapeMethodEnum.TRAFILATURA, ScrapeMethodEnum.PLAYWRIGHT],
                "requires_ua_rotation": True,
                "requires_stealth": False,
                "requires_proxy": False,
                "custom_headers": {},
                "rate_limit": 10,
                "paywall_type": PaywallTypeEnum.UNKNOWN,
            }

        return {
            "method": self._select_best_method(profile),
            "fallback_methods": profile.fallback_methods,
            "requires_ua_rotation": profile.requires_ua_rotation,
            "requires_stealth": profile.requires_stealth,
            "requires_proxy": profile.requires_proxy,
            "custom_headers": profile.custom_headers,
            "rate_limit": profile.rate_limit_per_minute,
            "paywall_type": profile.paywall_type,
        }

    def list_profiles(
        self,
        status: Optional[ScrapeStatusEnum] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SourceProfile]:
        """List source profiles with optional filtering"""
        profiles = list(self._cache.values())

        if status:
            profiles = [p for p in profiles if p.scrape_status == status]

        return profiles[offset:offset + limit]

    async def update_profile(self, domain: str, update: SourceProfileUpdate) -> Optional[SourceProfile]:
        """Manually update source profile settings"""
        if domain not in self._cache:
            return None

        profile = self._cache[domain]
        update_data = update.model_dump(exclude_unset=True)

        updated_profile = SourceProfile(
            id=profile.id,
            domain=domain,
            scrape_method=update_data.get("scrape_method", profile.scrape_method),
            fallback_methods=update_data.get("fallback_methods", profile.fallback_methods),
            paywall_type=update_data.get("paywall_type", profile.paywall_type),
            scrape_status=update_data.get("scrape_status", profile.scrape_status),
            success_rate=profile.success_rate,
            avg_response_time_ms=profile.avg_response_time_ms,
            total_attempts=profile.total_attempts,
            total_successes=profile.total_successes,
            total_failures=profile.total_failures,
            avg_word_count=profile.avg_word_count,
            avg_extraction_quality=profile.avg_extraction_quality,
            rate_limit_per_minute=update_data.get("rate_limit_per_minute", profile.rate_limit_per_minute),
            requires_ua_rotation=update_data.get("requires_ua_rotation", profile.requires_ua_rotation),
            requires_stealth=update_data.get("requires_stealth", profile.requires_stealth),
            requires_proxy=update_data.get("requires_proxy", profile.requires_proxy),
            custom_headers=update_data.get("custom_headers", profile.custom_headers),
            notes=update_data.get("notes", profile.notes),
            last_successful_scrape=profile.last_successful_scrape,
            last_failed_scrape=profile.last_failed_scrape,
            created_at=profile.created_at,
            updated_at=datetime.utcnow()
        )

        self._cache[domain] = updated_profile

        # Save to database
        await self._save_profile_to_db(updated_profile)

        return updated_profile

    def needs_profiling(self, url: str) -> bool:
        """Check if domain needs auto-profiling"""
        domain = self._extract_domain(url)
        profile = self._cache.get(domain)

        if not profile:
            return True

        if profile.scrape_status == ScrapeStatusEnum.UNKNOWN and profile.total_attempts < 3:
            return True

        if profile.scrape_status == ScrapeStatusEnum.BLOCKED and profile.total_attempts < 5:
            return True

        return False

    async def apply_profile(self, profile: SourceProfile) -> None:
        """Apply a profile from auto-profiler and save to database"""
        self._cache[profile.domain] = profile
        self._metrics[profile.domain] = {
            "attempts": profile.total_attempts,
            "successes": profile.total_successes,
            "failures": profile.total_failures,
            "total_response_time": profile.avg_response_time_ms * max(1, profile.total_attempts),
            "total_word_count": profile.avg_word_count * max(1, profile.total_successes),
            "total_quality": profile.avg_extraction_quality * max(1, profile.total_successes)
        }

        # Save to database
        await self._save_profile_to_db(profile)

        logger.info(f"Applied auto-profile for {profile.domain}: method={profile.scrape_method.value}")

    def clear_cache(self):
        """Clear in-memory cache (does not affect database)"""
        self._cache.clear()
        self._metrics.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall registry statistics"""
        profiles = list(self._cache.values())

        if not profiles:
            return {
                "total_sources": 0,
                "working": 0,
                "degraded": 0,
                "blocked": 0,
                "unknown": 0,
                "avg_success_rate": 0.0
            }

        return {
            "total_sources": len(profiles),
            "working": sum(1 for p in profiles if p.scrape_status == ScrapeStatusEnum.WORKING),
            "degraded": sum(1 for p in profiles if p.scrape_status == ScrapeStatusEnum.DEGRADED),
            "blocked": sum(1 for p in profiles if p.scrape_status == ScrapeStatusEnum.BLOCKED),
            "unknown": sum(1 for p in profiles if p.scrape_status == ScrapeStatusEnum.UNKNOWN),
            "avg_success_rate": sum(p.success_rate for p in profiles) / len(profiles) if profiles else 0.0
        }


# Singleton instance
_registry_instance: Optional[SourceRegistry] = None


def get_source_registry() -> SourceRegistry:
    """Get singleton Source Registry instance"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = SourceRegistry()
    return _registry_instance


async def initialize_source_registry(session_factory) -> SourceRegistry:
    """Initialize and return Source Registry with database connection"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = SourceRegistry()
    await _registry_instance.initialize(session_factory)
    return _registry_instance
