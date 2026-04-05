"""Tests for link extraction from HTML pages."""
import pytest
from app.services.link_extractor import ExtractedLink, extract_links

SAMPLE_HTML = """
<html>
<head><title>Test Page</title></head>
<body>
  <nav><a href="/home">Home</a><a href="/about">About</a></nav>
  <main>
    <article>
      <p>Interesting article about <a href="/science/quantum">quantum computing</a> and its applications.</p>
      <p>Read more on <a href="https://external.com/paper.pdf">this paper</a> by researchers.</p>
      <p>See also <a href="/science/ai">artificial intelligence</a> breakthroughs.</p>
    </article>
    <aside>
      <a href="/ads/buy-now">Buy Now!</a>
    </aside>
  </main>
  <footer><a href="/privacy">Privacy</a><a href="/imprint">Imprint</a></footer>
</body>
</html>
"""

def test_extract_links_returns_list():
    links = extract_links(SAMPLE_HTML, "https://example.com")
    assert isinstance(links, list)
    assert all(isinstance(l, ExtractedLink) for l in links)

def test_extract_links_resolves_relative_urls():
    links = extract_links(SAMPLE_HTML, "https://example.com")
    urls = [l.url for l in links]
    assert "https://example.com/science/quantum" in urls
    assert "https://external.com/paper.pdf" in urls

def test_extract_links_classifies_position():
    links = extract_links(SAMPLE_HTML, "https://example.com")
    nav_links = [l for l in links if l.position == "navigation"]
    main_links = [l for l in links if l.position == "main_content"]
    footer_links = [l for l in links if l.position == "footer"]
    assert len(nav_links) >= 2
    assert len(main_links) >= 2
    assert len(footer_links) >= 1

def test_extract_links_provides_anchor_text():
    links = extract_links(SAMPLE_HTML, "https://example.com")
    quantum_link = next(l for l in links if "quantum" in l.url)
    assert quantum_link.anchor_text == "quantum computing"

def test_extract_links_provides_context():
    links = extract_links(SAMPLE_HTML, "https://example.com")
    quantum_link = next(l for l in links if "quantum" in l.url)
    assert "Interesting article" in quantum_link.context

def test_extract_links_marks_internal_external():
    links = extract_links(SAMPLE_HTML, "https://example.com")
    quantum_link = next(l for l in links if "quantum" in l.url)
    external_link = next(l for l in links if "external.com" in l.url)
    assert quantum_link.is_internal is True
    assert external_link.is_internal is False

def test_extract_links_marks_documents():
    links = extract_links(SAMPLE_HTML, "https://example.com")
    pdf_link = next((l for l in links if "paper.pdf" in l.url), None)
    assert pdf_link is not None
    assert pdf_link.is_document is True

def test_extract_links_handles_empty_html():
    links = extract_links("", "https://example.com")
    assert links == []

def test_extract_links_handles_no_links():
    links = extract_links("<html><body><p>No links</p></body></html>", "https://example.com")
    assert links == []

def test_extract_links_deduplicates_urls():
    html = '<a href="/page">Link 1</a><a href="/page">Link 2</a>'
    links = extract_links(html, "https://example.com")
    urls = [l.url for l in links]
    assert urls.count("https://example.com/page") == 1

def test_extract_links_skips_javascript_mailto():
    html = '<a href="javascript:void(0)">JS</a><a href="mailto:x@y.com">Mail</a><a href="/real">Real</a>'
    links = extract_links(html, "https://example.com")
    assert len(links) == 1
    assert links[0].url == "https://example.com/real"

def test_extract_links_fallback_anchor_text():
    html = '<a href="/path/article-title"><img src="img.png"/></a>'
    links = extract_links(html, "https://example.com")
    assert links[0].anchor_text == "article-title"
