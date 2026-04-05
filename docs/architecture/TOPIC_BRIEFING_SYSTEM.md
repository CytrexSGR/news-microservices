# Topic Briefing System - Generische Architektur

> **Erstellt:** 2025-12-24
> **Ziel:** Automatische Content-Generierung für beliebige Themen-Kategorien
> **Use Cases:** Twitter Threads, Newsletter, Briefings, Alerts

---

## 1. Vorhandene Infrastruktur

### 1.1 Kategorie-System (bereits implementiert)

```python
# services/intelligence-service/app/services/category_mapper.py

DASHBOARD_CATEGORIES = {
    "geo": "Geopolitics",           # Konflikte, Politik, Diplomatie
    "finance": "Finance",           # Märkte, Wirtschaft, Business
    "tech": "Technology",           # Tech, Science, Innovation
    "security": "Security",         # Cyber, Humanitarian, Health
}

V3_TO_DASHBOARD = {
    "GEOPOLITICS_SECURITY": "geo",
    "POLITICS_SOCIETY": "geo",
    "CONFLICT": "geo",
    "ECONOMY_MARKETS": "finance",
    "FINANCE": "finance",
    "TECHNOLOGY_SCIENCE": "tech",
    "TECHNOLOGY": "tech",
    "SECURITY": "security",
    "HUMANITARIAN": "security",
    "HEALTH": "security",
}
```

### 1.2 Datenfluss (existiert)

```
┌─────────────┐    ┌──────────────────┐    ┌───────────────────┐
│ RSS/Scraping│───>│ Content-Analysis │───>│  Intelligence     │
│             │    │    V3 Service    │    │    Service        │
└─────────────┘    └──────────────────┘    └───────────────────┘
                          │                        │
                   tier0.category           clusters + events
                          │                        │
                          ▼                        ▼
                   ┌──────────────────────────────────┐
                   │      CategoryMapper              │
                   │  (V3 → Dashboard Kategorien)     │
                   └──────────────────────────────────┘
```

### 1.3 Problem: Kategorien nicht durchgängig

```bash
# Subcategories Endpoint zeigt:
{
  "geo": [{"name": "ukraine", "risk_score": 100.0}],
  "finance": [],   # LEER
  "tech": []       # LEER
}
```

---

## 2. Generisches Topic Briefing System

### 2.1 Architektur-Überblick

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TOPIC BRIEFING SYSTEM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         TOPIC REGISTRY                                 │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │ │
│  │  │   GEO    │ │ FINANCE  │ │   TECH   │ │ SECURITY │ │  CUSTOM  │     │ │
│  │  │Geopoliti-│ │ Markets  │ │AI, Crypto│ │ Cyber,   │ │ User-    │     │ │
│  │  │cal News  │ │ Economy  │ │ Science  │ │ Health   │ │ defined  │     │ │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘     │ │
│  └───────┼────────────┼────────────┼────────────┼────────────┼───────────┘ │
│          │            │            │            │            │             │
│          ▼            ▼            ▼            ▼            ▼             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      TOPIC FILTER ENGINE                               │ │
│  │                                                                        │ │
│  │   1. Category Match (DB category field)                                │ │
│  │   2. Keyword Match (fallback if category null)                         │ │
│  │   3. Entity Match (locations, organizations)                           │ │
│  │   4. Sentiment Filter (optional)                                       │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      CONTENT GENERATOR                                 │ │
│  │                                                                        │ │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│  │   │  Twitter    │  │ Newsletter  │  │  Executive  │  │   Alert     │  │ │
│  │   │  Thread     │  │  Digest     │  │  Briefing   │  │  Telegram   │  │ │
│  │   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      OUTPUT CHANNELS                                   │ │
│  │                                                                        │ │
│  │   Twitter/X │ Email │ Telegram │ Slack │ Webhook │ RSS │ API          │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Topic Registry (Konfiguration)

