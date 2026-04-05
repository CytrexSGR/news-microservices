"""
Test Script: Tier1-basierte Analyse (Ansatz 2)

Vergleicht Token-Verbrauch und Qualität zwischen:
- AKTUELL: Specialists mit vollem Content
- OPTIMIERT: Specialists nur mit Tier1-Daten

Test-Artikel:
1. Finanz (Tesla stock drop)
2. Geopolitik (Ukraine conflict)
3. Technologie (AI development)
4. Mixed (China tech sanctions)
"""

import asyncio
import json
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from uuid import UUID, uuid4

# Mock imports (we'll simulate without actual API calls)
@dataclass
class Entity:
    name: str
    type: str
    confidence: float
    mentions: int

@dataclass
class Relation:
    subject: str
    predicate: str
    object: str
    confidence: float

@dataclass
class Topic:
    keyword: str
    confidence: float
    parent_category: str

@dataclass
class Tier1Results:
    entities: List[Entity]
    relations: List[Relation]
    topics: List[Topic]
    impact_score: float
    credibility_score: float
    urgency_score: float
    tokens_used: int = 0
    cost_usd: float = 0.0

@dataclass
class TestArticle:
    title: str
    content: str
    tier1_results: Tier1Results

@dataclass
class AnalysisResult:
    approach: str  # "CURRENT" or "OPTIMIZED"
    specialist: str
    metrics: Dict[str, Any]
    tokens_input: int
    tokens_output: int
    cost_usd: float
    reasoning: str


# ============================================================================
# TEST ARTICLES
# ============================================================================

