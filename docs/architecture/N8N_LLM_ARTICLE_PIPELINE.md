# n8n + LLM Article Generation Pipeline

> **Erstellt:** 2025-12-24
> **Status:** DESIGN READY - Implementierung kann beginnen
> **Anforderung:** Kurze geschriebene Artikel aus News-Daten via OpenAI + Telegram Publishing

---

## 1. Executive Summary

**Ziel:** Automatische Artikel-Generierung aus Intelligence-Daten mit LLM und Publishing via Telegram.

**Vorhandene Infrastruktur:**
| Komponente | Status | Details |
|------------|--------|---------|
| n8n | ✅ Aktiv | Port 5678, healthy |
| Telegram Credentials | ✅ Vorhanden | "Telegram News Bot" (koRnmAXRHItX5Flf) |
| Intelligence Service | ✅ Funktional | Clusters + Events mit Entities |
| OpenAI Node | ✅ Verfügbar | `@n8n/n8n-nodes-langchain.openAi` |
| Bestehender Workflow | ✅ Template | "News Alerts V3 - Rich Analysis" |

**Geschätzter Aufwand:** 2-4 Stunden für MVP

---

## 2. Vorhandene Ressourcen

### 2.1 Bestehender Telegram Workflow

**Workflow:** `News Alerts V3 - Rich Analysis` (ID: 9Q88Yov7ztZBIhnk)

```
Stündlicher Trigger
    ↓
PostgreSQL Query (Top Analysierte News)
    ↓
Code Node (Nachricht formatieren)
    ↓
IF (News vorhanden?)
    ↓
Telegram senden (Chat ID: 1220225029)
```

**Telegram Credentials:**
- Name: "Telegram News Bot"
- ID: `koRnmAXRHItX5Flf`
- Chat ID: `1220225029`

### 2.2 Intelligence Service Daten

**Verfügbare Endpoints:**

```bash
# Top-Cluster nach Risk Score
GET http://localhost:8118/api/v1/intelligence/clusters?sort_by=risk_score&limit=10

# Events für einen Cluster
GET http://localhost:8118/api/v1/intelligence/clusters/{cluster_id}/events?limit=5

# Globale Übersicht
GET http://localhost:8118/api/v1/intelligence/overview
```

**Beispiel-Daten (echt):**
```json
{
  "name": "Syria, Isis, U.S. Troops",
  "risk_score": 100.0,
  "keywords": ["Syria", "ISIS", "U.S. troops"],
  "events": [
    {
      "title": "US strikes at Isis fighters in Syria after 3 Americans killed",
      "source": "SCMP",
      "sentiment": -0.9402,
      "entities": [
        {"name": "Pete Hegseth", "type": "PERSON"},
        {"name": "Syria", "type": "LOCATION"}
      ]
    }
  ]
}
```

### 2.3 OpenAI Node Konfiguration

**Node Type:** `@n8n/n8n-nodes-langchain.openAi`
**Version:** 2.1

**Unterstützte Modelle:**
- `gpt-4o-mini` (empfohlen für MVP - kostengünstig)
- `gpt-4o` (höhere Qualität)
- `o3-mini` (neueste Generation - erwähnte "5.2 Modelle")

**Beispiel-Konfiguration:**
```json
{
  "modelId": {
    "__rl": true,
    "mode": "list",
    "value": "gpt-4o-mini",
    "cachedResultName": "GPT-4O-MINI"
  },
  "messages": {
    "values": [
      {
        "role": "system",
        "content": "Du bist ein Nachrichtenanalyst..."
      },
      {
        "content": "={{ $json.events_text }}"
      }
    ]
  }
}
```

---

## 3. Architektur

### 3.1 Workflow-Design

