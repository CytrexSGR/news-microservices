"""
Quality Comparison Test: Current vs Hybrid Approach
Tests with REAL LLM API calls to compare quality metrics
"""

import asyncio
import os
import json
from typing import Dict, List, Any
from dataclasses import dataclass
from openai import OpenAI

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"

# Initialize OpenAI client (v1.0+ API)
client = OpenAI(api_key=OPENAI_API_KEY)


@dataclass
class Article:
    """Article data from database"""
    id: str
    title: str
    content: str
    url: str
    length_category: str


@dataclass
class SpecialistResult:
    """Results from a single specialist"""
    specialist: str
    findings: Dict[str, Any]
    tokens_used: int
    cost_usd: float


@dataclass
class ComparisonResult:
    """Quality comparison between approaches"""
    article_id: str
    article_title: str
    article_length: int

    # Current approach
    current_tokens: int
    current_cost: float
    current_results: Dict[str, Any]

    # Hybrid approach
    hybrid_tokens: int
    hybrid_cost: float
    hybrid_results: Dict[str, Any]

    # Quality metrics
    financial_symbols_match: float
    entity_overlap: float
    sentiment_consistency: float
    topic_agreement: float
    overall_quality_score: float

    # Token savings
    token_savings: int
    token_savings_percent: float
    cost_savings: float
    cost_savings_percent: float


def estimate_tokens(text: str) -> int:
    """Estimate tokens (rough approximation: 1 token ≈ 4 chars)"""
    return len(text) // 4


def get_test_articles() -> List[Article]:
    """Get predefined test articles with various characteristics"""
    return [
        Article(
            id="test_1",
            title="Tesla Stock Plunges After Disappointing Q3 Earnings Report",
            content="""Tesla Inc. (TSLA) shares fell sharply in after-hours trading following the company's third-quarter earnings report, which missed analyst expectations on both revenue and profit margins. The electric vehicle manufacturer reported revenue of $23.4 billion, below the consensus estimate of $24.1 billion. CEO Elon Musk acknowledged production challenges at the company's new Berlin and Texas facilities, citing supply chain disruptions and workforce shortages. The company's automotive gross margin contracted to 25.1% from 27.9% in the previous quarter, raising concerns about pricing pressure and increasing competition from traditional automakers entering the EV market. Analysts at Morgan Stanley downgraded the stock to "Equal Weight" from "Overweight," noting that the company faces headwinds from both macroeconomic conditions and industry-specific challenges. Tesla's stock price dropped 7.3% to $242.15 in extended trading.""",
            url="https://example.com/tesla-earnings",
            length_category="medium"
        ),
        Article(
            id="test_2",
            title="Fed Chair Powell Signals Potential Rate Hikes Amid Persistent Inflation",
            content="""Federal Reserve Chairman Jerome Powell indicated that the central bank may need to raise interest rates more than previously anticipated to combat stubbornly high inflation. Speaking at the Economic Club of New York, Powell emphasized that the Fed remains committed to bringing inflation back to its 2% target, even if it means accepting some economic pain. Recent data shows core PCE inflation running at 4.7%, well above the Fed's target. Market participants are now pricing in a 75% probability of a 50 basis point rate hike at the next FOMC meeting.""",
            url="https://example.com/fed-powell",
            length_category="short"
        ),
        Article(
            id="test_3",
            title="Ukraine Conflict Enters New Phase as Russia Mobilizes Additional Forces",
            content="""The ongoing conflict in Ukraine has intensified following Russia's announcement of partial military mobilization, calling up 300,000 additional reservists. This marks a significant escalation in the nine-month-old war. Ukrainian forces have made substantial gains in the northeast Kharkiv region, reclaiming over 6,000 square kilometers of territory previously held by Russian forces. President Volodymyr Zelenskyy called the mobilization a sign of desperation, while NATO Secretary-General Jens Stoltenberg warned of dangerous nuclear rhetoric from Moscow. The United States and European Union announced a new round of sanctions targeting Russian officials and oligarchs. Meanwhile, energy markets remain volatile, with European natural gas prices surging amid concerns about winter supplies. The UN estimates over 6 million Ukrainians have fled the country, creating Europe's largest refugee crisis since World War II. International humanitarian organizations are struggling to provide aid in contested regions. China has maintained its neutral stance while calling for diplomatic resolution.""",
            url="https://example.com/ukraine-conflict",
            length_category="medium"
        ),
        Article(
            id="test_4",
            title="Apple Unveils iPhone 15 with USB-C Port and Enhanced Camera System",
            content="""Apple today announced the iPhone 15 lineup at its annual September event, featuring the long-awaited transition to USB-C charging following European Union regulations mandating universal charging standards. The new phones include improved camera capabilities with a 48-megapixel main sensor and enhanced low-light performance. The Pro models feature Apple's new A17 Pro chip built on 3nm technology.""",
            url="https://example.com/apple-iphone15",
            length_category="short"
        ),
        Article(
            id="test_5",
            title="Breakthrough in Quantum Computing: IBM Achieves Error Correction Milestone",
            content="""IBM researchers have achieved a major breakthrough in quantum computing by demonstrating error correction that actually reduces errors rather than introducing new ones—a long-standing challenge in the field. The breakthrough, published in Nature, shows that their 127-qubit quantum processor can perform calculations with error rates below the critical threshold needed for practical quantum computing applications. This represents a significant step toward building fault-tolerant quantum computers capable of solving problems beyond the reach of classical supercomputers. The team used advanced error correction codes and real-time error detection to maintain quantum coherence for unprecedented durations. Google, Intel, and other tech giants are racing to achieve similar milestones, with billions of dollars invested in quantum computing research. Potential applications include drug discovery, optimization problems in logistics, cryptography, and materials science. However, experts caution that practical, large-scale quantum computers are still years away. The breakthrough has sparked increased investment interest, with quantum computing stocks rallying on the news. IBM's CEO Arvind Krishna stated this marks the beginning of the quantum utility era, where quantum computers will start delivering real-world value to businesses and researchers. Microsoft announced plans to integrate quantum capabilities into its Azure cloud platform, while Amazon is expanding its Braket quantum computing service. The race to achieve quantum advantage continues to intensify among tech giants and startups alike.""",
            url="https://example.com/ibm-quantum",
            length_category="long"
        )
    ]


