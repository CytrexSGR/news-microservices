# Claude Desktop Windows Setup - MCP Intelligence Server

## Überblick

Diese Anleitung erklärt, wie du Claude Desktop unter Windows mit dem MCP Intelligence Server verbindest, um direkten Zugriff auf alle Intelligence-Services zu erhalten.

## Voraussetzungen

### 1. Claude Desktop für Windows
**Download:** https://claude.ai/download

**Installation:**
1. Installer herunterladen (`Claude-Setup-x64.exe`)
2. Installation durchführen
3. Claude Desktop starten und einloggen

### 2. MCP Intelligence Server läuft
```bash
# Auf dem Linux-Server prüfen
docker ps | grep mcp-intelligence-server

# Sollte zeigen:
# mcp-intelligence-server ... Up ... 0.0.0.0:9001->8000/tcp
```

### 3. Netzwerkzugriff
- Windows-PC muss den Linux-Server erreichen können
- Port 9001 muss erreichbar sein
- Firewall-Regel ggf. nötig

## Konfiguration

### Schritt 1: Konfigurationsdatei finden

Claude Desktop speichert die MCP-Konfiguration in:

```
%APPDATA%\Claude\claude_desktop_config.json
```

**Vollständiger Pfad (typisch):**
```
C:\Users\<Username>\AppData\Roaming\Claude\claude_desktop_config.json
```

### Schritt 2: Konfigurationsdatei öffnen

**Option A: Windows Explorer**
1. Windows-Taste + R drücken
2. `%APPDATA%\Claude` eingeben
3. Enter drücken
4. `claude_desktop_config.json` mit Editor öffnen

**Option B: Direkt über Ausführen**
1. Windows-Taste + R drücken
2. `notepad %APPDATA%\Claude\claude_desktop_config.json` eingeben
3. Enter drücken

**Falls Datei nicht existiert:**
```json
{}
```
Erstelle eine leere JSON-Datei mit diesem Inhalt.

### Schritt 3: MCP Server konfigurieren

**Wichtig:** Ersetze `<SERVER-IP>` mit der IP-Adresse deines Linux-Servers!

```json
{
  "mcpServers": {
    "intelligence": {
      "command": "node",
      "args": [
        "-e",
        "const http = require('http'); const SERVER_URL = 'http://<SERVER-IP>:9001'; async function listTools() { return new Promise((resolve, reject) => { const req = http.get(`${SERVER_URL}/mcp/tools/list`, (res) => { let data = ''; res.on('data', (chunk) => { data += chunk; }); res.on('end', () => { resolve(JSON.parse(data)); }); }); req.on('error', reject); req.end(); }); } async function callTool(name, args) { return new Promise((resolve, reject) => { const postData = JSON.stringify({ name, arguments: args }); const options = { method: 'POST', headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(postData) } }; const req = http.request(`${SERVER_URL}/mcp/tools/call`, options, (res) => { let data = ''; res.on('data', (chunk) => { data += chunk; }); res.on('end', () => { resolve(JSON.parse(data)); }); }); req.on('error', reject); req.write(postData); req.end(); }); } const stdin = process.stdin; const stdout = process.stdout; stdin.setEncoding('utf8'); let buffer = ''; stdin.on('data', async (chunk) => { buffer += chunk; const lines = buffer.split('\\n'); buffer = lines.pop(); for (const line of lines) { if (line.trim()) { try { const request = JSON.parse(line); let response; if (request.method === 'tools/list') { const result = await listTools(); response = { jsonrpc: '2.0', id: request.id, result: result.tools }; } else if (request.method === 'tools/call') { const result = await callTool(request.params.name, request.params.arguments || {}); response = { jsonrpc: '2.0', id: request.id, result: { content: result.content, isError: result.isError } }; } else { response = { jsonrpc: '2.0', id: request.id, error: { code: -32601, message: 'Method not found' } }; } stdout.write(JSON.stringify(response) + '\\n'); } catch (error) { stdout.write(JSON.stringify({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error' } }) + '\\n'); } } } });"
      ],
      "env": {}
    }
  }
}
```