```
┌─────────────────────────────────────────────────────────────────┐
│              N8N LLM ARTICLE GENERATION PIPELINE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                                               │
│  │   Schedule   │  Alle 6h (oder on-demand via Webhook)         │
│  │   Trigger    │                                               │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │   HTTP Req   │  GET /intelligence/clusters?topic=geo         │
│  │  Intelligence│  (oder finance, security, tech)               │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │  Code Node   │  Filter & Format für LLM                      │
│  │   Prepare    │  - Top 5 Cluster extrahieren                  │
│  │    Data      │  - Events aggregieren                         │
│  └──────┬───────┘  - Quellen sammeln                            │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │   OpenAI     │  gpt-4o-mini                                  │
│  │   Generate   │  System Prompt: Nachrichtenanalyst            │
│  │   Article    │  Output: Kurzer Artikel (max 1000 Zeichen)    │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │  Code Node   │  - Telegram Formatierung                      │
│  │   Format     │  - Quellen anhängen (nur Namen)               │
│  │   Output     │  - Emoji hinzufügen                           │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │  Telegram    │  Chat ID: 1220225029                          │
│  │    Send      │  Parse Mode: Markdown                         │
│  └──────────────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Topic-basierte Varianten

| Topic | Filter Keywords | Emoji | Beschreibung |
|-------|-----------------|-------|--------------|
| `geo` | Syria, Ukraine, China, NATO, UN... | 🌍 | Geopolitik & Konflikte |
| `finance` | Market, Stock, Bitcoin, Fed, ECB... | 💰 | Finanz & Märkte |
| `tech` | AI, Cyber, Software, Startup... | 💻 | Technologie |
| `security` | Hack, Breach, Vulnerability... | 🔒 | Cybersecurity |

---

## 4. Implementierung

### 4.1 OpenAI Credentials anlegen

```bash
# n8n UI → Settings → Credentials → Add Credential
# Type: OpenAI API
# API Key: <OpenAI API Key>
# Name: "OpenAI - Article Generator"
```

### 4.2 Workflow Nodes

#### Node 1: Schedule Trigger

```json
{
  "type": "n8n-nodes-base.scheduleTrigger",
  "parameters": {
    "rule": {
      "interval": [
        {
          "field": "hours",
          "hoursInterval": 6
        }
      ]
    }
  }
}
```

#### Node 2: Fetch Intelligence Data

```json
{
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "GET",
    "url": "http://news-intelligence-service:8118/api/v1/intelligence/clusters",
    "qs": {
      "sort_by": "risk_score",
      "limit": "20"
    }
  }
}
```

#### Node 3: Filter & Prepare (Code Node)

```javascript
// Filter geopolitische Cluster und bereite Daten für LLM vor
const GEOPOLITIK_KEYWORDS = [
  "Syria", "Ukraine", "Russia", "China", "Taiwan", "Iran",
  "Israel", "Palestine", "North Korea", "Myanmar", "Afghanistan",
  "NATO", "UN", "sanctions", "troops", "military", "war",
  "conflict", "diplomacy", "treaty", "nuclear"
];

const clusters = $input.first().json.clusters || [];

// Filter geopolitische Cluster
const geoClusters = clusters.filter(cluster => {
  const name = cluster.name || "";
  const keywords = cluster.keywords || [];
  return GEOPOLITIK_KEYWORDS.some(kw =>
    name.toLowerCase().includes(kw.toLowerCase()) ||
    keywords.some(k => k.toLowerCase().includes(kw.toLowerCase()))
  );
}).slice(0, 5);

if (geoClusters.length === 0) {
  return [{ json: { skip: true, reason: "No geopolitical news" } }];
}

// Format für LLM
const eventsText = geoClusters.map(c => {
  const events = c.events?.slice(0, 2) || [];
  return `**${c.name}** (Risk: ${c.risk_score})\n` +
    events.map(e => `- ${e.title} (${e.source})`).join('\n');
}).join('\n\n');

// Quellen sammeln
const sources = [...new Set(
  geoClusters.flatMap(c =>
    (c.events || []).map(e => e.source)
  )
)].filter(Boolean).slice(0, 5);

return [{
  json: {
    skip: false,
    events_text: eventsText,
    sources: sources,
    cluster_count: geoClusters.length,
    topic: "Geopolitik"
  }
}];
```

#### Node 4: OpenAI Generate Article

```json
{
  "type": "@n8n/n8n-nodes-langchain.openAi",
  "typeVersion": 2.1,
  "parameters": {
    "resource": "text",
    "operation": "message",
    "modelId": {
      "__rl": true,
      "mode": "list",
      "value": "gpt-4o-mini"
    },
    "messages": {
      "values": [
        {
          "role": "system",
          "content": "Du bist ein erfahrener Nachrichtenanalyst. Schreibe kurze, prägnante Artikel über aktuelle Ereignisse.\n\nREGELN:\n- Maximal 800 Zeichen\n- Sachlich und neutral\n- Keine Spekulationen\n- Wichtigste Fakten zuerst\n- Deutsche Sprache\n- Keine Links oder URLs\n- Keine Emojis im Text (werden separat hinzugefügt)"
        },
        {
          "role": "user",
          "content": "=Schreibe einen kurzen Überblicksartikel über diese aktuellen geopolitischen Ereignisse:\n\n{{ $json.events_text }}\n\nFasse die wichtigsten Entwicklungen zusammen."
        }
      ]
    },
    "options": {
      "maxTokens": 500,
      "temperature": 0.7
    }
  }
}
```

#### Node 5: Format for Telegram (Code Node)

```javascript
const article = $input.first().json.message?.content ||
                $input.first().json.content ||
                $input.first().json.text || "";

const preparedData = $node["Filter & Prepare"].json;
const sources = preparedData.sources || [];
const topic = preparedData.topic || "News";

// Topic Emoji mapping
const topicEmoji = {
  "Geopolitik": "🌍",
  "Finance": "💰",
  "Tech": "💻",
  "Security": "🔒"
};

const emoji = topicEmoji[topic] || "📰";

// Format für Telegram
let telegramMessage = `${emoji} *${topic.toUpperCase()} BRIEFING*\n`;
telegramMessage += `━━━━━━━━━━━━━━━━━━━━━\n\n`;
telegramMessage += article;
telegramMessage += `\n\n━━━━━━━━━━━━━━━━━━━━━\n`;
telegramMessage += `📰 *Quellen:* ${sources.join(", ")}\n`;
telegramMessage += `⏰ ${new Date().toLocaleString('de-DE', {timeZone: 'Europe/Berlin'})}`;