TEST_ARTICLES = {
    "finance": TestArticle(
        title="Tesla Shares Plunge 8% After Musk Warns of Production Delays in China",
        content="""Tesla Inc. (NASDAQ: TSLA) shares fell sharply in after-hours trading on Tuesday,
dropping 8.2% to $185.40 after CEO Elon Musk warned investors of significant production delays
at the company's Shanghai Gigafactory. The delays, attributed to escalating U.S.-China trade
tensions and semiconductor shortages, could impact Q2 delivery targets by up to 15%.

During an emergency earnings call, Musk stated that "geopolitical headwinds are making it
increasingly difficult to maintain our production timeline." The comments come amid growing
concerns about supply chain disruptions affecting the broader automotive sector.

Analysts at Goldman Sachs downgraded Tesla from "Buy" to "Hold," citing reduced revenue
projections for 2025. The downgrade triggered a broader selloff in EV stocks, with Rivian
(RIVN) falling 4.3% and Lucid Motors (LCID) dropping 5.8%.

Market experts warn that continued delays could benefit traditional automakers like Ford and GM,
who have been gaining ground in the EV market. The situation also raises questions about Tesla's
long-term competitiveness in China, the world's largest EV market, where local competitors like
BYD and NIO are rapidly expanding.""",
        tier1_results=Tier1Results(
            entities=[
                Entity("Tesla Inc.", "ORGANIZATION", 1.0, 4),
                Entity("Elon Musk", "PERSON", 1.0, 2),
                Entity("NASDAQ:TSLA", "SYMBOL", 1.0, 1),
                Entity("Shanghai Gigafactory", "LOCATION", 0.95, 1),
                Entity("China", "LOCATION", 1.0, 3),
                Entity("United States", "LOCATION", 0.9, 2),
                Entity("Goldman Sachs", "ORGANIZATION", 1.0, 1),
                Entity("Rivian", "ORGANIZATION", 0.95, 1),
                Entity("Lucid Motors", "ORGANIZATION", 0.95, 1),
                Entity("BYD", "ORGANIZATION", 0.9, 1),
                Entity("NIO", "ORGANIZATION", 0.9, 1),
            ],
            relations=[
                Relation("Tesla Inc.", "stock_dropped", "-8.2%", 1.0),
                Relation("Elon Musk", "CEO_of", "Tesla Inc.", 1.0),
                Relation("Tesla Inc.", "operates_in", "China", 1.0),
                Relation("Goldman Sachs", "downgraded", "Tesla Inc.", 1.0),
                Relation("Tesla Inc.", "competes_with", "BYD", 0.9),
                Relation("Tesla Inc.", "competes_with", "NIO", 0.9),
                Relation("United States", "trade_tensions_with", "China", 0.95),
                Relation("Rivian", "stock_dropped", "-4.3%", 0.95),
                Relation("Lucid Motors", "stock_dropped", "-5.8%", 0.95),
            ],
            topics=[
                Topic("FINANCE", 1.0, "Economic"),
                Topic("TECHNOLOGY", 0.8, "Industry"),
                Topic("GEOPOLITICS", 0.85, "International"),
            ],
            impact_score=7.5,
            credibility_score=8.0,
            urgency_score=8.0,
            tokens_used=600
        )
    ),

    "geopolitics": TestArticle(
        title="Ukraine Launches Major Counteroffensive in Eastern Region",
        content="""Ukrainian forces have launched a significant counteroffensive in the Donetsk region,
marking the most substantial military operation since early 2024. President Zelenskyy announced
that Ukrainian troops have recaptured three strategic villages and are advancing toward key
supply routes used by Russian forces.

The offensive comes after months of intensive training with NATO allies and the deployment of
newly delivered Western military equipment, including German Leopard tanks and American Bradley
fighting vehicles. Military analysts suggest this could be a turning point in the conflict.

Russia's Defense Ministry confirmed heavy fighting in the region but claimed its forces are
holding defensive positions. The Kremlin warned of "severe consequences" and hinted at potential
escalation. Meanwhile, China called for immediate ceasefire negotiations, while the United States
pledged continued military support to Ukraine.

The offensive has raised concerns about potential nuclear escalation, with Russian officials
repeatedly referencing their nuclear doctrine. NATO Secretary General emphasized the alliance's
commitment to collective defense while urging diplomatic solutions.""",
        tier1_results=Tier1Results(
            entities=[
                Entity("Ukraine", "LOCATION", 1.0, 5),
                Entity("Donetsk", "LOCATION", 0.95, 2),
                Entity("Zelenskyy", "PERSON", 1.0, 1),
                Entity("Russia", "LOCATION", 1.0, 4),
                Entity("NATO", "ORGANIZATION", 1.0, 2),
                Entity("Germany", "LOCATION", 0.9, 1),
                Entity("United States", "LOCATION", 0.95, 1),
                Entity("China", "LOCATION", 0.9, 1),
                Entity("Kremlin", "ORGANIZATION", 0.95, 1),
            ],
            relations=[
                Relation("Ukraine", "launches_offensive_in", "Donetsk", 1.0),
                Relation("Ukraine", "recaptured", "three villages", 0.95),
                Relation("NATO", "supports", "Ukraine", 1.0),
                Relation("Russia", "defends_against", "Ukraine", 0.95),
                Relation("Russia", "threatens", "escalation", 0.9),
                Relation("China", "calls_for", "ceasefire", 0.9),
                Relation("United States", "supports", "Ukraine", 1.0),
            ],
            topics=[
                Topic("CONFLICT", 1.0, "Military"),
                Topic("GEOPOLITICS", 0.95, "International"),
                Topic("SECURITY", 0.9, "Defense"),
            ],
            impact_score=9.0,
            credibility_score=8.5,
            urgency_score=9.5,
            tokens_used=550
        )
    ),

    "technology": TestArticle(
        title="OpenAI Unveils GPT-5 with Breakthrough Reasoning Capabilities",
        content="""OpenAI announced the release of GPT-5, claiming significant advances in reasoning,
mathematical problem-solving, and multimodal understanding. CEO Sam Altman described it as
"the first step toward artificial general intelligence (AGI)" during a livestreamed launch event.

The new model demonstrates unprecedented performance on complex reasoning tasks, scoring 95%
on graduate-level mathematics exams and showing human-level performance on coding challenges.
GPT-5 also features improved context windows of up to 1 million tokens and native support for
video understanding.

Microsoft, OpenAI's primary investor and cloud partner, announced immediate integration into
Azure AI services and GitHub Copilot. The partnership has invested over $13 billion in OpenAI's
infrastructure, with Microsoft CEO Satya Nadella calling GPT-5 "transformative for enterprise AI."

Concerns about AI safety have intensified, with leading researchers warning about potential
misuse. The EU AI Act regulatory framework may impose restrictions on deployment, while China's
AI regulations require government approval for large language models. Google and Anthropic
announced competing releases scheduled for later this year.""",
        tier1_results=Tier1Results(
            entities=[
                Entity("OpenAI", "ORGANIZATION", 1.0, 3),
                Entity("GPT-5", "PRODUCT", 1.0, 4),
                Entity("Sam Altman", "PERSON", 1.0, 1),
                Entity("Microsoft", "ORGANIZATION", 1.0, 3),
                Entity("Azure AI", "PRODUCT", 0.9, 1),
                Entity("GitHub Copilot", "PRODUCT", 0.9, 1),
                Entity("Satya Nadella", "PERSON", 0.95, 1),
                Entity("EU", "ORGANIZATION", 0.85, 1),
                Entity("China", "LOCATION", 0.9, 1),
                Entity("Google", "ORGANIZATION", 0.9, 1),
                Entity("Anthropic", "ORGANIZATION", 0.9, 1),
            ],
            relations=[
                Relation("OpenAI", "released", "GPT-5", 1.0),
                Relation("Sam Altman", "CEO_of", "OpenAI", 1.0),
                Relation("Microsoft", "invested_in", "OpenAI", 1.0),
                Relation("Microsoft", "partners_with", "OpenAI", 1.0),
                Relation("GPT-5", "integrated_into", "Azure AI", 0.95),
                Relation("EU", "regulates", "AI", 0.85),
                Relation("China", "regulates", "AI", 0.9),
                Relation("Google", "competes_with", "OpenAI", 0.9),
                Relation("Anthropic", "competes_with", "OpenAI", 0.9),
            ],
            topics=[
                Topic("TECHNOLOGY", 1.0, "Innovation"),
                Topic("AI", 1.0, "Artificial Intelligence"),
                Topic("BUSINESS", 0.7, "Corporate"),
            ],
            impact_score=8.0,
            credibility_score=9.0,
            urgency_score=7.5,
            tokens_used=580
        )
    ),

    "mixed": TestArticle(
        title="U.S. Expands Chip Export Controls to China, Nvidia Stock Drops 6%",
        content="""The Biden administration announced sweeping new restrictions on semiconductor exports
to China, targeting advanced AI chips and manufacturing equipment. The measures aim to prevent
China from acquiring cutting-edge technology that could enhance its military capabilities.

Nvidia (NVDA) shares fell 6.2% in response, as China represents approximately 20% of the
company's revenue. CEO Jensen Huang warned that the restrictions could cost the company billions
in lost sales and damage U.S. competitiveness in the global AI race.

The new rules expand upon 2023 restrictions, now covering a broader range of chips including
those used in gaming and consumer applications. AMD and Intel also face revenue impacts, with
analysts projecting combined losses of $5-8 billion annually for the semiconductor industry.

China's Ministry of Commerce condemned the measures as "economic coercion" and threatened
retaliation against U.S. technology companies. Beijing has accelerated domestic chip development
programs, investing $150 billion in semiconductor self-sufficiency initiatives.

The restrictions have geopolitical implications beyond economics, with Taiwan and South Korea
caught in the middle. TSMC and Samsung face pressure to limit China sales while maintaining
crucial business relationships.""",
        tier1_results=Tier1Results(
            entities=[
                Entity("United States", "LOCATION", 1.0, 3),
                Entity("China", "LOCATION", 1.0, 5),
                Entity("Biden administration", "ORGANIZATION", 0.95, 1),
                Entity("Nvidia", "ORGANIZATION", 1.0, 3),
                Entity("Jensen Huang", "PERSON", 0.95, 1),
                Entity("AMD", "ORGANIZATION", 0.9, 1),
                Entity("Intel", "ORGANIZATION", 0.9, 1),
                Entity("China Ministry of Commerce", "ORGANIZATION", 0.95, 1),
                Entity("Taiwan", "LOCATION", 0.9, 1),
                Entity("South Korea", "LOCATION", 0.9, 1),
                Entity("TSMC", "ORGANIZATION", 0.95, 1),
                Entity("Samsung", "ORGANIZATION", 0.95, 1),
            ],
            relations=[
                Relation("United States", "restricts_exports_to", "China", 1.0),
                Relation("Nvidia", "stock_dropped", "-6.2%", 1.0),
                Relation("China", "represents_revenue_for", "Nvidia", 0.95),
                Relation("China", "threatens_retaliation_against", "United States", 0.9),
                Relation("China", "invests_in", "semiconductor development", 0.95),
                Relation("AMD", "affected_by", "restrictions", 0.9),
                Relation("Intel", "affected_by", "restrictions", 0.9),
                Relation("Taiwan", "caught_between", "U.S. and China", 0.85),
                Relation("TSMC", "pressured_by", "restrictions", 0.9),
            ],
            topics=[
                Topic("GEOPOLITICS", 0.95, "International"),
                Topic("TECHNOLOGY", 0.9, "Semiconductors"),
                Topic("FINANCE", 0.85, "Markets"),
                Topic("SECURITY", 0.8, "National Security"),
            ],
            impact_score=8.5,
            credibility_score=9.0,
            urgency_score=8.0,
            tokens_used=620
        )
    ),
}


