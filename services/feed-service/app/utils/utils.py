"""
Utility functions for Feed Service.
"""
from urllib.parse import urlparse
from fastapi import HTTPException


def parse_domain_from_url(url: str) -> str:
    """
    Extract domain from feed URL.

    Args:
        url: Feed URL (e.g., "https://example.com/feed.xml")

    Returns:
        Domain string (e.g., "example.com")

    Raises:
        HTTPException: If domain cannot be extracted

    Examples:
        >>> parse_domain_from_url("https://example.com/feed")
        'example.com'
        >>> parse_domain_from_url("https://www.news.org:8080/rss")
        'www.news.org:8080'
        >>> parse_domain_from_url("invalid-url")
        Raises HTTPException(400)
    """
    try:
        parsed_url = urlparse(str(url))

        # First try netloc (most common case)
        domain = parsed_url.netloc

        # Fallback: extract from path if netloc is empty
        if not domain and parsed_url.path:
            # Handle cases like "example.com/feed" without scheme
            domain = parsed_url.path.split('/')[0]

        # Validate domain exists
        if not domain or domain.strip() == '':
            raise ValueError(f"No domain found in URL: {url}")

        return domain

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract domain from feed URL '{url}': {str(e)}"
        )
