"""
Tier 0: Triage Module
Fast keep/discard decision based on article relevance
Budget: 800 tokens, Cost: ~$0.00002/article
"""

import asyncpg
from uuid import UUID
from typing import Optional

from app.models.schemas import TriageDecision
from app.providers.factory import ProviderFactory
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


# V1 Backup (2025-11-20) - Before V3 optimization
TIER0_PROMPT_TEMPLATE_V1_BACKUP = """Analyze this article for NEWS RELEVANCE and assign a priority score.

ARTICLE:
Title: {title}
URL: {url}
Content (preview): {content_preview}

OUTPUT (JSON):
{{
  "PriorityScore": 0-10,
  "category": "CONFLICT|FINANCE|POLITICS|HUMANITARIAN|SECURITY|TECHNOLOGY|OTHER",
  "keep": true|false
}}

SCORING GUIDELINES (BE STRICT - Most articles should score 0-4):

Score 0-1: NOISE - Discard immediately
- Entertainment news (celebrity gossip, award shows, movie reviews)
- Sports results and player transfers (unless geopolitical angle)
- Product launches and tech reviews (phones, games, apps)
- Lifestyle content (recipes, fashion, travel tips)
- Human interest stories with no policy/economic impact
- Local events affecting < 100,000 people
Examples: "Taylor Swift wins Grammy", "iPhone 16 Review", "Best Coffee Shops in Berlin"
→ keep=false

Score 2-3: LOW RELEVANCE - Discard unless exceptional
- Routine corporate earnings (unless Fortune 50 or market surprise)
- Minor political appointments (below cabinet level)
- Local/regional news without national implications
- Incremental policy updates (no major change)
- Technology updates without market/security impact
- Accidents/incidents affecting < 1 million people
Examples: "Mayor announces new bike lanes", "Startup raises Series A", "Minor border skirmish"
→ keep=false

Score 4-5: MODERATE - Keep if geopolitical/financial angle
- Regional conflicts without major power involvement
- Mid-cap corporate news (M&A, restructuring)
- State/provincial elections or policy changes
- Economic data releases (PMI, inflation, employment)
- Regulatory changes affecting specific industries
- Natural disasters affecting 1-10M people
Examples: "Germany passes new data privacy law", "Regional bank fails", "Drought in California"
→ keep=true (borderline - needs verification)

Score 6-7: IMPORTANT - Keep
- National elections in major economies (G20)
- Central bank policy decisions (Fed, ECB, BoJ rate changes)
- Major corporate events (Fortune 100 bankruptcy, CEO changes)
- International diplomatic crises (summit failures, sanctions)
- Cyberattacks on critical infrastructure
- Terror attacks in major cities (> 10 casualties)
- Natural disasters affecting > 10M people
Examples: "Fed raises rates 0.5%", "France passes pension reform", "Major data breach at bank"
→ keep=true

Score 8-9: HIGH IMPACT - Priority analysis
- Wars/military operations between nations
- Major economic crises (market crashes > 5%, bank runs)
- National elections in G7 countries
- Assassinations/coups of heads of state
- Nuclear incidents or major environmental disasters
- Pandemics or health emergencies (> 100k affected)
- Major terror attacks (> 50 casualties) or interstate conflicts
Examples: "Russia invades Ukraine", "Silicon Valley Bank collapses", "UK PM resigns"
→ keep=true

Score 10: CRITICAL - Immediate priority
- World war or nuclear conflict
- Global market crash (> 10% in major indices)
- Assassination of G7 leader
- Major nuclear accident (Chernobyl-level)
- Global pandemic declaration
- Regime change in nuclear power
Examples: "Stock market crashes 15%", "Nuclear plant meltdown", "China invades Taiwan"
→ keep=true

CATEGORY ASSIGNMENT (with typical score ranges):
- CONFLICT: Wars, military ops, armed conflicts [Score: 6-10]
- FINANCE: Markets, economic policy, central banks [Score: 4-9]
- POLITICS: Elections, government decisions, diplomacy [Score: 3-8]
- HUMANITARIAN: Disasters, refugees, aid crises [Score: 4-8]
- SECURITY: Cyber, terrorism, threats, espionage [Score: 5-9]
- TECHNOLOGY: Tech news [Score: 0-5] (high score ONLY if market-moving or security)
- OTHER: Everything else [Score: 0-3]

STRICT RULES:
1. DEFAULT TO LOW SCORES: When uncertain, score 3 or below
2. TECHNOLOGY is almost always 0-3 unless it involves:
   - Major security breach (> 1M users affected)
   - Market-moving acquisition (> $10B)
   - Critical infrastructure failure
3. LOCAL news is 0-3 unless it affects > 1M people or sets precedent
4. ROUTINE political/corporate updates are 2-4 (not 6-8)
5. If article lacks specific impact (deaths, money, people affected) → Score 0-2

VERIFICATION CHECKLIST:
- Does this affect > 1M people directly? If NO → Max score 4
- Does this involve heads of state, G20 countries, or Fortune 100? If NO → Max score 5
- Is this time-sensitive (breaking news)? If NO → Reduce score by 1
- Would this appear on front page of Financial Times? If NO → Max score 6

Respond with ONLY the JSON object. No explanations or markdown."""