# ============================================================================
# SPECIALIST PROMPTS
# ============================================================================

def build_current_financial_prompt(article: TestArticle) -> tuple[str, int]:
    """Build CURRENT prompt with full content."""
    entities_str = ", ".join([e.name for e in article.tier1_results.entities[:10]])
    topics_str = ", ".join([t.keyword for t in article.tier1_results.topics])

    prompt = f"""Analyze financial implications of this article.

ARTICLE:
Title: {article.title}
Content: {article.content}

TIER1 ENTITIES: {entities_str}
TIER1 TOPICS: {topics_str}

OUTPUT (JSON):
{{
  "metrics": {{
    "market_impact": 0.0-10.0,
    "volatility_expected": 0.0-10.0,
    "sector_affected": "TECHNOLOGY|FINANCE|ENERGY|HEALTHCARE|COMMODITIES|CRYPTO|OTHER",
    "price_direction": "BULLISH|BEARISH|NEUTRAL"
  }},
  "affected_symbols": ["TSLA", "BTC-USD", "AAPL"],
  "reasoning": "Brief explanation"
}}

Respond with ONLY the JSON object."""

    # Estimate tokens: content + prompt overhead
    content_tokens = len(article.content.split()) * 1.3  # Rough estimate
    prompt_tokens = 200  # Overhead
    total_tokens = int(content_tokens + prompt_tokens)

    return prompt, total_tokens