**Beispiel mit konkreter IP:**
```json
{
  "mcpServers": {
    "intelligence": {
      "command": "node",
      "args": [
        "-e",
        "const http = require('http'); const SERVER_URL = 'http://192.168.1.100:9001'; ..."
      ],
      "env": {}
    }
  }
}
```

### Schritt 4: Alternative - Einfachere Konfiguration mit npx

**Erstelle eine separate Proxy-Datei:**

1. Erstelle `mcp-proxy.js` auf deinem Windows-PC:

```javascript
// mcp-proxy.js
const http = require('http');
const SERVER_URL = process.env.MCP_SERVER_URL || 'http://192.168.1.100:9001';

async function listTools() {
  return new Promise((resolve, reject) => {
    const req = http.get(`${SERVER_URL}/mcp/tools/list`, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => { resolve(JSON.parse(data)); });
    });
    req.on('error', reject);
    req.end();
  });
}

async function callTool(name, args) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({ name, arguments: args });
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    };
    const req = http.request(`${SERVER_URL}/mcp/tools/call`, options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => { resolve(JSON.parse(data)); });
    });
    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

const stdin = process.stdin;
const stdout = process.stdout;
stdin.setEncoding('utf8');
let buffer = '';

stdin.on('data', async (chunk) => {
  buffer += chunk;
  const lines = buffer.split('\n');
  buffer = lines.pop();

  for (const line of lines) {
    if (line.trim()) {
      try {
        const request = JSON.parse(line);
        let response;

        if (request.method === 'tools/list') {
          const result = await listTools();
          response = {
            jsonrpc: '2.0',
            id: request.id,
            result: { tools: result.tools }
          };
        } else if (request.method === 'tools/call') {
          const result = await callTool(request.params.name, request.params.arguments || {});
          response = {
            jsonrpc: '2.0',
            id: request.id,
            result: {
              content: result.content,
              isError: result.isError
            }
          };
        } else {
          response = {
            jsonrpc: '2.0',
            id: request.id,
            error: { code: -32601, message: 'Method not found' }
          };
        }

        stdout.write(JSON.stringify(response) + '\n');
      } catch (error) {
        stdout.write(JSON.stringify({
          jsonrpc: '2.0',
          id: null,
          error: { code: -32700, message: 'Parse error: ' + error.message }
        }) + '\n');
      }
    }
  }
});
```

2. Dann in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "intelligence": {
      "command": "node",
      "args": ["C:\\Users\\<Username>\\mcp-proxy.js"],
      "env": {
        "MCP_SERVER_URL": "http://192.168.1.100:9001"
      }
    }
  }
}
```

### Schritt 5: Claude Desktop neu starten

**Wichtig:** Nach jeder Änderung an der Konfiguration muss Claude Desktop komplett neu gestartet werden!

1. Claude Desktop schließen (nicht nur minimieren!)
2. Sicherstellen, dass der Prozess beendet ist (Task-Manager prüfen)
3. Claude Desktop neu starten

## Verifikation

### 1. Verbindung testen

Nach dem Neustart von Claude Desktop solltest du in der Toolbar ein MCP-Symbol sehen.

**In Claude Desktop eingeben:**
```
Welche MCP-Tools sind verfügbar?
```

**Erwartete Antwort:**
Claude sollte 12 MCP-Tools auflisten:
- Intelligence: get_event_clusters, get_latest_events, get_intelligence_overview, get_cluster_details
- Narrative: analyze_text_narrative, get_narrative_frames, get_bias_analysis, get_narrative_overview
- Entity: canonicalize_entity, get_entity_clusters
- OSINT: detect_intelligence_patterns, analyze_graph_quality

### 2. Test-Tool aufrufen

**In Claude Desktop:**
```
Rufe get_intelligence_overview auf
```

**Erwartetes Verhalten:**
- Claude sendet Anfrage an MCP Server
- Server antwortet mit Intelligence-Daten
- Claude zeigt Zusammenfassung an

### 3. Fehlerbehebung bei Verbindungsproblemen

**Problem 1: "MCP Server nicht erreichbar"**

**Lösung:**
```bash
# Auf Windows-PC im CMD/PowerShell testen:
curl http://<SERVER-IP>:9001/health

