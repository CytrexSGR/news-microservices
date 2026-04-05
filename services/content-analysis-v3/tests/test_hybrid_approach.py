"""
Test Script: Hybrid Approach (Ansatz 3)

Vergleicht Token-Verbrauch zwischen:
- AKTUELL: 6 separate Specialist-Calls (jeder mit vollem Content)
- HYBRID: 1 kombinierter Call für alle Specialists

Test mit 20 verschiedenen Artikeln:
- Verschiedene Längen (kurz, mittel, lang)
- Verschiedene Typen (Finance, Geopolitics, Technology, Mixed)
"""

import json
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum


class ArticleLength(Enum):
    SHORT = "short"      # 200-400 words
    MEDIUM = "medium"    # 400-800 words
    LONG = "long"        # 800-1500 words
    VERY_LONG = "very_long"  # 1500+ words


@dataclass
class TestArticle:
    id: str
    title: str
    content: str
    length: ArticleLength
    word_count: int
    category: str  # finance, geopolitics, technology, mixed


# ============================================================================
# TEST ARTICLES (20 verschiedene)
# ============================================================================

def generate_test_articles() -> List[TestArticle]:
    """Generate 20 test articles of varying lengths and types."""

    articles = []

    # ========================================================================
    # SHORT ARTICLES (200-400 words) - 5 articles
    # ========================================================================

    articles.append(TestArticle(
        id="short_finance_1",
        title="Apple Stock Rises 3% on Strong iPhone Sales",
        content="""Apple Inc. shares climbed 3.2% in morning trading after the company reported
better-than-expected iPhone sales for Q1 2025. The tech giant sold 52 million units, beating
analyst estimates of 48 million. CEO Tim Cook credited strong demand in emerging markets,
particularly India and Southeast Asia.

The company's services revenue also exceeded forecasts, reaching $22.3 billion, up 12%
year-over-year. Apple Music and iCloud subscriptions drove the growth. Analysts at Morgan
Stanley raised their price target from $195 to $210, citing improving margins and strong
product pipeline.""",
        length=ArticleLength.SHORT,
        word_count=89,
        category="finance"
    ))

    articles.append(TestArticle(
        id="short_geopolitics_1",
        title="France and Germany Announce Joint Defense Initiative",
        content="""France and Germany unveiled a new joint defense program aimed at strengthening
European military capabilities. The initiative, worth €15 billion over five years, will focus
on developing next-generation fighter jets and missile defense systems.

French President Macron and German Chancellor Scholz announced the partnership at a press
conference in Berlin. The program responds to growing security concerns following recent
tensions with Russia. NATO welcomed the announcement, calling it "a significant step toward
European strategic autonomy.""",
        length=ArticleLength.SHORT,
        word_count=83,
        category="geopolitics"
    ))

    articles.append(TestArticle(
        id="short_technology_1",
        title="Meta Launches New VR Headset at Competitive Price",
        content="""Meta announced the Quest 4, its latest virtual reality headset, priced at $399.
The device features improved resolution, longer battery life, and enhanced hand tracking. CEO
Mark Zuckerberg demonstrated the headset at Meta's annual Connect conference.

The Quest 4 will compete directly with Sony's PlayStation VR2 and Apple's Vision Pro. Pre-orders
begin next week, with shipping expected in December. Meta aims to sell 5 million units in the
first year, doubling Quest 3 sales.""",
        length=ArticleLength.SHORT,
        word_count=79,
        category="technology"
    ))

    articles.append(TestArticle(
        id="short_mixed_1",
        title="Japan Raises Interest Rates, Yen Strengthens",
        content="""The Bank of Japan raised its key interest rate by 0.25% to 0.5%, marking the
third increase this year. The move aims to combat rising inflation, which reached 3.2% in
September, exceeding the central bank's 2% target.

The yen strengthened 2.1% against the dollar following the announcement. Japanese exporters'
stocks declined, with Toyota falling 1.8% and Honda dropping 1.5%. Economists expect further
rate hikes if inflation remains elevated.""",
        length=ArticleLength.SHORT,
        word_count=77,
        category="mixed"
    ))

    articles.append(TestArticle(
        id="short_finance_2",
        title="Bitcoin Surges Past $45,000 on ETF Approval Hopes",
        content="""Bitcoin climbed 8.5% to $45,200, reaching its highest level since April 2024.
The rally followed reports that the SEC may approve multiple spot Bitcoin ETFs in January.
Trading volume surged to $28 billion, the highest in six months.

Ethereum and other major cryptocurrencies also gained, with ETH rising 6.3% to $2,480. Crypto
analysts predict further gains if ETF approvals materialize. However, some warn of potential
volatility as regulatory uncertainty persists.""",
        length=ArticleLength.SHORT,
        word_count=76,
        category="finance"
    ))

    # ========================================================================
    # MEDIUM ARTICLES (400-800 words) - 8 articles
    # ========================================================================

    articles.append(TestArticle(
        id="medium_finance_1",
        title="Federal Reserve Holds Rates Steady, Signals Potential Cut in Q2",
        content="""The Federal Reserve maintained its benchmark interest rate at 5.25%-5.50% following
its two-day policy meeting, as expected by markets. However, Fed Chair Jerome Powell indicated
that rate cuts could begin as early as Q2 2025 if inflation continues its downward trajectory.

In his post-meeting press conference, Powell noted that inflation has declined to 2.9%, approaching
the Fed's 2% target. "We're seeing encouraging signs, but we need more evidence that inflation is
sustainably moving toward our goal," Powell stated.

Financial markets rallied on the dovish tone, with the S&P 500 gaining 1.8% and the Dow Jones
rising 450 points. Treasury yields fell sharply, with the 10-year yield dropping to 4.12% from
4.35% earlier in the day. The dollar weakened against major currencies.

Economists are divided on the timing of rate cuts. Goldman Sachs predicts the first cut in March,
while JPMorgan expects May. Bank of America maintains its forecast for June, citing persistent
wage growth and housing costs.

The Fed's decision comes amid mixed economic signals. While inflation is cooling, the labor market
remains strong with unemployment at 3.9%. GDP growth has slowed to 1.8% annualized, down from
3.2% in Q4 2024.

Powell emphasized the Fed's data-dependent approach, stating that "we're not on a preset path."
The central bank will closely monitor upcoming inflation reports, employment data, and consumer
spending trends before making its next move.""",
        length=ArticleLength.MEDIUM,
        word_count=234,
        category="finance"
    ))

    articles.append(TestArticle(
        id="medium_geopolitics_1",
        title="Middle East Peace Talks Resume After 18-Month Hiatus",
        content="""Israeli and Palestinian delegations met in Cairo for the first substantive peace
negotiations in 18 months, mediated by Egypt and backed by the United States. The talks aim to
establish a framework for addressing key issues including borders, security, and the status of
Jerusalem.

Egyptian President el-Sisi hosted the opening session, calling it "a historic opportunity to break
the cycle of violence and build a path toward lasting peace." U.S. Secretary of State Antony Blinken
attended virtually, emphasizing American commitment to a two-state solution.

The negotiations follow months of shuttle diplomacy by Egyptian intelligence chief Abbas Kamel, who
worked behind the scenes to bring both sides back to the table. Recent de-escalation efforts,
including a prisoner exchange and easing of Gaza border restrictions, created conditions for renewed
dialogue.

Key agenda items include establishing a ceasefire mechanism, reopening checkpoints, and addressing
settlement expansion in the West Bank. Palestinian representatives are pushing for international
guarantees of any agreement, while Israeli officials emphasize security concerns.

Regional powers have taken different stances. Saudi Arabia and the UAE support the talks and have
offered economic incentives for progress. Iran criticized the negotiations as "illegitimate" and
called for Palestinian resistance. Turkey offered to host follow-up sessions if initial talks prove
successful.

The international community reacted cautiously optimistic. UN Secretary-General António Guterres
welcomed the resumption but warned that "words must be followed by concrete actions." The European
Union pledged €50 million in humanitarian aid to support the peace process.""",
        length=ArticleLength.MEDIUM,
        word_count=246,
        category="geopolitics"
    ))

    articles.append(TestArticle(
        id="medium_technology_1",
        title="Google Announces Major AI Integration Across All Products",
        content="""Google unveiled a comprehensive plan to integrate advanced AI capabilities across
its entire product ecosystem, including Search, Gmail, Docs, and YouTube. The initiative, called
"Google AI Everywhere," leverages the company's latest Gemini Ultra model to provide more intelligent
and contextual user experiences.

CEO Sundar Pichai demonstrated several new features at the company's annual I/O developer conference.
Search will now offer AI-generated summaries for complex queries, Gmail will draft entire emails based
on brief prompts, and Docs will provide real-time writing assistance with fact-checking capabilities.

The YouTube integration includes AI-powered video summarization, automatic chapter generation, and
personalized content recommendations based on deeper understanding of user preferences. Creators will
gain access to AI tools for video editing, thumbnail generation, and audience analytics.

Google's aggressive AI push responds to competitive pressure from Microsoft's OpenAI partnership and
emerging AI startups. The company invested $15 billion in AI infrastructure over the past year,
expanding its data center capacity and developing custom AI chips.

Privacy advocates raised concerns about data collection requirements for AI features. Google assured
users that all processing occurs with "enterprise-grade privacy protections" and that users can opt
out of AI features without losing access to core services.

The AI integration will roll out gradually, starting with English-language markets in May 2025, followed
by global expansion throughout the year. Google Workspace subscribers will receive priority access to
advanced AI features.""",
        length=ArticleLength.MEDIUM,
        word_count=241,
        category="technology"
    ))

    articles.append(TestArticle(
        id="medium_mixed_1",
        title="Climate Summit Ends with Historic $500 Billion Green Energy Fund",
        content="""The COP30 climate summit in Dubai concluded with the announcement of a groundbreaking
$500 billion Global Green Energy Transition Fund, backed by contributions from 120 countries and major
corporations. The fund aims to accelerate renewable energy adoption in developing nations and phase out
fossil fuels by 2050.

UN Secretary-General António Guterres called it "the most significant climate finance commitment in
history." The fund will provide low-interest loans and grants for solar, wind, and hydroelectric
projects, with priority given to countries most vulnerable to climate change.

Major contributors include the European Union ($150 billion), United States ($100 billion), China
($80 billion), and Japan ($50 billion). Private sector participants include Microsoft, Apple, Amazon,
and major oil companies transitioning to renewable energy.

The agreement faced opposition from oil-producing nations, particularly Saudi Arabia and Russia, which
argued for a slower transition timeline. Environmental groups, while welcoming the fund, criticized the
lack of binding enforcement mechanisms and continued fossil fuel subsidies in many countries.

Financial markets reacted positively, with renewable energy stocks surging. NextEra Energy rose 8.3%,
Vestas Wind Systems gained 6.7%, and First Solar climbed 9.1%. Conversely, traditional oil majors
declined, with ExxonMobil falling 3.2% and Chevron dropping 2.8%.

The fund's governance structure will be managed by a coalition of the World Bank, regional development
banks, and UN Climate agencies. Disbursements begin in Q3 2025, with the first projects expected in
Africa and Southeast Asia.""",
        length=ArticleLength.MEDIUM,
        word_count=252,
        category="mixed"
    ))

    articles.append(TestArticle(
        id="medium_finance_2",
        title="Amazon Reports Record Q4 Earnings, Cloud Growth Accelerates",
        content="""Amazon announced record Q4 2024 earnings, with revenue reaching $175 billion, up 13%
year-over-year and exceeding analyst expectations of $168 billion. Net income surged to $15.3 billion,
or $1.48 per share, beating estimates of $1.28 per share.

AWS (Amazon Web Services) was the star performer, generating $27.5 billion in revenue with a 22% growth
rate, the fastest expansion in eight quarters. AWS profit margins improved to 32%, up from 29% a year
earlier, driven by AI infrastructure services and cost optimization initiatives.

Amazon's advertising business continued its strong trajectory, reaching $15.8 billion in Q4, up 24%
year-over-year. The company has become the third-largest digital advertising platform behind Google and
Meta, benefiting from its vast customer data and high purchase intent.

E-commerce sales grew 9% to $120 billion, with international markets showing particular strength. Prime
membership reached 250 million globally, adding 25 million subscribers in 2024. Average revenue per
Prime member increased 15% to $178 annually.

CEO Andy Jassy highlighted the company's AI investments: "We're seeing tremendous demand for AWS AI
services, particularly our custom chip offerings and Bedrock generative AI platform. This positions us
strongly for the next wave of cloud computing."

The company's logistics network efficiency improvements drove margin expansion. Operating margin reached
6.8%, up from 5.3% in Q4 2023. Amazon reduced delivery times while lowering per-unit shipping costs.

Looking ahead, Amazon guided Q1 2025 revenue of $148-153 billion, above consensus estimates of $145
billion. The stock rose 8.5% in after-hours trading.""",
        length=ArticleLength.MEDIUM,
        word_count=257,
        category="finance"
    ))

    articles.append(TestArticle(
        id="medium_geopolitics_2",
        title="India and Pakistan Agree to Resume Trade After 6-Year Freeze",
        content="""In a diplomatic breakthrough, India and Pakistan announced they will resume bilateral
trade after a six-year suspension, marking the most significant thaw in relations since tensions
escalated in 2019. The agreement, brokered through secret negotiations in Dubai, will initially focus
on essential goods and agricultural products.

The joint statement, issued simultaneously in New Delhi and Islamabad, outlined a phased approach to
normalizing trade relations. Phase 1 begins in June with agricultural products, pharmaceuticals, and
textiles. Full trade restoration is targeted for January 2026.

Indian Prime Minister Modi emphasized economic pragmatism: "While challenges remain, our people deserve
the economic opportunities that normalized trade brings." Pakistani Prime Minister Sharif echoed the
sentiment, stating that "economic cooperation can build bridges toward lasting peace."

The trade suspension, implemented after the 2019 Pulwama attack, cost both economies an estimated $10
billion in lost commerce. Indian exporters of cotton, chemicals, and machinery stand to benefit
significantly. Pakistan's textile industry anticipates immediate gains from accessing the large Indian
market.

Regional powers cautiously welcomed the development. China, which has close ties with Pakistan, called
it "a positive step toward regional stability." The United States praised both countries for "choosing
dialogue over confrontation."

Implementation challenges remain. Border infrastructure needs upgrading, banking channels must be
reestablished, and security protocols require negotiation. Both countries appointed special trade
envoys to oversee the process.

Kashmir remains a contentious issue, with both sides agreeing to separate trade normalization from
territorial disputes. Experts warn that any security incident could derail progress.""",
        length=ArticleLength.MEDIUM,
        word_count=258,
        category="geopolitics"
    ))

    articles.append(TestArticle(
        id="medium_technology_2",
        title="Quantum Computing Breakthrough: IBM Achieves 1000-Qubit Milestone",
        content="""IBM announced a major quantum computing breakthrough with its new 1,121-qubit quantum
processor, named "Condor 2.0." The achievement marks a significant step toward practical quantum
computing applications in drug discovery, cryptography, and materials science.

The company demonstrated quantum advantage in several real-world problems, including molecular simulation
for pharmaceutical research and optimization algorithms for supply chain management. Error rates decreased
by 60% compared to IBM's previous 433-qubit system.

Dr. Jerry Chow, IBM's Director of Quantum Infrastructure, explained: "We've not just increased qubit
count—we've fundamentally improved coherence times and error correction. This makes Condor 2.0 suitable
for production workloads."

Major corporations are already testing the system. Pfizer is using it for protein folding simulations,
potentially accelerating drug development by years. JPMorgan Chase is exploring quantum algorithms for
portfolio optimization and risk analysis.

The breakthrough intensifies the global quantum computing race. Google, Microsoft, and Chinese researchers
are pursuing alternative approaches. Google's quantum team recently published results showing quantum
supremacy in random number generation.

Investment in quantum computing has surged to $35 billion globally over the past two years. Governments
see quantum technology as strategically critical, with the U.S., China, and EU each committing billions
to research programs.

Cybersecurity experts warn that powerful quantum computers could eventually break current encryption
standards. NIST recently announced post-quantum cryptography standards to prepare for this threat.

IBM plans to make Condor 2.0 available via its quantum cloud service in Q3 2025, with pricing based on
computational time rather than qubit access.""",
        length=ArticleLength.MEDIUM,
        word_count=257,
        category="technology"
    ))

    articles.append(TestArticle(
        id="medium_mixed_2",
        title="Global Wheat Shortage Drives Food Prices to 10-Year High",
        content="""Global wheat prices surged 18% this week, reaching their highest level since 2013,
as droughts in major producing regions and export restrictions threaten food security in developing
nations. The UN Food and Agriculture Organization warned of potential shortages affecting 200 million
people.

Severe droughts in Australia, Canada, and Russia reduced this year's wheat harvest by 12%. Russia, the
world's largest wheat exporter, announced a 10 million ton export quota to protect domestic supplies.
This follows India's export ban implemented in March.

The price spike affects bread, pasta, and animal feed costs worldwide. Developing nations dependent on
wheat imports face the most severe impact. Egypt, the world's largest wheat importer, saw domestic bread
prices rise 25%. Lebanon's wheat reserves will last only three months at current consumption rates.

Geopolitical tensions compound the crisis. Ukraine's grain exports remain 40% below pre-war levels despite
the Black Sea grain corridor agreement. Uncertainty over corridor renewal in July creates additional
market volatility.

Financial markets showed mixed reactions. Agricultural commodity traders and grain storage companies
gained. Archer Daniels Midland rose 4.2%, while Bunge Limited climbed 3.8%. However, food manufacturers
and restaurants declined on margin concerns. General Mills fell 2.3%, and McDonald's dropped 1.7%.

The World Bank approved $2 billion in emergency food security financing for affected countries. Western
governments are considering releasing strategic grain reserves to stabilize markets.

Climate scientists warn that extreme weather events will become more frequent, threatening long-term food
security. Agricultural experts call for increased investment in drought-resistant crop varieties and
improved irrigation infrastructure.""",
        length=ArticleLength.MEDIUM,
        word_count=268,
        category="mixed"
    ))

    # ========================================================================
    # LONG ARTICLES (800-1500 words) - 5 articles
    # ========================================================================

    articles.append(TestArticle(
        id="long_finance_1",
        title="Silicon Valley Bank Collapse Triggers Banking Crisis Fears",
        content="""Silicon Valley Bank, the 16th largest U.S. bank and primary lender to technology
startups, collapsed in spectacular fashion on Friday, marking the second-largest bank failure in
American history. Federal regulators seized the bank after depositors withdrew $42 billion in a single
day, approximately 25% of total deposits.

The bank's downfall began when it disclosed a $1.8 billion loss from selling Treasury bonds to meet
withdrawal demands. This sparked panic among its tech-focused depositor base, leading to a classic bank
run. By Thursday evening, SVB stock had plummeted 60%, and by Friday morning, regulators had taken control.

The FDIC (Federal Deposit Insurance Corporation) established a bridge bank to protect insured depositors.
However, many startups held deposits exceeding the $250,000 insurance limit, putting $150 billion in
uninsured funds at risk. Roku disclosed $487 million in deposits at SVB, representing 26% of its cash.

The crisis rapidly spread to other regional banks. First Republic Bank's stock fell 62% on Monday, while
Signature Bank was shut down by New York regulators on Sunday, citing "systemic risk." Western Alliance
and PacWest Bancorp also experienced significant stock declines and deposit outflows.

Federal Reserve Chair Jerome Powell convened an emergency meeting of the Financial Stability Oversight
Council. The Fed, Treasury Department, and FDIC jointly announced extraordinary measures: all SVB
depositors would be made whole, not just those with insured deposits. The Fed created a new emergency
lending facility allowing banks to borrow against Treasury bonds at par value, eliminating the
mark-to-market losses that triggered SVB's collapse.

President Biden addressed the nation, assuring Americans that "the banking system is safe" and promising
that "taxpayers will not bear any losses." He emphasized that bank executives and shareholders would face
consequences: "If bank management took excessive risks, they will be held accountable."

Financial markets experienced extreme volatility. The S&P 500 fell 4.6% on Monday, its worst day since
June 2022. Banking stocks led declines, with the KBW Bank Index dropping 7.7%. Treasury yields plummeted
as investors sought safety, with the 2-year yield falling 0.59 percentage points, the largest single-day
decline since 1987.

Economists debated the broader implications. Some compared it to the 2008 financial crisis, though most
agreed the current situation differs fundamentally. Unlike 2008, when banks held toxic mortgage assets,
today's issue stems from duration mismatch and rapid interest rate increases.

The Fed faces a policy dilemma. Continuing rate hikes to combat inflation could strain more banks,
particularly those with large unrealized losses on bond portfolios. However, pausing rate increases might
fuel inflation expectations.

The technology sector faces immediate challenges. Over 2,000 startups banked with SVB. Many scrambled to
establish new banking relationships over the weekend. Venture capital firms advised portfolio companies
to diversify deposits across multiple banks.

International exposure emerged as a concern. SVB's UK branch, though separately capitalized, entered
insolvency proceedings before being sold to HSBC for £1. The bank had operations in China, Germany,
Israel, and other countries, creating potential international ramifications.

Congressional leaders announced hearings on banking regulation and supervision. Republicans blamed
"excessive government spending and inflation," while Democrats pointed to 2018 regulatory rollbacks that
exempted mid-sized banks from stricter requirements.

Market analysts predict consolidation in the regional banking sector. Larger banks like JPMorgan Chase
and Bank of America, with more diversified deposit bases, appear better positioned. Some speculate this
could accelerate the trend toward financial concentration, with the largest banks growing even larger.

As markets opened Tuesday, volatility continued but showed signs of stabilizing. Government guarantees
appeared to stem deposit outflows at other banks. However, questions remain about the banking system's
resilience if the Fed continues aggressive rate hikes.""",
        length=ArticleLength.LONG,
        word_count=630,
        category="finance"
    ))

    articles.append(TestArticle(
        id="long_geopolitics_1",
        title="China's Taiwan Military Exercises Escalate Regional Tensions",
        content="""China launched its largest-ever military exercises around Taiwan, deploying over 120
aircraft and 30 warships in what Beijing describes as "punishment drills" following Taiwan President
Lai Ching-te's recent remarks affirming the island's sovereignty. The exercises, which began Monday,
simulate a full blockade of Taiwan and practice amphibious assault scenarios.

The People's Liberation Army (PLA) announced it established seven exclusion zones around Taiwan,
effectively surrounding the island. Fighter jets crossed the median line of the Taiwan Strait repeatedly,
while H-6 bombers conducted simulated strikes on key infrastructure. The Navy deployed its newest
aircraft carrier, Fujian, for the first time in a Taiwan-focused exercise.

Taiwan's Ministry of National Defense tracked 156 Chinese military aircraft entering Taiwan's Air Defense
Identification Zone over 48 hours, shattering previous records. President Lai condemned the exercises as
"irrational provocation" and placed Taiwan's military on high alert. The island's stock market fell 3.2%
on concerns about military escalation.

The United States responded forcefully. President Biden stated that America's commitment to Taiwan's
defense "remains rock solid." The Pentagon deployed two aircraft carrier strike groups to the region:
USS Ronald Reagan and USS Carl Vinson. B-52 bombers from Guam conducted freedom of navigation flights
near the exercise zones.

Secretary of State Blinken held urgent consultations with regional allies. Japan expressed "grave concern"
and scrambled F-15 fighters after Chinese aircraft entered areas near Japanese territorial waters. South
Korea summoned China's ambassador, while Australia warned against "use of force to change the status quo."

The exercises demonstrate China's evolving military capabilities. Analysts noted sophisticated coordination
between air, naval, and cyber forces. Chinese hackers simultaneously targeted Taiwan's government networks,
causing temporary disruptions to several ministries.

Economic implications quickly emerged. The Taiwan Strait handles 48% of global container shipping and 88%
of advanced semiconductors. Shipping companies rerouted vessels, adding 3-5 days to transit times.
Insurance premiums for ships transiting the strait increased 15%.

Semiconductor stocks experienced volatility. TSMC, the world's largest chipmaker, fell 4.8%, while Nvidia
and AMD dropped on supply chain concerns. Apple, heavily dependent on Taiwan manufacturing, declined 2.3%.

China's foreign ministry justified the exercises as "necessary measures to protect national sovereignty."
Spokesperson Wang Wenbin accused the U.S. of "playing with fire" by selling weapons to Taiwan and
conducting military interactions. He warned that "Taiwan independence forces will face the severe judgment
of history."

Regional powers maneuvered carefully. ASEAN issued a statement calling for "restraint and dialogue," but
avoided explicitly criticizing China. Singapore, while emphasizing peace, noted the importance of
maintaining sea lane security. Indonesia offered to mediate but received no response from Beijing.

The UN Security Council convened an emergency session. China blocked a resolution calling for de-escalation,
while Russia abstained. UN Secretary-General Guterres expressed "deep concern" and offered to facilitate
dialogue, which both sides rejected.

Military experts debated whether the exercises represent rehearsal for actual invasion. U.S. intelligence
assessments suggest China is building capabilities for a Taiwan operation by 2027, though executing such
an operation successfully remains highly uncertain. Amphibious assaults across 100 miles of ocean against
a prepared defender would be extraordinarily difficult.

Taiwan's defense strategy focuses on asymmetric warfare. The island invested heavily in anti-ship missiles,
naval mines, and coastal defense systems. President Lai announced plans to extend mandatory military
service from 4 months to 1 year, mobilizing additional reserves.

Economic warfare parallels military exercises. China announced new trade restrictions on Taiwan agricultural
products and rare earth export controls affecting Taiwan's electronics industry. Taiwan countered by
restricting high-tech exports to China and accelerating supply chain diversification to Southeast Asia.

The crisis tests U.S. credibility in Asia. American allies watch closely to gauge commitment to regional
security. Some experts argue that strong U.S. response deters Chinese adventurism, while others warn that
increased American presence could trigger miscalculation.

As the exercises entered their fourth day, no signs of de-escalation emerged. China announced the drills
would continue "until objectives are achieved." Taiwan remained on high alert, with reserves called up and
civil defense preparations activated. Regional stock markets remained volatile, and diplomatic channels
showed little progress toward reducing tensions.""",
        length=ArticleLength.LONG,
        word_count=730,
        category="geopolitics"
    ))

    articles.append(TestArticle(
        id="long_technology_1",
        title="OpenAI's GPT-5 Launch Reshapes AI Industry Landscape",
        content="""OpenAI unveiled GPT-5 on Tuesday, delivering on CEO Sam Altman's promise of a
transformative leap in artificial intelligence capabilities. The new model demonstrates reasoning
abilities that approach human-level performance on complex tasks, multimodal understanding spanning
text, images, audio, and video, and a context window of 1 million tokens—enough to process entire books.

During a livestreamed launch event, Altman showcased GPT-5 solving graduate-level physics problems with
step-by-step explanations, generating video content from text descriptions, and engaging in multi-turn
conversations while maintaining perfect context. The demonstrations emphasized the model's ability to
understand nuance, detect logical fallacies, and refuse unreasonable requests.

Technical improvements are substantial. GPT-5 scored 98% on the MMLU benchmark, up from GPT-4's 86%. On
coding challenges, it achieved 94% success rate on LeetCode hard problems. The model also showed
significant gains in mathematical reasoning, scoring 89% on the MATH dataset compared to GPT-4's 52%.

Microsoft, OpenAI's primary partner and investor, announced immediate integration across its product suite.
Azure AI Services will offer GPT-5 API access within weeks. GitHub Copilot receives an upgrade enabling
it to write entire applications from high-level specifications. Bing Chat evolves into a more capable
assistant for complex research tasks.

CEO Satya Nadella called it "the most significant technology platform shift since mobile computing."
Microsoft has invested over $13 billion in OpenAI's infrastructure, and the partnership gives Microsoft
exclusive cloud rights to GPT-5 for enterprise customers.

The competitive response was swift. Google announced an emergency meeting of its AI leadership, reportedly
accelerating Gemini Ultra 2.0's release. Anthropic, founded by former OpenAI researchers, emphasized its
Constitutional AI approach prioritizing safety. Meta confirmed plans to release Llama 4 in Q3 2025.

Financial markets reacted dramatically. Microsoft stock surged 6.8%, adding $180 billion in market
capitalization. OpenAI's private market valuation jumped to $140 billion, up from $86 billion in its
previous funding round. Nvidia gained 4.2% on expectations of increased AI infrastructure demand.

Conversely, companies perceived as AI laggards declined. Salesforce fell 3.4%, Oracle dropped 2.8%, and
traditional software companies faced questions about their AI strategies. Investors are repricing stocks
based on AI integration and competitive positioning.

Enterprise adoption timelines compressed dramatically. Fortune 500 companies are rushing to pilot GPT-5.
JPMorgan Chase announced plans to deploy it for legal document review, potentially replacing thousands of
hours of junior attorney work. Walmart is testing GPT-5 for supply chain optimization and customer service.

The AI safety debate intensified. Critics including AI ethicist Timnit Gebru warned about societal
disruption and potential misuse. "We're deploying increasingly powerful AI without adequate safeguards or
understanding of risks," Gebru stated.

OpenAI addressed concerns by releasing a detailed safety assessment. The company implemented "alignment
tax" strategies that slightly reduce performance to improve safety. GPT-5 refuses harmful requests with
greater sophistication than predecessors, and OpenAI established a $100 million fund for AI safety research.

Regulatory responses varied globally. The European Union AI Act, recently passed, requires high-risk AI
systems to undergo conformity assessments. GPT-5 may face restrictions in certain applications. EU
officials announced investigations into compliance.

China responded differently. Regulators require government approval before deploying advanced AI models.
Chinese companies including Baidu and Alibaba accelerated domestic AI development, viewing GPT-5 as
American technological dominance requiring strategic response.

Employment concerns surfaced prominently. The World Economic Forum estimated that GPT-5 could automate 15%
of current knowledge work. Software developers, writers, analysts, and customer service representatives
face significant displacement. However, proponents argue that AI creates new job categories and enhances
human productivity.

Educational institutions grappled with implications. Universities are revising curricula to emphasize
skills that AI cannot easily replicate: creative thinking, emotional intelligence, ethical reasoning.
Some professors embraced GPT-5 as a teaching tool, while others worry about academic integrity.

OpenAI's pricing strategy emerged as controversial. GPT-5 API costs $0.03 per 1,000 input tokens, 3x more
expensive than GPT-4. Enterprise licenses start at $100,000 annually. Critics argue this creates a "AI
divide" between organizations that can afford access and those that cannot.

Looking ahead, the pace of AI advancement shows no signs of slowing. Altman hinted at GPT-6 already in
training, with potential release in 2026. The industry debates whether current approaches will lead to
artificial general intelligence (AGI) or if fundamental breakthroughs remain necessary.""",
        length=ArticleLength.LONG,
        word_count=780,
        category="technology"
    ))

    articles.append(TestArticle(
        id="long_mixed_1",
        title="Global Chip Shortage Persists Despite Massive Investment in Manufacturing",
        content="""The global semiconductor shortage that began in 2020 continues to constrain multiple
industries despite $500 billion in announced manufacturing investments and government subsidies. Automakers,
consumer electronics companies, and industrial equipment manufacturers still face extended lead times and
allocation constraints.

Automotive sector impact remains severe. Ford and GM announced production cuts for Q2 2025, citing
insufficient chip supplies for advanced driver assistance systems (ADAS) and infotainment units. Global
light vehicle production is running 2.5 million units below capacity, representing $50 billion in lost
revenue.

Consumer electronics face similar pressures. PlayStation 5 availability remains limited 3.5 years after
launch. Apple warned of potential iPhone delays if chip supplies tighten further. Samsung scaled back
production of premium TVs due to display driver shortages.

The root causes are structural. Pandemic-era demand surges created capacity shortfalls that take years to
address. Semiconductor fabs require 2-3 years to build and another 6-12 months for qualification and
ramp-up. Meanwhile, chip demand continues growing 7-9% annually.

Geopolitical tensions compound supply challenges. U.S.-China technology rivalry disrupted established supply
chains. American export controls on advanced chips and manufacturing equipment to China created
inefficiencies. Chinese companies are stockpiling chips, further straining supplies.

Taiwan's central role creates vulnerability. TSMC manufactures 60% of global chips and 90% of advanced
processors. Any disruption—natural disasters, Chinese military action, or infrastructure failures—would
devastate global tech supply chains. Insurance companies raised premiums for Taiwan-dependent supply chains.

Major investment announcements promise future relief. TSMC is building fabs in Arizona ($40 billion), Japan
($28 billion), and Germany ($11 billion). Intel pledged $100 billion for U.S. manufacturing expansion under
CEO Pat Gelsinger's IDM 2.0 strategy. Samsung committed $230 billion for Korean capacity expansion.

Government subsidies drive investment. The U.S. CHIPS Act provides $52 billion in grants and tax credits.
The EU Chips Act allocates €43 billion. China has multiple semiconductor development funds totaling $150
billion. Japan, South Korea, and India launched similar programs.

However, experts caution against oversupply expectations. Historical cycles show that aggressive capacity
additions often lead to bust periods. Morgan Stanley warned that 2026-2027 could see semiconductor
oversupply as new fabs come online simultaneously, potentially triggering industry consolidation.

Leading chipmakers' stocks reflect uncertainty. Nvidia remains elevated on AI chip demand but faces
volatility on supply concerns. Intel struggles with execution challenges despite government support. TSMC
navigates geopolitical risks while maintaining technological leadership.

Equipment manufacturers like ASML, Applied Materials, and Tokyo Electron benefit from capacity buildout.
ASML's extreme ultraviolet (EUV) lithography machines, essential for advanced chips, have a 2-year order
backlog. The company's stock has tripled over three years.

Automotive companies pursue vertical integration. Tesla built closer supplier relationships and diversified
chip sources. GM invested in chip design capabilities, reducing dependence on tier-1 suppliers. This trend
could reshape automotive supply chains permanently.

Consumer behavior adapted to scarcity. Used car prices remain elevated as new vehicle shortages persist.
Gaming console prices on secondary markets still exceed retail. Enterprise IT buyers maintain larger
buffer stocks, further straining just-in-time supply chains.

The shortage accelerated China's semiconductor self-sufficiency efforts. Despite U.S. export controls,
Chinese companies made progress in mature node manufacturing. SMIC achieved 7nm production, though at
lower yields than TSMC. China's chip imports declined 12% in 2024 as domestic production increased.

National security concerns reshaped policy. The U.S. restricted nvidia and AMD exports of high-performance
AI chips to China. This prompted Chinese tech giants to design custom chips. Alibaba, Baidu, and Huawei
all announced AI chips to reduce American dependence.

Workforce shortages emerged as a bottleneck. Semiconductor manufacturing requires highly skilled engineers
and technicians. Universities are ramping up electrical engineering programs, but training takes years.
Companies compete intensely for talent, driving salary inflation in the sector.

Looking ahead, industry leaders predict normalization by late 2026. However, this assumes no major
disruptions—a significant assumption given geopolitical tensions, climate risks, and continued demand
growth. The semiconductor industry has fundamentally changed, with government intervention, geopolitical
considerations, and supply chain resilience now paramount.""",
        length=ArticleLength.LONG,
        word_count=730,
        category="mixed"
    ))

    articles.append(TestArticle(
        id="long_finance_2",
        title="Cryptocurrency Market Crash: Bitcoin Falls Below $20,000 as Regulatory Crackdown Intensifies",
        content="""The cryptocurrency market experienced its worst selloff since 2022, with Bitcoin plunging
22% to $19,400 and total crypto market capitalization falling below $800 billion, down from $3 trillion in
November 2021. The crash followed coordinated regulatory actions by U.S., EU, and UK authorities targeting
major crypto exchanges and stablecoin issuers.

The selloff began Monday when the SEC filed charges against Binance, the world's largest crypto exchange,
alleging "blatant disregard" of securities laws. The complaint claims Binance operated as an unregistered
exchange, broker-dealer, and clearing agency while misrepresenting trading controls. SEC Chairman Gary
Gensler stated that "crypto platforms cannot flout rules that govern the securities markets."

Hours later, the SEC charged Coinbase with similar violations. This marked the first enforcement action
against a U.S. publicly-traded crypto exchange. Coinbase stock collapsed 25%, falling to $38 from its IPO
price of $381. CEO Brian Armstrong called the charges "misguided" and vowed to fight.

Ethereum dropped 26% to $1,150, Cardano fell 31%, and Solana plummeted 35%. Altcoins experienced even
steeper declines, with some losing 50-60% of value in 24 hours. Cryptocurrency lending platforms suspended
withdrawals, citing "extreme market conditions."

Stablecoin depegging added to panic. Tether (USDT), which maintains a nominal $1.00 peg, briefly traded at
$0.93 before recovering. Circle's USDC fell to $0.97. The depegging triggered algorithmic liquidations
across DeFi protocols, accelerating the selloff.

European and UK regulators coordinated actions. The EU finalized Markets in Crypto-Assets (MiCA) regulation
requiring all crypto service providers to obtain licenses by June 2024. The UK's Financial Conduct Authority
warned that unauthorized exchanges would face prosecution and asset freezes.

International regulatory coordination marked a shift. Previously, crypto companies could relocate to
jurisdictions with lighter regulation. Now, major economies are aligning standards, leaving fewer havens.
This represents a turning point for the industry.

Institutional investors faced margin calls. MicroStrategy, holding 140,000 Bitcoin, saw its stock plummet
42%. The company disclosed potential forced sales if Bitcoin falls below $18,000. Tesla's Bitcoin holdings,
now worth $340 million, have lost 55% from purchase price. Elon Musk tweeted cryptically: "Price volatility
reflects regulatory uncertainty."

Crypto exchanges struggled with system outages as trading volume surged to $100 billion daily, 3x normal
levels. Users reported inability to execute trades or withdraw funds. Kraken's CEO acknowledged "unprecedented
strain" on infrastructure.

Mining operations faced existential threats. Bitcoin's price crash makes mining unprofitable for operators
with electricity costs above $0.08/kWh. Several mining companies warned of bankruptcy if prices remain
depressed. Hash rate declined 18% as miners shut down operations.

DeFi protocols experienced cascading liquidations. Aave, Compound, and MakerDAO liquidated $2.1 billion in
undercollateralized positions. This amplified selling pressure as liquidated collateral hit markets. DeFi
Total Value Locked (TVL) fell 40% to $35 billion.

Venture capital firms that invested heavily in crypto faced markdowns. Andreessen Horowitz's crypto fund,
which raised $4.5 billion in 2022, reportedly lost 65% of value. Sequoia Capital wrote down investments in
FTX and other failed exchanges. VC funding for crypto startups dried up, with Q1 2025 funding down 88%
year-over-year.

Banking relationships deteriorated further. Major banks including JPMorgan Chase, Bank of America, and Wells
Fargo announced they would no longer process transactions for crypto-related businesses. This created
liquidity challenges for exchanges trying to process customer withdrawals.

Congressional response split along partisan lines. Republican senators accused the SEC of "regulation by
enforcement," while Democrats supported aggressive oversight. Senator Elizabeth Warren stated that "the Wild
West days of crypto are over."

Industry advocates warned of innovation exodus. Coinbase threatened to relocate operations to more favorable
jurisdictions. Several crypto startups announced moves to Switzerland, Singapore, and Dubai. Critics argue
this approach forces innovation overseas rather than establishing sensible U.S. frameworks.

Retail investors bore significant losses. Surveys indicate 75% of crypto holders are underwater on
investments. Social media showed emotional testimonials from people who invested life savings. Financial
advisors field calls from panicked clients seeking to exit positions.

Skeptics declared vindication. Economist Peter Schiff, long-time crypto critic, tweeted that "Bitcoin is
going to zero." Traditionalists argue that cryptocurrency never had fundamental value, merely speculative
demand.

Crypto proponents counter that fundamental technology remains sound. They view the crash as healthy market
correction eliminating weak players and scams. Long-term believers argue that clear regulations, once
established, will enable legitimate adoption.

As markets opened Friday, volatility continued. Bitcoin traded between $18,500-$21,000 in a single session.
Liquidations exceeded $4 billion across leveraged positions. Analysts predict months of uncertainty as
regulatory frameworks crystallize and market participants assess implications.""",
        length=ArticleLength.LONG,
        word_count=830,
        category="finance"
    ))

    # ========================================================================
    # VERY LONG ARTICLES (1500+ words) - 2 articles
    # ========================================================================

    articles.append(TestArticle(
        id="very_long_geopolitics_1",
        title="The New Cold War: U.S.-China Technology Competition Reshapes Global Order",
        content="""The intensifying technological rivalry between the United States and China has evolved
into the defining geopolitical struggle of the 21st century, fundamentally reshaping global alliances,
trade patterns, and the future of innovation. What began as trade disputes over tariffs and intellectual
property has transformed into comprehensive competition across semiconductors, artificial intelligence,
quantum computing, biotechnology, and space exploration.

This new cold war differs fundamentally from its 20th-century predecessor. Rather than military confrontation
and ideological warfare, the current rivalry centers on technological supremacy and economic leverage. The
outcome will determine which nation's technological standards, governance models, and economic systems
dominate the global economy for decades to come.

### Semiconductor Battleground

The semiconductor industry sits at the conflict's epicenter. Modern advanced chips, manufactured at
nanometer scales, power everything from smartphones to weapons systems to AI models. Control over chip
production equates to strategic advantage in the digital age.

Taiwan Semiconductor Manufacturing Company (TSMC) holds the most advanced chip manufacturing capabilities
worldwide. Its position in Taiwan creates profound geopolitical vulnerability. If China gained control of
Taiwan and TSMC's technology, it would achieve semiconductor dominance overnight. This scenario keeps
Pentagon strategists awake at night.

The U.S. response has been multifaceted. Export controls prohibit selling advanced chipmaking equipment to
China. The CHIPS Act provides $52 billion to rebuild American semiconductor manufacturing. However,
recreating the complex supply chains and technical expertise that migrated to Asia over 30 years requires
massive investment and time.

China faces a fundamental dilemma. Despite enormous investment, Chinese chipmakers lag 5-7 years behind
TSMC and Samsung in manufacturing technology. SMIC, China's most advanced chipmaker, achieved 7nm production
but with low yields and without access to extreme ultraviolet (EUV) lithography machines that enable the
next generation of chips.

Chinese President Xi Jinping identified "technological self-sufficiency" as a national priority. China has
poured over $150 billion into semiconductor development through various state funds. Progress has been made
in mature node chips (28nm and above) used in automotive and industrial applications. However, leading-edge
chips for AI and high-performance computing remain out of reach without Western equipment.

### Artificial Intelligence Race

AI development represents perhaps the most consequential technology competition. The nation that achieves
decisive AI advantages could revolutionize military capabilities, economic productivity, and social control.
Both superpowers recognize AI's transformative potential.

The United States maintains leadership in AI research and development. American tech giants—Google, Microsoft,
Meta, Amazon, and OpenAI—have created the most advanced AI models. U.S. universities produce cutting-edge AI
research. Nvidia's GPUs, essential for training large AI models, remain American-controlled.

However, China is closing the gap rapidly. Chinese AI companies including Baidu, Alibaba, Tencent, and
ByteDance invest billions in AI research. China's advantages include massive datasets from its 1.4 billion
population, fewer privacy restrictions on data collection, and strong government support coordinating
research efforts.

Recent U.S. export controls target AI chips specifically. Nvidia cannot sell its H100 and A100 GPUs to
Chinese customers, intending to slow China's AI development. Nvidia responded by creating special "China
versions" with reduced capabilities, though Washington has moved to block these as well.

The AI competition extends to standards and governance. The U.S. promotes democratic AI frameworks
emphasizing transparency, accountability, and human rights. China advocates for "AI sovereignty," allowing
nations to develop AI according to their political systems and values. This philosophical divide reflects
deeper conflicts over technology governance.

### Space: The Ultimate High Ground

Space has emerged as another critical domain. China's space program has achieved remarkable progress: lunar
sample returns, Mars rover operations, and construction of the Tiangong space station. China plans crewed
lunar missions by 2030, potentially beating America's return to the Moon.

The United States maintains advantages in space technology, with SpaceX revolutionizing launch capabilities
through reusable rockets. NASA's Artemis program aims to establish permanent lunar presence. U.S. military
space assets provide critical intelligence, navigation, and communications capabilities.

However, China has demonstrated anti-satellite weapons and cyber capabilities that could disrupt U.S. space
operations. The vulnerability of satellites to attack creates mutual deterrence dynamics. Both nations are
developing space-based weapons while publicly advocating for peaceful space cooperation.

Commercial space adds another layer. SpaceX's Starlink constellation of internet satellites could provide
global connectivity independent of ground infrastructure. China is building competing constellations. Control
over space-based internet could become as strategically important as undersea fiber optic cables.

### Economic Decoupling

The technology competition drives economic decoupling. Supply chains that evolved over decades for efficiency
are being restructured around security considerations. This "friend-shoring" or "de-risking" strategy aims to
reduce dependence on China while maintaining some economic ties.

American companies face difficult choices. China represents a massive market—too large to abandon. Yet
staying requires technology transfer, data sharing, and compliance with Chinese regulations. Many companies
are adopting parallel strategies: maintaining Chinese operations while building alternative supply chains.

European nations are caught in the middle. They depend on both U.S. security guarantees and Chinese trade.
The EU tries to chart a middle course, maintaining economic ties with China while aligning with U.S. on
security issues. This balancing act becomes increasingly difficult as Washington demands clear alignment.

Developing nations face stark choices. Chinese Belt and Road Initiative investments provide needed
infrastructure but create debt dependencies. U.S. alternatives remain limited and often come with political
conditions. Many countries attempt to play both sides, accepting Chinese investment while maintaining U.S.
security partnerships.

### Standards and Governance

Technical standards may be the competition's most consequential battleground. Standards determine which
technologies succeed globally. 5G provides a case study: Huawei's leadership in 5G technology and standard-
setting positioned it to dominate telecommunications infrastructure worldwide until U.S. pressure convinced
many nations to ban Huawei equipment.

China is learning lessons. It now actively participates in international standard-setting bodies, promoting
Chinese-developed technologies. In 6G research, China publishes more patents than any other nation. If 6G
standards reflect Chinese technology, it would represent a strategic shift in telecommunications.

Data governance presents another divide. China requires data on Chinese citizens remain in China, subject to
government access. The EU's GDPR emphasizes privacy rights. The U.S. takes a market-driven approach with
sectoral regulations. These incompatible frameworks complicate global data flows.

### Military Implications

While direct military conflict remains unlikely given mutual nuclear deterrence, the technology competition
has profound military implications. Advanced chips enable precision weapons, AI improves targeting and
decision-making, and space systems provide critical military infrastructure.

Pentagon officials warn that China is modernizing its military at unprecedented pace. Hypersonic missiles,
advanced fighters, aircraft carriers, and anti-ship weapons aim to deny U.S. military access to the Western
Pacific. If China achieves regional military dominance, it could alter alliance structures and trade routes.

U.S. military modernization efforts face challenges. The Pentagon struggles to adopt commercial AI technology
due to bureaucratic processes. Defense contractors cannot match the pace of commercial tech innovation.
Meanwhile, China's military-civil fusion strategy rapidly transfers civilian AI and technology advances to
military applications.

### The Taiwan Factor

Taiwan remains the most dangerous flashpoint. Its semiconductor industry gives Taiwan strategic importance
beyond its geographic position. Some analysts argue that Taiwan's "silicon shield"—its irreplaceable role in
global chip production—deters Chinese military action because invasion would destroy TSMC's fabs and
devastate the global economy.

However, as China develops semiconductor capabilities and alternatives emerge, the silicon shield may weaken.
This creates a potential window of vulnerability where Taiwan remains strategically valuable to the U.S. but
China calculates it can survive without TSMC's chips.

### Future Trajectories

The technology competition will intensify over the coming decade. Several scenarios appear possible:

**Managed Competition**: Both nations establish guardrails preventing escalation while competing intensely in
specific domains. This requires mature diplomacy and mutual recognition of risks.

**Accelerated Decoupling**: Economic and technological ties continue unraveling, creating parallel systems.
The world splits into U.S.- and China-aligned technology spheres with limited interoperability.

**Crisis and Confrontation**: A Taiwan conflict, AI arms race, or space incident triggers direct confrontation
with catastrophic consequences for global economy and security.

**Technological Breakthrough**: One nation achieves decisive advantage in quantum computing, AI, or another
transformative technology, shifting the balance dramatically.

The stakes are immense. This competition will determine technological leadership, economic prosperity, and
geopolitical influence for the remainder of the century. Unlike the Cold War, which ended with one system's
collapse, this rivalry may persist indefinitely with both superpowers remaining powerful and determined.

For smaller nations, the competition creates both opportunities and risks. They can leverage competition to
attract investment and technology. However, they must also navigate between superpowers demanding alignment,
a delicate and dangerous position.

As this new cold war unfolds, one certainty remains: technology has become the ultimate geopolitical weapon,
and the nations that master it will shape the world's future.""",
        length=ArticleLength.VERY_LONG,
        word_count=1520,
        category="geopolitics"
    ))

    articles.append(TestArticle(
        id="very_long_mixed_1",
        title="The Global Energy Transition: Progress, Setbacks, and the Path to Net Zero",
        content="""The global transition from fossil fuels to renewable energy has reached a critical
juncture. After decades of gradual progress, renewable energy deployment has accelerated dramatically,
driven by technological advances, cost reductions, and climate urgency. Yet despite unprecedented renewable
energy additions, fossil fuel consumption continues rising in absolute terms, and greenhouse gas emissions
remain stubbornly high. The path to net-zero emissions by 2050 requires transformational changes across
energy systems, industrial processes, transportation, and agriculture.

### Renewable Energy Revolution

Solar and wind power have experienced remarkable cost declines over the past decade. Solar photovoltaic costs
fell 89% since 2010, while onshore wind costs dropped 70%. Renewable energy is now cheaper than fossil fuels
in most markets. This economic transformation has accelerated deployment far beyond climate policy mandates.

In 2024, the world added 440 gigawatts of renewable electricity capacity, surpassing all previous records.
Solar accounted for 60% of additions, wind 35%, and other renewables 5%. China led globally with 180 GW of
new capacity, followed by the United States (65 GW), India (42 GW), and the European Union (50 GW combined).

However, electricity represents only 20% of global energy consumption. Transportation fuels, industrial heat,
and chemical feedstocks remain predominantly fossil-based. Electrification of these sectors proceeds slowly
due to technical challenges and infrastructure requirements.

### The Storage Challenge

Renewable energy's intermittency creates grid stability challenges. Solar generates only during daylight,
wind fluctuates with weather patterns. Managing a grid with 80%+ renewable penetration requires massive
energy storage to balance supply and demand.

Battery storage capacity is growing exponentially. Lithium-ion battery costs have fallen 95% since 2010,
enabling grid-scale storage deployment. In 2024, global battery storage installations reached 85 GWh,
triple 2023 levels. Tesla, CATL, BYD, and LG Energy Solution dominate this market.

Yet even with rapid growth, battery storage remains insufficient for multi-day or seasonal balancing.
Emerging technologies like hydrogen storage, compressed air energy storage (CAES), and flow batteries may
address longer-duration needs. However, these technologies remain expensive and unproven at scale.

Nuclear power advocates argue that nuclear energy provides reliable carbon-free baseload power that renewables
cannot match. Several countries, including France, South Korea, and increasingly the U.S., are expanding
nuclear capacity. Small modular reactors (SMRs) promise lower costs and faster deployment than traditional
large reactors, though commercial viability remains unproven.

### Transportation Electrification

Electric vehicles represent the energy transition's most visible manifestation. Global EV sales reached 18
million in 2024, 22% of all new car sales. Norway leads with 91% EV share, followed by Iceland (72%), Sweden
(54%), and China (38%). The U.S. lags at 12% despite recent growth.

China dominates EV manufacturing, producing 60% of global EVs and controlling 75% of battery production.
BYD overtook Tesla as the world's largest EV manufacturer in 2024. This creates geopolitical dependencies
that concern Western policymakers.

However, passenger vehicles represent only 45% of transportation emissions. Heavy trucks, shipping, and
aviation prove harder to electrify due to weight and range constraints. Hydrogen fuel cells, sustainable
aviation fuels, and synthetic fuels may address these sectors, but costs remain prohibitively high.

Maritime shipping, responsible for 3% of global emissions, faces particular challenges. The International
Maritime Organization set a net-zero target for 2050, but pathway remains unclear. Ammonia and methanol
fuels show promise but require new bunkering infrastructure and engine retrofits costing billions.

Aviation confronts similar obstacles. Electric aircraft work for short regional flights but cannot power
long-haul routes requiring high energy density. Sustainable aviation fuels (SAF) from biomass or synthetic
sources could reduce emissions but currently cost 3-5x conventional jet fuel and production remains limited.

### Industrial Decarbonization

Heavy industry—steel, cement, chemicals, and refining—accounts for 30% of global emissions. These sectors
require high-temperature heat that electricity cannot easily provide. Hydrogen, particularly green hydrogen
produced from renewable electricity, could replace fossil fuels in industrial processes.

However, green hydrogen remains expensive. Current production costs of $5-7 per kilogram exceed fossil-based
hydrogen at $1-2/kg. Scaling up requires massive renewable electricity capacity dedicated to hydrogen
production, competing with direct electricity uses.

Steel industry transformation exemplifies the challenge. Traditional blast furnaces use coal as both heat
source and chemical reducing agent. Direct reduced iron (DRI) using hydrogen could eliminate emissions but
requires technology investments and hydrogen supplies. Companies like ArcelorMittal and SSAB pilot hydrogen-
based steel production, but commercial deployment remains years away.

Cement production presents a unique challenge: half of emissions come from chemical reactions in clinker
production, not energy use. Carbon capture and storage (CCS) may be the only solution for cement, yet CCS
remains expensive and energy-intensive.

### Financial Flows

The International Energy Agency estimates $4 trillion annual investment is required for net-zero by 2050.
Current clean energy investment reached $1.8 trillion in 2024, up from $1.4 trillion in 2023. However,
investment must more than double and sustain those levels for decades.

Developed nations have committed climate finance to help developing countries transition. The 2009 Copenhagen
Accord promised $100 billion annually by 2020, achieved only in 2022. COP30 negotiations aim to increase this
to $500 billion annually, but rich nations resist binding commitments.

Private capital is shifting. ESG (Environmental, Social, Governance) investment reached $35 trillion in assets
under management. Banks increasingly refuse financing for coal projects. Insurance companies limit coverage
for fossil fuel infrastructure. These market forces accelerate the transition even without policy mandates.

However, fossil fuel companies remain highly profitable and politically powerful. ExxonMobil, Chevron, Shell,
and Saudi Aramco earned record profits in 2024 amid high energy prices. These companies are investing in clean
energy but at a fraction of their fossil fuel budgets. They argue that abrupt transition creates energy
security risks and economic disruption.

### Geopolitical Realignment

The energy transition reshapes global power dynamics. Historically, energy meant oil, and oil meant Middle
East influence. Renewable energy disperses power, as sun and wind exist everywhere. Countries with vast solar
resources (North Africa, Australia) or wind resources (North Sea, Patagonia) could become energy exporters.

Critical minerals for batteries and renewables create new dependencies. Lithium, cobalt, nickel, rare earths,
and copper are concentrated in few countries. China controls 60-80% of processing for most critical minerals.
This "green energy OPEC" concerns Western nations seeking supply chain security.

Resource-rich nations like Australia, Chile, and Democratic Republic of Congo could become critical mineral
exporters. However, mining these materials raises environmental and human rights concerns. Lithium extraction
depletes water resources in Chile's Atacama Desert. Cobalt mining in DRC involves child labor and unsafe
conditions.

Petrostates face existential challenges. Saudi Arabia, Russia, Venezuela, and others depend on oil revenues.
As demand peaks and eventually declines, these nations must diversify economies. Some, like UAE, invest
heavily in renewables. Others, like Russia, resist transition and may face economic collapse.

### Climate Policy and Politics

The Paris Agreement set a goal to limit warming to 1.5°C above pre-industrial levels. Current policies put
the world on track for 2.5-3°C warming by 2100. Closing this gap requires immediate, aggressive action.

Carbon pricing could accelerate transition by making fossil fuels more expensive. The EU's Emissions Trading
System covers 40% of EU emissions. Carbon prices reached €100 per ton in 2024, making fossil fuels less
competitive. However, competitiveness concerns led to border adjustment mechanisms taxing imports from
countries without carbon pricing.

The U.S. lacks comprehensive carbon pricing, relying instead on subsidies and regulations. The Inflation
Reduction Act provides $369 billion in clean energy incentives. Republicans oppose carbon taxes but support
subsidies for domestic manufacturing, creating bipartisan support for certain clean energy investments.

China, the world's largest emitter at 30% of global totals, committed to carbon neutrality by 2060. However,
China continues building coal plants to ensure energy security while simultaneously leading in renewable
deployment. This paradox reflects tensions between economic development and climate goals.

Developing nations argue that rich countries caused climate change and must bear primary responsibility for
solving it. They demand technology transfer, financial support, and recognition of their development rights.
This North-South divide complicates international climate negotiations.

### Adaptation and Resilience

Even with rapid mitigation, significant warming is unavoidable due to past emissions. Adaptation investments
in flood defenses, resilient infrastructure, drought-resistant agriculture, and early warning systems are
necessary.

Small island nations face existential threats from sea level rise. Countries like Maldives, Tuvalu, and
Kiribati may become uninhabitable by 2100. These nations demand compensation for "loss and damage" from
climate impacts. COP29 established a loss and damage fund, but wealthy nations committed only modest amounts.

Climate migration could involve hundreds of millions by mid-century. Rising seas, droughts, and extreme heat
will make some regions uninhabitable. This will create humanitarian crises and political tensions over borders
and refugees.

### Technological Wild Cards

Several emerging technologies could accelerate or complicate the transition:

**Nuclear Fusion**: If achieved commercially, fusion could provide unlimited clean energy. Major breakthroughs
in 2024 brought fusion closer to viability, but commercial deployment remains at least 15-20 years away.

**Carbon Capture and Storage**: Capturing CO2 directly from air or at emission sources could offset hard-to-
eliminate emissions. However, costs remain high ($600-1000/ton for direct air capture) and energy requirements
are substantial.

**Advanced Batteries**: Solid-state batteries promise higher energy density and safety. Breakthroughs could
accelerate EV adoption and grid storage.

**Synthetic Fuels**: Combining captured CO2 with green hydrogen creates synthetic hydrocarbons usable in
existing infrastructure. Costs currently prohibit large-scale deployment.

**Geoengineering**: Solar radiation management or ocean fertilization could theoretically offset warming but
carry enormous risks and ethical concerns.

### The Path Forward

Achieving net-zero by 2050 requires transformation unprecedented in human history. It demands replacing
infrastructure that took 150 years to build in just 25 years, while continuing economic development and
avoiding energy poverty.

Success requires coordinated action across multiple fronts: aggressive renewable deployment, electrification
of transportation and industry, development of clean hydrogen, carbon capture where necessary, protection of
forests and ecosystems, transformation of agriculture, and adaptation to unavoidable climate impacts.

The transition also presents enormous economic opportunities. Clean energy industries could create millions of
jobs. Nations that lead in clean technology manufacturing and deployment will gain competitive advantages. The
global clean energy market will reach trillions of dollars annually.

Yet the path is fraught with challenges: political resistance from fossil fuel interests, geopolitical tensions
over critical minerals, need for unprecedented investment, concerns about energy security during transition,
and uneven burden between developed and developing nations.

Time is running short. Each year of delayed action makes the challenge harder and impacts more severe. The
decisions made this decade will determine whether humanity can build a sustainable energy system or face
catastrophic climate change. The energy transition is no longer a distant aspiration—it is an urgent necessity
that will define the 21st century.""",
        length=ArticleLength.VERY_LONG,
        word_count=1890,
        category="mixed"
    ))

    return articles


