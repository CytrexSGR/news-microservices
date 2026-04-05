# Agent Service - Quick Start Guide

## 🚀 Schnellstart in 3 Schritten

### 1. Service überprüfen

```bash
# Agent Service Status prüfen
docker ps | grep agent-service

# Health Check
curl http://localhost:8110/health
```

**Erwartete Ausgabe:**
```json
{
  "status": "healthy",
  "service": "agent-service",
  "version": "1.0.0"
}
```

---

### 2. Terminal CLI nutzen (Empfohlen)

Das einfachste Interface für den Agent Service:

```bash
# Executable machen (einmalig)
chmod +x /home/cytrex/news-microservices/scripts/news-agent.sh

# Interaktiver Modus starten
./scripts/news-agent.sh

# Oder direkte Query
./scripts/news-agent.sh "Suche nach den neuesten KI-Artikeln"
```

**Features des CLI:**
- ✅ Automatisches Token Management
- ✅ Farbige Ausgabe
- ✅ Loading-Indikatoren
- ✅ Conversation History
- ✅ Interaktiver & Direct Mode

---

### 3. Beispiel-Queries

#### Einfache Suche
```bash
./scripts/news-agent.sh "Suche nach Artikeln über Künstliche Intelligenz"
```

#### Analyse & Report
```bash
./scripts/news-agent.sh "Finde die Top 5 KI-Artikel, analysiere ihre Stimmung und sende mir einen Bericht"
```

#### Themenrecherche
```bash
./scripts/news-agent.sh "Erstelle einen Überblick über Cybersecurity-Trends basierend auf den Artikeln der letzten 7 Tage"
```

---

## 📖 Verfügbare Tools

Der Agent kann folgende Tools nutzen:

| Tool | Beschreibung | Beispiel |
|------|--------------|----------|
| **search_articles** | Sucht Artikel in der Datenbank | "Suche nach KI-Artikeln" |
| **get_article_analysis** | Holt detaillierte Analysen | "Analysiere die Stimmung der gefundenen Artikel" |
| **send_report_email** | Versendet Report per Email | "Sende mir einen Bericht" |

---

## 💡 Beispiel-Workflows

### Workflow 1: Täglicher News-Brief

**Query:**
```
Suche die wichtigsten Tech-News der letzten 24 Stunden,
analysiere die Stimmung und erstelle einen Bericht mit den
Top 5 positiven und Top 5 negativen Artikeln. Sende mir den
Bericht per Email.
```

**Was der Agent tut:**
1. 🔍 Sucht nach Tech-Artikeln (letzten 24h)
2. 📊 Analysiert Sentiment aller Artikel
3. 📝 Erstellt strukturierten Report
4. 📧 Versendet Report an User-Email

---

### Workflow 2: Themen-Recherche

**Query:**
```
Finde alle Artikel über Blockchain aus den letzten 30 Tagen.
Extrahiere die wichtigsten Unternehmen und Produkte. Erstelle
eine Zusammenfassung der Haupttrends.
```

**Was der Agent tut:**
1. 🔍 Sucht Blockchain-Artikel (30 Tage)
2. 🏢 Extrahiert Entities (Unternehmen, Produkte)
3. 📈 Identifiziert Trends
4. 📄 Erstellt Zusammenfassung
5. 📧 Versendet Report

---

### Workflow 3: Konkurrenz-Monitoring

**Query:**
```
Suche nach Artikeln über OpenAI, Google AI und Anthropic.
Vergleiche die mediale Aufmerksamkeit und Stimmung. Erstelle
einen Vergleichsbericht.
```

**Was der Agent tut:**
1. 🔍 Sucht nach jedem Unternehmen
2. 📊 Analysiert Sentiment & Häufigkeit
3. 📉 Erstellt Vergleich
4. 📧 Versendet Bericht

---

## 🔧 Erweiterte Nutzung

### Conversation History anzeigen

```bash
# Letzte 10 Conversations
./scripts/news-agent.sh --history

# Letzte 50 Conversations
./scripts/news-agent.sh --history 50
```

### Specific Conversation Details

```bash
# Conversation ID aus History kopieren
./scripts/news-agent.sh --conversation <uuid>
```

### Custom Environment Variables

```bash
# Andere Server verwenden
export AGENT_URL="http://other-server:8110"
export AUTH_URL="http://other-server:8100"
export NEWS_AGENT_EMAIL="other@example.com"
export NEWS_AGENT_PASSWORD="password"

./scripts/news-agent.sh
```

---

## 🌐 Alternative Nutzung: cURL

Falls du das CLI-Script nicht nutzen möchtest:

### 1. Login & Token erhalten

```bash
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"andreas@test.com","password":"Aug2012#"}' \
  | jq -r '.access_token')

echo $TOKEN
```

### 2. Agent invoken

```bash
curl -X POST http://localhost:8110/api/v1/agent/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Suche nach KI-Artikeln und erstelle einen Bericht"
  }' | jq .
```

### 3. History abrufen

