#!/usr/bin/sh

SERENA_MCP_URL="${SERENA_MCP_URL:-http://serena:9121/sse}"

# stdin
claude mcp add sequential-thinking -s project -- npx -y @modelcontextprotocol/server-sequential-thinking

# sse
claude mcp add serena -s project --transport sse "$SERENA_MCP_URL"

# custom script
claude mcp add cognee -s project -- sh bin/run_cognee.sh