```python
# services/briefing-service/app/topics/registry.py

from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class TopicDefinition:
    """Definition eines Briefing-Topics"""
    id: str
    name: str
    display_name: str
    description: str

    # Filter-Kriterien
    categories: List[str]           # ["geo", "security"]
    keywords: List[str]             # Fallback wenn category null
    entity_types: List[str]         # ["LOCATION", "ORGANIZATION"]
    entity_patterns: List[str]      # ["NATO", "UN", "EU"]

    # Sentiment-Filter (optional)
    min_sentiment: Optional[float]  # -1.0 bis 1.0
    max_sentiment: Optional[float]

    # Ranking
    priority_keywords: List[str]    # Boost für diese Keywords
    risk_weight: float              # 0.0 - 1.0

    # Output-Konfiguration
    default_format: str             # "twitter", "newsletter", "briefing"
    max_items: int                  # Max Anzahl Events
    language: str                   # "en", "de"


# Vordefinierte Topics
TOPIC_REGISTRY: Dict[str, TopicDefinition] = {

    "geopolitical": TopicDefinition(
        id="geopolitical",
        name="Geopolitical",
        display_name="🌍 Geopolitical Briefing",
        description="Wars, conflicts, diplomacy, international relations",
        categories=["geo"],
        keywords=[
            "war", "conflict", "military", "troops", "sanctions",
            "NATO", "UN", "treaty", "diplomacy", "ambassador",
            "nuclear", "missile", "invasion", "ceasefire"
        ],
        entity_types=["LOCATION", "ORGANIZATION", "PERSON"],
        entity_patterns=[
            "Syria", "Ukraine", "Russia", "China", "Taiwan", "Iran",
            "Israel", "Palestine", "North Korea", "Myanmar", "Afghanistan",
            "NATO", "United Nations", "European Union"
        ],
        min_sentiment=None,
        max_sentiment=None,
        priority_keywords=["breaking", "urgent", "killed", "attack"],
        risk_weight=0.8,
        default_format="twitter",
        max_items=10,
        language="en"
    ),

    "finance": TopicDefinition(
        id="finance",
        name="Finance",
        display_name="💰 Finance & Markets",
        description="Stock markets, crypto, economy, central banks",
        categories=["finance"],
        keywords=[
            "stock", "market", "crypto", "bitcoin", "ethereum",
            "fed", "interest rate", "inflation", "gdp", "recession",
            "earnings", "ipo", "merger", "acquisition", "dividend"
        ],
        entity_types=["ORGANIZATION", "MONEY"],
        entity_patterns=[
            "Federal Reserve", "ECB", "SEC", "NYSE", "NASDAQ",
            "Bitcoin", "Ethereum", "S&P 500", "Dow Jones",
            "Goldman Sachs", "JPMorgan", "BlackRock"
        ],
        min_sentiment=None,
        max_sentiment=None,
        priority_keywords=["crash", "surge", "record", "plunge"],
        risk_weight=0.6,
        default_format="newsletter",
        max_items=15,
        language="en"
    ),

    "cybersecurity": TopicDefinition(
        id="cybersecurity",
        name="Cybersecurity",
        display_name="🔒 Cyber Security",
        description="Hacks, breaches, vulnerabilities, threat actors",
        categories=["security", "tech"],
        keywords=[
            "hack", "breach", "ransomware", "malware", "vulnerability",
            "CVE", "zero-day", "APT", "phishing", "data leak",
            "cyberattack", "DDoS", "encryption", "backdoor"
        ],
        entity_types=["ORGANIZATION", "TECHNOLOGY"],
        entity_patterns=[
            "APT", "Lazarus", "Cozy Bear", "Fancy Bear",
            "Microsoft", "Google", "CrowdStrike", "Mandiant",
            "CISA", "NSA", "FBI"
        ],
        min_sentiment=-1.0,
        max_sentiment=0.0,  # Meist negative News
        priority_keywords=["critical", "exploit", "compromised"],
        risk_weight=0.9,
        default_format="alert",
        max_items=5,
        language="en"
    ),

    "ai_tech": TopicDefinition(
        id="ai_tech",
        name="AI & Tech",
        display_name="🤖 AI & Technology",
        description="Artificial Intelligence, LLMs, tech innovation",
        categories=["tech"],
        keywords=[
            "AI", "artificial intelligence", "machine learning", "LLM",
            "GPT", "Claude", "OpenAI", "Anthropic", "Google DeepMind",
            "neural network", "transformer", "AGI", "robotics"
        ],
        entity_types=["ORGANIZATION", "TECHNOLOGY", "PERSON"],
        entity_patterns=[
            "OpenAI", "Anthropic", "Google", "Meta", "Microsoft",
            "Sam Altman", "Elon Musk", "Sundar Pichai",
            "ChatGPT", "Claude", "Gemini", "Llama"
        ],
        min_sentiment=None,
        max_sentiment=None,
        priority_keywords=["breakthrough", "launch", "release"],
        risk_weight=0.3,
        default_format="newsletter",
        max_items=10,
        language="en"
    ),

    "crypto": TopicDefinition(
        id="crypto",
        name="Crypto",
        display_name="₿ Crypto & Web3",
        description="Cryptocurrency, blockchain, DeFi, NFTs",
        categories=["finance", "tech"],
        keywords=[
            "bitcoin", "ethereum", "crypto", "blockchain", "defi",
            "nft", "web3", "altcoin", "stablecoin", "wallet",
            "binance", "coinbase", "sec", "regulation"
        ],
        entity_types=["ORGANIZATION", "MONEY"],
        entity_patterns=[
            "Bitcoin", "Ethereum", "Binance", "Coinbase", "Tether",
            "SEC", "CFTC", "Grayscale", "MicroStrategy"
        ],
        min_sentiment=None,
        max_sentiment=None,
        priority_keywords=["crash", "pump", "dump", "halving"],
        risk_weight=0.5,
        default_format="twitter",
        max_items=10,
        language="en"
    ),

    "climate": TopicDefinition(
        id="climate",
        name="Climate",
        display_name="🌡️ Climate & Environment",
        description="Climate change, environment, sustainability",
        categories=["security"],
        keywords=[
            "climate", "global warming", "carbon", "emissions",
            "renewable", "solar", "wind", "ev", "sustainability",
            "cop", "paris agreement", "net zero"
        ],
        entity_types=["LOCATION", "ORGANIZATION"],
        entity_patterns=[
            "IPCC", "COP", "Greenpeace", "EPA", "EU Green Deal",
            "Tesla", "BP", "Shell", "ExxonMobil"
        ],
        min_sentiment=None,
        max_sentiment=None,
        priority_keywords=["record", "disaster", "flooding", "wildfire"],
        risk_weight=0.4,
        default_format="briefing",
        max_items=8,
        language="en"
    ),
}
```

