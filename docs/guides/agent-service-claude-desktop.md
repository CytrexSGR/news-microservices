# Agent Service Integration mit Claude Desktop

## Executive Summary

**Status:** ❌ **Direkte Verbindung NICHT möglich**

Claude Desktop unterstützt **keine direkten HTTP REST API Verbindungen** zu externen Services. Claude Desktop verwendet ausschließlich das **Model Context Protocol (MCP)** für Tool-Integration, welches lokal laufende Server-Prozesse erfordert.

---

## Warum funktioniert es nicht?

### Claude Desktop Architektur

Claude Desktop ist eine Desktop-Anwendung mit folgenden Eigenschaften:

1. **MCP-Only Integration**
   - Claude Desktop kommuniziert nur mit MCP-Servern
   - MCP-Server müssen lokal als Prozess laufen
   - Keine HTTP/REST API Unterstützung

2. **Lokaler Prozess-Modell**
   - MCP-Server werden von Claude Desktop gestartet
   - Kommunikation über stdio (Standard Input/Output)
   - Keine Netzwerk-Sockets oder HTTP-Calls

3. **Security Model**
   - Alle Tools laufen im lokalen User-Context
   - Keine Remote-Service-Authentifizierung
   - Kein JWT Token Management

### Agent Service Architektur

Der Agent Service ist ein **HTTP REST API Service**:

1. **HTTP/JSON API**
   - FastAPI REST Endpoints
   - JWT Authentication erforderlich
   - Netzwerk-basierte Kommunikation

2. **Docker Container**
   - Läuft im Docker Network
   - Erreichbar über Port 8110
   - Separater Prozess vom Desktop

3. **Stateful Operations**
   - Datenbankpersistenz
   - Session Management
   - Multi-User Support

---

## Mögliche Workarounds

Obwohl eine direkte Integration nicht möglich ist, gibt es folgende Alternativen:

### Option 1: MCP Bridge Server (Empfohlen für Entwicklung)

Erstelle einen **lokalen MCP Server**, der als Bridge zum Agent Service fungiert.

**Architektur:**
```
Claude Desktop
    ↓ (stdio/MCP)
Local MCP Bridge Server (Python/Node.js)
    ↓ (HTTP/REST)
Agent Service (Docker Container)
```

**Implementation Schritte:**

1. **MCP Server erstellen** (Python Beispiel):

```python
# ~/.config/Claude/mcp-servers/agent-bridge/server.py
import httpx
import json
from mcp.server import Server, StdioServerTransport
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent

# Configuration
AGENT_SERVICE_URL = "http://localhost:8110"
JWT_TOKEN = "your-jwt-token-here"  # Muss regelmäßig erneuert werden

server = Server("agent-bridge")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return available tools from agent service"""
    return [
        Tool(
            name="invoke_agent",
            description="Execute an agentic workflow on the news platform",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query for the agent"
                    }
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute tool by forwarding to agent service"""
    if name != "invoke_agent":
        raise ValueError(f"Unknown tool: {name}")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AGENT_SERVICE_URL}/api/v1/agent/invoke",
            headers={
                "Authorization": f"Bearer {JWT_TOKEN}",
                "Content-Type": "application/json"
            },
            json={"query": arguments["query"]},
            timeout=180.0
        )
        response.raise_for_status()
        result = response.json()

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

async def main():
    async with StdioServerTransport() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="agent-bridge",
                server_version="1.0.0"
            )
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

2. **Dependencies installieren**:

```bash
pip install mcp httpx
```

3. **Claude Desktop konfigurieren**:

```json
// ~/.config/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "agent-bridge": {
      "command": "python",
      "args": ["/home/cytrex/.config/Claude/mcp-servers/agent-bridge/server.py"]
    }
  }
}
```

4. **JWT Token Management**:

Der JWT Token muss regelmäßig erneuert werden (Standard: 30 Minuten Gültigkeit).

**Automatische Token-Erneuerung:**

```python
# token_manager.py
import httpx
import time
from threading import Thread