```bash
curl -X GET "http://localhost:8110/api/v1/agent/conversations?limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## 📊 Output verstehen

### Success Response

```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED",
  "result": "Report has been generated and sent to your email.",
  "tool_calls": [
    {
      "tool_name": "search_articles",
      "arguments": {"query": "KI", "limit": 10},
      "status": "SUCCESS",
      "duration_seconds": 0.342
    },
    {
      "tool_name": "send_report_email",
      "arguments": {"subject": "KI Report", "body": "..."},
      "status": "SUCCESS",
      "duration_seconds": 1.234
    }
  ],
  "execution_time_seconds": 12.45,
  "tokens_used": {
    "prompt_tokens": 1234,
    "completion_tokens": 456,
    "total_tokens": 1690
  }
}
```

### Status Werte

- **COMPLETED:** ✅ Workflow erfolgreich abgeschlossen
- **PROCESSING:** ⏳ Workflow läuft noch (sollte nicht vorkommen bei synchronen Calls)
- **FAILED:** ❌ Workflow fehlgeschlagen

### Token Kosten

**GPT-4o Pricing (Stand 2025):**
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens

**Beispiel-Kosten:**
- 1690 tokens ≈ $0.02 (2 Cent)
- Typischer Workflow: $0.02-0.05 (2-5 Cent)

---

## ❌ Troubleshooting

### "Service not reachable"

```bash
# Services prüfen
docker ps | grep -E "(agent|auth)-service"

# Services starten falls nötig
cd /home/cytrex/news-microservices
docker compose up -d agent-service auth-service
```

### "Authentication failed"

```bash
# Credentials prüfen
echo "Email: andreas@test.com"
echo "Password: Aug2012#"

# Auth Service testen
curl http://localhost:8100/health

# Login manuell testen
curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"andreas@test.com","password":"Aug2012#"}' | jq .
```

### "Tool execution failed"

```bash
# Abhängige Services prüfen
docker ps | grep -E "(search|analysis|notification)-service"

# Service-Logs checken
docker logs news-agent-service --tail 50
```

### "Max iterations reached"

**Ursache:** Query zu komplex für 10 Iterationen

**Lösung:**
1. Query vereinfachen
2. In kleinere Schritte aufteilen
3. Iteration-Limit erhöhen (in .env: `AGENT_MAX_ITERATIONS=20`)

---

## 🔒 Security Best Practices

### Token Management

- ✅ Token wird automatisch gecached (25 Minuten)
- ✅ Cache-File: `/tmp/.news-agent-token`
- ✅ Automatische Erneuerung bei Ablauf

### Credentials

**Produktions-Deployment:**
```bash
# NIEMALS Credentials in Scripts hardcoden!
# Nutze Environment Variables:

export NEWS_AGENT_EMAIL="user@company.com"
export NEWS_AGENT_PASSWORD="$(cat ~/.news-agent-password)"

./scripts/news-agent.sh
```

---

## 📚 Weitere Dokumentation

Für detaillierte Informationen siehe:

- **Service-Dokumentation:** `/docs/services/agent-service.md`
- **Claude Desktop Integration:** `/docs/guides/agent-service-claude-desktop.md`
- **API-Referenz:** `http://localhost:8110/docs` (Swagger UI)

---

## 🎯 Best Practices für Queries

### ✅ Gute Queries

```
"Suche nach KI-Artikeln der letzten Woche und erstelle einen Report"
→ Klar, spezifisch, machbar

"Finde die Top 5 positiven Artikel über Blockchain"
→ Konkrete Anzahl, klares Kriterium

"Analysiere die Stimmung aller Artikel über Tesla und sende mir die Ergebnisse"
→ Klare Aktion, klares Ziel
```

### ❌ Problematische Queries

```
"Mache etwas Cooles mit den Daten"
→ Zu vage, keine klare Anweisung

"Analysiere ALLE Artikel in der Datenbank"
→ Zu umfangreich, Timeout-Gefahr

"Hacke die NASA"
→ Unethisch, nicht möglich, wird abgelehnt
```

### 💡 Query-Tipps

1. **Sei spezifisch:** "Letzte Woche" statt "kürzlich"
2. **Limitiere Ergebnisse:** "Top 10" statt "alle"
3. **Klar formulieren:** Eine Aktion pro Satz
4. **Email-Reports:** Explizit "sende mir einen Bericht" erwähnen

---

## 🚀 Nächste Schritte

1. **Probiere das CLI aus:**
   ```bash
   ./scripts/news-agent.sh
   ```

2. **Experimentiere mit Queries:**
   - Starte einfach
   - Kombiniere Tools
   - Optimiere basierend auf Results

3. **Check die API Docs:**
   ```bash
   open http://localhost:8110/docs
   ```

4. **Integriere in deine Workflows:**
   - Cronjobs für tägliche Reports
   - Scripts für Monitoring
   - Automatisierte Recherche

---

## 💬 Feedback & Support

**Fragen?** Siehe vollständige Dokumentation in `/docs/services/agent-service.md`

**Bugs?** Check die Logs: `docker logs news-agent-service`

**Feature Requests?** Dokumentiere in `docs/roadmap.md`

---

**Happy Agenting! 🤖**