### 2.3 Topic Filter Engine

```python
# services/briefing-service/app/engine/topic_filter.py

from typing import List, Dict, Any
import re

class TopicFilterEngine:
    """
    Filtert Clusters/Events basierend auf Topic-Definition
    """

    def __init__(self, topic: TopicDefinition):
        self.topic = topic
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        self.keyword_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(kw) for kw in self.topic.keywords) + r')\b',
            re.IGNORECASE
        )
        self.entity_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(e) for e in self.topic.entity_patterns) + r')\b',
            re.IGNORECASE
        )

    def matches_cluster(self, cluster: Dict[str, Any]) -> tuple[bool, float]:
        """
        Check if cluster matches topic

        Returns:
            (matches: bool, score: float)
        """
        score = 0.0

        # 1. Category match (highest priority)
        if cluster.get("category") in self.topic.categories:
            score += 0.5

        # 2. Keyword match
        name = cluster.get("name", "")
        keywords = cluster.get("keywords", [])
        text = f"{name} {' '.join(keywords)}"

        keyword_matches = self.keyword_pattern.findall(text)
        if keyword_matches:
            score += 0.3 * min(len(keyword_matches) / 3, 1.0)

        # 3. Entity match
        entity_matches = self.entity_pattern.findall(text)
        if entity_matches:
            score += 0.2 * min(len(entity_matches) / 2, 1.0)

        # 4. Priority keyword boost
        for pk in self.topic.priority_keywords:
            if pk.lower() in text.lower():
                score += 0.1

        # 5. Risk score consideration
        risk_score = cluster.get("risk_score", 0)
        score += (risk_score / 100) * self.topic.risk_weight * 0.2

        matches = score >= 0.3  # Threshold
        return matches, min(score, 1.0)

    def filter_clusters(
        self,
        clusters: List[Dict],
        limit: int = None
    ) -> List[Dict]:
        """
        Filter and rank clusters by topic relevance

        Returns:
            Sorted list of matching clusters with scores
        """
        scored_clusters = []

        for cluster in clusters:
            matches, score = self.matches_cluster(cluster)
            if matches:
                cluster["topic_score"] = score
                scored_clusters.append(cluster)

        # Sort by score descending
        scored_clusters.sort(key=lambda x: x["topic_score"], reverse=True)

        if limit:
            return scored_clusters[:limit]
        return scored_clusters
```

