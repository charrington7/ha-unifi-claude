# Changes

## 1.3.0

- The UniFi server now runs in its HTTP-only mode (UNIFI_MCP_STDIO_ENABLED=false, from unifi-mcp-shared 0.6.42), added upstream in https://github.com/sirkirby/unifi-mcp/issues/1047. This replaces a workaround that kept an unused input connection open just to stop the server from shutting down.
- UniFi server 0.48.1, relay 0.3.21, shared package pinned at 0.6.42.
- The startup test also checks the server keeps running on HTTP alone.

## 1.2.0

- UniFi server updated from 0.39.3 to 0.48.0, relay from 0.3.15 to 0.3.21.

## 1.0.0

- First version.
