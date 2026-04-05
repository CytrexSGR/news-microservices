"""
JSON-LD Schema.org Extractor

Extracts structured article metadata from JSON-LD markup.
"""
import json
import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class JSONLDExtractor:
    """Extracts Schema.org Article metadata from JSON-LD"""

    # Schema.org types we're interested in
    ARTICLE_TYPES = [
        "Article",
        "NewsArticle",
        "BlogPosting",
        "ReportageNewsArticle",
        "AnalysisNewsArticle",
        "OpinionNewsArticle",
        "ReviewNewsArticle",
        "BackgroundNewsArticle",
        "WebPage",
        "CreativeWork",
    ]

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def extract(self, html: str) -> Optional[Dict[str, Any]]:
        """
        Extract article metadata from JSON-LD in HTML.

        Args:
            html: HTML content to parse

        Returns:
            Extracted metadata dict or None if not found
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            jsonld_scripts = soup.find_all("script", type="application/ld+json")

            for script in jsonld_scripts:
                try:
                    data = json.loads(script.string)
                    result = self._process_jsonld(data)
                    if result:
                        return result
                except json.JSONDecodeError as e:
                    logger.debug(f"Invalid JSON-LD: {e}")
                    continue
                except Exception as e:
                    logger.debug(f"Error processing JSON-LD: {e}")
                    continue

            return None

        except Exception as e:
            logger.error(f"JSON-LD extraction failed: {e}")
            return None

    def _process_jsonld(self, data: Any) -> Optional[Dict[str, Any]]:
        """Process JSON-LD data recursively"""
        if isinstance(data, list):
            # Handle @graph or array of objects
            for item in data:
                result = self._process_jsonld(item)
                if result:
                    return result
            return None

        if not isinstance(data, dict):
            return None

        # Check for @graph
        if "@graph" in data:
            return self._process_jsonld(data["@graph"])

        # Check if this is an article type
        item_type = data.get("@type", "")
        if isinstance(item_type, list):
            item_types = item_type
        else:
            item_types = [item_type]

        is_article = any(
            t in self.ARTICLE_TYPES or
            t.endswith("Article") or
            t.endswith("Posting")
            for t in item_types
        )

        if not is_article:
            return None

        return self._extract_article_fields(data)

    def _extract_article_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant article fields"""
        result = {
            "schema_type": data.get("@type"),
            "headline": self._get_text(data.get("headline")),
            "description": self._get_text(data.get("description")),
            "article_body": self._get_text(data.get("articleBody")),
            "date_published": self._parse_date(data.get("datePublished")),
            "date_modified": self._parse_date(data.get("dateModified")),
            "author": self._extract_author(data.get("author")),
            "publisher": self._extract_publisher(data.get("publisher")),
            "main_entity_of_page": self._get_url(data.get("mainEntityOfPage")),
            "url": data.get("url"),
            "image": self._extract_image(data.get("image")),
            "keywords": self._extract_keywords(data.get("keywords")),
            "word_count": data.get("wordCount"),
            "section": self._get_text(data.get("articleSection")),
            "language": data.get("inLanguage"),
            "is_accessible_for_free": data.get("isAccessibleForFree"),
            "is_part_of": self._extract_is_part_of(data.get("isPartOf")),
        }

        # Remove None values
        result = {k: v for k, v in result.items() if v is not None}

        return result

    def _get_text(self, value: Any) -> Optional[str]:
        """Extract text from a value that might be a string or object"""
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip() if value.strip() else None
        if isinstance(value, dict):
            return value.get("@value") or value.get("name")
        if isinstance(value, list) and value:
            return self._get_text(value[0])
        return str(value) if value else None

    def _get_url(self, value: Any) -> Optional[str]:
        """Extract URL from value"""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return value.get("@id") or value.get("url")
        return None

    def _parse_date(self, value: Any) -> Optional[str]:
        """Parse and normalize date string"""
        if value is None:
            return None

        date_str = self._get_text(value)
        if not date_str:
            return None

        # Return ISO format string
        try:
            # Try parsing common formats
            for fmt in [
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
            ]:
                try:
                    dt = datetime.strptime(date_str.replace("+00:00", "Z").rstrip("Z"), fmt.rstrip("%z").rstrip("Z"))
                    return dt.isoformat()
                except ValueError:
                    continue

            # Return as-is if parsing fails
            return date_str
        except Exception:
            return date_str

    def _extract_author(self, author: Any) -> Optional[List[Dict[str, Any]]]:
        """Extract author information"""
        if author is None:
            return None

        authors = []

        if isinstance(author, str):
            authors.append({"name": author, "type": "Person"})
        elif isinstance(author, dict):
            authors.append(self._normalize_person_org(author))
        elif isinstance(author, list):
            for a in author:
                if isinstance(a, str):
                    authors.append({"name": a, "type": "Person"})
                elif isinstance(a, dict):
                    authors.append(self._normalize_person_org(a))

        return authors if authors else None

    def _normalize_person_org(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a Person or Organization object"""
        return {
            "type": data.get("@type", "Person"),
            "name": self._get_text(data.get("name")),
            "url": data.get("url"),
            "same_as": data.get("sameAs"),
        }

    def _extract_publisher(self, publisher: Any) -> Optional[Dict[str, Any]]:
        """Extract publisher information"""
        if publisher is None:
            return None

        if isinstance(publisher, str):
            return {"name": publisher, "type": "Organization"}

        if isinstance(publisher, dict):
            result = {
                "type": publisher.get("@type", "Organization"),
                "name": self._get_text(publisher.get("name")),
                "url": publisher.get("url"),
            }

            # Extract logo
            logo = publisher.get("logo")
            if logo:
                if isinstance(logo, str):
                    result["logo"] = logo
                elif isinstance(logo, dict):
                    result["logo"] = logo.get("url") or logo.get("@id")

            return {k: v for k, v in result.items() if v is not None}

        return None

    def _extract_image(self, image: Any) -> Optional[Dict[str, Any]]:
        """Extract image information"""
        if image is None:
            return None

        if isinstance(image, str):
            return {"url": image}

        if isinstance(image, list):
            if not image:
                return None
            # Take the first image
            return self._extract_image(image[0])

        if isinstance(image, dict):
            return {
                "url": image.get("url") or image.get("@id"),
                "width": image.get("width"),
                "height": image.get("height"),
                "caption": self._get_text(image.get("caption")),
            }

        return None

    def _extract_keywords(self, keywords: Any) -> Optional[List[str]]:
        """Extract keywords/tags"""
        if keywords is None:
            return None

        if isinstance(keywords, str):
            # Split by comma or return as single item
            if "," in keywords:
                return [k.strip() for k in keywords.split(",") if k.strip()]
            return [keywords.strip()] if keywords.strip() else None

        if isinstance(keywords, list):
            return [str(k).strip() for k in keywords if k]

        return None

    def _extract_is_part_of(self, is_part_of: Any) -> Optional[Dict[str, Any]]:
        """Extract isPartOf (e.g., special report, series)"""
        if is_part_of is None:
            return None

        if isinstance(is_part_of, str):
            return {"name": is_part_of}

        if isinstance(is_part_of, dict):
            return {
                "type": is_part_of.get("@type"),
                "name": self._get_text(is_part_of.get("name")),
                "url": is_part_of.get("url"),
            }

        return None

    def extract_all(self, html: str) -> List[Dict[str, Any]]:
        """
        Extract all JSON-LD blocks from HTML.

        Args:
            html: HTML content to parse

        Returns:
            List of all extracted JSON-LD objects
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            jsonld_scripts = soup.find_all("script", type="application/ld+json")

            results = []
            for script in jsonld_scripts:
                try:
                    data = json.loads(script.string)
                    results.append(data)
                except json.JSONDecodeError:
                    continue

            return results

        except Exception as e:
            logger.error(f"JSON-LD extraction failed: {e}")
            return []

    def has_article_jsonld(self, html: str) -> bool:
        """Check if HTML contains article-type JSON-LD"""
        return self.extract(html) is not None


# Singleton instance
_extractor: Optional[JSONLDExtractor] = None


def get_jsonld_extractor() -> JSONLDExtractor:
    """Get singleton JSON-LD extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = JSONLDExtractor()
    return _extractor