### 2.4 Content Generator (Multi-Format)

```python
# services/briefing-service/app/generators/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ContentGenerator(ABC):
    """Base class for content generators"""

    @abstractmethod
    async def generate(
        self,
        events: List[Dict],
        topic: TopicDefinition,
        **kwargs
    ) -> Any:
        pass


# services/briefing-service/app/generators/twitter.py

class TwitterThreadGenerator(ContentGenerator):
    """Generate Twitter threads from events"""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def generate(
        self,
        events: List[Dict],
        topic: TopicDefinition,
        max_tweets: int = 5,
        include_sources: bool = True
    ) -> Dict[str, Any]:

        # Format events for prompt
        events_text = self._format_events(events[:10])

        prompt = f"""Create a Twitter thread about {topic.display_name}.

EVENTS:
{events_text}

REQUIREMENTS:
- Maximum {max_tweets} tweets
- Each tweet max 280 characters
- Use relevant emojis
- First tweet should hook readers
- Last tweet should summarize
- Professional but engaging tone
- Language: {topic.language}

FORMAT:
Return as JSON array: ["tweet1", "tweet2", ...]
"""

        response = await self.llm.generate(prompt)
        tweets = self._parse_tweets(response)

        return {
            "tweets": tweets,
            "topic": topic.id,
            "event_count": len(events),
            "sources": [e.get("source_url") for e in events if e.get("source_url")]
        }


# services/briefing-service/app/generators/newsletter.py

class NewsletterGenerator(ContentGenerator):
    """Generate email newsletter digest"""

    async def generate(
        self,
        events: List[Dict],
        topic: TopicDefinition,
        format: str = "html"  # or "markdown"
    ) -> Dict[str, Any]:

        prompt = f"""Create a newsletter digest about {topic.display_name}.

EVENTS:
{self._format_events(events)}

STRUCTURE:
1. Executive Summary (2-3 sentences)
2. Top Stories (3-5 bullet points with headlines)
3. Key Developments (detailed paragraphs)
4. What to Watch (forward-looking)

FORMAT: {'HTML with inline styles' if format == 'html' else 'Markdown'}
LANGUAGE: {topic.language}
"""

        content = await self.llm.generate(prompt)

        return {
            "subject": f"{topic.display_name} - Daily Digest",
            "content": content,
            "format": format,
            "topic": topic.id
        }


# services/briefing-service/app/generators/briefing.py

class ExecutiveBriefingGenerator(ContentGenerator):
    """Generate executive-style briefings"""

    async def generate(
        self,
        events: List[Dict],
        topic: TopicDefinition,
        classification: str = "UNCLASSIFIED"
    ) -> Dict[str, Any]:

        prompt = f"""Create an executive intelligence briefing about {topic.display_name}.

EVENTS:
{self._format_events(events)}

FORMAT:
## EXECUTIVE BRIEFING: {topic.display_name.upper()}
**Classification:** {classification}
**Date:** [current date]
**Prepared by:** Automated Intelligence System

### SITUATION SUMMARY
[2-3 sentence overview]

### KEY DEVELOPMENTS
[Numbered list of 3-5 key points]

### RISK ASSESSMENT
[Current risk level and factors]

### RECOMMENDED ACTIONS
[2-3 actionable recommendations]

### SOURCES
[List sources]
"""

        content = await self.llm.generate(prompt)

        return {
            "title": f"Executive Briefing: {topic.name}",
            "content": content,
            "classification": classification,
            "topic": topic.id
        }
```