class TokenManager:
    def __init__(self, auth_url, email, password):
        self.auth_url = auth_url
        self.email = email
        self.password = password
        self.token = None
        self.refresh_thread = None

    def get_token(self):
        """Get current valid token"""
        if not self.token:
            self.refresh_token()
        return self.token

    def refresh_token(self):
        """Refresh JWT token"""
        response = httpx.post(
            f"{self.auth_url}/api/v1/auth/login",
            json={"email": self.email, "password": self.password}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]

    def start_auto_refresh(self, interval=1500):  # 25 minutes
        """Start background token refresh"""
        def refresh_loop():
            while True:
                time.sleep(interval)
                try:
                    self.refresh_token()
                except Exception as e:
                    print(f"Token refresh failed: {e}")

        self.refresh_thread = Thread(target=refresh_loop, daemon=True)
        self.refresh_thread.start()

# Usage in server.py
token_manager = TokenManager(
    auth_url="http://localhost:8100",
    email="andreas@test.com",
    password="Aug2012#"
)
token_manager.start_auto_refresh()

# In handle_call_tool:
JWT_TOKEN = token_manager.get_token()
```

**Vorteile:**
- ✅ Native Claude Desktop Integration
- ✅ Alle Claude Desktop Features verfügbar
- ✅ Tool-Auswahl durch Claude selbst

**Nachteile:**
- ❌ Komplexe Implementierung
- ❌ Token Management erforderlich
- ❌ Lokaler Server muss laufen
- ❌ Zusätzlicher Wartungsaufwand

---

### Option 2: Terminal-basierte Nutzung (Einfachste Lösung)

Verwende den Agent Service direkt über Terminal/Script ohne Claude Desktop.

**Shell Script erstellen:**

```bash
#!/bin/bash
# ~/.local/bin/news-agent

# Configuration
AGENT_URL="http://localhost:8110"
AUTH_URL="http://localhost:8100"
EMAIL="andreas@test.com"
PASSWORD="Aug2012#"

