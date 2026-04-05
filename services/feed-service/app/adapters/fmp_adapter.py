"""
FMP News Adapter for feed-service

Transforms FMP API news data into Article event format for content-analysis-v2 pipeline.
Treats FMP as a "virtual RSS feed" by publishing to article.created events.

Supported FMP Categories:
- general: General financial news
- stock: Stock market news
- forex: Foreign exchange news
- crypto: Cryptocurrency news
- mergers-acquisitions: M&A and SEC filings

Rate Limiting:
- FMP Starter plan: 300 calls/minute
- Staggered scheduling: 1 call per minute per category = 5 calls/5 minutes
- Peak usage: 1 call/min = 0.33% of limit (very safe)
"""
import logging
import hashlib
import json
from typing import Dict, List, Optional
from datetime import datetime, timezone
from dateutil import parser as date_parser

from app.clients.fmp_client import FMPServiceClient

logger = logging.getLogger(__name__)


class FMPNewsAdapter:
    """
    Adapter to fetch FMP news and transform it into Article event format.

    This enables FMP news to flow through the existing content-analysis-v2 pipeline
    without any changes to the analysis service.
    """

    def __init__(self, fmp_client: Optional[FMPServiceClient] = None):
        """
        Initialize FMP News Adapter.

        Args:
            fmp_client: Optional FMP client instance (creates default if None)
        """
        self.fmp_client = fmp_client or FMPServiceClient()

    async def fetch_news(
        self,
        category: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Fetch news from FMP and transform to Article format.

        Args:
            category: FMP category (general|stock|forex|crypto|mergers-acquisitions)
            limit: Number of articles to fetch

        Returns:
            List of article events ready for RabbitMQ publishing

        Example Output:
            [
                {
                    "event_type": "article.created",
                    "payload": {
                        "item_id": "fmp_abc123",
                        "feed_id": "fmp_general",
                        "title": "Market Update...",
                        "link": "https://...",
                        "content": "Article text...",
                        "source": "Bloomberg",
                        "published_at": "2025-11-21T10:00:00Z",
                        "source_type": "fmp",
                        "category": "general",
                        "symbols": ["AAPL", "MSFT"],
                        "raw_data": {...}
                    }
                }
            ]
        """
        try:
            # Fetch from fmp-service internal API
            news_items = await self.fmp_client.get_news(
                category=category,
                page=0,
                limit=limit
            )

            logger.info(f"Fetched {len(news_items)} {category} news from FMP")

            # Transform to article events
            article_events = []
            for news_item in news_items:
                try:
                    article_event = self._transform_to_article(news_item, category)
                    article_events.append(article_event)
                except Exception as e:
                    logger.error(
                        f"Failed to transform FMP news item: {e}",
                        extra={"news_item": news_item}
                    )
                    continue

            logger.info(
                f"Transformed {len(article_events)}/{len(news_items)} "
                f"{category} news to article events"
            )

            return article_events

        except Exception as e:
            logger.error(f"Failed to fetch FMP {category} news: {e}")
            raise

    def _transform_to_article(self, news_item: Dict, category: str) -> Dict:
        """
        Transform FMP news item to article.created event format.

        Handles two FMP formats:
        1. Regular news: {title, text, url, site, publishedDate, symbol[]}
        2. M&A filings: {companyName, targetedCompanyName, symbol, transactionDate, link}

        Args:
            news_item: FMP news item (raw format)
            category: FMP category for context

        Returns:
            Article event dict ready for RabbitMQ
        """
        # Detect M&A format (has companyName instead of title)
        if 'companyName' in news_item:
            return self._transform_ma_news(news_item, category)
        else:
            return self._transform_regular_news(news_item, category)

    def _transform_regular_news(self, news_item: Dict, category: str) -> Dict:
        """
        Transform regular FMP news format.

        FMP Format:
            {
                "title": "Market Update",
                "text": "Article content...",
                "url": "https://...",
                "site": "Bloomberg",
                "publishedDate": "2025-11-21 10:00:00",
                "symbol": "AAPL"  # Can be string or array
            }

        Article Format:
            {
                "event_type": "article.created",
                "payload": {
                    "item_id": "fmp_<hash>",
                    "feed_id": "fmp_<category>",
                    "title": "...",
                    "link": "...",
                    "content": "...",
                    "source": "...",
                    "published_at": "ISO8601",
                    "source_type": "fmp",
                    "category": "general|stock|forex|crypto",
                    "symbols": ["AAPL"],
                    "raw_data": {...}
                }
            }
        """
        # Extract fields (handle both DB and Live API formats)
        title = news_item.get('title', '')
        content = news_item.get('text') or news_item.get('content', '')
        url = news_item.get('url', '')
        source = news_item.get('site') or news_item.get('source', 'FMP')

        # Parse published date
        published_date_str = news_item.get('publishedDate') or news_item.get('publishedAt')
        published_at = self._parse_date(published_date_str)

        # Handle symbols (can be string or array)
        symbols = []
        symbol_data = news_item.get('symbol')
        if symbol_data:
            if isinstance(symbol_data, list):
                symbols = symbol_data
            elif isinstance(symbol_data, str):
                symbols = [symbol_data]

        # Generate unique item_id from content hash
        content_str = f"{title}|{url}|{published_date_str}"
        item_id = f"fmp_{hashlib.sha256(content_str.encode()).hexdigest()[:12]}"

        # Build article event
        return {
            "event_type": "article.created",
            "payload": {
                "item_id": item_id,
                "feed_id": f"fmp_{category}",
                "title": title,
                "link": url,
                "content": content,
                "source": source,
                "published_at": published_at,
                "source_type": "fmp",  # Marker for FMP-sourced articles
                "category": category,
                "symbols": symbols,
                "has_content": bool(content),
                "analysis_config": {
                    # FMP news gets full analysis pipeline
                    "enable_analysis_v2": True
                },
                "raw_data": news_item  # Store original for debugging
            }
        }

    def _transform_ma_news(self, news_item: Dict, category: str) -> Dict:
        """
        Transform M&A SEC filing format.

        FMP M&A Format:
            {
                "companyName": "Huntington Bancshares",
                "targetedCompanyName": "Cadence Bank",
                "symbol": "HBAN",
                "targetedSymbol": "CADE",
                "transactionDate": "2025-05-15 00:00:00",
                "acceptedDate": "2025-11-20 16:30:00",
                "link": "https://sec.gov/..."
            }

        Article Format (synthesized):
            - Title: "Company A acquiring Company B"
            - Content: Transaction details
            - Symbols: Both acquirer and target
        """
        company_name = news_item.get('companyName', 'Unknown')
        target_name = news_item.get('targetedCompanyName', 'Unknown')
        symbol = news_item.get('symbol', '')
        target_symbol = news_item.get('targetedSymbol', '')
        transaction_date = news_item.get('transactionDate', '')
        accepted_date = news_item.get('acceptedDate', '')
        link = news_item.get('link', '')

        # Synthesize title
        title = f"{company_name} acquiring {target_name}"

        # Synthesize content
        content = (
            f"SEC Filing: {company_name} ({symbol}) is acquiring "
            f"{target_name} ({target_symbol}). "
            f"Transaction Date: {transaction_date}. "
            f"Filing Accepted: {accepted_date}."
        )

        # Parse dates
        published_at = self._parse_date(accepted_date)

        # Symbols array (both companies)
        symbols = [s for s in [symbol, target_symbol] if s]

        # Generate unique item_id
        content_str = f"{company_name}|{target_name}|{transaction_date}"
        item_id = f"fmp_ma_{hashlib.sha256(content_str.encode()).hexdigest()[:12]}"

        # Build article event
        return {
            "event_type": "article.created",
            "payload": {
                "item_id": item_id,
                "feed_id": f"fmp_{category}",
                "title": title,
                "link": link,
                "content": content,
                "source": "SEC Filings (via FMP)",
                "published_at": published_at,
                "source_type": "fmp",
                "category": category,
                "symbols": symbols,
                "has_content": True,
                "analysis_config": {
                    "enable_analysis_v2": True
                },
                "raw_data": news_item
            }
        }

    def _parse_date(self, date_str: Optional[str]) -> str:
        """
        Parse various date formats to ISO8601 string.

        Handles:
        - "2025-11-21 10:00:00"
        - "2025-11-21T10:00:00Z"
        - "2025-11-21T10:00:00+00:00"

        Returns:
            ISO8601 formatted string
        """
        if not date_str:
            return datetime.now(timezone.utc).isoformat()

        try:
            # Parse with dateutil (handles most formats)
            dt = date_parser.parse(date_str)

            # Ensure timezone-aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return dt.isoformat()

        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return datetime.now(timezone.utc).isoformat()

    async def close(self):
        """Close FMP client connection."""
        await self.fmp_client.close()
