"""
Event Detection Service - Entity and Keyword Extraction
"""
import spacy
import logging
from typing import Dict, List, Any
from collections import Counter
import re

logger = logging.getLogger(__name__)

# Load spaCy model (lazy loading)
_nlp = None


def get_nlp():
    """Lazy load spaCy model"""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model: en_core_web_sm")
        except OSError:
            logger.error("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            _nlp = None
    return _nlp


class EventDetectionService:
    """Service for detecting and analyzing intelligence events"""

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities using spaCy

        Returns:
            Dict with persons, organizations, locations
        """
        nlp = get_nlp()
        if not nlp or not text:
            return {"persons": [], "organizations": [], "locations": []}

        doc = nlp(text[:10000])  # Limit text length

        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
        }

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities["persons"].append(ent.text)
            elif ent.label_ in ("ORG", "NORP"):
                entities["organizations"].append(ent.text)
            elif ent.label_ in ("GPE", "LOC"):
                entities["locations"].append(ent.text)

        # Deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords using TF-IDF-like approach

        Returns:
            List of top keywords
        """
        if not text:
            return []

        # Simple keyword extraction
        # Remove common words and extract noun phrases
        nlp = get_nlp()
        if not nlp:
            # Fallback: simple word frequency
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
            counter = Counter(words)
            return [word for word, _ in counter.most_common(max_keywords)]

        doc = nlp(text[:10000])

        # Extract noun chunks and named entities
        keywords = []
        for chunk in doc.noun_chunks:
            if len(chunk.text) > 3:
                keywords.append(chunk.text.lower())

        for ent in doc.ents:
            keywords.append(ent.text.lower())

        # Count and return most common
        counter = Counter(keywords)
        return [word for word, _ in counter.most_common(max_keywords)]

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using Levenshtein-like approach

        Returns:
            Similarity score (0-1)
        """
        if not text1 or not text2:
            return 0.0

        # Normalize texts
        t1 = set(text1.lower().split())
        t2 = set(text2.lower().split())

        if not t1 or not t2:
            return 0.0

        # Jaccard similarity
        intersection = len(t1.intersection(t2))
        union = len(t1.union(t2))

        return intersection / union if union > 0 else 0.0

    def is_duplicate(
        self,
        event1: Dict[str, Any],
        event2: Dict[str, Any],
        similarity_threshold: float = 0.8
    ) -> bool:
        """
        Check if two events are duplicates

        Args:
            event1: First event dict (must have 'title', 'published_at')
            event2: Second event dict
            similarity_threshold: Minimum similarity to consider duplicate

        Returns:
            True if duplicate
        """
        # Check title similarity
        title_sim = self.calculate_similarity(
            event1.get("title", ""),
            event2.get("title", "")
        )

        if title_sim >= similarity_threshold:
            # Check temporal proximity (within 1 hour)
            pub1 = event1.get("published_at")
            pub2 = event2.get("published_at")

            if pub1 and pub2:
                time_diff = abs((pub1 - pub2).total_seconds())
                if time_diff < 3600:  # 1 hour
                    return True

        return False


# Global instance
event_detection_service = EventDetectionService()
