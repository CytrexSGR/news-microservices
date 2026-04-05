# MCP Intelligence Server - Quick Test Card

## 🚨 KRITISCH: Wo bin ich?

### ❌ FALSCH: Claude.ai (Browser)
```
┌────────────────────────────────────────┐
│ 🔗 https://claude.ai/...        [X]   │
│ ^^^^^^^^^^^^^^^^^^^^^^                 │
│ URL-Leiste = FALSCHES Programm!        │
└────────────────────────────────────────┘
```

### ✅ RICHTIG: Claude Desktop (App)
```
┌────────────────────────────────────────┐
│ Claude                          [X]   │
│ ^^^^^^                                 │
│ Nur "Claude" = RICHTIGES Programm!     │
│ (Keine URL-Leiste)                     │
└────────────────────────────────────────┘
```

---

## ⚡ 60-Sekunden Test

### 1. Öffne Claude Desktop
```
Windows Start → "Claude" → Click purple icon
```

### 2. Verify Settings
```
☰ → Settings → Developer → MCP Servers

Muss existieren! Falls nicht → Falsches Programm!
```

### 3. Check Server Status
```
mcp-intelligence
Status: running ✅

Falls "stopped" → Logs lesen
Falls nicht vorhanden → Config prüfen
```

### 4. New Chat
```
"+ New Chat" (oben links)
Warte 2-3 Sekunden
```

### 5. Test Tools
```
Frage: "Liste alle verfügbaren MCP Tools auf."
```

### 6. Erwartetes Ergebnis
```
✅ ERFOLG:
"Verfügbare MCP Tools:
 • analyze_article
 • extract_entities
 • get_analysis_status
 • canonicalize_entity
 • get_entity_clusters
 • detect_intelligence_patterns
 • analyze_graph_quality
 • get_event_clusters
 • get_cluster_details
 • get_latest_events
 • get_intelligence_overview
 • analyze_text_narrative
 • get_narrative_frames
 • get_bias_analysis
 • get_narrative_overview"

❌ FEHLER:
"In dieser Claude.ai-Umgebung sind keine MCP Tools verfügbar"
→ Du bist im Browser! Öffne Claude Desktop App!
```

---

## 🔍 Schnell-Check: Bin ich richtig?

| Check | Claude Desktop ✅ | Claude.ai Web ❌ |
|-------|------------------|------------------|
| URL-Leiste? | NEIN | JA |
| Window Title? | "Claude" | "claude.ai - Chrome" |
| Settings → MCP? | JA | NEIN |
| Purple Icon in Taskbar? | JA (eigenes) | NEIN (Browser) |

**Wenn irgendetwas in der rechten Spalte zutrifft → FALSCHES PROGRAMM!**

---

## 🆘 Hilfe! Tools nicht gefunden!

### Check 1: Backend läuft?
```powershell
curl http://localhost:9001/health

Erwartung: StatusCode 200
```

### Check 2: Proxy läuft?
```powershell
node C:\mcp-intelligence-proxy.js

Sollte hängen (wartet auf Input) = GUT!
Ctrl+C zum Beenden
```

### Check 3: Logs lesen
```
C:\Users\andre\AppData\Roaming\Claude\logs\
→ mcp-server-mcp-intelligence.log

Suche nach:
✅ "Server started and connected successfully"
✅ "Message from server: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"tools\":[..."
❌ "[error]"
❌ "[warn] Extension mcp-intelligence not found"
```

### Check 4: Config prüfen
```
Settings → Developer → MCP Servers → mcp-intelligence → Bearbeiten

Muss sein:
{
  "command": "C:\\Program Files\\nodejs\\node.exe",
  "args": ["C:\\mcp-intelligence-proxy.js"],
  "env": {
    "MCP_SERVER_TYPE": "stdio"
  }
}
```

---

## 📊 Status Interpretation

### "running" in Settings
✅ Server startet ohne Fehler
⚠️ Bedeutet NICHT, dass Tools geladen sind!

### Tools in Chat angezeigt
✅ Volle Integration erfolgreich
✅ Proxy funktioniert
✅ Backend erreichbar
✅ Tools geladen

### "In dieser Session habe ich keine MCP Tools"
⚠️ Session vor Server-Start erstellt
→ Lösung: Neue Session erstellen

### "In dieser Claude.ai-Umgebung..."
❌ DU BIST IM BROWSER!
→ Lösung: Claude Desktop App öffnen

---

## 🎯 Success Criteria

**MCP Integration funktioniert wenn:**

1. ✅ Claude Desktop (App) - KEIN Browser
2. ✅ Settings → MCP → mcp-intelligence = running
3. ✅ New Chat erstellt
4. ✅ Frage nach Tools zeigt 15 Tools
5. ✅ Tool-Aufruf funktioniert (Test: `get_intelligence_overview`)

**Aktueller Status (laut Logs):**
- ✅ Proxy funktioniert (verified durch PowerShell-Test)
- ✅ Backend erreichbar (health check: 200 OK)
- ✅ Protocol handshake erfolgreich (logs: 16:52:03)
- ✅ 15 Tools erfolgreich übertragen (logs: 16:52:03)
- ⚠️ User testet möglicherweise in Claude.ai (Web) statt Claude Desktop (App)

---

## 🔄 Nächste Schritte

1. **Schließe alle Claude.ai Browser-Tabs**
2. **Öffne Claude Desktop App** (Purple Icon)
3. **Settings → MCP** (Muss existieren!)
4. **New Chat**
5. **"Liste alle verfügbaren MCP Tools auf"**
6. **Sollte 15 Tools zeigen**

**Falls immer noch Probleme:**
- Screenshot von Claude Desktop (komplettes Fenster)
- Logs: `C:\Users\andre\AppData\Roaming\Claude\logs\mcp-server-mcp-intelligence.log`
- Logs: `C:\Users\andre\AppData\Roaming\Claude\logs\main.log`

---

**Quick Reminder:**
```
Browser = ❌ Funktioniert NICHT
Desktop App = ✅ Funktioniert
```

**Wie du es erkennst:**
```
Siehst du "https://" in einer Adressleiste?
→ Schließen und Claude Desktop öffnen!
```