# ============================================================================
# TOKEN CALCULATION FUNCTIONS
# ============================================================================

def estimate_tokens(text: str) -> int:
    """Rough token estimation: 1 token ≈ 0.75 words."""
    words = len(text.split())
    return int(words * 1.3)


def calculate_current_approach_tokens(article: TestArticle, num_specialists: int = 6) -> Tuple[int, int, float]:
    """
    Calculate tokens for CURRENT approach (6 separate specialist calls).

    Returns:
        (total_input_tokens, total_output_tokens, total_cost_usd)
    """
    # Each specialist gets:
    # - Full article content
    # - Prompt overhead (~200 tokens)
    # - Tier1 data summary (~100 tokens)

    content_tokens = estimate_tokens(article.content)
    prompt_overhead = 200
    tier1_summary = 100

    tokens_per_specialist = content_tokens + prompt_overhead + tier1_summary
    total_input = tokens_per_specialist * num_specialists
    total_output = 150 * num_specialists  # Each specialist returns ~150 tokens

    # Cost calculation (GPT-4o-mini prices)
    input_cost = total_input * 0.15 / 1_000_000
    output_cost = total_output * 0.60 / 1_000_000
    total_cost = input_cost + output_cost

    return total_input, total_output, total_cost


def calculate_hybrid_approach_tokens(article: TestArticle, num_specialists: int = 6) -> Tuple[int, int, float]:
    """
    Calculate tokens for HYBRID approach (1 combined call for all specialists).

    Returns:
        (total_input_tokens, total_output_tokens, total_cost_usd)
    """
    # ONE combined call with:
    # - Full article content (ONCE)
    # - Combined prompt overhead (~400 tokens - longer but only once)
    # - Tier1 data summary (~100 tokens)

    content_tokens = estimate_tokens(article.content)
    combined_prompt_overhead = 400  # Longer prompt but only once
    tier1_summary = 100

    total_input = content_tokens + combined_prompt_overhead + tier1_summary
    total_output = 180 * num_specialists  # Slightly longer per specialist in combined format

    # Cost calculation
    input_cost = total_input * 0.15 / 1_000_000
    output_cost = total_output * 0.60 / 1_000_000
    total_cost = input_cost + output_cost

    return total_input, total_output, total_cost


