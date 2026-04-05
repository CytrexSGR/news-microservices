"""Tests for JSON-LD Extractor"""
import pytest
from app.services.extraction.jsonld_extractor import JSONLDExtractor, get_jsonld_extractor


class TestJSONLDExtractor:
    @pytest.fixture
    def extractor(self):
        return JSONLDExtractor()

    @pytest.fixture
    def sample_article_jsonld(self):
        return '''
        <html>
        <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": "Breaking News: Test Article",
            "description": "This is a test article description",
            "datePublished": "2024-01-15T10:30:00Z",
            "dateModified": "2024-01-15T11:00:00Z",
            "author": {
                "@type": "Person",
                "name": "John Doe",
                "url": "https://example.com/author/johndoe"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Example News",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://example.com/logo.png"
                }
            },
            "image": "https://example.com/article-image.jpg",
            "keywords": "breaking news, test, article",
            "articleSection": "Technology"
        }
        </script>
        </head>
        <body></body>
        </html>
        '''

    def test_extract_basic_article(self, extractor, sample_article_jsonld):
        result = extractor.extract(sample_article_jsonld)

        assert result is not None
        assert result["headline"] == "Breaking News: Test Article"
        assert result["description"] == "This is a test article description"
        assert result["schema_type"] == "NewsArticle"

    def test_extract_author(self, extractor, sample_article_jsonld):
        result = extractor.extract(sample_article_jsonld)

        assert result["author"] is not None
        assert len(result["author"]) == 1
        assert result["author"][0]["name"] == "John Doe"
        assert result["author"][0]["type"] == "Person"

    def test_extract_publisher(self, extractor, sample_article_jsonld):
        result = extractor.extract(sample_article_jsonld)

        assert result["publisher"] is not None
        assert result["publisher"]["name"] == "Example News"
        assert result["publisher"]["logo"] == "https://example.com/logo.png"

    def test_extract_dates(self, extractor, sample_article_jsonld):
        result = extractor.extract(sample_article_jsonld)

        assert result["date_published"] is not None
        assert "2024-01-15" in result["date_published"]
        assert result["date_modified"] is not None

    def test_extract_keywords(self, extractor, sample_article_jsonld):
        result = extractor.extract(sample_article_jsonld)

        assert result["keywords"] is not None
        assert len(result["keywords"]) == 3
        assert "breaking news" in result["keywords"]

    def test_extract_image(self, extractor, sample_article_jsonld):
        result = extractor.extract(sample_article_jsonld)

        assert result["image"] is not None
        assert result["image"]["url"] == "https://example.com/article-image.jpg"

    def test_extract_section(self, extractor, sample_article_jsonld):
        result = extractor.extract(sample_article_jsonld)

        assert result["section"] == "Technology"

    def test_no_jsonld(self, extractor):
        html = "<html><body><p>No JSON-LD here</p></body></html>"
        result = extractor.extract(html)

        assert result is None

    def test_invalid_jsonld(self, extractor):
        html = '''
        <html>
        <head>
        <script type="application/ld+json">
        { invalid json here }
        </script>
        </head>
        </html>
        '''
        result = extractor.extract(html)

        assert result is None

    def test_non_article_jsonld(self, extractor):
        html = '''
        <html>
        <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Example Corp"
        }
        </script>
        </head>
        </html>
        '''
        result = extractor.extract(html)

        assert result is None

    def test_multiple_authors(self, extractor):
        html = '''
        <html>
        <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Multi-author article",
            "author": [
                {"@type": "Person", "name": "Alice"},
                {"@type": "Person", "name": "Bob"}
            ]
        }
        </script>
        </head>
        </html>
        '''
        result = extractor.extract(html)

        assert result is not None
        assert len(result["author"]) == 2
        assert result["author"][0]["name"] == "Alice"
        assert result["author"][1]["name"] == "Bob"

    def test_author_as_string(self, extractor):
        html = '''
        <html>
        <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Simple author",
            "author": "Jane Smith"
        }
        </script>
        </head>
        </html>
        '''
        result = extractor.extract(html)

        assert result is not None
        assert result["author"][0]["name"] == "Jane Smith"

    def test_graph_structure(self, extractor):
        html = '''
        <html>
        <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "Organization", "name": "Publisher"},
                {"@type": "NewsArticle", "headline": "Article in Graph"}
            ]
        }
        </script>
        </head>
        </html>
        '''
        result = extractor.extract(html)

        assert result is not None
        assert result["headline"] == "Article in Graph"

    def test_image_object(self, extractor):
        html = '''
        <html>
        <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "With image object",
            "image": {
                "@type": "ImageObject",
                "url": "https://example.com/image.jpg",
                "width": 1200,
                "height": 630
            }
        }
        </script>
        </head>
        </html>
        '''
        result = extractor.extract(html)

        assert result is not None
        assert result["image"]["url"] == "https://example.com/image.jpg"
        assert result["image"]["width"] == 1200
        assert result["image"]["height"] == 630

    def test_image_array(self, extractor):
        html = '''
        <html>
        <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "With image array",
            "image": [
                "https://example.com/image1.jpg",
                "https://example.com/image2.jpg"
            ]
        }
        </script>
        </head>
        </html>
        '''
        result = extractor.extract(html)

        assert result is not None
        assert result["image"]["url"] == "https://example.com/image1.jpg"

    def test_keywords_as_list(self, extractor):
        html = '''
        <html>
        <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Keywords as list",
            "keywords": ["tech", "news", "innovation"]
        }
        </script>
        </head>
        </html>
        '''
        result = extractor.extract(html)

        assert result is not None
        assert len(result["keywords"]) == 3

    def test_blog_posting_type(self, extractor):
        html = '''
        <html>
        <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": "My Blog Post"
        }
        </script>
        </head>
        </html>
        '''
        result = extractor.extract(html)

        assert result is not None
        assert result["schema_type"] == "BlogPosting"
        assert result["headline"] == "My Blog Post"

    def test_has_article_jsonld(self, extractor, sample_article_jsonld):
        assert extractor.has_article_jsonld(sample_article_jsonld) is True

        no_article = "<html><body>No JSON-LD</body></html>"
        assert extractor.has_article_jsonld(no_article) is False

    def test_extract_all(self, extractor):
        html = '''
        <html>
        <head>
        <script type="application/ld+json">
        {"@type": "Organization", "name": "Org1"}
        </script>
        <script type="application/ld+json">
        {"@type": "Article", "headline": "Article"}
        </script>
        </head>
        </html>
        '''
        results = extractor.extract_all(html)

        assert len(results) == 2

    def test_accessible_for_free(self, extractor):
        html = '''
        <html>
        <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": "Paywalled Article",
            "isAccessibleForFree": false
        }
        </script>
        </head>
        </html>
        '''
        result = extractor.extract(html)

        assert result is not None
        assert result["is_accessible_for_free"] is False

    def test_singleton_instance(self):
        e1 = get_jsonld_extractor()
        e2 = get_jsonld_extractor()
        assert e1 is e2

    def test_multiple_types(self, extractor):
        """Test handling of multiple @type values"""
        html = '''
        <html>
        <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": ["NewsArticle", "Article"],
            "headline": "Multi-type Article"
        }
        </script>
        </head>
        </html>
        '''
        result = extractor.extract(html)

        assert result is not None
        assert result["headline"] == "Multi-type Article"