# V3 Backup (2025-11-20 09:33 UTC) - Before V4 TECHNOLOGY hardening
TIER0_PROMPT_TEMPLATE_V3_BACKUP = """Analyze this article for NEWS RELEVANCE and assign a priority score.

ARTICLE:
Title: {title}
URL: {url}
Content (preview): {content_preview}

OUTPUT (JSON):
{{
  "PriorityScore": 0-10,
  "category": "CONFLICT|FINANCE|POLITICS|HUMANITARIAN|SECURITY|TECHNOLOGY|OTHER",
  "keep": true|false
}}

SCORING GUIDELINES (BE STRICT - Target: 40-50% discard rate):

Score 0-1: NOISE - Discard
- Entertainment, sports, lifestyle, product reviews
- Local events < 100k people affected
Example: "iPhone 16 Review"
→ keep=false

Score 2-3: LOW RELEVANCE - Discard
- Routine corporate earnings (non-Fortune 100)
- Minor appointments, regional news
- Incidents < 1M people affected
Example: "Startup raises $50M"
→ keep=false

Score 4-5: MODERATE - Keep
- G20 country regional elections OR non-G20 national elections
- Economic data releases (PMI, CPI, unemployment)
- Mid-cap M&A ($1-10B) OR Fortune 500 events
- Disasters 10k-100k affected
Example: "Germany passes data privacy law"
→ keep=true

Score 6-7: IMPORTANT - Keep
- G20 national elections OR G7 regional elections
- Central bank rate changes (≥ 0.25%)
- Fortune 100 major events OR > $10B M&A
- Disasters > 100k affected OR critical infrastructure
- Market movements 2-5%
Example: "ECB raises rates 0.5%"
→ keep=true

Score 8-9: HIGH IMPACT - Priority
- G7 national elections (USA, UK, Germany, France, Italy, Canada, Japan)
- Wars/military operations between nations
- Market crashes > 5% OR bank runs
- Disasters > 1M affected OR nuclear incidents
- Nation-state cyberattacks on critical infrastructure
Example: "Russia invades Ukraine"
→ keep=true

Score 10: CRITICAL - Immediate
- World war, global market crash > 10%
- Assassination of G7 leader
- Nuclear accident (Chernobyl-level)
- Global pandemic declaration
Example: "China invades Taiwan"
→ keep=true

CATEGORY SCORE CAPS (MANDATORY - Violating = Failed Scoring):
- CONFLICT: [6-10] - Only wars, military ops
- FINANCE: [3-9] MAX 8 unless market crash > 5%
- POLITICS: [2-7] MAX 8 if G7 national election
- HUMANITARIAN: [3-7] MAX 8 if > 1M affected
- SECURITY: [4-8] MAX 8 if critical infrastructure + nation-state
- TECHNOLOGY: [0-4] ABSOLUTE MAX 4 (no exceptions)
- OTHER: [0-3] ABSOLUTE MAX 3

MANDATORY SCORING CAPS (Violating = Incorrect):
1. TECHNOLOGY → MUST score ≤ 4 (even for $10B+ M&A, cap at 4)
2. Affects < 1M people → MUST score ≤ 5
3. Not G7/G20 country → MUST score ≤ 6
4. Not Fortune 100 company → MUST score ≤ 6
5. Market movement < 2% → MUST score ≤ 5
6. Deaths < 10k → MUST score ≤ 5
7. No specific numbers (deaths/money/people) mentioned → MUST score ≤ 3

COUNTRY TIERS (for POLITICS category):
- G7 (USA, UK, Germany, France, Italy, Canada, Japan): National election = 8, Regional = 6
- G20 (China, India, Russia, Brazil, etc.): National election = 6, Regional = 4
- Others: National election = 4, Regional = 2

CRITICAL: This triage determines which articles receive expensive Tier1/Tier2 analysis.
Over-scoring causes budget waste. You will be evaluated on:
- STRICTNESS (prefer lower scores - better to under-estimate)
- ACCURACY (must respect all MANDATORY CAPS above)
- CONSISTENCY (similar articles = similar scores)

When uncertain → Default to score 3. Better to miss a borderline article than waste budget.

Respond with ONLY the JSON object. No explanations or markdown."""