# Sollte zurückgeben:
# {"status":"healthy","service":"mcp-intelligence-server","version":"1.0.0"}
```

**Wenn curl nicht funktioniert:**
- IP-Adresse prüfen
- Port 9001 in Firewall freigeben (Linux-Server)
- Netzwerkverbindung prüfen

**Problem 2: "Node nicht gefunden"**

**Lösung:**
1. Node.js installieren: https://nodejs.org
2. Version prüfen: `node --version` (sollte v18+ sein)
3. Claude Desktop neu starten

**Problem 3: "Parse error in config"**

**Lösung:**
1. JSON-Syntax prüfen (keine fehlenden Kommas, Klammern)
2. Online JSON Validator verwenden: https://jsonlint.com
3. Backslashes in Pfaden müssen doppelt sein: `C:\\Users\\...`

## Netzwerk-Konfiguration

### Variante A: Direkter Zugriff (LAN)

**Voraussetzung:** Windows-PC und Linux-Server im gleichen Netzwerk

**Linux-Server IP finden:**
```bash
# Auf Linux-Server:
ip addr show | grep "inet " | grep -v 127.0.0.1
```

**Firewall-Regel (Linux-Server):**
```bash
sudo ufw allow 9001/tcp
sudo ufw reload
```

**Windows-Firewall:**
Normalerweise kein Problem (ausgehende Verbindungen erlaubt)

### Variante B: SSH-Tunnel (Remote)

**Wenn Server nicht direkt erreichbar:**

**Auf Windows-PC (PowerShell):**
```powershell
ssh -L 9001:localhost:9001 cytrex@<SERVER-IP>
```

**Dann in claude_desktop_config.json:**
```json
"MCP_SERVER_URL": "http://localhost:9001"
```

**Vorteil:**
- Verschlüsselte Verbindung
- Funktioniert über Internet
- Keine Firewall-Änderungen nötig

### Variante C: ngrok (Einfachster Remote-Zugriff)

**Auf Linux-Server:**
```bash
# ngrok installieren (einmalig)
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Token registrieren (ngrok.com Account erforderlich)
ngrok config add-authtoken <YOUR-TOKEN>

# Tunnel starten
ngrok http 9001
```

**Output:**
```
Forwarding  https://abc123.ngrok.io -> http://localhost:9001
```

**In claude_desktop_config.json:**
```json
"MCP_SERVER_URL": "https://abc123.ngrok.io"
```

**Vorteil:**
- Funktioniert überall
- HTTPS verschlüsselt
- Keine Firewall-Konfiguration

**Nachteil:**
- Öffentlich erreichbar (nicht für Production!)
- ngrok-URL ändert sich bei jedem Neustart (kostenpflichtig: statische URL)

## Erweiterte Konfiguration

### Mehrere MCP Server

```json
{
  "mcpServers": {
    "intelligence": {
      "command": "node",
      "args": ["C:\\Users\\<Username>\\mcp-proxy.js"],
      "env": {
        "MCP_SERVER_URL": "http://192.168.1.100:9001"
      }
    },
    "another-service": {
      "command": "node",
      "args": ["C:\\Users\\<Username>\\another-proxy.js"],
      "env": {
        "MCP_SERVER_URL": "http://192.168.1.100:9002"
      }
    }
  }
}
```

### Logging aktivieren

```json
{
  "mcpServers": {
    "intelligence": {
      "command": "node",
      "args": ["C:\\Users\\<Username>\\mcp-proxy.js"],
      "env": {
        "MCP_SERVER_URL": "http://192.168.1.100:9001",
        "DEBUG": "true"
      }
    }
  }
}
```

Dann in `mcp-proxy.js` am Anfang hinzufügen:
```javascript
if (process.env.DEBUG === 'true') {
  console.error('[MCP Debug] Starting proxy...');
}
```

## Performance-Optimierung

### Verbindungs-Pooling

Standard-Konfiguration verwendet ein neues HTTP-Request pro Tool-Call. Für bessere Performance:

**In mcp-proxy.js:**
```javascript
const http = require('http');
const keepAliveAgent = new http.Agent({ keepAlive: true });