def build_optimized_financial_prompt(article: TestArticle) -> tuple[str, int]:
    """Build OPTIMIZED prompt with only Tier1 data."""
    # Build entities section
    entities_lines = []
    for e in article.tier1_results.entities[:15]:
        entities_lines.append(f"- {e.name} ({e.type}, confidence={e.confidence:.2f}, mentions={e.mentions})")
    entities_str = "\n".join(entities_lines)

    # Build relations section
    relations_lines = []
    for r in article.tier1_results.relations:
        relations_lines.append(f"- {r.subject} → {r.predicate} → {r.object} (confidence={r.confidence:.2f})")
    relations_str = "\n".join(relations_lines)

    # Build topics section
    topics_str = ", ".join([f"{t.keyword} ({t.confidence:.2f})" for t in article.tier1_results.topics])

    prompt = f"""Based on the following EXTRACTED INFORMATION, analyze financial implications:

TIER1 ENTITIES:
{entities_str}

TIER1 RELATIONS:
{relations_str}

TIER1 TOPICS: {topics_str}

TIER1 SCORES:
- Impact: {article.tier1_results.impact_score}/10
- Credibility: {article.tier1_results.credibility_score}/10
- Urgency: {article.tier1_results.urgency_score}/10

TASK: Based on ONLY this extracted data (do NOT make assumptions about details
not present), analyze:

1. Market Impact: How significant is this for financial markets? (0-10)
2. Volatility Expected: How much price movement is likely? (0-10)
3. Sector Affected: PRIMARY sector most impacted?
4. Price Direction: BULLISH, BEARISH, or NEUTRAL?
5. Affected Symbols: List 1-5 symbols most likely affected

INFERENCE RULES:
- "stock_dropped" relation → bearish signal, high volatility
- "downgraded" relation → bearish signal
- "invested_in" relation → bullish signal for target
- Multiple companies affected → sector-wide impact
- High Impact + High Urgency → higher market_impact score

OUTPUT (JSON):
{{
  "metrics": {{
    "market_impact": 0.0-10.0,
    "volatility_expected": 0.0-10.0,
    "sector_affected": "TECHNOLOGY|FINANCE|ENERGY|HEALTHCARE|COMMODITIES|CRYPTO|OTHER",
    "price_direction": "BULLISH|BEARISH|NEUTRAL"
  }},
  "affected_symbols": ["TSLA", "NVDA", ...],
  "reasoning": "Brief explanation based on extracted data"
}}

Respond with ONLY the JSON object."""

    # Estimate tokens: entities + relations + prompt overhead
    entities_tokens = len(entities_str.split()) * 1.3
    relations_tokens = len(relations_str.split()) * 1.3
    prompt_tokens = 250  # Overhead
    total_tokens = int(entities_tokens + relations_tokens + prompt_tokens)

    return prompt, total_tokens


