# Windows Claude Desktop - Quick Start

## 🚀 Schnellstart (5 Minuten)

### 1. Server-IP herausfinden

**Auf dem Linux-Server:**
```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
# Beispiel-Output: inet 192.168.1.100/24
```

➡️ **Merke dir diese IP:** `192.168.1.100`

### 2. Verbindung testen

**Auf Windows (CMD/PowerShell):**
```powershell
curl http://192.168.1.100:9001/health
```

**Erwartete Antwort:**
```json
{"status":"healthy","service":"mcp-intelligence-server","version":"1.0.0"}
```

✅ Funktioniert? → Weiter zu Schritt 3
❌ Fehler? → Siehe [Firewall-Setup](#firewall-setup) unten

### 3. Proxy-Datei erstellen

**Erstelle `C:\mcp-intelligence-proxy.js`:**

**WICHTIG:** Das vollständige Script findest du in [mcp-intelligence-proxy-fixed.js](mcp-intelligence-proxy-fixed.js) oder kopiere es von hier:

```javascript
#!/usr/bin/env node

/**
 * MCP Intelligence Server Proxy for Claude Desktop
 * Protocol Version: 2025-06-18
 */

const http = require('http');
const SERVER_URL = process.env.MCP_SERVER_URL || 'http://192.168.1.100:9001';

async function listTools() {
  return new Promise((resolve, reject) => {
    http.get(`${SERVER_URL}/mcp/tools/list`, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => { resolve(JSON.parse(data)); });
    }).on('error', reject).end();
  });
}

async function callTool(name, args) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({ name, arguments: args });
    const req = http.request(`${SERVER_URL}/mcp/tools/call`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    }, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => { resolve(JSON.parse(data)); });
    });
    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

process.stdin.setEncoding('utf8');
let buffer = '';

process.stdin.on('data', async (chunk) => {
  buffer += chunk;
  const lines = buffer.split('\n');
  buffer = lines.pop();

  for (const line of lines) {
    if (!line.trim()) continue;

    try {
      const request = JSON.parse(line);
      let response;

      if (request.method === 'tools/list') {
        const result = await listTools();
        response = { jsonrpc: '2.0', id: request.id, result: { tools: result.tools } };
      } else if (request.method === 'tools/call') {
        const result = await callTool(request.params.name, request.params.arguments || {});
        response = { jsonrpc: '2.0', id: request.id, result };
      } else {
        response = { jsonrpc: '2.0', id: request.id, error: { code: -32601, message: 'Method not found' } };
      }

      process.stdout.write(JSON.stringify(response) + '\n');
    } catch (error) {
      process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id: null, error: { code: -32700, message: error.message } }) + '\n');
    }
  }
});
```

**WICHTIG:** Ändere `192.168.1.100` auf DEINE Server-IP!

### 4. Claude Desktop konfigurieren

**Windows-Taste + R** drücken, dann eingeben:
```
notepad %APPDATA%\Claude\claude_desktop_config.json
```

**Inhalt (anpassen mit DEINER Server-IP):**
```json
{
  "mcpServers": {
    "intelligence": {
      "command": "node",
      "args": ["C:\\mcp-intelligence-proxy.js"],
      "env": {
        "MCP_SERVER_URL": "http://192.168.1.100:9001"
      }
    }
  }
}
```

**Speichern** und schließen.

### 5. Claude Desktop neu starten

1. Claude Desktop **komplett schließen** (Task-Manager prüfen!)
2. Claude Desktop **neu starten**

### 6. Testen! 🎉

**In Claude Desktop eingeben:**
```
Welche MCP-Tools sind verfügbar?
```

**Sollte zeigen:**
- ✅ 12 Intelligence-Tools
- ✅ Tool-Kategorien: Intelligence, Narrative, Entity, OSINT

**Test-Aufruf:**
```
Rufe get_intelligence_overview auf
```

---

## 🔧 Firewall-Setup

### Linux-Server (falls Verbindung fehlschlägt)

```bash
# Port 9001 freigeben
sudo ufw allow 9001/tcp
sudo ufw reload

# Status prüfen
sudo ufw status | grep 9001
```

### Alternative: SSH-Tunnel

**Auf Windows (PowerShell):**
```powershell
ssh -L 9001:localhost:9001 cytrex@192.168.1.100
```

**Dann in claude_desktop_config.json ändern:**
```json
"MCP_SERVER_URL": "http://localhost:9001"
```

Tunnel läuft, solange SSH-Fenster offen ist!

---

## ❌ Probleme?

### "curl: command not found" (Windows)

**Lösung:** PowerShell statt CMD verwenden, oder:
```powershell
Invoke-WebRequest -Uri http://192.168.1.100:9001/health
```

### "node: command not found"

**Lösung:** Node.js installieren:
1. https://nodejs.org herunterladen
2. LTS-Version installieren
3. CMD/PowerShell neu öffnen
4. Testen: `node --version`

### Tools werden nicht angezeigt

**Checkliste:**
- [ ] Claude Desktop komplett neu gestartet?
- [ ] Datei gespeichert: `%APPDATA%\Claude\claude_desktop_config.json`?
- [ ] Server erreichbar: `curl http://<IP>:9001/health`?
- [ ] Node.js installiert: `node --version`?
- [ ] Pfad korrekt: `C:\\mcp-intelligence-proxy.js` (doppelte Backslashes)?

### JSON-Fehler in Config

**Lösung:** Prüfe mit https://jsonlint.com

**Häufig:** Komma vergessen oder zu viel

---

## 📚 Vollständige Dokumentation

Für Details siehe: [claude-desktop-windows-setup.md](claude-desktop-windows-setup.md)

- Erweiterte Konfiguration
- Mehrere MCP Server
- Performance-Optimierung
- Sicherheits-Best-Practices
- Troubleshooting-Guide

---

## 🎯 Was du jetzt hast

✅ **12 MCP Tools** direkt in Claude Desktop:
- **Intelligence:** Event-Clustering, Pattern Detection
- **Narrative:** Bias-Analyse, Frame Detection
- **Entity:** Kanonisierung, Clustering
- **OSINT:** Graph-Qualität, Anomalie-Erkennung

✅ **Performance:**
- Cache Hit Ratio: >50%
- Circuit Breaker Protection
- Response Time: <1s (p95)

✅ **Monitoring:**
- Grafana Dashboard: http://192.168.1.100:3002
- Prometheus Metrics: http://192.168.1.100:9001/metrics

---

**Happy Coding! 🚀**
