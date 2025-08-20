#!/usr/bin/sh

d=$(cd $(dirname $0) && pwd)
cd $d/../


# --- 1. nvmのインストールと有効化 ---
curl -sSL -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # nvmをロードする推奨方法

# --- 2. Node.jsのインストールと使用 ---
# 最新のLTS(長期サポート)版をインストールし、現在のセッションで使用する
# 'nvm use'も内部的に実行されるため、別途'use'コマンドは不要
nvm install --lts

# --- 3. プロジェクトの依存関係をインストール ---
# これはプロジェクトのローカルパッケージなので変更なし
npm install


sh bin/install_claudecode.sh

sh bin/install_codexcli.sh

sh bin/install_geminicli.sh

sh bin/install_cursorcli.sh