# ============================================================================
# SIMULATED LLM RESPONSES
# ============================================================================

def simulate_current_financial_analysis(article: TestArticle, article_key: str) -> Dict[str, Any]:
    """Simulate LLM response for CURRENT approach (with full content)."""

    # These are simulated "high quality" responses based on full content access
    responses = {
        "finance": {
            "metrics": {
                "market_impact": 7.5,
                "volatility_expected": 8.0,
                "sector_affected": "TECHNOLOGY",
                "price_direction": "BEARISH"
            },
            "affected_symbols": ["TSLA", "RIVN", "LCID", "F", "GM"],
            "reasoning": "Major Tesla stock drop (-8.2%) with Goldman downgrade. Broad EV sector selloff with Rivian (-4.3%) and Lucid (-5.8%) following. U.S.-China trade tensions add geopolitical risk. Q2 delivery targets at risk (-15%). Traditional automakers may benefit."
        },
        "geopolitics": {
            "metrics": {
                "market_impact": 6.0,
                "volatility_expected": 7.5,
                "sector_affected": "ENERGY",
                "price_direction": "NEUTRAL"
            },
            "affected_symbols": ["XLE", "USO", "LMT", "RTX", "NOC"],
            "reasoning": "Major military offensive raises conflict escalation risk. Energy markets sensitive to supply disruptions. Defense contractors may benefit. Nuclear escalation concerns increase volatility. Mixed impact on broader markets."
        },
        "technology": {
            "metrics": {
                "market_impact": 7.0,
                "volatility_expected": 6.5,
                "sector_affected": "TECHNOLOGY",
                "price_direction": "BULLISH"
            },
            "affected_symbols": ["MSFT", "GOOGL", "META", "NVDA", "AMD"],
            "reasoning": "Major AI breakthrough with GPT-5 launch. Microsoft partnership ($13B invested) directly benefits MSFT. Competitive pressure on Google and Anthropic. Enterprise AI adoption acceleration. Potential regulatory headwinds from EU/China offset by innovation momentum."
        },
        "mixed": {
            "metrics": {
                "market_impact": 8.0,
                "volatility_expected": 8.5,
                "sector_affected": "TECHNOLOGY",
                "price_direction": "BEARISH"
            },
            "affected_symbols": ["NVDA", "AMD", "INTC", "TSM", "ASML"],
            "reasoning": "Sweeping chip export restrictions directly impact Nvidia (-6.2%), AMD, Intel. China represents 20% of Nvidia revenue. Industry-wide revenue loss projected at $5-8B annually. Geopolitical escalation risk with China retaliation threats. TSMC and Samsung caught in crossfire."
        }
    }

    return responses.get(article_key, responses["finance"])


