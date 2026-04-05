# Chrome DevTools MCP Setup

**Erstellt:** 2025-10-17
**Problem:** Chrome DevTools MCP konnte sich nicht mit Chrome verbinden
**Lösung:** Chrome muss manuell mit Remote Debugging gestartet werden

---

## Das Problem

Chrome DevTools MCP Fehler:
- `Protocol error (Target.setDiscoverTargets): Target closed`
- `Not connected`

**Root Cause:** Das MCP startet Chrome nicht automatisch in Claude Code. Es muss mit einem bereits laufenden Chrome verbunden werden.

---

## Die Lösung

### 1. Chrome mit Remote Debugging starten

```bash
~/scripts/start-chrome-devtools.sh
```

Oder manuell:
```bash
google-chrome \
  --remote-debugging-port=9222 \
  --no-first-run \
  --no-default-browser-check \
  --no-sandbox \
  --disable-dev-shm-usage \
  --headless=new \
  > /tmp/chrome.log 2>&1 &
```

**Wichtig:** `--no-sandbox` ist für Entwicklung OK, aber nicht für Produktion.

### 2. Verify Chrome läuft

```bash
# Check Chrome process
ps aux | grep "[c]hrome.*remote-debugging"

# Test DevTools API
curl -s http://localhost:9222/json/version | jq '.'

# Expected output:
# {
#   "Browser": "Chrome/141.0.7390.107",
#   "Protocol-Version": "1.3",
#   "webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser/..."
# }
```

### 3. Claude Code Konfiguration

**Datei:** `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "chrome-devtools-mcp@latest",
        "--browserUrl",
        "http://127.0.0.1:9222"
      ]
    }
  }
}
```

### 4. Claude Code neu starten

Nach Config-Änderungen **MUSS** Claude Code neu gestartet werden.

---

## Verwendung

Nach Setup funktionieren die MCP Tools:

```javascript
// Neue Seite öffnen
mcp__chrome-devtools__new_page({
  url: "http://localhost:3000",
  timeout: 30000
})

// Seiten auflisten
mcp__chrome-devtools__list_pages()

// Screenshot machen
mcp__chrome-devtools__screenshot({
  format: "png"
})
```

---

## Troubleshooting

### Chrome startet nicht

```bash
# Check logs
tail -f /tmp/chrome.log

# Common issues:
# - Port 9222 bereits belegt → killall chrome
# - Sandbox error → --no-sandbox verwenden
# - Display error → --headless=new verwenden
```

### MCP verbindet nicht

```bash
# 1. Chrome läuft?
curl http://localhost:9222/json/version

# 2. MCP konfiguriert?
cat ~/.config/claude/claude_desktop_config.json | jq '.mcpServers."chrome-devtools"'

# 3. Claude Code neu starten!
```

### Permission denied

```bash
# Sandbox issues → use --no-sandbox flag
# Script nicht ausführbar → chmod +x ~/scripts/start-chrome-devtools.sh
```

---

## Automatischer Start (Optional)

Um Chrome automatisch beim System-Start zu starten:

```bash
# Systemd service erstellen
sudo nano /etc/systemd/system/chrome-devtools.service
```

```ini
[Unit]
Description=Chrome with Remote Debugging for DevTools MCP
After=network.target

[Service]
Type=forking
User=cytrex
ExecStart=/home/cytrex/scripts/start-chrome-devtools.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable chrome-devtools
sudo systemctl start chrome-devtools
```

---

## Warum --no-sandbox?

**Problem:** Chrome sandbox benötigt spezielle Kernel-Features (user namespaces).

**Error ohne --no-sandbox:**
```
FATAL:sandbox/linux/services/credentials.cc:131] Check failed: . : Permission denied (13)
```

**Lösungen:**
1. ✅ **Development:** `--no-sandbox` verwenden (wie wir es tun)
2. **Production:** Systemd mit Capabilities konfigurieren
3. **Docker:** `--cap-add=SYS_ADMIN` oder `--security-opt seccomp=unconfined`

**Für lokale Entwicklung ist --no-sandbox akzeptabel.**

---

## Logs & Debugging

```bash
# Chrome logs
tail -f /tmp/chrome.log

# DevTools API testen
curl -s http://localhost:9222/json/list | jq '.'

# Neue Seite via API öffnen
curl -X PUT -d '{"url":"https://example.com"}' \
  http://localhost:9222/json/new | jq '.'

# Seite schließen
curl -X DELETE http://localhost:9222/json/close/<PAGE_ID>
```

---

## Zusammenfassung

**Setup Steps:**
1. ✅ Chrome mit `~/scripts/start-chrome-devtools.sh` starten
2. ✅ Config in `~/.config/claude/claude_desktop_config.json` erstellen
3. ✅ Claude Code neu starten
4. ✅ MCP Tools nutzen

**Quick Test:**
```bash
# 1. Start Chrome
~/scripts/start-chrome-devtools.sh

# 2. Test API
curl http://localhost:9222/json/version

# 3. Restart Claude Code

# 4. Try MCP tools
```

**Time to fix:** ~15 Minuten
**Time saved:** Stunden debugging ✅

---

*Last updated: 2025-10-17 - Initial setup after MCP connection issues*