### 2.5 Unified Briefing API

```python
# services/briefing-service/app/api/briefings.py

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from enum import Enum

router = APIRouter(prefix="/api/v1/briefings", tags=["Briefings"])


class OutputFormat(str, Enum):
    TWITTER = "twitter"
    NEWSLETTER = "newsletter"
    BRIEFING = "briefing"
    ALERT = "alert"
    JSON = "json"


@router.get("/generate/{topic_id}")
async def generate_briefing(
    topic_id: str,
    hours: int = Query(6, ge=1, le=48),
    format: OutputFormat = Query(OutputFormat.TWITTER),
    max_items: int = Query(10, ge=1, le=50),
    language: str = Query("en"),
    include_sources: bool = Query(True)
):
    """
    Generate a briefing for a specific topic

    Args:
        topic_id: Topic identifier (geopolitical, finance, cybersecurity, etc.)
        hours: Hours to look back
        format: Output format (twitter, newsletter, briefing, alert, json)
        max_items: Maximum events to include
        language: Output language
        include_sources: Include source URLs

    Returns:
        Generated content in requested format
    """
    # 1. Get topic definition
    topic = TOPIC_REGISTRY.get(topic_id)
    if not topic:
        raise HTTPException(404, f"Topic not found: {topic_id}")

    # 2. Fetch clusters from intelligence service
    clusters = await intelligence_client.get_clusters(
        hours=hours,
        limit=50,
        sort_by="risk_score"
    )

    # 3. Filter by topic
    filter_engine = TopicFilterEngine(topic)
    matching_clusters = filter_engine.filter_clusters(clusters, limit=max_items)

    if not matching_clusters:
        return {"message": f"No {topic.name} events in last {hours} hours"}

    # 4. Get events for matching clusters
    events = []
    for cluster in matching_clusters[:5]:
        cluster_events = await intelligence_client.get_cluster_events(
            cluster["id"], limit=3
        )
        events.extend(cluster_events)

    # 5. Generate content
    generator = get_generator(format)
    result = await generator.generate(
        events=events,
        topic=topic,
        language=language,
        include_sources=include_sources
    )

    return result


@router.get("/topics")
async def list_topics():
    """List all available briefing topics"""
    return {
        "topics": [
            {
                "id": t.id,
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "default_format": t.default_format
            }
            for t in TOPIC_REGISTRY.values()
        ]
    }


@router.get("/preview/{topic_id}")
async def preview_topic(
    topic_id: str,
    hours: int = Query(6, ge=1, le=48)
):
    """
    Preview what events would be included in a briefing
    (without LLM generation - for testing/debugging)
    """
    topic = TOPIC_REGISTRY.get(topic_id)
    if not topic:
        raise HTTPException(404, f"Topic not found: {topic_id}")

    clusters = await intelligence_client.get_clusters(hours=hours, limit=50)
    filter_engine = TopicFilterEngine(topic)
    matching = filter_engine.filter_clusters(clusters, limit=10)

    return {
        "topic": topic_id,
        "hours": hours,
        "total_clusters": len(clusters),
        "matching_clusters": len(matching),
        "clusters": [
            {
                "name": c["name"],
                "score": c["topic_score"],
                "risk_score": c["risk_score"],
                "event_count": c.get("event_count", 0)
            }
            for c in matching
        ]
    }
```

---

## 3. MCP Integration

### 3.1 MCP Tools für Briefings

```python
# services/mcp-intelligence-server/app/mcp/tools.py

@tool
async def generate_topic_briefing(
    topic: str = "geopolitical",
    hours: int = 6,
    format: str = "twitter",
    language: str = "en"
) -> dict:
    """
    Generate a briefing for any supported topic.

    Args:
        topic: Topic ID (geopolitical, finance, cybersecurity, ai_tech, crypto, climate)
        hours: Hours to look back (1-48)
        format: Output format (twitter, newsletter, briefing, alert)
        language: Language code (en, de)

    Returns:
        Generated briefing content
    """
    return await briefing_client.generate(topic, hours, format, language)


@tool
async def list_briefing_topics() -> dict:
    """List all available briefing topics with descriptions."""
    return await briefing_client.list_topics()


@tool
async def preview_topic_coverage(
    topic: str,
    hours: int = 6
) -> dict:
    """
    Preview which events would be included in a topic briefing.
    Useful for understanding topic coverage without generating content.
    """
    return await briefing_client.preview(topic, hours)
```