async def call_openai(prompt: str, max_tokens: int = 1000) -> Dict[str, Any]:
    """Make actual OpenAI API call (v1.0+ API)"""
    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a specialized news analysis expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.1
        )

        usage = response.usage
        content = response.choices[0].message.content

        return {
            "content": content,
            "tokens_input": usage.prompt_tokens,
            "tokens_output": usage.completion_tokens,
            "tokens_total": usage.total_tokens,
            "cost_usd": (usage.prompt_tokens * 0.00015 + usage.completion_tokens * 0.0006) / 1000
        }
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return {
            "content": "{}",
            "tokens_input": 0,
            "tokens_output": 0,
            "tokens_total": 0,
            "cost_usd": 0.0
        }


# =============================================================================
# CURRENT APPROACH: 6 Separate Specialist Calls
# =============================================================================

async def current_financial_analyst(article: Article) -> SpecialistResult:
    """Financial Analyst - Current approach (separate call with content)"""
    prompt = f"""Analyze this article for financial metrics:

Title: {article.title}
Content: {article.content}

Extract:
1. Financial symbols mentioned (e.g., AAPL, TSLA, BTC-USD)
2. Market impact (bullish/bearish/neutral)
3. Key financial metrics mentioned

Return JSON: {{"symbols": [], "market_impact": "", "metrics": []}}"""

    response = await call_openai(prompt, max_tokens=500)

    try:
        findings = json.loads(response['content'])
    except:
        findings = {"symbols": [], "market_impact": "neutral", "metrics": []}

    return SpecialistResult(
        specialist="financial_analyst",
        findings=findings,
        tokens_used=response['tokens_total'],
        cost_usd=response['cost_usd']
    )


async def current_sentiment_analyzer(article: Article) -> SpecialistResult:
    """Sentiment Analyzer - Current approach"""
    prompt = f"""Analyze sentiment of this article:

Title: {article.title}
Content: {article.content}

Return JSON: {{"overall_sentiment": "positive|negative|neutral", "confidence": 0.0-1.0, "emotional_tone": ""}}"""

    response = await call_openai(prompt, max_tokens=300)

    try:
        findings = json.loads(response['content'])
    except:
        findings = {"overall_sentiment": "neutral", "confidence": 0.5, "emotional_tone": "neutral"}

    return SpecialistResult(
        specialist="sentiment_analyzer",
        findings=findings,
        tokens_used=response['tokens_total'],
        cost_usd=response['cost_usd']
    )


