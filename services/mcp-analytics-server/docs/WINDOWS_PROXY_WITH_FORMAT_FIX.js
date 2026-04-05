#!/usr/bin/env node

/**
 * MCP Intelligence Server Proxy (Windows)
 *
 * Bridges Windows Claude Desktop with Linux MCP Intelligence Server
 * Converts backend tool format to MCP specification format
 *
 * Protocol: MCP (Model Context Protocol) 2025-06-18
 * Transport: JSON-RPC 2.0 over stdin/stdout
 */

const http = require('http');
const readline = require('readline');

// Configuration
const SERVER_URL = 'http://localhost:9001';
const DEBUG = process.env.DEBUG === 'true';

// Logging utility
function log(message, data = null) {
  if (DEBUG && data) {
    console.error('[MCP Proxy]', message, JSON.stringify(data));
  } else {
    console.error('[MCP Proxy]', message);
  }
}

/**
 * Convert backend tool format to MCP inputSchema format
 *
 * Backend format:
 * {
 *   "name": "tool_name",
 *   "parameters": [
 *     {"name": "param1", "type": "string", "required": true, "description": "..."}
 *   ]
 * }
 *
 * MCP format:
 * {
 *   "name": "tool_name",
 *   "inputSchema": {
 *     "type": "object",
 *     "properties": {
 *       "param1": {"type": "string", "description": "..."}
 *     },
 *     "required": ["param1"]
 *   }
 * }
 */
function convertToolToMCPFormat(backendTool) {
  const properties = {};
  const required = [];

  // Convert parameters array to properties object
  if (backendTool.parameters && Array.isArray(backendTool.parameters)) {
    for (const param of backendTool.parameters) {
      properties[param.name] = {
        type: param.type,
        description: param.description
      };

      // Add enum if present
      if (param.enum && Array.isArray(param.enum) && param.enum.length > 0) {
        properties[param.name].enum = param.enum;
      }

      // Add to required array if required
      if (param.required) {
        required.push(param.name);
      }
    }
  }

  // Build MCP-compliant tool definition
  const mcpTool = {
    name: backendTool.name,
    description: backendTool.description,
    inputSchema: {
      type: 'object',
      properties: properties
    }
  };

  // Only add required if there are required parameters
  if (required.length > 0) {
    mcpTool.inputSchema.required = required;
  }

  return mcpTool;
}

// HTTP request helper
async function makeRequest(path) {
  return new Promise((resolve, reject) => {
    log(`Making HTTP request to: ${SERVER_URL}${path}`);

    const req = http.get(`${SERVER_URL}${path}`, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          log(`HTTP response received from ${path}`);
          resolve(result);
        } catch (error) {
          log(`Error parsing response from ${path}:`, error);
          reject(error);
        }
      });
    });

    req.on('error', (error) => {
      log(`HTTP request error for ${path}:`, error);
      reject(error);
    });

    req.end();
  });
}

// MCP Protocol: List tools from backend and convert to MCP format
async function listTools() {
  try {
    const result = await makeRequest('/mcp/tools/list');

    if (!result.tools || !Array.isArray(result.tools)) {
      log('Warning: Backend returned invalid tools format');
      return { tools: [] };
    }

    // Convert each tool to MCP format
    const mcpTools = result.tools.map(convertToolToMCPFormat);

    log(`Converted ${mcpTools.length} tools to MCP format`);

    return { tools: mcpTools };
  } catch (error) {
    log('Error fetching tools list:', error);
    throw error;
  }
}

// MCP Protocol: Call tool on backend
async function callTool(toolName, toolArgs) {
  try {
    return await makeRequest(`/mcp/tools/call?name=${toolName}&args=${encodeURIComponent(JSON.stringify(toolArgs))}`);
  } catch (error) {
    log(`Error calling tool ${toolName}:`, error);
    throw error;
  }
}

// MCP Protocol: Message handler
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
            version: '1.0.1'  // Incremented version
          }
        }
      };
    }

    // MCP Protocol: Tools List (with format conversion)
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

    // Unknown method
    log('Unknown method:', request.method);
    return {
      jsonrpc: '2.0',
      id: request.id,
      error: {
        code: -32601,
        message: 'Method not found',
        data: { method: request.method }
      }
    };

  } catch (error) {
    log('Error handling request:', error);
    return {
      jsonrpc: '2.0',
      id: request.id,
      error: {
        code: -32603,
        message: 'Internal error',
        data: { error: error.message }
      }
    };
  }
}

// Main: Set up stdin/stdout communication
async function main() {
  log('MCP Intelligence Server Proxy starting...');
  log(`Server URL: "${SERVER_URL}"`);
  log(`DEBUG mode: ${DEBUG}`);

  const stdin = process.stdin;
  const stdout = process.stdout;

  // Line-buffered input processing
  let buffer = '';

  stdin.setEncoding('utf8');

  stdin.on('data', async (chunk) => {
    buffer += chunk;

    // Process complete lines
    const lines = buffer.split('\n');
    buffer = lines.pop() || ''; // Keep incomplete line in buffer

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const request = JSON.parse(line);
        const response = await handleMessage(request);

        // Only write response if not null (notifications return null)
        if (response !== null) {
          stdout.write(JSON.stringify(response) + '\n');
        }
      } catch (error) {
        log('Parse error:', error);
        // Send error response
        stdout.write(JSON.stringify({
          jsonrpc: '2.0',
          id: null,
          error: {
            code: -32700,
            message: 'Parse error',
            data: { error: error.message }
          }
        }) + '\n');
      }
    }
  });

  stdin.on('end', () => {
    log('stdin closed, exiting...');
    process.exit(0);
  });

  stdin.on('error', (error) => {
    log('stdin error:', error);
    process.exit(1);
  });

  // Keep process alive
  process.stdin.resume();

  log('Proxy ready, waiting for requests...');
}

// Start the proxy
main().catch((error) => {
  log('Fatal error:', error);
  process.exit(1);
});