return [{
  json: {
    telegram_message: telegramMessage,
    article_length: article.length,
    sources_count: sources.length
  }
}];
```

#### Node 6: Send to Telegram

```json
{
  "type": "n8n-nodes-base.telegram",
  "parameters": {
    "chatId": "1220225029",
    "text": "={{ $json.telegram_message }}",
    "additionalFields": {
      "parse_mode": "Markdown",
      "disable_web_page_preview": true
    }
  },
  "credentials": {
    "telegramApi": {
      "id": "koRnmAXRHItX5Flf",
      "name": "Telegram News Bot"
    }
  }
}
```

---

## 5. Erweiterungen

### 5.1 Multi-Topic Workflow

```
Webhook Trigger (topic parameter)
    ↓
Switch Node (topic: geo/finance/tech/security)
    ↓
[Topic-spezifische Filter]
    ↓
OpenAI (topic-spezifischer Prompt)
    ↓
Telegram
```

### 5.2 Approval Workflow (Optional)

```
... LLM Generation ...
    ↓
Wait Node (1 hour timeout)
    ↓
Telegram (Preview an Admin)
    ↓
Webhook (Approve/Reject Buttons)
    ↓
IF Approved → Publish to Channel
```

### 5.3 Email Integration

```json
{
  "type": "n8n-nodes-base.emailSend",
  "parameters": {
    "fromEmail": "news@example.com",
    "toEmail": "={{ $json.subscriber_email }}",
    "subject": "=🌍 Geopolitik Briefing - {{ $now.format('dd.MM.yyyy') }}",
    "html": "={{ $json.html_article }}"
  }
}
```

---

## 6. Kosten-Schätzung

### OpenAI API Kosten (gpt-4o-mini)

| Metrik | Wert | Kosten |
|--------|------|--------|
| Input Tokens | ~500 pro Artikel | $0.00015 |
| Output Tokens | ~300 pro Artikel | $0.00060 |
| **Pro Artikel** | ~800 Tokens | **~$0.00075** |
| **Pro Tag (4x)** | ~3200 Tokens | **~$0.003** |
| **Pro Monat** | ~96000 Tokens | **~$0.09** |

**Fazit:** Extrem kostengünstig (~$0.10/Monat für 4 Artikel/Tag)

---

## 7. Beispiel-Output

**Telegram Message (simuliert):**

```
🌍 *GEOPOLITIK BRIEFING*
━━━━━━━━━━━━━━━━━━━━━

Die USA haben nach dem Tod von drei amerikanischen Soldaten
Vergeltungsschläge gegen ISIS-Stellungen in Syrien geflogen.
Verteidigungsminister Pete Hegseth kündigte weitere Maßnahmen an.

In Myanmar verschärft sich die humanitäre Krise, während die
Arakan Army weiter vorrückt. Die UN fordert einen sofortigen
Waffenstillstand.

An der afghanisch-pakistanischen Grenze steigen die Spannungen
nach diplomatischen Differenzen zwischen beiden Ländern.

━━━━━━━━━━━━━━━━━━━━━
📰 *Quellen:* SCMP, BBC, Reuters
⏰ 24.12.2025, 14:30:45
```

---

## 8. Implementierungs-Schritte

### Phase 1: MVP (2-4 Stunden)

1. [ ] OpenAI API Credentials in n8n anlegen
2. [ ] Neuen Workflow "Topic Briefing Generator" erstellen
3. [ ] Nodes wie oben beschrieben konfigurieren
4. [ ] Manuell testen (Execute Workflow)
5. [ ] Schedule aktivieren (alle 6h)

### Phase 2: Multi-Topic (1-2 Stunden)

1. [ ] Webhook Trigger hinzufügen
2. [ ] Switch Node für Topics
3. [ ] Topic-spezifische Prompts

### Phase 3: Production (2-4 Stunden)

1. [ ] Error Handling (Retry, Fallback)
2. [ ] Logging (Erfolgsrate, Token-Verbrauch)
3. [ ] Monitoring Dashboard

---

## 9. Referenzen

- [TOPIC_BRIEFING_SYSTEM.md](TOPIC_BRIEFING_SYSTEM.md) - Generalisiertes Topic System
- [GEOPOLITICAL_TWITTER_WORKFLOW_ANALYSIS.md](../analysis/GEOPOLITICAL_TWITTER_WORKFLOW_ANALYSIS.md) - Ursprüngliche Analyse
- [CLAUDE.n8n.md](../../CLAUDE.n8n.md) - n8n Development Guide
- Bestehender Workflow: "News Alerts V3 - Rich Analysis" (9Q88Yov7ztZBIhnk)

---

## Changelog

| Datum | Autor | Änderung |
|-------|-------|----------|
| 2025-12-24 | Claude | Initial Architecture Design |