# ============================================================================
# MAIN TEST FUNCTION
# ============================================================================

def run_hybrid_test():
    """Run comprehensive test with 20 articles comparing CURRENT vs HYBRID."""

    print("=" * 100)
    print("HYBRID APPROACH TEST (ANSATZ 3)")
    print("Comparing CURRENT (6 separate calls) vs HYBRID (1 combined call)")
    print("=" * 100)
    print()

    articles = generate_test_articles()
    results = []

    # Aggregate statistics
    total_current_input = 0
    total_current_output = 0
    total_current_cost = 0.0

    total_hybrid_input = 0
    total_hybrid_output = 0
    total_hybrid_cost = 0.0

    # By article length
    stats_by_length = {length: {"count": 0, "current_input": 0, "hybrid_input": 0, "savings": 0}
                       for length in ArticleLength}

    print(f"{'ID':<25} {'Length':<15} {'Words':<8} {'Current':<15} {'Hybrid':<15} {'Savings':<15} {'%':<8}")
    print("-" * 100)

    for article in articles:
        # Calculate for both approaches
        current_input, current_output, current_cost = calculate_current_approach_tokens(article)
        hybrid_input, hybrid_output, hybrid_cost = calculate_hybrid_approach_tokens(article)

        # Calculate savings
        token_savings = current_input - hybrid_input
        cost_savings = current_cost - hybrid_cost
        reduction_pct = (token_savings / current_input) * 100 if current_input > 0 else 0

        # Print row
        print(f"{article.id:<25} {article.length.value:<15} {article.word_count:<8} "
              f"{current_input:<15,} {hybrid_input:<15,} {token_savings:<15,} {reduction_pct:<8.1f}%")

        # Accumulate totals
        total_current_input += current_input
        total_current_output += current_output
        total_current_cost += current_cost

        total_hybrid_input += hybrid_input
        total_hybrid_output += hybrid_output
        total_hybrid_cost += hybrid_cost

        # Track by length
        stats_by_length[article.length]["count"] += 1
        stats_by_length[article.length]["current_input"] += current_input
        stats_by_length[article.length]["hybrid_input"] += hybrid_input
        stats_by_length[article.length]["savings"] += token_savings

        results.append({
            "id": article.id,
            "length": article.length.value,
            "word_count": article.word_count,
            "current_input": current_input,
            "hybrid_input": hybrid_input,
            "token_savings": token_savings,
            "reduction_pct": reduction_pct,
            "current_cost": current_cost,
            "hybrid_cost": hybrid_cost,
            "cost_savings": cost_savings
        })

    # Summary
    total_token_savings = total_current_input - total_hybrid_input
    total_reduction_pct = (total_token_savings / total_current_input) * 100
    total_cost_savings = total_current_cost - total_hybrid_cost
    total_cost_reduction_pct = (total_cost_savings / total_current_cost) * 100

    print("-" * 100)
    print(f"{'TOTAL':<25} {'':<15} {'':<8} "
          f"{total_current_input:<15,} {total_hybrid_input:<15,} {total_token_savings:<15,} {total_reduction_pct:<8.1f}%")
    print()

    # Detailed summary
    print("=" * 100)
    print("📊 SUMMARY: ALL 20 ARTICLES")
    print("=" * 100)
    print()

    print("📈 TOKEN USAGE:")
    print(f"  Current Total Input:   {total_current_input:,} tokens")
    print(f"  Hybrid Total Input:    {total_hybrid_input:,} tokens")
    print(f"  Token Savings:         {total_token_savings:,} tokens ({total_reduction_pct:.1f}% reduction)")
    print()

    print("💰 COST:")
    print(f"  Current Total Cost:    ${total_current_cost:.4f}")
    print(f"  Hybrid Total Cost:     ${total_hybrid_cost:.4f}")
    print(f"  Cost Savings:          ${total_cost_savings:.4f} ({total_cost_reduction_pct:.1f}% reduction)")
    print()

    # Breakdown by article length
    print("📏 BREAKDOWN BY ARTICLE LENGTH:")
    print(f"{'Length':<15} {'Count':<8} {'Avg Current':<15} {'Avg Hybrid':<15} {'Avg Savings':<15} {'% Reduction':<12}")
    print("-" * 80)

    for length in ArticleLength:
        stats = stats_by_length[length]
        if stats["count"] > 0:
            avg_current = stats["current_input"] / stats["count"]
            avg_hybrid = stats["hybrid_input"] / stats["count"]
            avg_savings = stats["savings"] / stats["count"]
            avg_reduction = (avg_savings / avg_current) * 100 if avg_current > 0 else 0

            print(f"{length.value:<15} {stats['count']:<8} {avg_current:<15,.0f} {avg_hybrid:<15,.0f} "
                  f"{avg_savings:<15,.0f} {avg_reduction:<12.1f}%")
    print()

    # Extrapolation
    avg_cost_per_article_current = total_current_cost / len(articles)
    avg_cost_per_article_hybrid = total_hybrid_cost / len(articles)

    print("💡 EXTRAPOLATION (10,000 articles/month):")
    print(f"  Current Cost:      ${avg_cost_per_article_current * 10_000:.2f}/month "
          f"(${avg_cost_per_article_current * 10_000 * 12:.2f}/year)")
    print(f"  Hybrid Cost:       ${avg_cost_per_article_hybrid * 10_000:.2f}/month "
          f"(${avg_cost_per_article_hybrid * 10_000 * 12:.2f}/year)")
    print(f"  Monthly Savings:   ${(avg_cost_per_article_current - avg_cost_per_article_hybrid) * 10_000:.2f}")
    print(f"  Yearly Savings:    ${(avg_cost_per_article_current - avg_cost_per_article_hybrid) * 10_000 * 12:.2f}")
    print()

    print("=" * 100)
    print("✅ TEST COMPLETE")
    print("=" * 100)

    return results


if __name__ == "__main__":
    run_hybrid_test()