async function callTool(name, args) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({ name, arguments: args });
    const options = {
      method: 'POST',
      agent: keepAliveAgent,  // Wiederverwendung von Verbindungen
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    };
    // ... rest bleibt gleich
  });
}
```

### Timeout-Konfiguration

```javascript
const options = {
  method: 'POST',
  timeout: 30000,  // 30 Sekunden Timeout
  headers: { /* ... */ }
};
```

## Troubleshooting

### Logs prüfen

**Claude Desktop Logs:**
```
%APPDATA%\Claude\logs\
```

**MCP Server Logs:**
```bash
docker logs mcp-intelligence-server --tail 100 -f
```

### Häufige Fehler

**Error: ECONNREFUSED**
- Server nicht erreichbar
- IP/Port prüfen
- Firewall prüfen

**Error: Parse error**
- JSON-Syntax-Fehler in claude_desktop_config.json
- Mit JSON Validator prüfen

**Error: ETIMEDOUT**
- Netzwerk-Timeout
- Server antwortet nicht rechtzeitig
- Timeout erhöhen oder Server-Performance prüfen

**Tools werden nicht angezeigt**
- Claude Desktop nicht neu gestartet
- Konfigurationsdatei nicht gespeichert
- Node.js nicht installiert

## Sicherheit

### Empfehlungen

1. **Keine öffentliche Exposition**
   - MCP Server nicht direkt ins Internet
   - Nur über VPN/SSH-Tunnel

2. **Authentifizierung (optional)**
   - API-Key in Header
   - In mcp-proxy.js hinzufügen:
   ```javascript
   headers: {
     'Content-Type': 'application/json',
     'X-API-Key': process.env.API_KEY
   }
   ```

3. **HTTPS (Production)**
   - nginx Reverse Proxy mit SSL
   - Let's Encrypt Zertifikat

## Monitoring

### Verbindung überwachen

**In Claude Desktop eingeben:**
```
Gib mir die Server-Health
```

**Sollte zeigen:**
```json
{
  "status": "healthy",
  "service": "mcp-intelligence-server",
  "version": "1.0.0"
}
```

### Grafana Dashboard

Öffne: http://<SERVER-IP>:3002

Navigate zu: `Services` → `MCP Intelligence Server - Production Monitoring`

Hier siehst du:
- Tool Call Rate
- Cache Hit Ratio
- Circuit Breaker Status
- Response Times

## Nächste Schritte

Nach erfolgreicher Einrichtung:

1. **Tools testen**
   - Alle 12 MCP Tools durchprobieren
   - Performance beobachten

2. **Grafana überwachen**
   - Dashboard öffnen während du Tools verwendest
   - Cache-Effektivität prüfen

3. **Dokumentation lesen**
   - [MCP Tools Reference](../README.md)
   - [Grafana Dashboard Guide](grafana-dashboard-guide.md)
   - [k6 Load Testing](../k6-tests/README.md)

## Support

**Bei Problemen:**

1. Logs prüfen (siehe oben)
2. Verifikation durchlaufen (siehe oben)
3. Issue erstellen mit:
   - Windows-Version
   - Node.js-Version (`node --version`)
   - Claude Desktop-Version
   - Fehler-Logs
   - Netzwerk-Setup (LAN/Remote/Tunnel)

---

**Erstellt:** 2025-12-04
**Version:** 1.0.0
**Maintainer:** MCP Intelligence Server Team
