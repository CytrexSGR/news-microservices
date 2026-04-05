#!/usr/bin/env node

/**
 * MCP Intelligence Server Proxy for Claude Desktop
 *
 * WICHTIG: Ändere die SERVER_URL (Zeile 19) auf deine Server-IP!
 *
 * Protocol Version: 2025-06-18
 */

const http = require('http');

// ============================================================================
// CONFIGURATION - ÄNDERE DIESE ZEILE MIT DEINER SERVER-IP!
// ============================================================================
const SERVER_URL = process.env.MCP_SERVER_URL || 'http://localhost:9001';
// ============================================================================

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
    // MCP Protocol: Notifications (no response needed)
    // Note: Check for 'id' property existence, not truthiness (id can be 0!)
    if (!('id' in request)) {
      log('Received notification (no response needed):', request.method);
      return null; // Don't respond to notifications
    }

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
        if (response !== null) {
          stdout.write(JSON.stringify(response) + '\n');
        }
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
