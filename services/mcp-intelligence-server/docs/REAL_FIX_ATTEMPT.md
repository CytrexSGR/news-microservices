# MCP Intelligence Server - Real Fix Attempt

## Problem Statement

**Status:**
- ✅ Server running in Claude Desktop Settings
- ✅ Logs show 15 tools successfully transmitted (16:52:03)
- ✅ Protocol handshake successful
- ❌ Tools NOT appearing in chat sessions

**Critical Warning in main.log:**
```
[warn] UtilityProcess Check: Extension mcp-intelligence not found in installed extensions
```

This suggests Claude Desktop is confusing the stdio server with an extension.

---

## Hypothesis

Claude Desktop may be treating `mcp-intelligence` as an extension name rather than a stdio server, despite the `MCP_SERVER_TYPE=stdio` environment variable.

**Possible causes:**
1. Name collision with extension namespace
2. Cache/state issue in Claude Desktop
3. Tool registration bug in Claude Desktop
4. Environment variable not being respected

---

## Fix Attempt #1: Rename Server

### Why This Might Work

The name `mcp-intelligence` follows the pattern of marketplace extensions. Renaming it to something clearly local (e.g., `local-intelligence-server`) might prevent the confusion.

### Steps

1. **Update Windows config:**

`%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "local-intelligence-server": {
      "command": "C:\\Program Files\\nodejs\\node.exe",
      "args": ["C:\\mcp-intelligence-proxy.js"],
      "env": {
        "MCP_SERVER_TYPE": "stdio"
      }
    }
  }
}
```

2. **Restart Claude Desktop:**
   - Close Claude Desktop completely (Exit from taskbar)
   - Re-open Claude Desktop
   - Check Settings → MCP → Should show "local-intelligence-server"

3. **Test in new chat:**
   - Create new chat
   - Ask: "Liste alle verfügbaren MCP Tools auf"

---

## Fix Attempt #2: Clear Claude Desktop Cache

### Why This Might Work

Claude Desktop might have cached the server as "extension not found" and isn't re-checking.

### Steps

1. **Close Claude Desktop completely**

2. **Clear cache directories:**

```powershell
# In PowerShell:
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Cache\*"
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Code Cache\*"
```

**Warning:** This clears all cached data. Conversation history is NOT affected (stored separately).

3. **Restart Claude Desktop**

4. **Check logs:**
   - Should NOT see "Extension mcp-intelligence not found" warning
   - Should see successful server start

5. **Test in new chat**

---

## Fix Attempt #3: Explicit Server Type in Config

### Why This Might Work

Maybe the environment variable isn't being read correctly. Try a different config approach.

### Steps

1. **Try alternative config format:**

```json
{
  "mcpServers": {
    "local-intel": {
      "command": "node",
      "args": ["C:\\mcp-intelligence-proxy.js"],
      "type": "stdio"
    }
  }
}
```

Note: Using "type" field instead of environment variable.

2. **Restart and test**

---

## Fix Attempt #4: Verify Tool Registration

### Check if tools are loaded but not exposed

1. **Check Claude Desktop developer tools:**
   - In Claude Desktop: Help → Toggle Developer Tools
   - Console tab
   - Look for MCP-related messages
   - Search for "mcp-intelligence" or "tools"

2. **Check for JavaScript errors:**
   - Errors related to tool registration
   - Errors related to extension loading

3. **Look for tool list:**
   - In Console, type: `localStorage` or `sessionStorage`
   - Look for MCP tool information

---

## Fix Attempt #5: Minimal Test Server

### Create simplest possible MCP server to rule out proxy issues

**Create: `C:\minimal-mcp-test.js`:**

```javascript
#!/usr/bin/env node

const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

function log(msg) {
  console.error('[Minimal MCP]', msg);
}

rl.on('line', (line) => {
  try {
    const request = JSON.parse(line);
    log('Request: ' + request.method);

    let response = null;

    if (request.method === 'initialize') {
      response = {
        jsonrpc: '2.0',
        id: request.id,
        result: {
          protocolVersion: '2025-06-18',
          capabilities: { tools: {} },
          serverInfo: {
            name: 'minimal-test-server',
            version: '1.0.0'
          }
        }
      };
    }

    if (request.method === 'tools/list') {
      response = {
        jsonrpc: '2.0',
        id: request.id,
        result: {
          tools: [{
            name: 'test_tool',
            description: 'Simple test tool',
            inputSchema: {
              type: 'object',
              properties: {},
              required: []
            }
          }]
        }
      };
    }

    if (request.method === 'tools/call') {
      response = {
        jsonrpc: '2.0',
        id: request.id,
        result: {
          content: [{
            type: 'text',
            text: 'Test tool executed successfully!'
          }]
        }
      };
    }

    if (response) {
      console.log(JSON.stringify(response));
    }
  } catch (error) {
    log('Error: ' + error.message);
  }
});

log('Minimal MCP server started');
```

**Config:**
```json
{
  "mcpServers": {
    "minimal-test": {
      "command": "node",
      "args": ["C:\\minimal-mcp-test.js"]
    }
  }
}
```

**Expected:**
- Server starts
- 1 tool: "test_tool"
- Should appear in chat

**If this works:**
- Problem is in mcp-intelligence-proxy.js

**If this doesn't work:**
- Problem is in Claude Desktop configuration/setup

---

## Diagnostic Questions

1. **Version Check:**
   - What Claude Desktop version? (Help → About)
   - Expected: 1.0.1405 or higher

2. **Other MCP Servers:**
   - Do you have other MCP servers configured?
   - Do THEY work in chat?

3. **Tool Appearance:**
   - How are you checking for tools?
   - Asking "Liste alle verfügbaren MCP Tools"?
   - Or trying to use them directly?

4. **Session Timing:**
   - Do you see any loading indicator when creating new chat?
   - How long do you wait after "New Chat" before asking?

5. **Logs Detail:**
   - After creating new chat, what appears in mcp-server-mcp-intelligence.log?
   - Does it show initialize + tools/list sequence?

---

## Next Steps

**Immediate action:**

1. Try Fix #1 (Rename to "local-intelligence-server")
2. If that doesn't work, try Fix #2 (Clear cache)
3. If that doesn't work, try Fix #5 (Minimal test server)

**Report back:**
- Which fix you tried
- New logs after the fix
- Screenshot of chat when you ask for tools
- Claude Desktop version (Help → About)

---

## Understanding the Warning

```
[warn] UtilityProcess Check: Extension mcp-intelligence not found in installed extensions
```

**What this means:**
- Claude Desktop checked if "mcp-intelligence" is an installed extension
- It's NOT an extension (it's a stdio server)
- This warning SHOULD be harmless if `MCP_SERVER_TYPE=stdio` is set
- But the warning suggests Claude Desktop is still treating it as extension

**Why this matters:**
- Extensions use different loading mechanism
- stdio servers use process spawn
- If Claude Desktop thinks it's an extension, it won't spawn the process correctly
- Even though it shows "running", the tools might not be registered

**This is likely a Claude Desktop bug** - it should recognize stdio servers by:
1. The environment variable `MCP_SERVER_TYPE=stdio`
2. The command/args structure (not a marketplace ID)

But the warning shows it's still checking for it as an extension FIRST.