---

## 4. n8n Workflow Integration

### 4.1 Scheduled Topic Briefings

```json
{
  "name": "Scheduled Topic Briefings",
  "nodes": [
    {
      "name": "Cron Trigger",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "cronExpression": "0 */6 * * *"
      }
    },
    {
      "name": "Generate Geo Briefing",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://briefing-service:8000/api/v1/briefings/generate/geopolitical",
        "method": "GET",
        "qs": {
          "hours": 6,
          "format": "twitter"
        }
      }
    },
    {
      "name": "Post to Twitter",
      "type": "n8n-nodes-base.twitter",
      "parameters": {
        "text": "={{$json.tweets[0]}}"
      }
    }
  ]
}
```

### 4.2 Multi-Topic Daily Digest

```
06:00 UTC → Geopolitical Briefing → Twitter
08:00 UTC → Finance Briefing → Newsletter (Email)
10:00 UTC → Cybersecurity Alert → Telegram
12:00 UTC → AI/Tech Briefing → Twitter
18:00 UTC → Daily Digest (all topics) → Newsletter
```

---

## 5. Implementierungs-Roadmap

### Phase 1: Foundation (2-3 Tage)
- [ ] Topic Registry implementieren
- [ ] Topic Filter Engine bauen
- [ ] Test mit echten Cluster-Daten

### Phase 2: Content Generation (2-3 Tage)
- [ ] LLM Integration (OpenAI)
- [ ] Twitter Generator
- [ ] Newsletter Generator

### Phase 3: API & MCP (1-2 Tage)
- [ ] FastAPI Endpoints
- [ ] MCP Tools hinzufügen
- [ ] Swagger Dokumentation

### Phase 4: Output Channels (2-3 Tage)
- [ ] Twitter API Integration
- [ ] Email (Sendgrid/SES)
- [ ] Telegram Bot
- [ ] n8n Workflows

### Phase 5: Scheduling & Monitoring (1-2 Tage)
- [ ] Scheduled Jobs (Celery)
- [ ] Metrics & Logging
- [ ] Error Handling

**Gesamt: ~10-15 Tage für vollständige Implementierung**

---

## 6. Quick Win: MCP-Only Lösung (1 Tag)

Ohne neuen Service - nur MCP Tool:

```python
# Direkt in mcp-intelligence-server

TOPIC_KEYWORDS = {
    "geopolitical": ["Syria", "Ukraine", "Russia", "China", "Taiwan", "NATO", "war", "conflict"],
    "finance": ["stock", "market", "crypto", "bitcoin", "fed", "inflation"],
    "cybersecurity": ["hack", "breach", "ransomware", "vulnerability", "CVE"],
    "ai_tech": ["AI", "OpenAI", "GPT", "Claude", "machine learning"],
}

@tool
async def quick_topic_briefing(topic: str, hours: int = 6) -> dict:
    """Quick topic briefing using keyword matching"""

    keywords = TOPIC_KEYWORDS.get(topic, [])

    # Get all clusters
    clusters = await get_clusters(hours=hours, limit=50)

    # Filter by keywords
    matching = [
        c for c in clusters
        if any(kw.lower() in c["name"].lower() for kw in keywords)
    ]

    # Get events
    events = []
    for c in matching[:5]:
        events.extend(await get_cluster_events(c["id"], limit=2))

    # Format for LLM
    return {
        "topic": topic,
        "cluster_count": len(matching),
        "events": [
            {"title": e["title"], "source": e["source"], "sentiment": e["sentiment"]}
            for e in events
        ],
        "prompt_suggestion": f"Create a {topic} Twitter thread from these events..."
    }
```

---

## Changelog

| Datum | Änderung |
|-------|----------|
| 2025-12-24 | Initial Architecture Design |
