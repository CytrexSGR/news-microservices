"""
Clustering Service - DBSCAN for Event Clustering
"""
import logging
from typing import List, Dict, Any, Optional
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


def calculate_time_window(newest_event_time: datetime) -> str:
    """
    Calculate time window category based on newest event age

    Args:
        newest_event_time: Timestamp of newest event in cluster

    Returns:
        Time window string: '1h', '6h', '12h', '24h', 'week', 'month'
    """
    now = datetime.utcnow()
    hours_old = (now - newest_event_time).total_seconds() / 3600

    if hours_old <= 1:
        return '1h'
    elif hours_old <= 6:
        return '6h'
    elif hours_old <= 12:
        return '12h'
    elif hours_old <= 24:
        return '24h'
    elif hours_old <= 168:  # 7 days
        return 'week'
    elif hours_old <= 720:  # 30 days
        return 'month'
    else:
        return 'older'


class ClusteringService:
    """Service for clustering intelligence events using DBSCAN"""

    def __init__(self, eps: float = 0.55, min_samples: int = 10):
        """
        Initialize DBSCAN clustering service.

        Args:
            eps: Epsilon parameter for DBSCAN (default 0.55).
                 With cosine metric, this means cosine_distance <= 0.55
                 which translates to cosine_similarity >= 0.45 (45% match).
            min_samples: Minimum events required to form a cluster (default 10).
        """
        self.eps = eps
        self.min_samples = min_samples
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )

    def vectorize_events(self, events: List[Dict[str, Any]]) -> np.ndarray:
        """
        Convert events to TF-IDF feature vectors

        Args:
            events: List of event dicts with 'title' and 'keywords'

        Returns:
            Feature matrix (n_events x n_features)
        """
        if not events:
            return np.array([])

        # Combine title and keywords for each event
        texts = []
        for event in events:
            title = event.get("title", "")
            keywords = " ".join(event.get("keywords", []))
            texts.append(f"{title} {keywords}")

        try:
            vectors = self.vectorizer.fit_transform(texts)
            return vectors.toarray()
        except Exception as e:
            logger.error(f"Failed to vectorize events: {e}")
            return np.array([])

    def cluster_events(
        self,
        events: List[Dict[str, Any]],
        algorithm: str = "dbscan"
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Cluster events using DBSCAN

        Args:
            events: List of event dicts
            algorithm: Clustering algorithm (only "dbscan" supported for now)

        Returns:
            Dict mapping cluster_id to list of events
        """
        if len(events) < self.min_samples:
            logger.warning(f"Not enough events to cluster: {len(events)} < {self.min_samples}")
            return {}

        # Vectorize events
        vectors = self.vectorize_events(events)
        if vectors.size == 0:
            return {}

        # Run DBSCAN
        dbscan = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric='cosine')
        labels = dbscan.fit_predict(vectors)

        # Group events by cluster
        clusters = {}
        for idx, label in enumerate(labels):
            if label == -1:  # Noise
                continue

            if label not in clusters:
                clusters[label] = []

            clusters[label].append(events[idx])

        logger.info(f"Clustered {len(events)} events into {len(clusters)} clusters")
        return clusters

    def _filter_quality_keywords(self, keywords: List[str]) -> List[str]:
        """
        Filter keywords for quality - remove stopwords, short words, numbers, etc.

        Returns:
            Filtered list of high-quality keywords
        """
        import re

        # Comprehensive stopwords (German + English + common noise)
        stopwords = {
            # English stopwords
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'from', 'by', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'it', 'its', 'it\'s', 'he', 'she', 'they',
            'them', 'their', 'what', 'which', 'who', 'when', 'where', 'why', 'how',
            'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
            'very', 'just', 'now', 'here', 'there', 'then', 'about', 'after',
            'before', 'between', 'into', 'through', 'during', 'above', 'below',

            # German stopwords
            'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen',
            'einem', 'einer', 'eines', 'und', 'oder', 'aber', 'nicht', 'ist',
            'sind', 'war', 'waren', 'wird', 'werden', 'wurde', 'wurden', 'hat',
            'haben', 'hatte', 'hatten', 'sein', 'seine', 'seiner', 'seinem',
            'seinen', 'mit', 'von', 'zu', 'aus', 'bei', 'nach', 'für', 'über',
            'unter', 'auf', 'an', 'in', 'im', 'als', 'wie', 'wenn', 'dann',
            'doch', 'nur', 'noch', 'auch', 'schon', 'mehr', 'sehr', 'kann',
            'könnte', 'sollte', 'muss', 'müssen', 'durch', 'gegen', 'ohne',
            'bis', 'seit', 'während', 'wegen', 'denn', 'weil', 'da', 'ob',
            'dass', 'was', 'wer', 'wo', 'wann', 'warum', 'wie', 'welche',
            'welcher', 'welches', 'dieser', 'diese', 'dieses', 'jener', 'jene',
            'jenes', 'alle', 'alles', 'einige', 'manche', 'viele', 'wenige',

            # Common news/article words
            'says', 'said', 'new', 'news', 'latest', 'breaking', 'update',
            'report', 'reports', 'according', 'former', 'current', 'amid',
            'über', 'nach', 'neue', 'neuer', 'neues', 'laut', 'bericht',
        }

        filtered = []
        for kw in keywords:
            kw_lower = kw.lower().strip()

            # Skip if empty or too short (< 3 chars)
            if not kw_lower or len(kw_lower) < 3:
                continue

            # Skip if stopword
            if kw_lower in stopwords:
                continue

            # Skip if pure number or contains mostly digits
            if re.match(r'^[\d\s\-\.]+$', kw_lower):
                continue

            # Skip if single letter repeated (e.g., "AAA", "bbb")
            if len(set(kw_lower.replace(' ', ''))) == 1:
                continue

            # Skip if looks like a date pattern (e.g., "2024", "Nov", "Monday")
            if re.match(r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|mon|tue|wed|thu|fri|sat|sun)', kw_lower):
                continue

            filtered.append(kw)

        return filtered

    def create_cluster_metadata(
        self,
        cluster_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate cluster metadata from events with intelligent keyword filtering

        Returns:
            Dict with name, keywords, sources, etc.
        """
        if not cluster_events:
            return {}

        # Extract keywords from all events
        all_keywords = []
        for event in cluster_events:
            keywords = event.get("keywords", [])
            # Filter empty and apply quality filtering
            all_keywords.extend([kw for kw in keywords if kw and kw.strip()])

        # Apply quality filtering to keywords
        filtered_keywords = self._filter_quality_keywords(all_keywords)

        # Get most common filtered keywords
        from collections import Counter
        keyword_counts = Counter(filtered_keywords)
        top_keywords = [kw for kw, _ in keyword_counts.most_common(10)]

        # Generate cluster name with intelligent fallback
        cluster_name = None

        # Strategy 1: Use top filtered keywords (preferred)
        if top_keywords:
            cluster_name = ", ".join(top_keywords[:3]).title()

        # Strategy 2: Extract entities from events if no keywords
        if not cluster_name:
            all_entities = []
            for event in cluster_events:
                entities = event.get("entities", [])
                # Extract entity names/text
                for entity in entities:
                    if isinstance(entity, dict):
                        entity_text = entity.get("normalized_text") or entity.get("text")
                        if entity_text and entity_text.strip():
                            all_entities.append(entity_text.strip())

            # Apply quality filtering to entities
            filtered_entities = self._filter_quality_keywords(all_entities)

            if filtered_entities:
                entity_counts = Counter(filtered_entities)
                top_entities = [e for e, _ in entity_counts.most_common(3)]
                cluster_name = ", ".join(top_entities).title()

        # Strategy 3: Extract common words from titles with improved filtering
        if not cluster_name:
            import re
            all_title_words = []

            for event in cluster_events:
                title = event.get("title", "")
                # Extract words (alphanumeric only, 3+ chars)
                words = re.findall(r'\b[a-zA-ZäöüÄÖÜß]{3,}\b', title.lower())
                all_title_words.extend(words)

            # Apply quality filtering
            filtered_title_words = self._filter_quality_keywords(all_title_words)

            if filtered_title_words:
                word_counts = Counter(filtered_title_words)
                top_words = [w for w, _ in word_counts.most_common(3)]
                cluster_name = " ".join(top_words).title()

        # Strategy 4: Last resort - descriptive name with event count
        if not cluster_name:
            cluster_name = f"Cluster ({len(cluster_events)} Events)"

        # Count sources
        sources = {}
        for event in cluster_events:
            source = event.get("source", "Unknown")
            sources[source] = sources.get(source, 0) + 1

        top_sources = [
            {"name": source, "count": count}
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Calculate average sentiment
        sentiments = [e.get("sentiment", 0) for e in cluster_events if e.get("sentiment")]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

        # Determine cluster category from events (majority vote)
        # Valid categories: geo, finance, tech
        category_counts = Counter()
        for event in cluster_events:
            cat = event.get("category")
            if cat and cat in ("geo", "finance", "tech"):
                category_counts[cat] += 1

        # Use most common category, default to "geo" for news intelligence
        cluster_category = category_counts.most_common(1)[0][0] if category_counts else "geo"

        return {
            "name": cluster_name,
            "event_count": len(cluster_events),
            "keywords": top_keywords,
            "top_sources": top_sources,
            "avg_sentiment": avg_sentiment,
            "category": cluster_category,
            "is_active": True,
        }


# Global instance
clustering_service = ClusteringService()
