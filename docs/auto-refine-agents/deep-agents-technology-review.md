# Deep Agents 技術調査レポート

**調査日**: 2025-11-03  
**目的**: LangChain Deep Agents の技術的詳細を把握し、auto-refine-agents プロジェクトへの応用可能性を評価する  
**調査対象**: [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents)

---

## 1. 概要

### 1.1 何者か

Deep Agents は、LangChain の創設者によって開発された、複雑で長期的なタスクを自律的に遂行できるエージェント構築のための Python ライブラリです。

**基本情報**:
- **リポジトリ**: [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents)
- **パッケージ**: [deepagents (PyPI)](https://pypi.org/project/deepagents/)
- **最新バージョン**: 0.2.4 (2025-10-31)
- **ライセンス**: MIT
- **Python要件**: >=3.11, <4.0
- **公式ドキュメント**: [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview)

### 1.2 設計思想

従来の「LLM→ツール呼び出し→ループ」型の「浅い（shallow）」エージェントの限界を克服するため、以下の4つの要素を標準装備しています：

1. **計画ツール** (`write_todos`) - 複雑なタスクをサブタスクに分解・追跡
2. **サブエージェント** (`task` ツール) - 専門的なサブエージェントへの委譲
3. **ファイルシステム** - コンテキスト管理と長文データの外部化
4. **詳細なシステムプロンプト** - Claude Code にインスパイアされた詳細な指示

**インスピレーション**: Claude Code, Deep Research, Manus などの成功アプリケーションのパターンを一般化

---

## 2. アーキテクチャ

### 2.1 コア設計原則

- **LangGraph ベース**: エージェントは LangGraph の `Runnable`（グラフ）として実装
- **ミドルウェア合成**: 機能は独立したミドルウェアとして実装され、必要に応じて組み合わせ可能
- **プラガブルバックエンド**: ファイルシステムは複数のバックエンド実装を切り替え可能

### 2.2 エージェント生成

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    tools=[...],                 # 任意の LangChain Tool/関数
    system_prompt="...",         # 詳細プロンプト（ユースケース特化を推奨）
    model="anthropic:claude-...",# 任意の LangChain チャットモデルも可
    middleware=[...],            # 追加ミドルウェア（任意）
    subagents=[...],             # サブエージェント定義 or 事前構築グラフ
    interrupt_on={...},          # HITL 設定（ツールごと）
    backend=...                  # ファイルシステムのバックエンド（後述）
)
```

生成されたエージェントは標準的な LangGraph グラフとして操作可能：
- `agent.invoke(...)` - 同期実行
- `agent.astream(...)` - 非同期ストリーミング
- LangGraph のチェックポイント/メモリ機能もそのまま利用可能

---

## 3. コア機能詳細

### 3.1 Planning & Task Decomposition

**実装**: `TodoListMiddleware`

- **ツール**: `write_todos` - ToDoリストの作成・更新
- **機能**: 
  - 複雑なタスクを離散的なステップに分解
  - 進捗追跡
  - 新しい情報に基づく計画の適応的更新
- **使用例**: Claude Code のように、複雑なマルチステップタスクの前に ToDo リストを書き出し、実行中に更新

### 3.2 Context Management

**実装**: `FilesystemMiddleware`

**提供ツール**:
- `ls` - ファイル一覧
- `read_file` - ファイル読み込み（オフセット・行数指定可）
- `write_file` - ファイル作成
- `edit_file` - ファイル編集（文字列置換）
- `glob` - パターンマッチング
- `grep` - テキスト検索

**用途**:
- 大きなコンテキストをメモリにオフロード（コンテキストウィンドウオーバーフロー防止）
- 可変長のツール結果（web検索、RAG結果など）の処理
- 中間成果物の保存・再利用

### 3.3 Subagent Spawning

**実装**: `SubAgentMiddleware`

- **ツール**: `task` - 専門的なサブエージェントの生成・呼び出し
- **利点**:
  - コンテキスト分離（メインエージェントのコンテキストをクリーンに保つ）
  - 特定のサブタスクに深く集中可能
  - カスタムプロンプト・ツールセットを持つサブエージェントの定義

**サブエージェント定義**:
```python
subagent = {
    "name": "research-agent",
    "description": "Used to research more in depth questions",
    "system_prompt": "You are a great researcher",
    "tools": [internet_search],
    "model": "openai:gpt-4o",  # オプション: メインエージェントのモデルをオーバーライド
    "middleware": [],            # オプション: 追加ミドルウェア
    "interrupt_on": {...}        # オプション: カスタム HITL 設定
}
```

**事前構築グラフの利用**:
```python
from deepagents.middleware.subagents import CompiledSubAgent

