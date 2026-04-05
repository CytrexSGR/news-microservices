# Claude Desktop vs Claude.ai Web - Critical Differences

## ⚠️ Das Problem

**MCP Tools funktionieren NUR in Claude Desktop (lokale App), NICHT in Claude.ai (Browser)!**

---

## 🖥️ Claude Desktop (App) ✅ RICHTIG

### So sieht es aus:

**Window Title:**
```
Claude                                    [_ □ X]
```
_(Kein "claude.ai" in der Titelleiste, keine URL-Leiste)_

**Main Interface:**
```
┌─────────────────────────────────────────────────────┐
│ ☰  New Chat                                    ⚙️   │
├─────────────────────────────────────────────────────┤
│                                                     │
│   Your conversations                                │
│   ├─ Today                                         │
│   ├─ Yesterday                                     │
│   └─ Previous 7 Days                               │
│                                                     │
│   [Chat messages hier...]                          │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Type a message...                              [→] │
└─────────────────────────────────────────────────────┘
```

### Settings → MCP Servers:

```
Developer
  MCP Servers
    Lokale MCP-Server
    ├── mcp-intelligence
    │   Status: running ✅
    │   Befehl: C:\Program Files\nodejs\node.exe
    │   Argumente: C:\mcp-intelligence-proxy.js
    │   Umgebungsvariablen: MCP_SERVER_TYPE=stdio
    │   [Logs anzeigen] [Neu starten] [Bearbeiten]
```

### Available Tools Response:

```
Ich habe Zugriff auf folgende MCP Tools:

Analysis (3 Tools):
• analyze_article - Analyze article using content-analysis-v3
• extract_entities - Extract named entities
• get_analysis_status - Get analysis status

Entity (2 Tools):
• canonicalize_entity - Canonicalize entity
• get_entity_clusters - Get entity clusters

Intelligence (6 Tools):
• detect_intelligence_patterns - Detect intelligence patterns
• analyze_graph_quality - Analyze knowledge graph
• get_event_clusters - Get event clusters
• get_cluster_details - Get cluster details
• get_latest_events - Get latest events
• get_intelligence_overview - Get intelligence overview

Narrative (4 Tools):
• analyze_text_narrative - Analyze narrative frames
• get_narrative_frames - Get narrative frames
• get_bias_analysis - Get bias analysis
• get_narrative_overview - Get narrative overview
```

### Installation:

```
C:\Users\andre\AppData\Local\Programs\Claude\
├── Claude.exe          ← Main executable
├── resources\
└── ...
```

### How to Open:

1. **Windows Start Menu:** Type "Claude" → Click "Claude"
2. **Desktop Icon:** Double-click purple Claude icon
3. **Taskbar:** Purple icon (if pinned)
4. **Direct:** `C:\Users\andre\AppData\Local\Programs\Claude\Claude.exe`

---

## 🌐 Claude.ai Web (Browser) ❌ FALSCH FÜR MCP

### So sieht es aus:

**Browser Tab:**
```
claude.ai - Google Chrome                [_ □ X]
```
_(Browser-Tab, URL-Leiste zeigt "https://claude.ai/...")_

**Main Interface:**
```
┌─────────────────────────────────────────────────────┐
│ 🔗 https://claude.ai/chat/...                   ⚙️  │
├─────────────────────────────────────────────────────┤
│                                                     │
│   [Same chat interface wie Desktop...]             │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Type a message...                              [→] │
└─────────────────────────────────────────────────────┘
```

### Settings → MCP Servers:

**❌ EXISTIERT NICHT!**

Settings in Claude.ai Web hat KEINE MCP-Option.

### Available Tools Response:

```
In dieser Claude.ai-Umgebung sind keine MCP (Model Context Protocol) Tools direkt verfügbar.

Verfügbare Standard-Tools:
• web_search - Websuche
• web_fetch - Webseiten abrufen
• bash_tool - Bash-Befehle
• str_replace - Text ersetzen
• view - Dateien anzeigen
• create_file - Dateien erstellen
• conversation_search - Unterhaltungen durchsuchen
• recent_chats - Letzte Chats
• memory_user_edits - Benutzer-Edits
```

_(Das sind die Standard-Tools von Claude.ai Web, KEINE MCP Tools!)_

### How to Access:

1. Open Chrome/Edge/Firefox
2. Go to https://claude.ai
3. Login with account

---

## 🔍 Wie erkenne ich, was ich verwende?

### Test 1: Window Title

**Claude Desktop:**
- Title: `Claude` (ohne ".ai")
- Kein Browser-Tab
- Keine URL-Leiste

**Claude.ai Web:**
- Title: `claude.ai - Chrome/Edge/Firefox`
- Browser-Tab sichtbar
- URL-Leiste: `https://claude.ai/...`