# Get JWT token
TOKEN=$(curl -s -X POST "$AUTH_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "❌ Authentication failed"
  exit 1
fi

# Read query from arguments or prompt
if [ $# -eq 0 ]; then
  echo "Enter your query:"
  read QUERY
else
  QUERY="$*"
fi

# Invoke agent
echo "🤖 Processing query: $QUERY"
echo ""

RESPONSE=$(curl -s -X POST "$AGENT_URL/api/v1/agent/invoke" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"$QUERY\"}")

# Display results
echo "$RESPONSE" | jq '.'

# Display summary
STATUS=$(echo "$RESPONSE" | jq -r '.status')
RESULT=$(echo "$RESPONSE" | jq -r '.result')
TOKENS=$(echo "$RESPONSE" | jq -r '.tokens_used.total_tokens')
TIME=$(echo "$RESPONSE" | jq -r '.execution_time_seconds')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Status: $STATUS"
echo "Result: $RESULT"
echo "Tokens: $TOKENS"
echo "Time: ${TIME}s"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

**Nutzung:**

```bash
chmod +x ~/.local/bin/news-agent

# Interactive mode
news-agent

# Direct query
news-agent "Suche nach KI-Artikeln und erstelle einen Bericht"
```

**Vorteile:**
- ✅ Einfach zu implementieren
- ✅ Keine zusätzlichen Dependencies
- ✅ Direkter API-Zugriff
- ✅ Scriptable und automatisierbar

**Nachteile:**
- ❌ Keine KI-Unterstützung beim Query-Schreiben
- ❌ Keine Konversations-Historie
- ❌ Manuelle Query-Formulierung

---

### Option 3: Web UI (Beste User Experience)

Erstelle eine einfache Web-Oberfläche für den Agent Service.

**Minimal React Frontend:**

```typescript
// AgentChat.tsx
import { useState } from 'react';

export function AgentChat() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Get token (implement token management)
      const token = await getToken();

      // Invoke agent
      const response = await fetch('http://localhost:8110/api/v1/agent/invoke', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="agent-chat">
      <form onSubmit={handleSubmit}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="What would you like the agent to do?"
          rows={4}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Processing...' : 'Execute'}
        </button>
      </form>

      {result && (
        <div className="result">
          <h3>Status: {result.status}</h3>
          <p>{result.result}</p>
          <details>
            <summary>Tool Calls ({result.tool_calls.length})</summary>
            <pre>{JSON.stringify(result.tool_calls, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
}
```

**Integration in bestehendes Frontend:**

```bash
cd /home/cytrex/news-microservices/frontend

# Add agent chat page
mkdir -p src/pages/agent
cat > src/pages/agent/AgentPage.tsx << 'EOF'
// Agent page implementation
EOF

# Update routing
# Add route in App.tsx or routing config
```

**Vorteile:**
- ✅ Beste User Experience
- ✅ Konversations-Historie möglich
- ✅ Multi-User Support
- ✅ Einfache Deployment mit bestehendem Frontend

**Nachteile:**
- ❌ Mehr Implementierungsaufwand
- ❌ Separate UI-Komponente

---

### Option 4: Postman/Insomnia Collection

Erstelle eine API Collection für manuelle Tests.

**Postman Collection:**

```json
{
  "info": {
    "name": "Agent Service API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "1. Login",
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.environment.set(\"jwt_token\", pm.response.json().access_token);"
            ]
          }
        }
      ],
      "request": {
        "method": "POST",
        "header": [],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"andreas@test.com\",\n  \"password\": \"Aug2012#\"\n}",
          "options": {
            "raw": {
              "language": "json"
            }
          }
        },
        "url": "http://localhost:8100/api/v1/auth/login"
      }
    },
    {
      "name": "2. Invoke Agent",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{jwt_token}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"query\": \"Suche nach Artikeln über Künstliche Intelligenz und erstelle einen Bericht\"\n}",
          "options": {
            "raw": {
              "language": "json"
            }
          }
        },
        "url": "http://localhost:8110/api/v1/agent/invoke"
      }
    },
    {
      "name": "3. List Conversations",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{jwt_token}}"
          }
        ],
        "url": {
          "raw": "http://localhost:8110/api/v1/agent/conversations?limit=10",
          "host": ["192", "168", "178", "86"],
          "port": "8110",
          "path": ["api", "v1", "agent", "conversations"],
          "query": [
            {
              "key": "limit",
              "value": "10"
            }
          ]
        }
      }
    }
  ]
}
```

**Import in Postman:**
1. Postman öffnen
2. File → Import → Paste JSON
3. Environment erstellen mit `base_url` und `jwt_token` Variablen
4. Collection ausführen

**Vorteile:**
- ✅ Schnelles Testing
- ✅ Keine Programmierung erforderlich
- ✅ Team-Sharing möglich

**Nachteile:**
- ❌ Manuelle Bedienung
- ❌ Keine Automatisierung

---

## Zusammenfassung

| Option | Komplexität | Integration | Empfehlung |
|--------|-------------|-------------|------------|
| **MCP Bridge Server** | Hoch | Claude Desktop | Nur für fortgeschrittene Nutzer |
| **Terminal Script** | Niedrig | Standalone | ✅ **Empfohlen für CLI-Nutzer** |
| **Web UI** | Mittel | Browser | ✅ **Empfohlen für beste UX** |
| **Postman** | Niedrig | Standalone | ✅ **Empfohlen für Testing** |

---

## Empfohlene Lösung

Für die meisten Use Cases: **Terminal Script + Web UI**

1. **Entwicklung & Testing:** Terminal Script
2. **Produktive Nutzung:** Web UI Integration
3. **API Testing:** Postman Collection

---

## Technische Limitierungen

### Warum kann Claude Desktop nicht direkt HTTP APIs verwenden?

1. **Security Model:** Claude Desktop isoliert Tools in lokalen Prozessen
2. **MCP Design:** MCP ist für lokale, vertrauenswürdige Tools konzipiert
3. **State Management:** MCP-Server sind stateless, HTTP APIs sind stateful
4. **Authentication:** MCP hat keine built-in Auth, HTTP APIs erfordern JWT/OAuth

### Alternative: Claude API (Anthropic)

Wenn du Claude's KI für den Agent Service nutzen möchtest, könntest du:

1. **Claude API direkt aufrufen** (statt Claude Desktop):
   ```python
   import anthropic

   client = anthropic.Anthropic(api_key="your-key")

   response = client.messages.create(
       model="claude-3-5-sonnet-20241022",
       tools=[...],  # Define your tools
       messages=[{"role": "user", "content": query}]
   )
   ```

2. **Agent Service als Claude Tool anbieten**:
   Der Agent Service könnte selbst als Tool für Claude API definiert werden.

---

## Support & Feedback

Falls du eine spezifische Integration-Anforderung hast, kontaktiere das Development Team für eine maßgeschneiderte Lösung.

---

**Last Updated:** 2025-10-23
**Document Version:** 1.0.0