async def current_entity_extractor(article: Article) -> SpecialistResult:
    """Entity Extractor - Current approach"""
    prompt = f"""Extract entities from this article:

Title: {article.title}
Content: {article.content}

Return JSON: {{"persons": [], "organizations": [], "locations": [], "events": []}}"""

    response = await call_openai(prompt, max_tokens=500)

    try:
        findings = json.loads(response['content'])
    except:
        findings = {"persons": [], "organizations": [], "locations": [], "events": []}

    return SpecialistResult(
        specialist="entity_extractor",
        findings=findings,
        tokens_used=response['tokens_total'],
        cost_usd=response['cost_usd']
    )


async def current_topic_classifier(article: Article) -> SpecialistResult:
    """Topic Classifier - Current approach"""
    prompt = f"""Classify topics in this article:

Title: {article.title}
Content: {article.content}

Return JSON: {{"primary_topic": "", "secondary_topics": [], "categories": []}}"""

    response = await call_openai(prompt, max_tokens=300)

    try:
        findings = json.loads(response['content'])
    except:
        findings = {"primary_topic": "general", "secondary_topics": [], "categories": []}

    return SpecialistResult(
        specialist="topic_classifier",
        findings=findings,
        tokens_used=response['tokens_total'],
        cost_usd=response['cost_usd']
    )


async def current_approach(article: Article) -> Dict[str, Any]:
    """Execute current approach: 6 separate specialist calls"""
    print(f"  📞 Current Approach: Making 6 separate API calls...")

    # Run all specialists in parallel (as current system does)
    results = await asyncio.gather(
        current_financial_analyst(article),
        current_sentiment_analyzer(article),
        current_entity_extractor(article),
        current_topic_classifier(article),
    )

    total_tokens = sum(r.tokens_used for r in results)
    total_cost = sum(r.cost_usd for r in results)

    aggregated = {
        "specialists": {r.specialist: r.findings for r in results},
        "total_tokens": total_tokens,
        "total_cost": total_cost
    }

    print(f"  ✅ Current: {total_tokens} tokens, ${total_cost:.6f}")

    return aggregated


# =============================================================================
# HYBRID APPROACH: 1 Combined Call
# =============================================================================

async def hybrid_approach(article: Article) -> Dict[str, Any]:
    """Execute hybrid approach: 1 combined specialist call"""
    print(f"  🔄 Hybrid Approach: Making 1 combined API call...")

    combined_prompt = f"""You are a multi-specialist news analysis system. Analyze this article from 4 specialist perspectives:

Title: {article.title}
Content: {article.content}

Provide analysis from these specialists:

1. FINANCIAL_ANALYST: Extract financial symbols (e.g., AAPL, TSLA), market impact (bullish/bearish/neutral), key metrics
2. SENTIMENT_ANALYZER: Overall sentiment (positive/negative/neutral), confidence (0-1), emotional tone
3. ENTITY_EXTRACTOR: Extract persons, organizations, locations, events
4. TOPIC_CLASSIFIER: Primary topic, secondary topics, categories

Return VALID JSON in this exact format:
{{
  "financial_analyst": {{
    "symbols": [],
    "market_impact": "",
    "metrics": []
  }},
  "sentiment_analyzer": {{
    "overall_sentiment": "",
    "confidence": 0.0,
    "emotional_tone": ""
  }},
  "entity_extractor": {{
    "persons": [],
    "organizations": [],
    "locations": [],
    "events": []
  }},
  "topic_classifier": {{
    "primary_topic": "",
    "secondary_topics": [],
    "categories": []
  }}
}}"""

    response = await call_openai(combined_prompt, max_tokens=1500)

    try:
        findings = json.loads(response['content'])
    except:
        findings = {
            "financial_analyst": {"symbols": [], "market_impact": "neutral", "metrics": []},
            "sentiment_analyzer": {"overall_sentiment": "neutral", "confidence": 0.5, "emotional_tone": "neutral"},
            "entity_extractor": {"persons": [], "organizations": [], "locations": [], "events": []},
            "topic_classifier": {"primary_topic": "general", "secondary_topics": [], "categories": []}
        }

    print(f"  ✅ Hybrid: {response['tokens_total']} tokens, ${response['cost_usd']:.6f}")

    return {
        "specialists": findings,
        "total_tokens": response['tokens_total'],
        "total_cost": response['cost_usd']
    }


