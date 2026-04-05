"""
Burst Detection Service for analytics-service.

Detects sudden spikes in entity mentions using Kleinberg's algorithm.
Used as a Breaking News indicator.

Dependencies: pybursts, numpy
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import numpy as np
import structlog

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


@dataclass
class Burst:
    """Represents a detected burst in entity mentions."""
    entity: str
    level: int          # Burst intensity (1-5)
    start_time: datetime
    end_time: datetime
    mention_count: int
    baseline_rate: float
    spike_factor: float  # How many x above baseline

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dict."""
        return {
            "entity": self.entity,
            "level": self.level,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "mention_count": self.mention_count,
            "baseline_rate": round(self.baseline_rate, 4),
            "spike_factor": round(self.spike_factor, 2),
        }


class BurstDetectionService:
    """
    Kleinberg's burst detection algorithm.

    Detects sudden increases in entity mention frequency
    that indicate breaking news.
    """

    def __init__(
        self,
        sensitivity: float = 2.0,
        state_penalty: float = 0.5
    ):
        """
        Initialize burst detection service.

        Args:
            sensitivity: s parameter (higher = more sensitive)
            state_penalty: gamma parameter (higher = fewer bursts)
        """
        self.sensitivity = sensitivity
        self.state_penalty = state_penalty

    async def detect_bursts(
        self,
        entity: str,
        hours: int = 24,
        min_mentions: int = 10,
        db: AsyncSession = None
    ) -> List[Burst]:
        """
        Detect bursts for a specific entity.

        Args:
            entity: Entity name to check
            hours: Time window to analyze
            min_mentions: Minimum mentions required for analysis
            db: Database session

        Returns:
            List of Burst objects sorted by intensity
        """
        if db is None:
            logger.warning("No database session provided for burst detection")
            return []

        # Get mention timestamps from DB
        mentions = await self._get_entity_mentions(entity, hours, db)

        if len(mentions) < min_mentions:
            logger.debug(
                "Insufficient mentions for burst detection",
                entity=entity,
                mentions=len(mentions),
                min_required=min_mentions
            )
            return []

        # Convert to offsets (seconds since first mention)
        offsets = [(m - mentions[0]).total_seconds() for m in mentions]

        # Run Kleinberg algorithm
        try:
            from pybursts import kleinberg
            bursts = kleinberg(
                offsets=offsets,
                s=self.sensitivity,
                gamma=self.state_penalty
            )
        except ImportError:
            logger.error("pybursts not installed, cannot detect bursts")
            return []
        except Exception as e:
            logger.error("Kleinberg algorithm failed", error=str(e), entity=entity)
            return []

        # Convert to Burst objects
        result = []
        for level, start_idx, end_idx in bursts:
            if level > 0:  # Only include actual bursts
                start_idx = int(start_idx)
                end_idx = int(end_idx)

                result.append(Burst(
                    entity=entity,
                    level=level,
                    start_time=mentions[start_idx],
                    end_time=mentions[end_idx],
                    mention_count=end_idx - start_idx,
                    baseline_rate=len(mentions) / hours,
                    spike_factor=self._calculate_spike_factor(
                        mentions, start_idx, end_idx, hours
                    )
                ))

        sorted_bursts = sorted(result, key=lambda b: b.level, reverse=True)

        logger.info(
            "Burst detection completed",
            entity=entity,
            total_mentions=len(mentions),
            bursts_found=len(sorted_bursts),
            max_level=sorted_bursts[0].level if sorted_bursts else 0
        )

        return sorted_bursts

    async def get_all_active_bursts(
        self,
        hours: int = 6,
        min_level: int = 2,
        db: AsyncSession = None
    ) -> List[Burst]:
        """
        Scan all entities for active bursts.

        Used for Breaking News detection.

        Args:
            hours: Time window to analyze
            min_level: Minimum burst intensity
            db: Database session

        Returns:
            All bursts above min_level sorted by intensity
        """
        if db is None:
            logger.warning("No database session provided")
            return []

        # Get entities with recent activity
        active_entities = await self._get_active_entities(hours, db)

        logger.info(
            "Scanning entities for bursts",
            entity_count=len(active_entities),
            hours=hours,
            min_level=min_level
        )

        all_bursts = []
        for entity in active_entities:
            try:
                bursts = await self.detect_bursts(entity, hours, db=db)
                all_bursts.extend([b for b in bursts if b.level >= min_level])
            except Exception as e:
                logger.error("Error detecting bursts for entity", entity=entity, error=str(e))

        return sorted(all_bursts, key=lambda b: b.level, reverse=True)

    async def _get_entity_mentions(
        self,
        entity: str,
        hours: int,
        db: AsyncSession
    ) -> List[datetime]:
        """
        Query article_analysis for entity mention timestamps.
        """
        # Note: hours is interpolated directly (it's a validated integer)
        query = text(f"""
            SELECT created_at
            FROM article_analysis
            WHERE tier1_results->'entities' @> :entity_json
              AND created_at > NOW() - INTERVAL '{hours} hours'
            ORDER BY created_at ASC
        """)

        # Format entity as JSON array element
        entity_json = f'[{{"name": "{entity}"}}]'

        result = await db.execute(query, {
            "entity_json": entity_json
        })

        return [row.created_at for row in result.fetchall()]

    async def _get_active_entities(
        self,
        hours: int,
        db: AsyncSession,
        min_mentions: int = 5
    ) -> List[str]:
        """
        Get entities with recent activity (>min_mentions mentions).
        """
        # Note: hours is interpolated directly (it's a validated integer)
        query = text(f"""
            WITH entity_mentions AS (
                SELECT
                    jsonb_array_elements(tier1_results->'entities')->>'name' as entity
                FROM article_analysis
                WHERE created_at > NOW() - INTERVAL '{hours} hours'
                  AND tier1_results->'entities' IS NOT NULL
            )
            SELECT entity, COUNT(*) as mention_count
            FROM entity_mentions
            WHERE entity IS NOT NULL
            GROUP BY entity
            HAVING COUNT(*) >= :min_mentions
            ORDER BY COUNT(*) DESC
            LIMIT 100
        """)

        result = await db.execute(query, {
            "min_mentions": min_mentions
        })

        return [row.entity for row in result.fetchall()]

    def _calculate_spike_factor(
        self,
        mentions: List[datetime],
        start_idx: int,
        end_idx: int,
        total_hours: int
    ) -> float:
        """Calculate how many times above baseline the burst is."""
        burst_count = end_idx - start_idx

        if burst_count <= 0 or start_idx >= len(mentions) or end_idx >= len(mentions):
            return 1.0

        burst_duration = (mentions[end_idx] - mentions[start_idx]).total_seconds() / 3600
        burst_hours = max(0.1, burst_duration)  # Avoid division by zero

        burst_rate = burst_count / burst_hours
        baseline_rate = len(mentions) / total_hours

        if baseline_rate <= 0:
            return burst_rate

        return burst_rate / baseline_rate


# Singleton instance
burst_detection_service = BurstDetectionService()
