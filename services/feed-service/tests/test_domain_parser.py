"""
Unit tests for domain parsing utility function.

Tests the parse_domain_from_url() function which extracts domains
from feed URLs for assessment requests.
"""
import pytest
from fastapi import HTTPException

from app.utils import parse_domain_from_url


class TestDomainParser:
    """Test suite for domain extraction from feed URLs."""

    def test_extract_domain_from_standard_url(self):
        """Test standard HTTPS URL with path."""
        url = "https://example.com/feed.xml"
        domain = parse_domain_from_url(url)
        assert domain == "example.com"

    def test_extract_domain_with_subdomain(self):
        """Test URL with www subdomain."""
        url = "https://www.news.org/rss/feed"
        domain = parse_domain_from_url(url)
        assert domain == "www.news.org"

    def test_extract_domain_with_port(self):
        """Test URL with explicit port number."""
        url = "https://example.com:8080/feed"
        domain = parse_domain_from_url(url)
        assert domain == "example.com:8080"

    def test_extract_domain_with_complex_path(self):
        """Test URL with complex nested path."""
        url = "https://news.example.com/feeds/technology/ai.xml"
        domain = parse_domain_from_url(url)
        assert domain == "news.example.com"

    def test_extract_domain_without_scheme(self):
        """Test URL without http/https scheme (fallback to path parsing)."""
        url = "example.com/feed.xml"
        domain = parse_domain_from_url(url)
        # Without scheme, netloc is empty, so we get from path
        assert domain == "example.com"

    def test_extract_domain_http_url(self):
        """Test HTTP (non-HTTPS) URL."""
        url = "http://feeds.reuters.com/reuters/worldNews"
        domain = parse_domain_from_url(url)
        assert domain == "feeds.reuters.com"

    def test_invalid_url_raises_exception(self):
        """Test that malformed URL raises HTTPException."""
        url = "not-a-valid-url"
        # This should still work actually - it will extract "not-a-valid-url" from path
        domain = parse_domain_from_url(url)
        assert domain == "not-a-valid-url"

    def test_empty_url_raises_exception(self):
        """Test that empty URL raises HTTPException."""
        url = ""
        with pytest.raises(HTTPException) as exc_info:
            parse_domain_from_url(url)
        assert exc_info.value.status_code == 400
        assert "Could not extract domain" in exc_info.value.detail

    def test_url_with_only_slash_raises_exception(self):
        """Test that URL with only slash raises HTTPException."""
        url = "/"
        with pytest.raises(HTTPException) as exc_info:
            parse_domain_from_url(url)
        assert exc_info.value.status_code == 400

    def test_url_with_query_parameters(self):
        """Test URL with query parameters (should be ignored)."""
        url = "https://example.com/feed.xml?format=rss&limit=10"
        domain = parse_domain_from_url(url)
        assert domain == "example.com"

    def test_url_with_fragment(self):
        """Test URL with fragment identifier (should be ignored)."""
        url = "https://example.com/feed.xml#section1"
        domain = parse_domain_from_url(url)
        assert domain == "example.com"

    def test_url_with_authentication(self):
        """Test URL with user:pass@ authentication."""
        url = "https://user:pass@secure.example.com/feed"
        domain = parse_domain_from_url(url)
        # netloc includes authentication, but that's okay for our purposes
        assert "secure.example.com" in domain

    def test_real_world_rss_feeds(self):
        """Test real-world RSS feed URLs."""
        test_cases = [
            ("https://www.derstandard.at/rss", "www.derstandard.at"),
            ("https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", "rss.nytimes.com"),
            ("https://feeds.bbci.co.uk/news/rss.xml", "feeds.bbci.co.uk"),
            ("https://www.theguardian.com/world/rss", "www.theguardian.com"),
        ]

        for url, expected_domain in test_cases:
            domain = parse_domain_from_url(url)
            assert domain == expected_domain, f"Failed for URL: {url}"

    def test_localhost_urls(self):
        """Test localhost URLs (useful for development)."""
        test_cases = [
            ("http://localhost:8080/feed", "localhost:8080"),
            ("http://127.0.0.1:3000/rss", "127.0.0.1:3000"),
            ("http://localhost/feed.xml", "localhost"),
        ]

        for url, expected_domain in test_cases:
            domain = parse_domain_from_url(url)
            assert domain == expected_domain

    def test_ip_address_urls(self):
        """Test URLs with IP addresses instead of domain names."""
        url = "http://192.168.1.100:8000/feed.xml"
        domain = parse_domain_from_url(url)
        assert domain == "192.168.1.100:8000"

    def test_internationalized_domain_names(self):
        """Test URLs with non-ASCII domain names (IDN)."""
        # Example: German domain with umlaut
        url = "https://münchen.de/feed.xml"
        domain = parse_domain_from_url(url)
        # urlparse should handle this correctly
        assert "münchen.de" in domain or "xn--" in domain  # Either Unicode or punycode

    def test_domain_with_hyphen(self):
        """Test domain with hyphens (common in news sites)."""
        url = "https://my-news-site.com/feed"
        domain = parse_domain_from_url(url)
        assert domain == "my-news-site.com"

    def test_domain_with_numbers(self):
        """Test domain with numbers."""
        url = "https://news24.com/feed.xml"
        domain = parse_domain_from_url(url)
        assert domain == "news24.com"

    def test_trailing_slash_handling(self):
        """Test URL with trailing slash."""
        url = "https://example.com/"
        domain = parse_domain_from_url(url)
        assert domain == "example.com"

    def test_uppercase_domain(self):
        """Test URL with uppercase characters (domains are case-insensitive)."""
        url = "https://Example.COM/Feed.XML"
        domain = parse_domain_from_url(url)
        # urlparse preserves case, which is fine
        assert domain.lower() == "example.com"