# =============================================================================
# QUALITY METRICS
# =============================================================================

def calculate_financial_match(current: Dict, hybrid: Dict) -> float:
    """Calculate overlap of financial symbols"""
    current_symbols = set(current.get("specialists", {}).get("financial_analyst", {}).get("symbols", []))
    hybrid_symbols = set(hybrid.get("specialists", {}).get("financial_analyst", {}).get("symbols", []))

    if not current_symbols and not hybrid_symbols:
        return 1.0  # Both found nothing = perfect match

    if not current_symbols or not hybrid_symbols:
        return 0.0  # One found something, other didn't

    intersection = len(current_symbols & hybrid_symbols)
    union = len(current_symbols | hybrid_symbols)

    return intersection / union if union > 0 else 0.0


def calculate_entity_overlap(current: Dict, hybrid: Dict) -> float:
    """Calculate entity extraction overlap"""
    current_entities = current.get("specialists", {}).get("entity_extractor", {})
    hybrid_entities = hybrid.get("specialists", {}).get("entity_extractor", {})

    overlaps = []
    for entity_type in ["persons", "organizations", "locations", "events"]:
        current_set = set(current_entities.get(entity_type, []))
        hybrid_set = set(hybrid_entities.get(entity_type, []))

        if not current_set and not hybrid_set:
            overlaps.append(1.0)
        elif not current_set or not hybrid_set:
            overlaps.append(0.0)
        else:
            intersection = len(current_set & hybrid_set)
            union = len(current_set | hybrid_set)
            overlaps.append(intersection / union if union > 0 else 0.0)

    return sum(overlaps) / len(overlaps)


def calculate_sentiment_consistency(current: Dict, hybrid: Dict) -> float:
    """Check if sentiment analysis is consistent"""
    current_sentiment = current.get("specialists", {}).get("sentiment_analyzer", {}).get("overall_sentiment", "")
    hybrid_sentiment = hybrid.get("specialists", {}).get("sentiment_analyzer", {}).get("overall_sentiment", "")

    return 1.0 if current_sentiment == hybrid_sentiment else 0.0


def calculate_topic_agreement(current: Dict, hybrid: Dict) -> float:
    """Check topic classification agreement"""
    current_topic = current.get("specialists", {}).get("topic_classifier", {}).get("primary_topic", "")
    hybrid_topic = hybrid.get("specialists", {}).get("topic_classifier", {}).get("primary_topic", "")

    return 1.0 if current_topic == hybrid_topic else 0.5  # Partial credit if different


def compare_quality(article: Article, current: Dict, hybrid: Dict) -> ComparisonResult:
    """Compare quality metrics between approaches"""

    # Calculate quality metrics
    financial_match = calculate_financial_match(current, hybrid)
    entity_overlap = calculate_entity_overlap(current, hybrid)
    sentiment_consistency = calculate_sentiment_consistency(current, hybrid)
    topic_agreement = calculate_topic_agreement(current, hybrid)

    overall_quality = (financial_match + entity_overlap + sentiment_consistency + topic_agreement) / 4.0

    # Calculate token/cost savings
    token_savings = current['total_tokens'] - hybrid['total_tokens']
    token_savings_percent = (token_savings / current['total_tokens']) * 100 if current['total_tokens'] > 0 else 0

    cost_savings = current['total_cost'] - hybrid['total_cost']
    cost_savings_percent = (cost_savings / current['total_cost']) * 100 if current['total_cost'] > 0 else 0

    return ComparisonResult(
        article_id=article.id,
        article_title=article.title,
        article_length=len(article.content),

        current_tokens=current['total_tokens'],
        current_cost=current['total_cost'],
        current_results=current['specialists'],

        hybrid_tokens=hybrid['total_tokens'],
        hybrid_cost=hybrid['total_cost'],
        hybrid_results=hybrid['specialists'],

        financial_symbols_match=financial_match,
        entity_overlap=entity_overlap,
        sentiment_consistency=sentiment_consistency,
        topic_agreement=topic_agreement,
        overall_quality_score=overall_quality,

        token_savings=token_savings,
        token_savings_percent=token_savings_percent,
        cost_savings=cost_savings,
        cost_savings_percent=cost_savings_percent
    )


# =============================================================================
# MAIN TEST
# =============================================================================

