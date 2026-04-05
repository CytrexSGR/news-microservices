# MCP Intelligence Server - Verification Checklist

## ⚠️ CRITICAL: Claude.ai Web vs Claude Desktop

**MCP Tools funktionieren NUR in Claude Desktop (App), NICHT in Claude.ai (Browser)!**

### Unterschiede

| Claude Desktop (App) ✅ | Claude.ai (Web) ❌ |
|--------------------------|-------------------|
| Windows-Applikation | Browser (chrome/edge/etc.) |
| Lila Icon in Taskleiste | claude.ai URL |
| MCP Tools verfügbar | Keine MCP Tools |
| Lokale Konfiguration | Server-seitig |
| Settings → MCP | Kein MCP-Menü |

---

## ✅ Verification Steps

### 1. Bestätige Claude Desktop Installation

**Check:**
```
C:\Users\andre\AppData\Local\Programs\Claude\
```

**Erwartetes Ergebnis:**
- `Claude.exe` vorhanden
- Version 1.0.1405 oder höher

**Falls NICHT vorhanden:**
- Download: https://claude.ai/download
- Installiere Claude Desktop für Windows

---

### 2. Öffne Claude Desktop (NICHT Browser!)

**So öffnen:**
1. Windows Start-Menü → "Claude"
2. ODER: Lila Icon in Taskleiste
3. ODER: Doppelklick auf `C:\Users\andre\AppData\Local\Programs\Claude\Claude.exe`

**Verify:**
- Fenster-Titel sollte sein: "Claude" (nicht "Claude.ai")
- URL-Leiste gibt es NICHT (ist kein Browser)

---

### 3. Prüfe MCP Server Status

**In Claude Desktop:**
1. Klicke oben links auf "☰" (Hamburger-Menü)
2. Wähle "Settings"
3. Scrolle zu "Developer" → "MCP Servers"

**Erwartetes Ergebnis:**
```
Lokale MCP-Server
├── mcp-intelligence
│   Status: running ✅
│   Befehl: C:\Program Files\nodejs\node.exe
│   Argumente: C:\mcp-intelligence-proxy.js
│   Umgebungsvariablen: MCP_SERVER_TYPE=stdio
```

**Falls "stopped" oder "error":**
- Klicke auf Server-Name → Logs anzeigen
- Kopiere Logs und sende sie mir

---

### 4. Erstelle NEUE Chat-Session in Claude Desktop

**WICHTIG:** MCP Tools werden beim Session-Start geladen!

**Steps:**
1. In Claude Desktop: Klicke auf "+ New Chat" (oben links)
2. Warte 2-3 Sekunden (Server-Verbindung)
3. Tippe exakt diese Frage:

```
Liste alle verfügbaren MCP Tools auf.
```

---

### 5. Erwartete Antwort

**Sollte anzeigen:**
```
Verfügbare MCP Tools:

**Analysis (3 Tools):**
1. analyze_article - Analyze article using content-analysis-v3 AI pipeline
2. extract_entities - Extract named entities from analyzed article
3. get_analysis_status - Get analysis status for article

**Entity (2 Tools):**
4. canonicalize_entity - Canonicalize entity to resolve duplicates
5. get_entity_clusters - Get entity clusters for given type

**Intelligence (6 Tools):**
6. detect_intelligence_patterns - Detect intelligence patterns in knowledge graph
7. analyze_graph_quality - Analyze knowledge graph data quality
8. get_event_clusters - Get event clusters from intelligence analysis
9. get_cluster_details - Get detailed information about specific event cluster
10. get_latest_events - Get latest intelligence events
11. get_intelligence_overview - Get intelligence overview dashboard

**Narrative (4 Tools):**
12. analyze_text_narrative - Analyze text for narrative frames and bias
13. get_narrative_frames - Get narrative frames from article analysis
14. get_bias_analysis - Get bias analysis across articles
15. get_narrative_overview - Get narrative analysis overview dashboard
```

---

## ❌ Wenn Tools NICHT angezeigt werden

### Check 1: Logs lesen

**Lokation:**
```
C:\Users\andre\AppData\Roaming\Claude\logs\
```

**Wichtige Dateien:**
- `mcp-server-mcp-intelligence.log` - Proxy communication
- `main.log` - Claude Desktop errors

**Was zu suchen:**
```
# Gutes Zeichen:
[info] Message from server: {"jsonrpc":"2.0","id":1,"result":{"tools":[...15 tools...]}}

# Schlechtes Zeichen:
[error] ...
[warn] Extension mcp-intelligence not found
```

**Wenn Fehler gefunden:**
- Kopiere die letzten 50 Zeilen
- Sende mir die Logs

### Check 2: Server-Verbindung testen

**In PowerShell:**
```powershell
# Test backend health
curl http://localhost:9001/health

# Erwartete Antwort:
StatusCode: 200
Content: {"status":"healthy","service":"mcp-intelligence-server","version":"1.0.0"}
```

**Falls Fehler:**
- Backend ist nicht erreichbar
- Starte Backend auf Linux-Server neu

### Check 3: Proxy manuell testen

**In PowerShell:**
```powershell
cd C:\
node mcp-intelligence-proxy.js
```

**Dann tippe:**
```json
{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
```

**Erwartete Antwort:**
- JSON response mit `"name":"mcp-intelligence-server-proxy"`
- Keine Errors

**Dann tippe:**
```json
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
```

**Erwartete Antwort:**
- JSON mit 15 tools
- Keine Errors

**Falls Fehler:**
- Proxy-Code hat Bug
- Sende mir die Fehlermeldung

---

## 🎯 Quick Verification (1 Minute)

1. ✅ Öffne Claude Desktop (App) - NICHT Browser
2. ✅ Settings → MCP → Status "running"
3. ✅ New Chat erstellen
4. ✅ Frage: "Liste alle verfügbaren MCP Tools auf"
5. ✅ Sollte 15 Tools anzeigen

**Falls NICHT:**
- Logs senden: `C:\Users\andre\AppData\Roaming\Claude\logs\`
- Screenshot von Claude Desktop Settings → MCP

---

## 📊 Success Criteria

**MCP Integration erfolgreich wenn:**

1. ✅ Server zeigt "running" in Claude Desktop Settings
2. ✅ Logs zeigen erfolgreiche tools/list response (15 tools)
3. ✅ Claude Desktop zeigt alle 15 Tools bei Nachfrage
4. ✅ Tool kann erfolgreich aufgerufen werden (Test: `get_intelligence_overview`)

**Aktueller Status (laut Logs 16:52:03):**
- ✅ Server running
- ✅ Protocol handshake successful
- ✅ 15 tools transmitted
- ⚠️ User testet möglicherweise in falscher Umgebung (Claude.ai Web statt Claude Desktop)

---

## 🆘 Hilfe

**Falls immer noch nicht funktioniert:**

Sende mir:
1. Screenshot von Claude Desktop (komplettes Fenster)
2. Logs: `C:\Users\andre\AppData\Roaming\Claude\logs\mcp-server-mcp-intelligence.log`
3. Logs: `C:\Users\andre\AppData\Roaming\Claude\logs\main.log`
4. Output von: `curl http://localhost:9001/health`

**Wichtig:** Stelle sicher, dass du CLAUDE DESKTOP nutzt, nicht Claude.ai im Browser!