custom_subagent = CompiledSubAgent(
    name="data-analyzer",
    description="Specialized agent for complex data analysis tasks",
    runnable=custom_graph  # 事前に構築した LangGraph グラフ
)
```

### 3.4 Long-term Memory

**実装**: LangGraph の `Store` との統合

- **機能**: スレッド間で持続的なメモリを拡張
- **用途**: 以前の会話から情報を保存・取得、エージェントをまたいだ知識の共有

### 3.5 Human-in-the-Loop (HITL)

**実装**: LangGraph の `interrupt` 機能との統合

- **設定**: `interrupt_on` パラメータでツールごとに人間の承認を要求
- **動作**: エージェントが指定されたツールを実行する前に一時停止し、ユーザーのフィードバックを待つ
- **決定オプション**: approve, edit, reject など

```python
agent = create_deep_agent(
    tools=[get_weather],
    interrupt_on={
        "get_weather": {
            "allowed_decisions": ["approve", "edit", "reject"]
        },
    }
)
```

---

## 4. ファイルシステムバックエンド

### 4.1 バックエンドの種類

#### StateBackend (エフェメラル、デフォルト)

**動作**:
- LangGraph エージェントの state にファイルを保存
- 現在のスレッド内でのみ持続
- チェックポイント経由で複数のエージェントターン間で持続

**用途**:
- 中間結果のスクラッチパッド
- 大きなツール出力の自動エビクション（エージェントが後で少しずつ読み戻せる）

#### FilesystemBackend (ローカルディスク)

**動作**:
- 設定可能な `root_dir` の下で実際のファイルを読み書き
- `root_dir` は絶対パスである必要がある
- `virtual_mode=True` でサンドボックス化・パス正規化が可能

**セキュリティ機能**:
- 安全なパス解決
- シンボリックリンクトラバーサルの防止（可能な限り）
- ripgrep による高速 `grep` サポート

**用途**:
- ローカルマシンのプロジェクト
- CI サンドボックス
- マウントされた永続ボリューム

#### StoreBackend (LangGraph Store)

**動作**:
- LangGraph の `BaseStore` にファイルを保存
- スレッド間での永続的なストレージを可能に

**用途**:
- LangGraph store が既に設定されている環境（Redis、Postgres、クラウド実装など）
- LangSmith Deployments 経由でのデプロイ（自動的に store がプロビジョニングされる）

#### CompositeBackend (ルーター)

**動作**:
- パスプレフィックスに基づいて異なるバックエンドにルーティング
- 元のパスプレフィックスをリスト・検索結果で保持

**用途**:
- エフェメラルストレージとスレッド横断ストレージの併用
- 複数の情報源を単一のファイルシステムとして提供（例: `/memories/` は Store、`/docs/` はカスタムバックエンド）

**使用例**:
```python
from deepagents.backends import StateBackend, StoreBackend
from deepagents.backends.composite import CompositeBackend