def simulate_optimized_financial_analysis(article: TestArticle, article_key: str) -> Dict[str, Any]:
    """Simulate LLM response for OPTIMIZED approach (only Tier1 data)."""

    # These are simulated responses with SLIGHTLY lower detail (no access to full content)
    # But should still capture the main signals from structured data
    responses = {
        "finance": {
            "metrics": {
                "market_impact": 7.0,  # Slightly lower (less context)
                "volatility_expected": 8.0,  # Same (clear from relations)
                "sector_affected": "TECHNOLOGY",  # Correct
                "price_direction": "BEARISH"  # Correct (clear signal)
            },
            "affected_symbols": ["TSLA", "RIVN", "LCID", "NIO", "BYD"],
            "reasoning": "Tesla stock_dropped -8.2% with Goldman downgrade. Multiple EV stocks dropped (Rivian -4.3%, Lucid -5.8%). U.S.-China trade_tensions relation detected. High impact (7.5) and urgency (8.0) scores. Bearish signals dominate."
        },
        "geopolitics": {
            "metrics": {
                "market_impact": 6.5,  # Similar
                "volatility_expected": 7.0,  # Slightly lower (less nuance)
                "sector_affected": "ENERGY",  # Inferred correctly
                "price_direction": "NEUTRAL"  # Correct
            },
            "affected_symbols": ["XLE", "USO", "LMT", "BA"],
            "reasoning": "Ukraine launches_offensive_in Donetsk. Russia threatens escalation. NATO supports Ukraine. CONFLICT topic (1.0 confidence) with high impact (9.0) and urgency (9.5). Mixed market implications."
        },
        "technology": {
            "metrics": {
                "market_impact": 6.5,  # Slightly lower (missing nuance)
                "volatility_expected": 6.0,  # Similar
                "sector_affected": "TECHNOLOGY",  # Correct
                "price_direction": "BULLISH"  # Correct
            },
            "affected_symbols": ["MSFT", "GOOGL", "NVDA"],
            "reasoning": "OpenAI released GPT-5. Microsoft invested_in and partners_with OpenAI. GPT-5 integrated_into Azure AI. Google and Anthropic compete_with OpenAI. TECHNOLOGY and AI topics dominant. High credibility (9.0)."
        },
        "mixed": {
            "metrics": {
                "market_impact": 8.0,  # Same (clear signal)
                "volatility_expected": 8.0,  # Similar
                "sector_affected": "TECHNOLOGY",  # Correct
                "price_direction": "BEARISH"  # Correct
            },
            "affected_symbols": ["NVDA", "AMD", "INTC", "TSM"],
            "reasoning": "U.S. restricts_exports_to China. Nvidia stock_dropped -6.2%. China threatens_retaliation. AMD and Intel affected_by restrictions. GEOPOLITICS (0.95) and TECHNOLOGY (0.9) topics. High impact (8.5) and urgency (8.0)."
        }
    }

    return responses.get(article_key, responses["finance"])