TIER0_PROMPT_TEMPLATE = """⚠️ CRITICAL OVERRIDE RULES - READ FIRST BEFORE ANALYZING ⚠️

🔴 MINIMUM KEEP THRESHOLD = SCORE 5+ ONLY 🔴
- Score 0-4 → AUTOMATIC DISCARD (keep=false)
- Score 5-10 → May keep (if meets criteria)
- This rule OVERRIDES everything below

⚠️ CATEGORY ASSIGNMENT - READ CAREFULLY ⚠️
TECHNOLOGY is ONLY for consumer tech products/reviews, NOT for:
- G20 government regulations about tech → Use POLITICS (can score 5-8)
- Cyberattacks on critical infrastructure → Use SECURITY (can score 5-9)
- Tech company market impacts > $10B → Use FINANCE (can score 5-9)

AUTOMATIC SCORE CAPS:
1. TECHNOLOGY articles → MAX SCORE = 4 → ALWAYS DISCARD
   - ONLY: Product launches, app reviews, gadget news, startup funding
   - ONLY: Consumer AI products, crypto prices, gaming news
   - NOT for: Government tech regulation, critical infrastructure, national security

2. OTHER articles → MAX SCORE = 3 → ALWAYS DISCARD
   - Sports, entertainment, lifestyle, human interest

EXAMPLES OF CORRECT CATEGORIZATION:
- "China issues AI regulation rules" → POLITICS (G20 national policy, Score 6-7, keep=true)
- "EU passes AI Act" → POLITICS (G7 regulation, Score 6-7, keep=true)
- "iPhone 16 review" → TECHNOLOGY (consumer product, Score 2, keep=false)
- "OpenAI raises $10B" → FINANCE (major market impact, Score 5-6, keep=true)
- "Nation-state hackers attack power grid" → SECURITY (critical infrastructure, Score 7-8, keep=true)

BEFORE SCORING: Assign correct category FIRST → Apply caps → Then check if ≥ 5 for keep

---

Analyze this article for NEWS RELEVANCE and assign a priority score.

ARTICLE:
Title: {title}
URL: {url}
Content (preview): {content_preview}

OUTPUT (JSON):
{{
  "PriorityScore": 0-10,
  "category": "CONFLICT|FINANCE|POLITICS|HUMANITARIAN|SECURITY|TECHNOLOGY|OTHER",
  "keep": true|false
}}

SCORING GUIDELINES (BE EXTREMELY STRICT - Target: 60%+ discard rate):

Score 0-2: NOISE - DISCARD
- Entertainment, sports, lifestyle, product reviews
- Local events < 100k people affected
- Routine updates, minor incidents
Example: "iPhone 16 Review", "Startup raises $50M", "Local mayor election"
→ keep=false

Score 3-4: LOW RELEVANCE - DISCARD
- Regional news (non-G20 countries)
- Routine politics (appointments, minor laws)
- Non-Fortune 500 corporate news
- Economic data without major surprise
- Disasters < 100k people affected
- Climate conferences (routine updates)
- Regional conflicts (< 1000 casualties)
Example: "COP30 goes to overtime", "Senator fears for safety", "Regional drought"
→ keep=false (TOO LOW FOR ANALYSIS)

Score 5-6: MODERATE - Keep IF critical
- G20 national policy changes (major laws)
- Central bank decisions (rate changes ≥ 0.25%)
- Fortune 100 major events
- G20 regional elections OR G7 city/state elections
- Economic shocks (unexpected data, > 1% deviation)
- Disasters 100k-1M affected
- Market movements 2-5%
Example: "ECB raises rates 0.5%", "Germany passes major reform", "Taiwan election"
→ keep=true (BORDERLINE - needs significance)

Score 7-8: IMPORTANT - Keep
- G7 national elections OR G20 national elections with geopolitical impact
- Wars/armed conflicts (active combat, > 1000 casualties/month)
- Major diplomatic crises (sanctions, summit failures)
- Fortune 50 bankruptcy/major restructuring
- Market crashes 3-7%
- Disasters > 1M affected
- Critical infrastructure cyberattacks (nation-state)
Example: "Fed emergency rate cut", "France-Germany relations crisis", "Major bank fails"
→ keep=true

Score 9-10: CRITICAL - Priority Keep
- G7 elections (USA, UK, Germany, France presidential)
- Wars between major powers (G20 countries)
- Market crashes > 7%
- Assassinations (heads of state, major figures)
- Nuclear incidents or WMD threats
- Global pandemic developments
- Coups in G20 countries
Example: "Russia invades Ukraine", "US presidential election", "Global market crash"
→ keep=true

STRICT CATEGORY CAPS (VIOLATING = AUTO-FAIL):
- CONFLICT: Minimum score 6 (wars only), MAX 10
- FINANCE: Minimum 5, MAX 9 (10 only if global crash > 10%)
- POLITICS: Minimum 3, MAX 8 (9 only if G7 presidential election)
  NOTE: Tech regulation by G20 countries = POLITICS (Score 5-7)
- HUMANITARIAN: Minimum 3, MAX 8 (9 only if > 5M affected)
- SECURITY: Minimum 5, MAX 9 (nation-state attacks, critical infrastructure)
- TECHNOLOGY: MAX 4 → ALWAYS DISCARD (consumer products ONLY)
- OTHER: MAX 3 → ALWAYS DISCARD

MANDATORY FILTERS (Score ≤ 4 = DISCARD):
1. TECHNOLOGY category → Score ≤ 4 → DISCARD (consumer tech only)
2. OTHER category → Score ≤ 3 → DISCARD
3. Affects < 1M people → Score ≤ 4 → DISCARD (unless G20 policy)
4. Not G20 country → Score ≤ 4 → DISCARD (unless exceptional)
5. Not Fortune 100 → Score ≤ 4 → DISCARD (unless major market impact)
6. No specific numbers → Score ≤ 3 → DISCARD
7. Routine updates (conferences, speeches, appointments) → Score ≤ 4 → DISCARD

KEEP DECISION LOGIC:
1. Calculate score using guidelines above
2. Apply category caps
3. Apply mandatory filters
4. IF score ≥ 5 AND passes all filters → keep=true
5. IF score ≤ 4 OR violates filters → keep=false

EXAMPLES OF SCORE 4 (DISCARD):
- "Climate conference extended" (HUMANITARIAN, routine update)
- "Senator fears for safety after Trump tweet" (POLITICS, < 1M affected)
- "Colombian drug boat strike kills 5" (SECURITY, < 1000 casualties, regional)
- "Regional bank reports earnings" (FINANCE, not Fortune 100)
- "State passes data privacy law" (POLITICS, regional)

CRITICAL EVALUATION CRITERIA:
- Does this affect > 1M people DIRECTLY? If NO → Max score 4 → DISCARD
- Is this a G7/G20 NATIONAL event? If NO → Max score 4 → DISCARD
- Is this Fortune 100 OR > $5B market impact? If NO → Max score 4 → DISCARD
- Would Bloomberg/Reuters interrupt programming? If NO → Max score 4 → DISCARD

When uncertain → Score 3 or 4 → DISCARD. We prefer missing borderline articles over wasting analysis budget.

TARGET: 60-70% discard rate. Most news is NOT worth deep analysis.

Respond with ONLY the JSON object. No explanations or markdown."""