composite_backend = lambda rt: CompositeBackend(
    default=StateBackend(rt),  # デフォルトはエフェメラル
    routes={
        "/memories/": StoreBackend(rt),  # /memories/ は永続化
        "/docs/": CustomBackend()        # /docs/ はカスタムバックエンド
    }
)
```

### 4.2 バックエンドプロトコル

カスタムバックエンドを実装するには、`BackendProtocol` を実装する必要があります：

**必須メソッド**:
- `ls_info(path: str) -> list[FileInfo]` - ディレクトリ一覧
- `read(file_path: str, offset: int = 0, limit: int = 2000) -> str` - ファイル読み込み
- `grep_raw(pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str` - テキスト検索
- `glob_info(pattern: str, path: str = "/") -> list[FileInfo]` - パターンマッチング
- `write(file_path: str, content: str) -> WriteResult` - ファイル作成（create-only）
- `edit(file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult` - ファイル編集

**ポリシーフック**: バックエンドをサブクラス化またはラップして、エンタープライズルールを強制可能

---

## 5. カスタマイズオプション

### 5.1 モデル

- **デフォルト**: `"claude-sonnet-4-5-20250929"`
- **カスタマイズ**: 任意の LangChain ChatModel オブジェクトを指定可能

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o")
agent = create_deep_agent(model=model)
```

### 5.2 システムプロンプト

- **デフォルト**: Claude Code にインスパイアされた詳細なプロンプト（組み込みツールの使用方法を含む）
- **推奨**: 各ユースケースに特化したカスタムプロンプトを追加
- **重要**: プロンプトの品質が Deep Agent の成功に大きく影響

### 5.3 ツール

- 標準的な tool-calling エージェントと同様に、ツールセットを提供可能
- ミドルウェアで自動的に追加されるツール（`write_todos`, `ls`, `read_file` など）と組み合わせて使用

### 5.4 ミドルウェア

- **組み込みミドルウェア**: `TodoListMiddleware`, `FilesystemMiddleware`, `SubAgentMiddleware`
- **カスタムミドルウェア**: `AgentMiddleware` を継承して独自の機能を追加可能

```python
from langchain.agents.middleware import AgentMiddleware

class WeatherMiddleware(AgentMiddleware):
    tools = [get_weather, get_temperature]

agent = create_deep_agent(
    middleware=[WeatherMiddleware()]
)
```

### 5.5 同期/非同期

- 以前のバージョンでは `async_create_deep_agent` が分離されていたが、現在は `create_deep_agent` に統合
- 同期・非同期の両方で同じファクトリを使用
- MCP ツールを使用する場合は async 版を推奨（MCP ツールは非同期）

---

## 6. MCP (Model Context Protocol) 連携

Deep Agents は MCP ツールと連携可能：

- **実装**: LangChain MCP Adapter ライブラリを使用
- **インストール**: `pip install langchain-mcp-adapters`
- **使用例**:

```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent

async def main():
    # MCP ツールを収集
    mcp_client = MultiServerMCPClient(...)
    mcp_tools = await mcp_client.get_tools()
    
    # エージェント作成
    agent = create_deep_agent(tools=mcp_tools, ....)
    
    # エージェントをストリーミング
    async for chunk in agent.astream(
        {"messages": [{"role": "user", "content": "what is langgraph?"}]},
        stream_mode="values"
    ):
        if "messages" in chunk:
            chunk["messages"][-1].pretty_print()

asyncio.run(main())
```

---

## 7. LangChain エコシステムとの関係

### 7.1 LangGraph

- **基盤**: Deep Agents は LangGraph 上に構築
- **機能**: グラフ実行、状態管理、チェックポイント、Store 機能を活用

### 7.2 LangChain

- **統合**: ツールとモデルの統合がシームレスに動作
- **互換性**: 既存の LangChain ツール・モデル・インテグレーションをそのまま利用可能

### 7.3 LangSmith

- **デプロイ**: LangSmith Deployment 経由でデプロイ可能
- **観測**: LangSmith Observability でモニタリング可能
- **自動プロビジョニング**: LangSmith Deployments では store が自動的にプロビジョニングされる

---

## 8. auto-refine-agents への応用可能性

### 8.1 マッピング

auto-refine-agents の「計画→下書き→批評→改稿→検証」ループを Deep Agents の構成要素にマッピング：

| auto-refine フェーズ | Deep Agents の要素 |
|---------------------|-------------------|
| **計画** | `TodoListMiddleware` (`write_todos`) でタスク分解・順序決定・進捗追跡 |
| **下書き・改稿** | `FilesystemMiddleware` で `/workspace/draft.md`, `/workspace/revision_n.md` を継続保存（長文をコンテキストから外部化） |
| **批評** | `SubAgentMiddleware` で「批評サブエージェント」をスポーンし、ドラフトを精査→改善指示をファイル出力 |
| **検証** | 別サブエージェントで requirement checklist を走査（`grep`/`glob` で仕様・コード・資料を検索） |
| **公開・副作用操作** | `interrupt_on` で人間の承認ゲートを設定 |
| **長期記憶** | `/memories/` を `StoreBackend` にルーティングし、過去の学び・失敗例・定石を永続化 |

### 8.2 サブエージェント設計例

**役割分担**:
1. **Drafter** - 草稿生成エージェント
2. **Critic** - 観点別レビューエージェント（正確性、一貫性、セキュリティ、性能など）
3. **Refiner** - 批評に基づく改善エージェント
4. **Verifier** - 要件・テスト観点のチェックエージェント

**コンテキスト分離**:
- 各サブエージェントは独立したコンテキストで動作
- メインエージェントは全体のオーケストレーションに専念
- 長文のドラフト・批評結果はファイルシステムに保存し、必要に応じて読み込み

### 8.3 プロンプト設計

- デフォルトプロンプトに「auto-refine の手順・観点・品質基準」を追記
- ミドルウェアの `system_prompt` 拡張を活用して、各フェーズのガイダンスを強化

### 8.4 導入ステップ（推奨）

1. **目的の明確化**: まずは「自動リサーチ→要約→自己批評→再要約」のような小さなパイロットで開始
2. **エージェント生成**: 
   - `create_deep_agent(tools=[web_search など], backend=CompositeBackend(...))`
   - `/memories/` は `StoreBackend`、ワークスペースは `StateBackend`（エフェメラル）
3. **サブエージェント定義**: `research-agent`, `critic-agent`, `refine-agent` を個別プロンプトで定義
4. **HITL 設定**（任意）: 外部書き込みやコストの高いツールに `interrupt_on` を設定
5. **観測・収集**: LangSmith でトレースし、ToDo・ファイル生成の妥当性を確認
6. **段階的拡張**: `grep`/`glob` と RAG を追加、コードベース適用、テスト生成→実行まで拡張

---

## 9. リスクと注意点

### 9.1 非同期 API の記述差異

- ドキュメント内で「`create_deep_agent` に統合」と「`async_create_deep_agent` を使用」の記述が混在
- 実装時は使用バージョンで動作確認を推奨

### 9.2 セキュリティ

- `FilesystemBackend` はローカルファイルシステムへの書き込みを伴う
- 必ずルートのサンドボックス化とポリシーガードを設定（Backends ドキュメントのポリシーフック参照）

### 9.3 長期運用

- `StoreBackend` の運用（容量、リテンション、PII 方針）と監査ログ設計が必要
- ファイルシステムの肥大化を防ぐためのクリーンアップ戦略を検討

### 9.4 プロンプト設計の重要性

- デフォルトプロンプトは汎用的。auto-refine の成功には、ユースケース特化プロンプトと評価ルーブリックが鍵

---

## 10. 参考リンク

### 公式リソース

- **GitHub**: [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents)
- **ドキュメント概要**: [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview)
- **バックエンド**: [Backends](https://docs.langchain.com/oss/python/deepagents/backends)
- **サブエージェント**: [Subagents](https://docs.langchain.com/oss/python/deepagents/subagents)
- **HITL**: [Human-in-the-loop](https://docs.langchain.com/oss/python/deepagents/human-in-the-loop)
- **長期記憶**: [Long-term memory](https://docs.langchain.com/oss/python/deepagents/long-term-memory)
- **API リファレンス**: [reference.langchain.com/python/deepagents](https://reference.langchain.com/python/deepagents/)
- **PyPI**: [deepagents](https://pypi.org/project/deepagents/)

### 関連ライブラリ

- **LangChain MCP Adapters**: [langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters)

---

## 11. 調査のまとめ

### 11.1 主要な発見

1. **ミドルウェア合成アーキテクチャ**: 機能が独立したミドルウェアとして実装され、必要に応じて組み合わせ可能
2. **プラガブルバックエンド**: ファイルシステムが複数のバックエンド実装を切り替え可能（エフェメラル・永続・ルーティング）
3. **auto-refine への自然なマッピング**: 計画・批評・改稿のループが Deep Agents の標準機能に自然にマッピング可能
4. **LangChain エコシステムとの統合**: LangGraph、LangChain、LangSmith との統合がシームレス

### 11.2 次のステップ

1. **PoC 実装**: 最小限の auto-refine エージェントを Deep Agents で構築
2. **バックエンド設計**: `/memories/`, `/workspace/`, `/docs/` などのルーティング設計
3. **サブエージェント定義**: Drafter, Critic, Refiner, Verifier のプロンプト設計
4. **評価**: LangSmith でのトレースと品質評価

---

**調査完了**: 2025-11-03