async def run_quality_test():
    """Run quality comparison test with real LLM calls"""
    print("="*100)
    print("QUALITY COMPARISON TEST: Current vs Hybrid Approach")
    print("="*100)
    print()

    # Get predefined test articles
    print("📚 Loading test articles...")
    articles = get_test_articles()
    print(f"✅ Loaded {len(articles)} articles")
    print()

    # Test each article
    results: List[ComparisonResult] = []

    for i, article in enumerate(articles, 1):
        print(f"{'='*100}")
        print(f"📄 ARTICLE {i}/{len(articles)}: {article.title[:80]}...")
        print(f"   Length: {len(article.content)} chars ({article.length_category})")
        print()

        # Run current approach
        current_result = await current_approach(article)

        # Run hybrid approach
        hybrid_result = await hybrid_approach(article)

        # Compare quality
        comparison = compare_quality(article, current_result, hybrid_result)
        results.append(comparison)

        print()
        print(f"  📊 QUALITY METRICS:")
        print(f"     Financial Symbols Match: {comparison.financial_symbols_match*100:.1f}%")
        print(f"     Entity Overlap:          {comparison.entity_overlap*100:.1f}%")
        print(f"     Sentiment Consistency:   {comparison.sentiment_consistency*100:.1f}%")
        print(f"     Topic Agreement:         {comparison.topic_agreement*100:.1f}%")
        print(f"     ⭐ OVERALL QUALITY:      {comparison.overall_quality_score*100:.1f}%")
        print()
        print(f"  💰 SAVINGS:")
        print(f"     Token Savings:  {comparison.token_savings} ({comparison.token_savings_percent:.1f}%)")
        print(f"     Cost Savings:   ${comparison.cost_savings:.6f} ({comparison.cost_savings_percent:.1f}%)")
        print()

    # Overall summary
    print("="*100)
    print("📊 OVERALL SUMMARY")
    print("="*100)
    print()

    avg_quality = sum(r.overall_quality_score for r in results) / len(results)
    avg_token_savings = sum(r.token_savings_percent for r in results) / len(results)
    avg_cost_savings = sum(r.cost_savings_percent for r in results) / len(results)

    total_current_tokens = sum(r.current_tokens for r in results)
    total_hybrid_tokens = sum(r.hybrid_tokens for r in results)
    total_current_cost = sum(r.current_cost for r in results)
    total_hybrid_cost = sum(r.hybrid_cost for r in results)

    print(f"✅ Average Quality Score:        {avg_quality*100:.1f}%")
    print(f"💰 Average Token Savings:        {avg_token_savings:.1f}%")
    print(f"💰 Average Cost Savings:         {avg_cost_savings:.1f}%")
    print()
    print(f"📊 Total Tokens:")
    print(f"   Current Approach: {total_current_tokens} tokens")
    print(f"   Hybrid Approach:  {total_hybrid_tokens} tokens")
    print(f"   Savings:          {total_current_tokens - total_hybrid_tokens} tokens ({((total_current_tokens - total_hybrid_tokens) / total_current_tokens * 100):.1f}%)")
    print()
    print(f"💵 Total Cost:")
    print(f"   Current Approach: ${total_current_cost:.6f}")
    print(f"   Hybrid Approach:  ${total_hybrid_cost:.6f}")
    print(f"   Savings:          ${total_current_cost - total_hybrid_cost:.6f} ({((total_current_cost - total_hybrid_cost) / total_current_cost * 100):.1f}%)")
    print()

    # Quality verdict
    print("="*100)
    print("🎯 VERDICT")
    print("="*100)

    if avg_quality >= 0.9:
        print("✅ EXCELLENT: Hybrid approach maintains >90% quality while reducing costs!")
        print("   Recommendation: PROCEED with implementation")
    elif avg_quality >= 0.75:
        print("✅ GOOD: Hybrid approach maintains >75% quality with significant cost savings")
        print("   Recommendation: PROCEED with careful monitoring")
    elif avg_quality >= 0.6:
        print("⚠️  ACCEPTABLE: Some quality loss but cost savings may justify")
        print("   Recommendation: Further optimization needed before production")
    else:
        print("❌ INSUFFICIENT: Quality loss too significant")
        print("   Recommendation: DO NOT implement without major improvements")

    print()
    print("="*100)


if __name__ == "__main__":
    asyncio.run(run_quality_test())
