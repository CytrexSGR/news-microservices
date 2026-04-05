"""Extract and classify links from HTML pages."""
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.tar', '.gz', '.csv'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico'}
NAV_TAGS = {'nav', 'header'}
FOOTER_TAGS = {'footer'}
SIDEBAR_CLASSES = {'sidebar', 'aside', 'widget', 'ad', 'advertisement', 'promo'}


@dataclass
class ExtractedLink:
    url: str
    anchor_text: str
    context: str
    is_internal: bool
    position: str  # main_content, navigation, footer, sidebar
    is_document: bool = False


def _get_position(tag: Tag) -> str:
    for parent in tag.parents:
        if not isinstance(parent, Tag):
            continue
        if parent.name in NAV_TAGS:
            return "navigation"
        if parent.name in FOOTER_TAGS:
            return "footer"
        if parent.name in {'aside'}:
            return "sidebar"
        classes = set(parent.get('class', []))
        if classes & SIDEBAR_CLASSES:
            return "sidebar"
    return "main_content"


def _get_context(tag: Tag, max_words: int = 50) -> str:
    block_tags = {
        'p', 'div', 'li', 'td', 'section', 'article', 'blockquote',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    }
    parent = tag.parent
    while parent and parent.name not in block_tags:
        parent = parent.parent
    if parent is None:
        return ""
    text = parent.get_text(separator=" ", strip=True)
    words = text.split()
    return " ".join(words[:max_words])


def _is_document_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in DOCUMENT_EXTENSIONS)


def extract_links(html: str, base_url: str) -> List[ExtractedLink]:
    """Extract, classify, and deduplicate links from HTML."""
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    seen_urls: set = set()
    results: List[ExtractedLink] = []
    base_domain = urlparse(base_url).netloc

    for tag in soup.find_all("a", href=True):
        href = tag["href"]

        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        url = urljoin(base_url, href)
        path = urlparse(url).path.lower()

        if any(path.endswith(ext) for ext in IMAGE_EXTENSIONS):
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        anchor_text = tag.get_text(strip=True)
        if not anchor_text:
            anchor_text = (
                tag.get("title", "")
                or urlparse(url).path.split("/")[-1]
                or url
            )

        results.append(ExtractedLink(
            url=url,
            anchor_text=anchor_text,
            context=_get_context(tag),
            is_internal=urlparse(url).netloc == base_domain,
            position=_get_position(tag),
            is_document=_is_document_url(url),
        ))

    return results
