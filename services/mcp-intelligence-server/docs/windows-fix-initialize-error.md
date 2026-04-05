# Fix: "Method not found" Initialize Error

## Problem

Claude Desktop sendet beim Verbindungsaufbau eine `initialize` Anfrage (MCP-Protokoll), aber das Proxy-Script antwortet mit **"Method not found"**.

**Fehler-Log:**
```
Message from client: {"method":"initialize",...}
Message from server: {"jsonrpc":"2.0","id":0,"error":{"code":-32601,"message":"Method not found"}}
Server disconnected.
```

## Ursache

Das ursprüngliche Proxy-Script unterstützt nur `tools/list` und `tools/call`, aber **nicht** die MCP-Protokoll-Initialisierung (`initialize` Methode).

## Lösung

Verwende das **korrigierte Proxy-Script**, das das vollständige MCP-Protokoll unterstützt.

---

## Schritt-für-Schritt-Fix

### 1. Neue Proxy-Datei herunterladen

**Auf dem Linux-Server:**
```bash
# Proxy-Datei ist hier:
cat /home/cytrex/news-microservices/services/mcp-intelligence-server/docs/mcp-intelligence-proxy-fixed.js
```

**Oder direkt von unten kopieren** (siehe [Vollständiges Proxy-Script](#vollständiges-proxy-script))

### 2. Alte Proxy-Datei ersetzen

**Auf Windows:**

1. Öffne die alte Datei:
   ```
   C:\mcp-intelligence-proxy.js
   ```

2. **Lösche den gesamten Inhalt**

3. **Kopiere das neue Proxy-Script** (siehe unten)

4. **Ändere die IP-Adresse** in Zeile 18:
   ```javascript
   const SERVER_URL = process.env.MCP_SERVER_URL || 'http://192.168.1.100:9001';
   ```
   Ersetze `192.168.1.100` mit **deiner Server-IP**!

5. **Speichern**

### 3. Claude Desktop neu starten

1. Claude Desktop **komplett schließen**
2. Task-Manager öffnen (Strg+Shift+Esc)
3. Prüfen, ob `Claude.exe` noch läuft → Beenden falls ja
4. Claude Desktop **neu starten**

### 4. Testen

**In Claude Desktop eingeben:**
```
Welche MCP-Tools sind verfügbar?
```

**Sollte jetzt funktionieren!** ✅

---

## Vollständiges Proxy-Script

**Speichere dieses Script als `C:\mcp-intelligence-proxy.js`:**

```javascript
#!/usr/bin/env node

/**
 * MCP Intelligence Server Proxy for Claude Desktop
 *
 * This proxy implements the MCP (Model Context Protocol) and forwards
 * requests to the MCP Intelligence Server running on a remote host.
 *
 * Protocol Version: 2025-06-18
 */

const http = require('http');
const SERVER_URL = process.env.MCP_SERVER_URL || 'http://192.168.1.100:9001';

// Enable debug logging if DEBUG environment variable is set
const DEBUG = process.env.DEBUG === 'true';

function log(message, data) {
  if (DEBUG) {
    console.error(`[MCP Proxy] ${message}`, data ? JSON.stringify(data) : '');
  }
}

/**
 * List all available MCP tools from the server
 */
async function listTools() {
  return new Promise((resolve, reject) => {
    log('Fetching tools list from server...');

    const req = http.get(`${SERVER_URL}/mcp/tools/list`, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          log('Tools list received:', result);
          resolve(result);
        } catch (error) {
          log('Error parsing tools list:', error);
          reject(error);
        }
      });
    });

    req.on('error', (error) => {
      log('Error fetching tools list:', error);
      reject(error);
    });

    req.end();
  });
}

/**
 * Call a specific MCP tool on the server
 */
async function callTool(name, args) {
  return new Promise((resolve, reject) => {
    log(`Calling tool: ${name}`, args);

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
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          log('Tool call result:', result);
          resolve(result);
        } catch (error) {
          log('Error parsing tool call result:', error);
          reject(error);
        }
      });
    });

    req.on('error', (error) => {
      log('Error calling tool:', error);
      reject(error);
    });

    req.write(postData);
    req.end();
  });
}

/**
 * Handle MCP protocol messages
 */
async function handleMessage(request) {
  log('Received request:', request);

  try {
    // MCP Protocol: Initialize
    if (request.method === 'initialize') {
      log('Handling initialize request');
      return {
        jsonrpc: '2.0',
        id: request.id,
        result: {
          protocolVersion: '2025-06-18',
          capabilities: {
            tools: {}
          },
          serverInfo: {
            name: 'mcp-intelligence-server-proxy',
            version: '1.0.0'
          }
        }
      };
    }

    // MCP Protocol: Tools List
    if (request.method === 'tools/list') {
      log('Handling tools/list request');
      const result = await listTools();
      return {
        jsonrpc: '2.0',
        id: request.id,
        result: {
          tools: result.tools || []
        }
      };
    }

    // MCP Protocol: Tool Call
    if (request.method === 'tools/call') {
      log('Handling tools/call request');
      const toolName = request.params.name;
      const toolArgs = request.params.arguments || {};

      const result = await callTool(toolName, toolArgs);

      // Convert server response to MCP format
      return {
        jsonrpc: '2.0',
        id: request.id,
        result: {
          content: result.content || [],
          isError: result.isError || false
        }
      };
    }

    // MCP Protocol: Ping (optional)
    if (request.method === 'ping') {
      log('Handling ping request');
      return {
        jsonrpc: '2.0',
        id: request.id,
        result: {}
      };
    }

    // Unknown method
    log('Unknown method:', request.method);
    return {
      jsonrpc: '2.0',
      id: request.id,
      error: {
        code: -32601,
        message: `Method not found: ${request.method}`
      }
    };

  } catch (error) {
    log('Error handling message:', error);
    return {
      jsonrpc: '2.0',
      id: request.id,
      error: {
        code: -32603,
        message: `Internal error: ${error.message}`
      }
    };
  }
}

/**
 * Main event loop - read from stdin, process messages, write to stdout
 */
async function main() {
  log('MCP Intelligence Server Proxy starting...');
  log('Server URL:', SERVER_URL);

  const stdin = process.stdin;
  const stdout = process.stdout;

  stdin.setEncoding('utf8');
  let buffer = '';

  stdin.on('data', async (chunk) => {
    buffer += chunk;
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const request = JSON.parse(line);
        const response = await handleMessage(request);
        stdout.write(JSON.stringify(response) + '\n');
      } catch (error) {
        log('Parse error:', error);
        stdout.write(JSON.stringify({
          jsonrpc: '2.0',
          id: null,
          error: {
            code: -32700,
            message: `Parse error: ${error.message}`
          }
        }) + '\n');
      }
    }
  });

  stdin.on('end', () => {
    log('stdin closed, exiting...');
    process.exit(0);
  });

  // Handle process signals
  process.on('SIGINT', () => {
    log('SIGINT received, exiting...');
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    log('SIGTERM received, exiting...');
    process.exit(0);
  });
}

// Start the proxy
main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
```

**WICHTIG:** Ändere in Zeile 18 die IP-Adresse:
```javascript
const SERVER_URL = process.env.MCP_SERVER_URL || 'http://DEINE-SERVER-IP:9001';
```

---

## Was wurde geändert?

### Vorher (fehlerhaft):
```javascript
if (request.method === 'tools/list') { ... }
else if (request.method === 'tools/call') { ... }
else {
  // "Method not found" für alles andere, inkl. "initialize"
}
```

### Nachher (korrekt):
```javascript
if (request.method === 'initialize') {
  // MCP-Protokoll-Initialisierung
  return {
    protocolVersion: '2025-06-18',
    capabilities: { tools: {} },
    serverInfo: { name: '...', version: '...' }
  };
}
else if (request.method === 'tools/list') { ... }
else if (request.method === 'tools/call') { ... }
else if (request.method === 'ping') { ... }
```

---

## Debug-Modus aktivieren (optional)

Falls es immer noch nicht funktioniert, aktiviere Debug-Logging:

**In `claude_desktop_config.json`:**
```json
{
  "mcpServers": {
    "intelligence": {
      "command": "node",
      "args": ["C:\\mcp-intelligence-proxy.js"],
      "env": {
        "MCP_SERVER_URL": "http://192.168.1.100:9001",
        "DEBUG": "true"
      }
    }
  }
}
```

**Logs anschauen:**
```
%APPDATA%\Claude\logs\mcp-*.log
```

---

## Verifikation

Nach dem Fix sollte der Log zeigen:

```
[intelligence] [info] Message from client: {"method":"initialize",...}
[intelligence] [info] Message from server: {"jsonrpc":"2.0","id":0,"result":{"protocolVersion":"2025-06-18",...}}
[intelligence] [info] Server started successfully
```

**Kein "Method not found" mehr!** ✅

---

## Nächste Schritte

Nach erfolgreicher Verbindung:

1. **Tools testen:**
   ```
   Welche MCP-Tools sind verfügbar?
   Rufe get_intelligence_overview auf
   ```

2. **Grafana öffnen:**
   ```
   http://<SERVER-IP>:3002
   Services → MCP Intelligence Server - Production Monitoring
   ```

3. **Performance beobachten:**
   - Tool Call Rate
   - Cache Hit Ratio
   - Response Times

---

## Support

Falls es immer noch nicht funktioniert:

1. **Logs prüfen:**
   - Windows: `%APPDATA%\Claude\logs\`
   - Linux: `docker logs mcp-intelligence-server`

2. **Verbindung testen:**
   ```powershell
   curl http://<SERVER-IP>:9001/health
   ```

3. **Issue erstellen** mit:
   - Vollständiger Fehler-Log
   - Proxy-Script-Version
   - Node.js-Version
   - Netzwerk-Setup

---

**Erstellt:** 2025-12-04
**Problem:** Initialize-Method nicht implementiert
**Lösung:** Vollständiges MCP-Protokoll im Proxy-Script