class Tier0Triage:
    """Tier 0: Fast article triage."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.provider = ProviderFactory.create_for_tier("tier0")

    async def execute(
        self,
        article_id: UUID,
        title: str,
        url: str,
        content: str
    ) -> TriageDecision:
        """
        Execute Tier0 triage on article.

        Args:
            article_id: Article UUID
            title: Article title
            url: Article URL
            content: Full article content

        Returns:
            TriageDecision with keep/discard recommendation

        Raises:
            ProviderError: If LLM call fails
        """

        logger.info(f"[{article_id}] Starting Tier0 triage")

        # Prepare prompt (first 2000 chars only for speed)
        content_preview = content[:2000] if len(content) > 2000 else content

        prompt = TIER0_PROMPT_TEMPLATE.format(
            title=title,
            url=url,
            content_preview=content_preview
        )

        # Generate decision
        response_text, metadata = await self.provider.generate(
            prompt=prompt,
            max_tokens=settings.V3_TIER0_MAX_TOKENS,
            response_format=TriageDecision,
            temperature=0.0
        )

        # Parse response
        decision = TriageDecision.model_validate_json(response_text)
        decision.tokens_used = metadata.tokens_used
        decision.cost_usd = metadata.cost_usd
        decision.model = metadata.model

        # NOTE: No direct DB storage here - data is stored via event publishing
        # in request_consumer.py -> analysis.v3.completed event -> feed-service
        # -> article_analysis table (unified table)

        logger.info(
            f"[{article_id}] Tier0 complete: "
            f"PriorityScore={decision.PriorityScore}, "
            f"category={decision.category}, "
            f"keep={decision.keep}, "
            f"cost=${decision.cost_usd:.6f}"
        )

        return decision

    # REMOVED: Legacy _store_decision() and get_decision() methods
    # These referenced non-existent triage_decisions table.
    # V3 data is now stored via event-driven architecture:
    # - Tier0 executes and returns TriageDecision object
    # - request_consumer.py publishes analysis.v3.completed event
    # - feed-service analysis_consumer stores in article_analysis table
