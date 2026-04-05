# Windows Claude Desktop - Test Instructions

**Status:** Proxy script vollständig & bereit zum Testen (2025-12-04 - v1.0.2)

**Alle Bugs behoben:**
- ✅ Bug #1: `initialize` method implementiert
- ✅ Bug #2: Notification handling hinzugefügt (keine Antworten auf Notifications)
- ✅ Bug #3: Null-Response-Bug behoben (kein `"null"` nach stdout)
- ✅ Bug #4: **Falsy ID Check** - `id: 0` wird nicht mehr als Notification behandelt
- ✅ Server IP konfiguriert (localhost:9001)

**Changelog v1.0.2 (CRITICAL FIX - MUST UPDATE!):**
- **Fixed:** Changed notification check from `if (!request.id)` to `if (!('id' in request))`
- **Bug:** JavaScript `!0` is `true`, so `id: 0` was treated as notification!
- **Impact:** Initialize request (id: 0) returned null → timeout after 60s
- **Details:** [BUGFIX_FALSY_ID_CHECK.md](BUGFIX_FALSY_ID_CHECK.md)

**Previous Version (v1.0.1):**
- Fixed: Main loop now checks `if (response !== null)` before writing to stdout
- Details: [BUGFIX_NOTIFICATION_NULL_RESPONSE.md](BUGFIX_NOTIFICATION_NULL_RESPONSE.md)

---

## Schnellstart (5 Minuten)

### 1. Datei nach Windows kopieren

**Option A: Über SSH/SCP (empfohlen)**
```powershell
# Auf deinem Windows PC:
scp cytrex@localhost:/home/cytrex/news-microservices/services/mcp-intelligence-server/docs/WINDOWS_PROXY_COMPLETE.js C:\mcp-intelligence-proxy.js
```

**Option B: Manuelles Kopieren**
1. Öffne `/home/cytrex/news-microservices/services/mcp-intelligence-server/docs/WINDOWS_PROXY_COMPLETE.js` auf dem Linux-Server
2. Kopiere den kompletten Inhalt
3. Speichere ihn als `C:\mcp-intelligence-proxy.js` auf Windows

### 2. Claude Desktop Config anpassen

Öffne die Claude Desktop Config:
```
%APPDATA%\Claude\claude_desktop_config.json
```

Füge den MCP Server hinzu:
```json
{
  "mcpServers": {
    "mcp-intelligence": {
      "command": "node",
      "args": ["C:\\mcp-intelligence-proxy.js"]
    }
  }
}
```

### 3. Claude Desktop neu starten

1. Claude Desktop komplett beenden (Taskleiste-Icon: Rechtsklick → Exit)
2. Claude Desktop neu starten

### 4. Verbindung testen

In Claude Desktop eingeben:
```
Welche MCP-Tools sind verfügbar?
```

**Erwartetes Ergebnis:**
Claude listet 15 MCP Intelligence Tools auf:
- Intelligence Tools: 4 (summarize, extract, research, report)
- Narrative Tools: 4 (extract, analyze, detect, compare)
- Entity Tools: 2 (entity_analysis, entity_network)
- OSINT Tools: 2 (profile, analysis)
- Advanced Tools: 3 (semantic_search, knowledge_graph, entity_canonicalization)

---

## Wenn es nicht funktioniert

### Debug-Modus aktivieren

**Option 1: Umgebungsvariable (empfohlen)**
```json
{
  "mcpServers": {
    "mcp-intelligence": {
      "command": "node",
      "args": ["C:\\mcp-intelligence-proxy.js"],
      "env": {
        "DEBUG": "true"
      }
    }
  }
}
```

**Option 2: In der Proxy-Datei**
Ändere Zeile 20 in `WINDOWS_PROXY_COMPLETE.js`:
```javascript
const DEBUG = true;  // Immer aktiviert
```

### Logs anschauen

Windows PowerShell:
```powershell
# Claude Desktop logs
Get-Content $env:APPDATA\Claude\logs\mcp*.log -Tail 50
```

### Häufige Probleme

**Problem: "Method not found: initialize"**
- **Ursache:** Alte Version des Proxy Scripts
- **Lösung:** Aktuelle `WINDOWS_PROXY_COMPLETE.js` neu kopieren

**Problem: "Zod validation error" oder "Required: id"**
- **Ursache:** Alte Version ohne Notification-Handling
- **Lösung:** Aktuelle `WINDOWS_PROXY_COMPLETE.js` neu kopieren

**Problem: "Connection refused"**
- **Ursache:** Server nicht erreichbar oder falsche IP
- **Lösung:**
  1. Prüfe Server läuft: `curl http://localhost:9001/health`
  2. Prüfe Firewall auf Windows
  3. Prüfe Netzwerkverbindung

**Problem: "ECONNREFUSED" oder Timeout**
- **Ursache:** MCP Intelligence Server nicht gestartet
- **Lösung:** Auf Linux-Server starten:
  ```bash
  cd /home/cytrex/news-microservices
  docker compose up -d mcp-intelligence-server
  ```

---

## Verifikation

**Test 1: Tool List**
```
Welche MCP-Tools sind verfügbar?
```
Erwartung: 15 Tools aufgelistet

**Test 2: Tool Call (einfach)**
```
Führe eine Intelligence Summary für den Begriff "artificial intelligence" durch.
```
Erwartung: Strukturierte Summary mit Schlüsselthemen

**Test 3: Tool Call (komplex)**
```
Analysiere die narrative Struktur folgenden Texts: "Breaking news: Scientists discover new energy source..."
```
Erwartung: Narrative-Analyse mit Framing, Sentiment, Themes

---

## Technische Details

**Proxy-Implementierung:**
- MCP Protocol Version: 2025-06-18
- Unterstützte Methoden: `initialize`, `tools/list`, `tools/call`, `ping`
- Notification-Handling: Keine Antworten auf Notifications (z.B. `notifications/initialized`)
- Transport: JSON-RPC 2.0 über stdin/stdout
- Backend: HTTP GET/POST zu `http://localhost:9001/mcp/tools/*`

**Netzwerk-Anforderungen:**
- Windows PC muss localhost:9001 erreichen können (Port 9001 offen)
- Keine VPN/Proxy zwischen Windows und Linux-Server
- LAN-Verbindung empfohlen (Latenz < 10ms)

---

## Nächste Schritte

Nach erfolgreichem Test:
1. ✅ Verbindung verifiziert
2. 📝 Weitere Test-Szenarien durchführen (siehe [docs/windows-quickstart.md](windows-quickstart.md))
3. 🔍 Performance monitoren (Latenz, Cache-Hits)
4. 📊 Grafana Dashboard aufrufen: http://localhost:3002

---

**Erstellt:** 2025-12-04
**Status:** Ready for Testing
**Proxy Version:** 1.0.0 (Complete)