### Test 2: Settings Check

**Claude Desktop:**
- Settings → Developer → **MCP Servers vorhanden** ✅

**Claude.ai Web:**
- Settings → Developer → **Kein MCP-Menü** ❌

### Test 3: Taskbar/Start Menu

**Claude Desktop:**
- Purple icon in Taskbar
- Start Menu: "Claude" (app)

**Claude.ai Web:**
- Browser icon (Chrome/Edge/etc.)
- Start Menu: "Google Chrome" / "Microsoft Edge"

---

## 📊 Feature Comparison

| Feature | Claude Desktop | Claude.ai Web |
|---------|---------------|--------------|
| MCP Tools | ✅ Yes | ❌ No |
| Local Server Connection | ✅ Yes | ❌ No |
| Custom Integrations | ✅ Yes | ❌ No |
| File System Access | ✅ Yes (via MCP) | ❌ No |
| Conversation History | ✅ Synced | ✅ Synced |
| Web Search | ✅ Yes | ✅ Yes |
| Code Generation | ✅ Yes | ✅ Yes |
| Settings → MCP | ✅ Yes | ❌ No |

---

## 🎯 Deine Situation

**Laut deiner letzten Nachricht:**

```
"In dieser Claude.ai-Umgebung sind keine MCP (Model Context Protocol) Tools direkt verfügbar."
```

**Das ist die Antwort von Claude.ai Web, NICHT Claude Desktop!**

**Die Tools die du aufgelistet hast:**
- `web_search`
- `web_fetch`
- `bash_tool`
- `str_replace`
- `view`
- `create_file`

**Das sind Claude.ai Web Tools, KEINE MCP Tools!**

---

## ✅ Was du tun musst

### Schritt 1: Schließe den Browser

Schließe Chrome/Edge/Firefox wo Claude.ai läuft.

### Schritt 2: Öffne Claude Desktop

**Option A: Start Menu**
```
Windows Start → Type "Claude" → Click "Claude" (purple icon)
```

**Option B: Direct Launch**
```
C:\Users\andre\AppData\Local\Programs\Claude\Claude.exe
```

**Option C: Taskbar** (wenn gepinned)
```
Click purple Claude icon in taskbar
```

### Schritt 3: Verify

**Du bist in Claude Desktop wenn:**
1. ✅ Kein Browser-Tab sichtbar
2. ✅ Kein URL-Leiste
3. ✅ Window-Titel ist nur "Claude"
4. ✅ Settings → Developer → MCP Servers existiert

### Schritt 4: Check MCP Status

```
Settings → Developer → MCP Servers

Sollte zeigen:
mcp-intelligence: running ✅
```

### Schritt 5: New Chat

1. Click "+ New Chat" (top left)
2. Wait 2-3 seconds (server connects)
3. Ask: "Liste alle verfügbaren MCP Tools auf"

### Schritt 6: Verify Response

**Erwartete Antwort:**
```
Verfügbare MCP Tools:

Analysis:
• analyze_article
• extract_entities
• get_analysis_status

[... 12 weitere Tools ...]
```

**NICHT diese Antwort:**
```
In dieser Claude.ai-Umgebung sind keine MCP Tools verfügbar
```

---

## 🆘 Troubleshooting

### "Ich habe kein Claude Desktop"

**Download:**
https://claude.ai/download

**Install:**
1. Download Claude-Setup.exe
2. Run installer
3. Follow prompts
4. Launch Claude Desktop

### "Claude Desktop startet nicht"

**Check:**
```powershell
# In PowerShell:
Test-Path "C:\Users\andre\AppData\Local\Programs\Claude\Claude.exe"
```

**If False:**
- Claude Desktop not installed
- Download and install from https://claude.ai/download

**If True but doesn't start:**
- Right-click → Run as Administrator
- Check Windows Event Viewer for errors

### "Ich sehe MCP Server, aber Tools nicht"

**Das ist ein anderes Problem!**

Siehe: [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)

---

## 📝 Summary

**Das Wichtigste:**

1. **Claude Desktop** = Lokale Windows-App = ✅ MCP Tools funktionieren
2. **Claude.ai Web** = Browser-Version = ❌ Keine MCP Tools

**Du MUSST Claude Desktop verwenden, nicht den Browser!**

**Aktuell nutzt du wahrscheinlich:** Claude.ai Web (Browser)
**Du solltest nutzen:** Claude Desktop (App)

**Quick Check:**
- Siehst du eine URL-Leiste? → ❌ Falsches Programm
- Kein URL-Leiste, nur "Claude" als Title? → ✅ Richtiges Programm

---

**Nächster Schritt:** Öffne Claude Desktop (App) und erstelle neue Chat-Session dort!