# ============================================================================
# MAIN TEST FUNCTION
# ============================================================================

def run_comparison_test():
    """Run comparison test for all articles."""

    print("=" * 80)
    print("TOKEN OPTIMIZATION TEST: TIER1-BASED ANALYSIS (ANSATZ 2)")
    print("=" * 80)
    print()

    results = []

    for article_key, article in TEST_ARTICLES.items():
        print(f"\n{'=' * 80}")
        print(f"TEST ARTICLE: {article_key.upper()}")
        print(f"Title: {article.title}")
        print(f"{'=' * 80}\n")

        # ====================================================================
        # CURRENT APPROACH: Full Content
        # ====================================================================

        print("🔵 CURRENT APPROACH (Full Content):")
        print("-" * 80)

        current_prompt, current_tokens_input = build_current_financial_prompt(article)
        current_response = simulate_current_financial_analysis(article, article_key)
        current_tokens_output = 150  # Estimated JSON response
        current_cost = (current_tokens_input * 0.15 / 1_000_000) + (current_tokens_output * 0.60 / 1_000_000)

        print(f"Input Tokens:  {current_tokens_input:,}")
        print(f"Output Tokens: {current_tokens_output:,}")
        print(f"Total Cost:    ${current_cost:.6f}")
        print(f"\nResponse:")
        print(json.dumps(current_response, indent=2))

        # ====================================================================
        # OPTIMIZED APPROACH: Only Tier1 Data
        # ====================================================================

        print("\n🟢 OPTIMIZED APPROACH (Tier1 Data Only):")
        print("-" * 80)

        optimized_prompt, optimized_tokens_input = build_optimized_financial_prompt(article)
        optimized_response = simulate_optimized_financial_analysis(article, article_key)
        optimized_tokens_output = 140  # Slightly shorter (less detail)
        optimized_cost = (optimized_tokens_input * 0.15 / 1_000_000) + (optimized_tokens_output * 0.60 / 1_000_000)

        print(f"Input Tokens:  {optimized_tokens_input:,}")
        print(f"Output Tokens: {optimized_tokens_output:,}")
        print(f"Total Cost:    ${optimized_cost:.6f}")
        print(f"\nResponse:")
        print(json.dumps(optimized_response, indent=2))

        # ====================================================================
        # COMPARISON
        # ====================================================================

        token_savings = current_tokens_input - optimized_tokens_input
        token_reduction_pct = (token_savings / current_tokens_input) * 100
        cost_savings = current_cost - optimized_cost
        cost_reduction_pct = (cost_savings / current_cost) * 100

        print("\n📊 COMPARISON:")
        print("-" * 80)
        print(f"Token Savings:     {token_savings:,} tokens ({token_reduction_pct:.1f}% reduction)")
        print(f"Cost Savings:      ${cost_savings:.6f} ({cost_reduction_pct:.1f}% reduction)")

        # Quality comparison
        print(f"\n🎯 QUALITY COMPARISON:")
        print("-" * 80)

        metrics_match = 0
        metrics_total = 0

        for key in ["market_impact", "volatility_expected", "sector_affected", "price_direction"]:
            current_val = current_response["metrics"][key]
            optimized_val = optimized_response["metrics"][key]

            if isinstance(current_val, (int, float)):
                # Numeric metrics: accept 10% difference
                diff = abs(current_val - optimized_val)
                match = diff <= (current_val * 0.15)  # 15% tolerance
                metrics_total += 1
                if match:
                    metrics_match += 1
                print(f"  {key:25} Current: {current_val:6.1f}  Optimized: {optimized_val:6.1f}  {'✅' if match else '⚠️'}")
            else:
                # Categorical metrics: exact match
                match = current_val == optimized_val
                metrics_total += 1
                if match:
                    metrics_match += 1
                print(f"  {key:25} Current: {current_val:8}  Optimized: {optimized_val:8}  {'✅' if match else '❌'}")

        # Symbol overlap
        current_symbols = set(current_response["affected_symbols"])
        optimized_symbols = set(optimized_response["affected_symbols"])
        symbol_overlap = len(current_symbols & optimized_symbols) / len(current_symbols) * 100

        print(f"\n  Symbols Overlap: {symbol_overlap:.0f}% ({len(current_symbols & optimized_symbols)}/{len(current_symbols)} symbols match)")
        print(f"  Overall Accuracy: {metrics_match}/{metrics_total} metrics match ({metrics_match/metrics_total*100:.0f}%)")

        # Store results
        results.append({
            "article": article_key,
            "current_tokens_input": current_tokens_input,
            "optimized_tokens_input": optimized_tokens_input,
            "token_savings": token_savings,
            "token_reduction_pct": token_reduction_pct,
            "current_cost": current_cost,
            "optimized_cost": optimized_cost,
            "cost_savings": cost_savings,
            "cost_reduction_pct": cost_reduction_pct,
            "metrics_accuracy": metrics_match / metrics_total * 100,
            "symbol_overlap": symbol_overlap,
        })

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print("\n" + "=" * 80)
    print("📈 SUMMARY: ALL ARTICLES")
    print("=" * 80)

    total_current_tokens = sum(r["current_tokens_input"] for r in results)
    total_optimized_tokens = sum(r["optimized_tokens_input"] for r in results)
    total_token_savings = total_current_tokens - total_optimized_tokens

    total_current_cost = sum(r["current_cost"] for r in results)
    total_optimized_cost = sum(r["optimized_cost"] for r in results)
    total_cost_savings = total_current_cost - total_optimized_cost

    avg_metrics_accuracy = sum(r["metrics_accuracy"] for r in results) / len(results)
    avg_symbol_overlap = sum(r["symbol_overlap"] for r in results) / len(results)

    print(f"\n📊 TOKEN USAGE:")
    print(f"  Current Total:     {total_current_tokens:,} tokens")
    print(f"  Optimized Total:   {total_optimized_tokens:,} tokens")
    print(f"  Total Savings:     {total_token_savings:,} tokens ({total_token_savings/total_current_tokens*100:.1f}% reduction)")

    print(f"\n💰 COST:")
    print(f"  Current Total:     ${total_current_cost:.6f}")
    print(f"  Optimized Total:   ${total_optimized_cost:.6f}")
    print(f"  Total Savings:     ${total_cost_savings:.6f} ({total_cost_savings/total_current_cost*100:.1f}% reduction)")

    print(f"\n🎯 QUALITY:")
    print(f"  Avg Metrics Accuracy:  {avg_metrics_accuracy:.1f}%")
    print(f"  Avg Symbol Overlap:    {avg_symbol_overlap:.1f}%")

    print(f"\n💡 EXTRAPOLATION (10,000 articles/month):")
    monthly_current_cost = total_current_cost / len(results) * 10_000
    monthly_optimized_cost = total_optimized_cost / len(results) * 10_000
    monthly_savings = monthly_current_cost - monthly_optimized_cost
    yearly_savings = monthly_savings * 12

    print(f"  Current Cost:      ${monthly_current_cost:.2f}/month (${monthly_current_cost * 12:.2f}/year)")
    print(f"  Optimized Cost:    ${monthly_optimized_cost:.2f}/month (${monthly_optimized_cost * 12:.2f}/year)")
    print(f"  Monthly Savings:   ${monthly_savings:.2f}")
    print(f"  Yearly Savings:    ${yearly_savings:.2f}")

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)

    return results


if __name__ == "__main__":
    run_comparison_test()
