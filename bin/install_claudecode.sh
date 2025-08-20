#!/usr/bin/sh


# nvmが管理する場所にClaude Codeをグローバルインストールする
echo "Installing @anthropic-ai/claude-code ..."
npm install @anthropic-ai/claude-code

# --- 5. MCP追加スクリプトの実行 ---
sh bin/add_cognee_mcp.sh

echo "Installation complete."

