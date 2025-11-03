`architecture.md`のアーキテクチャ構成の要点を抽出中。


[1 tool called]

`architecture.md` のアーキテクチャ構成の概要・要点を簡潔にまとめます。

## アーキテクチャ構成の概要

### 基本構造：3層ループ構造

自己改善型AIエージェントのアーキテクチャで、**3つの階層ループ**で構成されています。

#### 1. **Inner-Loop（計画ループ）** - タスク実行の核
```
目標正規化 → プランナー → 文脈管理子(ACE) → 実行者 → 評価者 → リファイナ → (文脈管理子へフィードバック)
```
- **プランナー**: Many-Shot ICLで計画生成
- **文脈管理子(ACE)**: ワーキングメモリ/エピソード記憶/RAG/Playbookを管理
- **実行者**: ツール/コード/API実行、長文脈圧縮
- **評価者**: ルーブリック/テスト/摂動ロバスト性で評価
- **リファイナ**: 差分パッチ/次試行のA/B設計

#### 2. **Middle-Loop（自己改良ループ）** - 経験から学習
- **失敗解析**: Inner-Loopの失敗を分析
- **Prompt → LoRA生成**: ICLの成果をパラメータ更新に変換（Drag-and-Drop LLM手法）
- Playbook StoreとEarly Experience DBへ知識を蓄積

#### 3. **Outer-Loop（モデル適応ループ）** - モデル自体の改善
- **基盤LLM** + **Adapter/LoRA Manager**
- **DPO/RLHF学習**: 好みデータからモデルを改善
- Middle-Loopで生成されたLoRAを統合

### 補助システム

- **メモリ/知識ストア**: Task WM、Episodic Memory、Semantic/RAG Index、Playbook Store、Early Experience DB
- **外部ツール**: API/関数呼び出し、コーパス/ウェブ/DB、文脈圧縮/OCR
- **通信/標準/安全**: エージェント通信プロトコル、脅威モデル/監査ログ
- **観測/可視化**: ダッシュボード/リプレイで実行ログ・スコア・コストを可視化

### 設計思想の要点

1. **ICLの永続化**: Inner-LoopのICL成果を、Middle-LoopでLoRA化し、Outer-Loopでモデルに統合
2. **文脈の自己最適化**: ACEが文脈を動的に管理・改善
3. **多層的学習**: タスク実行（Inner）→ 経験学習（Middle）→ モデル改善（Outer）の3段階で能力向上

このアーキテクチャは、論文で言及されている**ICL、コンテキストエンジニアリング、RL系手法**を統合した自己改善型エージェントの実装案です。

### 実務上の要点（強化）
- 評価健全性: Rubric/Spec 準拠 + 摂動ロバスト性 + 監査ログ + HITL 昇格
- 並列運用: 各エージェントは Git worktree を分離し、`.agent/`（含 FTS DB）は共有しない
- 共有正典: `agent/registry/` に prompts/playbooks/rubrics/config( *.defaults.yaml ) を管理（Git）。RAGの対象外。pull=`agent/registry→.agent` / push=`.agent→PR→agent/registry`
- 参照: `evaluation-governance.md`, `worktree-guide.md`

### 関連ドキュメント
- [MVP/ポストMVPのスコープ定義](./mvp-scope.md)