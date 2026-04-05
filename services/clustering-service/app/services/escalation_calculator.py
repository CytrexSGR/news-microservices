"""Escalation Calculator Service.

Orchestrates multi-signal escalation scoring using:
- 50% embedding similarity to anchor points
- 30% content analysis from narrative frames
- 20% keyword heuristic matching

This service is the core orchestrator for the Intelligence Interpretation Layer,
calculating escalation levels for news clusters across three domains:
geopolitical, military, and economic.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.escalation import EscalationAnchor, EscalationDomain


@dataclass
class EscalationSignal:
    """Individual escalation signal result.

    Represents the output from a single signal source (embedding, content, or keywords)
    for a specific domain.

    Attributes:
        domain: Escalation domain (geopolitical, military, economic)
        level: Escalation level 1-5
        confidence: Confidence score 0.0-1.0
        source: Signal source identifier (embedding, content, keywords)
        matched_anchor_id: UUID of matched anchor (for embedding signals)
        matched_keywords: List of matched keywords (for keyword signals)
        reasoning: Explanation of the signal determination
    """

    domain: str  # geopolitical, military, economic
    level: int  # 1-5
    confidence: float  # 0.0-1.0
    source: str  # embedding, content, keywords
    matched_anchor_id: Optional[UUID] = None
    matched_keywords: Optional[List[str]] = None
    reasoning: Optional[str] = None


@dataclass
class DomainEscalation:
    """Escalation result for a single domain.

    Combines multiple signals into a weighted score for one domain.

    Attributes:
        domain: Escalation domain
        level: Final escalation level 1-5
        score: Combined score 0.000-1.000
        signals: List of contributing signals
        confidence: Overall confidence in the result
    """

    domain: str
    level: int  # 1-5
    score: Decimal  # 0.000-1.000
    signals: List[EscalationSignal]
    confidence: float


@dataclass
class EscalationResult:
    """Complete escalation calculation result.

    Contains escalation assessments for all three domains plus combined metrics.

    Attributes:
        geopolitical: Geopolitical domain escalation
        military: Military domain escalation
        economic: Economic domain escalation
        combined_level: Maximum level across all domains (1-5)
        combined_score: Weighted average score
        calculated_at: Timestamp of calculation
        cluster_id: UUID of the analyzed cluster
        article_count: Number of articles in the cluster
    """

    geopolitical: DomainEscalation
    military: DomainEscalation
    economic: DomainEscalation
    combined_level: int  # 1-5 (max of domains)
    combined_score: Decimal  # weighted average
    calculated_at: datetime
    cluster_id: UUID
    article_count: int


class EscalationCalculator:
    """Orchestrates multi-signal escalation calculation.

    This service calculates escalation levels for news clusters by combining
    three distinct signals:
    - Embedding similarity (50%): Cosine similarity to domain-specific anchors
    - Content analysis (30%): Analysis of narrative frames and sentiment
    - Keyword heuristics (20%): Pattern matching against escalatory keywords

    Usage:
        async with async_session() as session:
            calculator = EscalationCalculator(session)
            result = await calculator.calculate_cluster_escalation(
                cluster_id=uuid,
                cluster_embedding=embedding_vector,
                cluster_text=combined_text,
                article_count=5
            )

    Signal Weights:
        EMBEDDING_WEIGHT: 0.50 (50% of final score)
        CONTENT_WEIGHT: 0.30 (30% of final score)
        KEYWORD_WEIGHT: 0.20 (20% of final score)
    """

    # Signal weights (must sum to 1.0)
    EMBEDDING_WEIGHT = 0.50
    CONTENT_WEIGHT = 0.30
    KEYWORD_WEIGHT = 0.20

    # Level thresholds (score ranges for each level)
    LEVEL_THRESHOLDS = [
        (0.0, 0.2, 1),  # Routine
        (0.2, 0.4, 2),  # Elevated
        (0.4, 0.6, 3),  # Significant
        (0.6, 0.8, 4),  # High
        (0.8, 1.0, 5),  # Critical
    ]

    # Escalatory language patterns by level (level -> list of patterns)
    ESCALATION_PATTERNS = {
        1: [  # Routine/Baseline
            r'\b(routine|normal|standard|regular|typical|usual)\b',
            r'\b(stable|calm|peaceful|cooperation)\b',
            r'\b(dialogue|talks|negotiations? continuing)\b',
        ],
        2: [  # Elevated/Monitoring
            r'\b(concerns?|watching|monitoring|attention)\b',
            r'\b(increased activity|heightened|elevated)\b',
            r'\b(tensions? rising|growing concerns?)\b',
            r'\b(disputed|contested|disagreement)\b',
        ],
        3: [  # Significant/Alert
            r'\b(significant|serious|substantial|major)\b',
            r'\b(warnings?|alerts?|advisories?)\b',
            r'\b(escalation|escalating|intensifying)\b',
            r'\b(threats?|threatening|confrontation)\b',
            r'\b(sanctions?|restrictions?|embargo)\b',
        ],
        4: [  # Severe/Crisis
            r'\b(crisis|critical|severe|urgent|emergency)\b',
            r'\b(military action|armed forces|troops deployed)\b',
            r'\b(attacks?|strikes?|offensive)\b',
            r'\b(ultimatum|deadline|demands?)\b',
            r'\b(mobilization|build-?up)\b',
        ],
        5: [  # Critical/Emergency
            r'\b(war|warfare|combat|invasion)\b',
            r'\b(catastroph|devastat|massive casualties)\b',
            r'\b(nuclear|wmd|chemical|biological)\b',
            r'\b(collapse|breakdown|complete failure)\b',
            r'\b(state of emergency|martial law)\b',
        ],
    }

    # Domain-specific intensifiers that boost levels
    DOMAIN_INTENSIFIERS = {
        'geopolitical': [
            r'\b(international|global|regional|bilateral|multilateral)\b',
            r'\b(diplomatic|summit|treaty|agreement)\b',
            r'\b(allies?|alliance|coalition|bloc)\b',
        ],
        'military': [
            r'\b(military|armed forces|troops|soldiers)\b',
            r'\b(weapons?|missiles?|artillery|tanks?)\b',
            r'\b(naval|airborne|ground forces)\b',
            r'\b(defense|offensive|strategic)\b',
        ],
        'economic': [
            r'\b(economic|financial|market|trade)\b',
            r'\b(sanctions?|tariffs?|embargo)\b',
            r'\b(inflation|recession|crash|default)\b',
            r'\b(currency|central bank|federal reserve)\b',
        ],
    }

    def __init__(self, session: AsyncSession):
        """Initialize calculator with database session.

        Args:
            session: AsyncSession for database operations
        """
        self.session = session
        self._anchor_cache: Dict[str, List[EscalationAnchor]] = {}

    @classmethod
    def validate_weights(cls) -> bool:
        """Validate that signal weights sum to 1.0.

        Returns:
            True if weights sum to 1.0, False otherwise
        """
        total = cls.EMBEDDING_WEIGHT + cls.CONTENT_WEIGHT + cls.KEYWORD_WEIGHT
        return abs(total - 1.0) < 0.0001  # Allow for floating point imprecision

    def score_to_level(self, score: float) -> int:
        """Convert a combined score (0-1) to an escalation level (1-5).

        Args:
            score: Combined score between 0.0 and 1.0

        Returns:
            Escalation level between 1 and 5
        """
        for lower, upper, level in self.LEVEL_THRESHOLDS:
            if lower <= score < upper:
                return level
        return 5  # Max level for score >= 0.8

    async def calculate_cluster_escalation(
        self,
        cluster_id: UUID,
        cluster_embedding: List[float],
        cluster_text: str,
        article_count: int,
    ) -> EscalationResult:
        """Calculate escalation levels for a cluster.

        Orchestrates the full escalation calculation by:
        1. Loading anchors for all domains
        2. Calculating signals from each source (embedding, content, keywords)
        3. Combining signals with weighted averaging
        4. Determining final levels and scores

        Args:
            cluster_id: UUID of the cluster
            cluster_embedding: 1536-dimensional embedding vector
            cluster_text: Combined text from cluster articles
            article_count: Number of articles in cluster

        Returns:
            EscalationResult with per-domain and combined scores
        """
        domains = ["geopolitical", "military", "economic"]
        domain_escalations = {}

        for domain in domains:
            # Calculate all three signals for this domain
            embedding_signal = await self._calculate_embedding_signal(domain, cluster_embedding)
            content_signal = await self._calculate_content_signal(domain, cluster_text)
            keyword_signal = await self._calculate_keyword_signal(domain, cluster_text)

            signals = [embedding_signal, content_signal, keyword_signal]

            # Combine signals into domain escalation
            domain_escalations[domain] = self._combine_signals(domain, signals)

        # Calculate combined metrics across all domains
        combined_level = max(de.level for de in domain_escalations.values())

        # Weighted average score across domains (equal weights)
        total_score = sum(de.score for de in domain_escalations.values())
        combined_score = (total_score / Decimal("3")).quantize(Decimal("0.001"))

        return EscalationResult(
            geopolitical=domain_escalations["geopolitical"],
            military=domain_escalations["military"],
            economic=domain_escalations["economic"],
            combined_level=combined_level,
            combined_score=combined_score,
            calculated_at=datetime.now(),
            cluster_id=cluster_id,
            article_count=article_count,
        )

    async def _calculate_embedding_signal(
        self,
        domain: str,
        embedding: List[float],
    ) -> EscalationSignal:
        """Calculate escalation signal from embedding similarity.

        Uses cosine similarity against domain anchor embeddings
        to find the closest matching escalation level.

        Args:
            domain: Escalation domain (geopolitical/military/economic)
            embedding: 1536-dimensional cluster embedding

        Returns:
            EscalationSignal with level and confidence
        """
        import numpy as np

        anchors = await self._load_anchors(domain)

        if not anchors:
            # No anchors available - return neutral level 3
            return EscalationSignal(
                domain=domain,
                level=3,
                confidence=0.0,
                source="embedding",
                reasoning="No anchors available for domain"
            )

        # Convert input embedding to numpy array
        input_vec = np.array(embedding, dtype=np.float32)
        input_norm = np.linalg.norm(input_vec)

        if input_norm == 0:
            return EscalationSignal(
                domain=domain,
                level=3,
                confidence=0.0,
                source="embedding",
                reasoning="Zero-norm input embedding"
            )

        input_vec = input_vec / input_norm

        best_similarity = -1.0
        best_anchor = None

        for anchor in anchors:
            # anchor.embedding is a pgvector Vector - convert to numpy
            anchor_vec = np.array(anchor.embedding, dtype=np.float32)
            anchor_norm = np.linalg.norm(anchor_vec)

            if anchor_norm == 0:
                continue

            anchor_vec = anchor_vec / anchor_norm

            # Cosine similarity (dot product of normalized vectors)
            similarity = float(np.dot(input_vec, anchor_vec))

            # Apply anchor weight
            weighted_similarity = similarity * float(anchor.weight or 1.0)

            if weighted_similarity > best_similarity:
                best_similarity = weighted_similarity
                best_anchor = anchor

        if best_anchor is None:
            return EscalationSignal(
                domain=domain,
                level=3,
                confidence=0.0,
                source="embedding",
                reasoning="No valid anchor embeddings found"
            )

        # Convert similarity to confidence (0-1)
        # Similarity ranges from -1 to 1, we map to 0-1
        confidence = max(0.0, min(1.0, (best_similarity + 1.0) / 2.0))

        return EscalationSignal(
            domain=domain,
            level=best_anchor.level,
            confidence=confidence,
            source="embedding",
            matched_anchor_id=best_anchor.id,
            reasoning=f"Best match: {best_anchor.label} (similarity: {best_similarity:.3f})"
        )

    async def _calculate_content_signal(
        self,
        domain: str,
        text: str,
    ) -> EscalationSignal:
        """Calculate escalation signal from content analysis.

        Analyzes narrative frames, sentiment patterns, and
        escalatory language in the cluster text.

        Args:
            domain: Escalation domain
            text: Combined cluster text

        Returns:
            EscalationSignal with level and confidence
        """
        import re

        if not text or not text.strip():
            return EscalationSignal(
                domain=domain,
                level=3,
                confidence=0.0,
                source="content",
                reasoning="Empty text provided"
            )

        text_lower = text.lower()

        # Count pattern matches per level
        level_scores: Dict[int, float] = {level: 0.0 for level in range(1, 6)}
        matched_patterns: List[str] = []

        for level, patterns in self.ESCALATION_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    level_scores[level] += len(matches)
                    matched_patterns.append(f"L{level}: {pattern[:30]}")

        # Apply domain-specific intensifier bonus
        domain_bonus = 0.0
        if domain in self.DOMAIN_INTENSIFIERS:
            for pattern in self.DOMAIN_INTENSIFIERS[domain]:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    domain_bonus += 0.1 * len(matches)

        domain_bonus = min(domain_bonus, 0.5)  # Cap at 0.5

        # Calculate weighted level
        total_matches = sum(level_scores.values())

        if total_matches == 0:
            # No matches - return neutral
            return EscalationSignal(
                domain=domain,
                level=3,
                confidence=0.2,  # Low confidence
                source="content",
                reasoning="No escalation patterns matched"
            )

        # Weighted average of levels
        weighted_sum = sum(level * score for level, score in level_scores.items())
        avg_level = weighted_sum / total_matches

        # Apply domain bonus (pushes toward higher levels)
        adjusted_level = avg_level + domain_bonus
        final_level = max(1, min(5, round(adjusted_level)))

        # Confidence based on match density and consistency
        text_length = len(text.split())
        match_density = min(1.0, total_matches / max(text_length / 50, 1))

        # Higher confidence when matches are concentrated in fewer levels
        level_concentration = max(level_scores.values()) / max(total_matches, 1)

        confidence = min(1.0, 0.3 + (0.4 * match_density) + (0.3 * level_concentration))

        return EscalationSignal(
            domain=domain,
            level=final_level,
            confidence=confidence,
            source="content",
            reasoning=f"Matched {int(total_matches)} patterns, avg level {avg_level:.2f}, domain bonus {domain_bonus:.2f}"
        )

    async def _calculate_keyword_signal(
        self,
        domain: str,
        text: str,
    ) -> EscalationSignal:
        """Calculate escalation signal from keyword matching.

        Matches text against domain-specific escalation keywords
        from anchor points.

        Args:
            domain: Escalation domain
            text: Combined cluster text

        Returns:
            EscalationSignal with level and matched keywords
        """
        import re

        if not text or not text.strip():
            return EscalationSignal(
                domain=domain,
                level=3,
                confidence=0.0,
                source="keywords",
                matched_keywords=[],
                reasoning="Empty text provided"
            )

        anchors = await self._load_anchors(domain)

        if not anchors:
            return EscalationSignal(
                domain=domain,
                level=3,
                confidence=0.0,
                source="keywords",
                matched_keywords=[],
                reasoning="No anchors available for domain"
            )

        text_lower = text.lower()

        # Score each anchor based on keyword matches
        anchor_scores = []  # List of (anchor, score, matched_keywords)

        for anchor in anchors:
            keywords = anchor.keywords or []
            if not keywords:
                continue

            matched = []
            for keyword in keywords:
                # Case-insensitive word boundary match
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    matched.append(keyword)

            if matched:
                # Score based on percentage of keywords matched
                match_ratio = len(matched) / len(keywords)
                weight = float(anchor.weight or 1.0)
                score = match_ratio * weight
                anchor_scores.append((anchor, score, matched))

        if not anchor_scores:
            return EscalationSignal(
                domain=domain,
                level=3,
                confidence=0.1,  # Low confidence - no keywords matched
                source="keywords",
                matched_keywords=[],
                reasoning="No anchor keywords matched in text"
            )

        # Sort by score descending
        anchor_scores.sort(key=lambda x: x[1], reverse=True)
        best_anchor, best_score, best_matched = anchor_scores[0]

        # Collect all matched keywords across anchors
        all_matched = []
        for _, _, matched in anchor_scores:
            all_matched.extend(matched)
        all_matched = list(set(all_matched))  # Deduplicate

        # Confidence based on match quality
        # - Higher when more keywords matched
        # - Higher when matches concentrated in one anchor
        total_anchors_matched = len(anchor_scores)
        concentration = 1.0 / total_anchors_matched if total_anchors_matched > 0 else 1.0

        confidence = min(1.0, 0.2 + (0.5 * best_score) + (0.3 * concentration))

        return EscalationSignal(
            domain=domain,
            level=best_anchor.level,
            confidence=confidence,
            source="keywords",
            matched_anchor_id=best_anchor.id,
            matched_keywords=all_matched,
            reasoning=f"Best anchor: {best_anchor.label} (score: {best_score:.2f}, {len(best_matched)} keywords)"
        )

    def _combine_signals(
        self,
        domain: str,
        signals: List[EscalationSignal],
    ) -> DomainEscalation:
        """Combine multiple signals into domain escalation.

        Applies weighted average:
        - Embedding: 50%
        - Content: 30%
        - Keywords: 20%

        Args:
            domain: Escalation domain
            signals: List of signals from different sources

        Returns:
            DomainEscalation with combined level and score
        """
        if not signals:
            return DomainEscalation(
                domain=domain,
                level=3,
                score=Decimal("0.500"),
                signals=[],
                confidence=0.0,
            )

        # Map source to weight
        source_weights = {
            "embedding": self.EMBEDDING_WEIGHT,
            "content": self.CONTENT_WEIGHT,
            "keywords": self.KEYWORD_WEIGHT,
        }

        # Calculate weighted sum
        weighted_level_sum = 0.0
        weighted_confidence_sum = 0.0
        total_weight = 0.0

        for signal in signals:
            weight = source_weights.get(signal.source, 0.0)
            if weight > 0:
                weighted_level_sum += signal.level * weight
                weighted_confidence_sum += signal.confidence * weight
                total_weight += weight

        if total_weight == 0:
            return DomainEscalation(
                domain=domain,
                level=3,
                score=Decimal("0.500"),
                signals=signals,
                confidence=0.0,
            )

        # Normalize if weights don't sum to 1 (e.g., missing signals)
        avg_level = weighted_level_sum / total_weight
        avg_confidence = weighted_confidence_sum / total_weight

        # Convert level to score (1-5 -> 0.0-1.0)
        score = Decimal(str((avg_level - 1) / 4)).quantize(Decimal("0.001"))

        # Round level to nearest integer
        final_level = max(1, min(5, round(avg_level)))

        return DomainEscalation(
            domain=domain,
            level=final_level,
            score=score,
            signals=signals,
            confidence=avg_confidence,
        )

    async def _load_anchors(self, domain: str) -> List[EscalationAnchor]:
        """Load active anchors for a domain from cache or database.

        Implements a simple in-memory cache to avoid repeated database queries
        for anchor data within a single calculation session.

        Args:
            domain: Escalation domain

        Returns:
            List of active EscalationAnchor records
        """
        if domain not in self._anchor_cache:
            # Query active anchors for domain
            stmt = (
                select(EscalationAnchor)
                .where(EscalationAnchor.domain == domain)
                .where(EscalationAnchor.is_active == True)
                .order_by(EscalationAnchor.level)
            )
            result = await self.session.execute(stmt)
            self._anchor_cache[domain] = list(result.scalars().all())

        return self._anchor_cache[domain]

    def clear_cache(self) -> None:
        """Clear the anchor cache.

        Should be called when anchor data may have changed, or at the start
        of a new calculation batch to ensure fresh data.
        """
        self._anchor_cache.clear()

    def get_cached_domains(self) -> List[str]:
        """Get list of domains currently in cache.

        Returns:
            List of domain names that have been cached
        """
        return list(self._anchor_cache.keys())
