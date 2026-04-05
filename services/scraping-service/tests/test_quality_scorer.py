"""Tests for Content Quality Scorer"""
import pytest
from app.services.quality_scorer import ContentQualityScorer, get_quality_scorer


class TestContentQualityScorer:
    @pytest.fixture
    def scorer(self):
        return ContentQualityScorer()

    @pytest.fixture
    def good_content(self):
        return """
        This is a well-written article about technology and innovation.
        It contains multiple paragraphs with varied sentence structures.

        The second paragraph continues the discussion with more details.
        We explore various aspects of the topic at hand.
        This creates a comprehensive and informative piece.

        The third paragraph wraps up the main points discussed.
        Readers should now have a good understanding of the subject.
        Thank you for reading this informative article.
        """ * 10  # Repeat to get good word count

    @pytest.fixture
    def poor_content(self):
        return "Short. Bad."

    @pytest.fixture
    def sample_html(self):
        return """
        <html>
        <body>
        <article>
            <h1>Article Title</h1>
            <p>First paragraph of the article.</p>
            <h2>Section Heading</h2>
            <p>Second paragraph with more details.</p>
            <ul>
                <li>List item one</li>
                <li>List item two</li>
            </ul>
            <blockquote>An important quote.</blockquote>
            <figure>
                <img src="image.jpg" alt="Image">
            </figure>
        </article>
        </body>
        </html>
        """

    @pytest.fixture
    def sample_metadata(self):
        return {
            "title": "Article Title",
            "extracted_author": "John Doe",
            "publish_date": "2024-01-15",
            "description": "Article description",
            "image": "https://example.com/image.jpg"
        }

    def test_score_good_content(self, scorer, good_content, sample_html, sample_metadata):
        result = scorer.score_content(
            content=good_content,
            html=sample_html,
            metadata=sample_metadata
        )

        assert result.overall_score >= 0.6
        assert result.word_count_score >= 0.5
        assert result.metadata_score >= 0.8

    def test_score_poor_content(self, scorer, poor_content):
        result = scorer.score_content(content=poor_content)

        assert result.overall_score < 0.5
        assert result.word_count_score < 0.3

    def test_score_empty_content(self, scorer):
        result = scorer.score_content(content="")

        assert result.overall_score < 0.3
        assert result.word_count_score == 0.0

    def test_score_none_content(self, scorer):
        result = scorer.score_content(content=None)

        assert result.overall_score < 0.3

    def test_score_without_html(self, scorer, good_content, sample_metadata):
        result = scorer.score_content(
            content=good_content,
            metadata=sample_metadata
        )

        # Should still produce valid score
        assert 0 <= result.overall_score <= 1
        assert result.structure_score == 0.5  # Neutral when no HTML

    def test_score_without_metadata(self, scorer, good_content, sample_html):
        result = scorer.score_content(
            content=good_content,
            html=sample_html
        )

        assert result.metadata_score == 0.0
        assert result.overall_score > 0  # Other factors contribute

    def test_word_count_scoring(self, scorer):
        # Very short content
        result_short = scorer.score_content("Hello world.")
        assert result_short.word_count_score < 0.3

        # Medium content (100-500 words)
        medium_content = "Word " * 300
        result_medium = scorer.score_content(medium_content)
        assert result_medium.word_count_score >= 0.5

        # Ideal content (500+ words)
        ideal_content = "Word " * 600
        result_ideal = scorer.score_content(ideal_content)
        assert result_ideal.word_count_score >= 0.9

    def test_metadata_scoring(self, scorer, good_content):
        # Full metadata
        full_metadata = {
            "title": "Title",
            "author": "Author",
            "publish_date": "2024-01-01",
            "description": "Description",
            "image": "image.jpg"
        }
        result_full = scorer.score_content(good_content, metadata=full_metadata)
        assert result_full.metadata_score >= 0.8

        # Partial metadata
        partial_metadata = {"title": "Title"}
        result_partial = scorer.score_content(good_content, metadata=partial_metadata)
        assert result_partial.metadata_score < 0.5

    def test_structure_scoring(self, scorer, good_content, sample_html):
        result = scorer.score_content(good_content, html=sample_html)

        assert result.structure_score >= 0.5
        assert result.details["structural_elements_found"] >= 5

    def test_structure_scoring_minimal_html(self, scorer, good_content):
        minimal_html = "<div><p>Just a paragraph.</p></div>"
        result = scorer.score_content(good_content, html=minimal_html)

        assert result.structure_score < 0.8

    def test_readability_scoring(self, scorer):
        # Well-structured content
        good = "This is a well-written sentence. It has good length. The content flows naturally.\n\nThis is a new paragraph."
        result_good = scorer.score_content(good)
        assert result_good.readability_score >= 0.4

        # Very long sentences
        long_sentence = ("This is a very long sentence that goes on and on without any breaks " * 10)
        result_long = scorer.score_content(long_sentence)
        assert result_long.readability_score < result_good.readability_score

    def test_quality_details(self, scorer, good_content, sample_html, sample_metadata):
        result = scorer.score_content(good_content, sample_html, sample_metadata)

        assert "word_count" in result.details
        assert "metadata_fields_present" in result.details
        assert "structural_elements_found" in result.details
        assert "avg_sentence_length" in result.details
        assert "paragraph_count" in result.details

        assert result.details["word_count"] > 0

    def test_get_quality_category(self, scorer):
        assert scorer.get_quality_category(0.9) == "excellent"
        assert scorer.get_quality_category(0.8) == "excellent"
        assert scorer.get_quality_category(0.7) == "good"
        assert scorer.get_quality_category(0.6) == "good"
        assert scorer.get_quality_category(0.5) == "fair"
        assert scorer.get_quality_category(0.4) == "fair"
        assert scorer.get_quality_category(0.3) == "poor"
        assert scorer.get_quality_category(0.0) == "poor"

    def test_singleton_instance(self):
        s1 = get_quality_scorer()
        s2 = get_quality_scorer()
        assert s1 is s2

    def test_score_with_variants_metadata(self, scorer, good_content):
        # Test with different metadata field name variants
        metadata = {
            "extracted_title": "Title",
            "extracted_author": "Author",
        }
        result = scorer.score_content(good_content, metadata=metadata)
        assert result.metadata_score > 0
