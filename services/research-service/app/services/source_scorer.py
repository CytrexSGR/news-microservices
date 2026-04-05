"""
Source quality scoring service for research results.

Evaluates and scores sources based on authority, freshness, relevance,
credibility, and diversity to ensure high-quality research outputs.
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from collections import Counter

logger = logging.getLogger(__name__)


# Known credible source domains with authority scores
CREDIBLE_SOURCES = {
    # Academic and Research
    "arxiv.org": 95,
    "scholar.google.com": 95,
    "researchgate.net": 90,
    "pubmed.ncbi.nlm.nih.gov": 95,
    "ieee.org": 90,
    "acm.org": 90,
    "springer.com": 85,
    "sciencedirect.com": 85,
    "nature.com": 95,
    "science.org": 95,
    "cell.com": 90,

    # News Organizations
    "reuters.com": 90,
    "apnews.com": 90,
    "bbc.com": 85,
    "bbc.co.uk": 85,
    "nytimes.com": 85,
    "washingtonpost.com": 85,
    "theguardian.com": 85,
    "economist.com": 85,
    "wsj.com": 85,
    "ft.com": 85,
    "bloomberg.com": 85,

    # Government and Official
    "gov": 95,
    "edu": 90,
    "mil": 90,
    "un.org": 90,
    "who.int": 95,
    "cdc.gov": 95,
    "nih.gov": 95,
    "nasa.gov": 95,
    "europa.eu": 90,

    # Technology
    "github.com": 80,
    "stackoverflow.com": 75,
    "medium.com": 70,
    "dev.to": 70,
    "hackernews.com": 75,

    # Wikipedia and References
    "wikipedia.org": 75,
    "wikimedia.org": 75,
}

# Blacklisted domains (known for misinformation or low quality)
BLACKLISTED_SOURCES = {
    "example-fake-news.com",
    "clickbait-site.com",
    "spam-domain.com",
    # Add actual problematic domains as identified
}

# Academic TLDs and patterns
ACADEMIC_PATTERNS = [
    r"\.edu$",
    r"\.ac\.[a-z]{2}$",
    r"\.edu\.[a-z]{2}$",
    r"university",
    r"college",
    r"institute",
    r"research",
]

# Official/Government TLDs
OFFICIAL_PATTERNS = [
    r"\.gov$",
    r"\.mil$",
    r"\.gov\.[a-z]{2}$",
    r"\.org$",  # Many NGOs and organizations
]


class SourceScorer:
    """Service for scoring and ranking research sources."""

    def __init__(
        self,
        min_quality_threshold: int = 40,
        enable_blacklist: bool = True,
        enable_whitelist: bool = True,
    ):
        """
        Initialize the source scorer.

        Args:
            min_quality_threshold: Minimum score (0-100) for a source to be included
            enable_blacklist: Whether to filter blacklisted domains
            enable_whitelist: Whether to boost whitelisted domains
        """
        self.min_quality_threshold = min_quality_threshold
        self.enable_blacklist = enable_blacklist
        self.enable_whitelist = enable_whitelist

        logger.info(
            f"SourceScorer initialized with threshold={min_quality_threshold}, "
            f"blacklist={'enabled' if enable_blacklist else 'disabled'}, "
            f"whitelist={'enabled' if enable_whitelist else 'disabled'}"
        )

    def score_sources(
        self,
        sources: List[Dict[str, Any]],
        query: str,
        context: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Score a list of sources and return them ranked by quality.

        Args:
            sources: List of source dictionaries with keys: url, title, snippet, published_date
            query: Original research query for relevance scoring
            context: Optional context for relevance evaluation

        Returns:
            List of sources with quality scores, filtered and sorted by score
        """
        scored_sources = []
        domains_seen = Counter()

        for source in sources:
            # Extract domain
            domain = self._extract_domain(source.get("url", ""))

            # Check blacklist
            if self.enable_blacklist and domain in BLACKLISTED_SOURCES:
                logger.info(f"Filtered blacklisted source: {domain}")
                continue

            # Track domain diversity
            domains_seen[domain] += 1

            # Calculate individual scores
            authority_score = self._calculate_authority_score(source)
            freshness_score = self._calculate_freshness_score(source)
            relevance_score = self._calculate_relevance_score(source, query, context)
            credibility_score = self._calculate_credibility_score(source)
            diversity_penalty = self._calculate_diversity_penalty(domains_seen[domain])

            # Calculate weighted overall score
            overall_score = (
                authority_score * 0.30 +
                freshness_score * 0.20 +
                relevance_score * 0.25 +
                credibility_score * 0.25
            ) - diversity_penalty

            # Ensure score is in valid range
            overall_score = max(0, min(100, overall_score))

            # Filter by minimum threshold
            if overall_score < self.min_quality_threshold:
                logger.debug(
                    f"Filtered low-quality source: {source.get('url')} "
                    f"(score: {overall_score:.2f})"
                )
                continue

            # Add scores to source
            source_with_scores = {
                **source,
                "quality_score": round(overall_score, 2),
                "authority_score": round(authority_score, 2),
                "freshness_score": round(freshness_score, 2),
                "relevance_score": round(relevance_score, 2),
                "credibility_score": round(credibility_score, 2),
                "domain": domain,
                "domain_count": domains_seen[domain],
            }

            scored_sources.append(source_with_scores)

        # Sort by quality score (descending)
        scored_sources.sort(key=lambda x: x["quality_score"], reverse=True)

        logger.info(
            f"Scored {len(scored_sources)} sources "
            f"(filtered {len(sources) - len(scored_sources)} low-quality sources)"
        )

        return scored_sources

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception as e:
            logger.warning(f"Failed to parse URL {url}: {e}")
            return ""

    def _calculate_authority_score(self, source: Dict[str, Any]) -> float:
        """
        Calculate domain authority score (0-100).

        Based on:
        - Known credible sources
        - Academic/official domains
        - Domain age indicators
        """
        url = source.get("url", "")
        domain = self._extract_domain(url)

        # Check whitelist
        if self.enable_whitelist and domain in CREDIBLE_SOURCES:
            return CREDIBLE_SOURCES[domain]

        # Check for academic domains
        for pattern in ACADEMIC_PATTERNS:
            if re.search(pattern, domain, re.IGNORECASE):
                return 85.0

        # Check for official/government domains
        for pattern in OFFICIAL_PATTERNS:
            if re.search(pattern, domain):
                # .org is less authoritative than .gov
                if pattern == r"\.org$":
                    return 70.0
                return 90.0

        # Check TLD quality
        if domain.endswith((".com", ".net", ".io")):
            return 60.0
        elif domain.endswith((".info", ".biz")):
            return 50.0
        elif domain.endswith((".xyz", ".tk", ".ml")):
            return 40.0

        # Default score for unknown domains
        return 55.0

    def _calculate_freshness_score(self, source: Dict[str, Any]) -> float:
        """
        Calculate freshness score (0-100).

        Based on publication date:
        - 100: Within last 24 hours
        - 90: Within last week
        - 70: Within last month
        - 50: Within last 6 months
        - 30: Within last year
        - 10: Older than a year
        """
        published_date = source.get("published_date")

        if not published_date:
            # No date information - return neutral score
            return 50.0

        try:
            # Parse date (handle various formats)
            if isinstance(published_date, str):
                # Try ISO format first
                try:
                    pub_date = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
                except ValueError:
                    # Try other common formats
                    from dateutil import parser
                    pub_date = parser.parse(published_date)
            elif isinstance(published_date, datetime):
                pub_date = published_date
            else:
                return 50.0

            # Ensure timezone-aware
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            age = now - pub_date

            if age < timedelta(days=1):
                return 100.0
            elif age < timedelta(days=7):
                return 90.0
            elif age < timedelta(days=30):
                return 70.0
            elif age < timedelta(days=180):
                return 50.0
            elif age < timedelta(days=365):
                return 30.0
            else:
                # Older sources still have value for historical context
                return 10.0

        except Exception as e:
            logger.warning(f"Failed to parse date {published_date}: {e}")
            return 50.0

    def _calculate_relevance_score(
        self,
        source: Dict[str, Any],
        query: str,
        context: Optional[str] = None,
    ) -> float:
        """
        Calculate relevance score (0-100).

        Based on:
        - Query terms in title
        - Query terms in snippet/description
        - Context match (if provided)
        """
        title = (source.get("title") or "").lower()
        snippet = (source.get("snippet") or source.get("description") or "").lower()
        citation_context = (source.get("citation_context") or "").lower()

        query_terms = query.lower().split()
        score = 0.0

        # Title relevance (max 40 points)
        title_matches = sum(1 for term in query_terms if term in title)
        if title_matches > 0:
            title_score = min(40, (title_matches / len(query_terms)) * 40)
            score += title_score

        # Snippet relevance (max 30 points)
        snippet_matches = sum(1 for term in query_terms if term in snippet)
        if snippet_matches > 0:
            snippet_score = min(30, (snippet_matches / len(query_terms)) * 30)
            score += snippet_score

        # Citation context relevance (max 30 points)
        if citation_context:
            context_matches = sum(1 for term in query_terms if term in citation_context)
            if context_matches > 0:
                context_score = min(30, (context_matches / len(query_terms)) * 30)
                score += context_score
        else:
            # No citation context - add 15 points baseline
            score += 15

        return min(100.0, score)

    def _calculate_credibility_score(self, source: Dict[str, Any]) -> float:
        """
        Calculate credibility score (0-100).

        Based on:
        - Presence of author information
        - Presence of publication metadata
        - Content completeness
        - URL structure (no suspicious patterns)
        """
        score = 50.0  # Baseline

        # Author information (+20 points)
        if source.get("author"):
            score += 20

        # Publication date (+15 points)
        if source.get("published_date"):
            score += 15

        # Complete content (+10 points)
        snippet = source.get("snippet") or source.get("description") or ""
        if len(snippet) > 100:
            score += 10

        # Clean URL structure (+5 points, -10 for suspicious)
        url = source.get("url", "")
        if url:
            # Check for suspicious patterns
            suspicious_patterns = [
                r"\d{10,}",  # Long numeric strings
                r"[?&]ref=",  # Referral links
                r"redirect",
                r"tracking",
                r"click",
                r"ad=",
            ]

            is_suspicious = any(
                re.search(pattern, url.lower()) for pattern in suspicious_patterns
            )

            if is_suspicious:
                score -= 10
            else:
                score += 5

        return max(0.0, min(100.0, score))

    def _calculate_diversity_penalty(self, domain_count: int) -> float:
        """
        Calculate penalty for source diversity (avoid echo chambers).

        Returns penalty points (0-20) to subtract from overall score.
        More sources from same domain = higher penalty.
        """
        if domain_count <= 1:
            return 0.0
        elif domain_count == 2:
            return 5.0
        elif domain_count == 3:
            return 10.0
        elif domain_count == 4:
            return 15.0
        else:
            return 20.0

    def get_quality_report(
        self, scored_sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a quality report for scored sources.

        Args:
            scored_sources: List of sources with quality scores

        Returns:
            Report dictionary with statistics and recommendations
        """
        if not scored_sources:
            return {
                "total_sources": 0,
                "avg_quality_score": 0.0,
                "quality_distribution": {},
                "top_domains": [],
                "recommendations": ["No sources to analyze"],
            }

        # Calculate statistics
        scores = [s["quality_score"] for s in scored_sources]
        avg_score = sum(scores) / len(scores)

        # Quality distribution
        quality_distribution = {
            "excellent": sum(1 for s in scores if s >= 80),
            "good": sum(1 for s in scores if 60 <= s < 80),
            "fair": sum(1 for s in scores if 40 <= s < 60),
            "poor": sum(1 for s in scores if s < 40),
        }

        # Top domains
        domain_counts = Counter(s["domain"] for s in scored_sources)
        top_domains = [
            {"domain": domain, "count": count}
            for domain, count in domain_counts.most_common(5)
        ]

        # Generate recommendations
        recommendations = []

        if avg_score < 60:
            recommendations.append(
                "Overall source quality is low. Consider refining the research query "
                "or expanding to more authoritative sources."
            )

        if quality_distribution["excellent"] == 0:
            recommendations.append(
                "No excellent-quality sources found. Consider including academic or "
                "official sources in the research."
            )

        # Check for diversity
        if len(top_domains) > 0 and top_domains[0]["count"] > len(scored_sources) * 0.4:
            recommendations.append(
                f"Sources are heavily concentrated in {top_domains[0]['domain']}. "
                "Consider diversifying sources to avoid echo chambers."
            )

        # Check freshness
        old_sources = sum(
            1 for s in scored_sources
            if s.get("freshness_score", 100) < 30
        )
        if old_sources > len(scored_sources) * 0.5:
            recommendations.append(
                "Many sources are outdated. Consider prioritizing more recent publications."
            )

        if not recommendations:
            recommendations.append("Source quality is good overall. No immediate concerns.")

        return {
            "total_sources": len(scored_sources),
            "avg_quality_score": round(avg_score, 2),
            "min_score": round(min(scores), 2),
            "max_score": round(max(scores), 2),
            "quality_distribution": quality_distribution,
            "top_domains": top_domains,
            "recommendations": recommendations,
        }


# Global instance
source_scorer = SourceScorer(
    min_quality_threshold=40,
    enable_blacklist=True,
    enable_whitelist=True,
)
