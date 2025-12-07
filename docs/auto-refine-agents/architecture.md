# 論文情報解析


特に **LLM / 強化学習（RL） / ICL（In‑Context Learning＝文脈内学習） / コンテキストエンジニアリング（プロンプトや入出力文脈の設計最適化）** に関わる情報を機械的に拾い漏れなく抽出しています。
※以下、「title_guess / year_guess」はファイル先頭やメタデータからの**自動推定**です（HTML保存のためタイトルが「Skip to…」等になる箇所あり）。必要なら DOI / arXiv を突合して厳密化できます。

---

## 実行サマリ（直接の回答）

* Zip を `/mnt/data/NotebookLM.zip` から展開し、**全ファイルをインベントリ化**。
* **ファイル名 + 軽量全文スキャン（PDFは先頭〜数ページ、テキスト/HTMLは先頭一部）**でキーワードマッチを行い、**関連候補を200件上限で抽出**。
* **上位30件**について、タイトル・年・抽出カテゴリ（LLM/RL/ICL/Context Eng.）・冒頭/アブストラクトに相当する本文リードを自動要約化。
* 結果をダウンロード可能なファイルとして出力：

  * インベントリ: [notebooklm_inventory.csv](sandbox:/mnt/data/notebooklm_inventory.csv)
  * 候補一覧（ファイル名フィルタ）: [notebooklm_candidates.csv](sandbox:/mnt/data/notebooklm_candidates.csv)
  * 関連候補（高速スキャン）: [notebooklm_relevant_fast.csv](sandbox:/mnt/data/notebooklm_relevant_fast.csv)
  * 上位30件レポート（タイトル/年/要旨リード付）: [notebooklm_relevant_report_top30.csv](sandbox:/mnt/data/notebooklm_relevant_report_top30.csv)
  * 上位30件のMarkdown要約: [notebooklm_top30_summary.md](sandbox:/mnt/data/notebooklm_top30_summary.md)

---

## 抽出結果の要点（カテゴリ別の把握）

**用語の短い説明**

* **ICL**：プロンプト内の数ショット例など**文脈だけ**で能力を引き出す現象/手法。
* **コンテキストエンジニアリング**：ICLを含む広義の**文脈設計**（プロンプト設計、RAG設計、位置埋め込みや長文脈最適化、工具/ツール接続の文脈づけ）全般。
* **RL（強化学習）**：報酬に基づく方策最適化（RLHF/DPO/自己対戦FTなど、LLM最適化を含む）。

### 1) ICL（文脈内学習）

* **Many‑Shot In‑Context Learning**（`NotebookLM/Many-Shot In-Context Learning/...`、year_guess=2024）：多数ショットでの ICL 挙動・スケーリングを扱う資料。
* **CoT Reasoning: A Brittle Mirage / Is Chain‑of‑Thought Reasoning a Mirage?**（`.../CoT Reasoning_...` / `.../Is Chain-of-Thought...`、year_guess=2025）：**思考連鎖（CoT）**の脆さ・安定性・再現性への批判・検証。ICLの限界条件が示唆されます。
* **Drag‑and‑Drop LLMs: Zero‑Shot Prompt‑to‑Weights**（`.../ドラッグ＆ドロップLLM_...`、year_guess=2025）：**プロンプトを直接重みへ写像**する発想で、ICLとパラメトリック学習の橋渡しを示す新潮流（仮説的に ICL↔微調整の接続）。

**示唆**：

* **多ショット**ほど ICL は統計的に安定化するが、**CoT の脆性**が示す通り、誘導文脈の**摂動**や**分布外**に脆い面もある。
* Prompt‑to‑Weights系は、**「ICLで出ている最適化信号を一歩進めてパラメータへ定着」**する路線で、**文脈→モデル更新**の短絡化を示す。

### 2) コンテキストエンジニアリング（Context Engineering）

* **Agentic Context Engineering: Evolving Contexts for Self‑Improving LMs**（`.../Agentic Context Engineering...`、year_guess=2025）：**エージェント自身が文脈を進化させ自己改善**する枠組み。
* **Effective Context Engineering for AI Agents**（`.../Effective Context Engineering...`、year_guess=2025）：**エージェント文脈設計の実践ガイド**的資料。
* **Gemini for Google Workspace Prompting Guide 101**（`.../Prompting Guide 101/...`、year_guess=2024）：実務向け**プロンプト設計の作法**を体系化。
* **DeepSeek‑OCR: Contexts Optical Compression**（`.../DeepSeek_OCR_paper.pdf.html`、year_guess=2025）：**長文脈の圧縮（情報保持とコスト均衡）**に踏み込む流れ。

**示唆**：

* 単純なプロンプト設計から、**長文脈の圧縮/要約/再配置**、**エージェントによる自己文脈最適化**へ焦点が移動。
* 実運用では、**文脈予算（トークン）**と**損失（性能劣化）**のトレードオフ管理がカギ。

### 3) LLM一般・スケーリング/長期実行

* **The Illusion of Diminishing Returns: Measuring Long Horizon Execution in LLMs**（`.../LLM Long Horizon Execution...`、year_guess=2025）：**長期遂行評価**での見かけの逓減を測定・再定義。
* **Polynomial‑Time Learning of Linear Attention**（`.../Polynomial-Time Learning of Linear Attention...`、year_guess=2024）：**線形アテンションの学習理論**側面。
* **How People Use ChatGPT**（`.../How People Use ChatGPT/...`、year_guess=2025）：**ユーザ利用実態**から設計・提示の指針を得る資料。

**示唆**：

* 「スケールしても長期タスクで伸びに頭打ちに見える」現象は**測定設計**に依存、**評価指標のリフト**が重要。
* 設計上は**注意機構の計算効率**と**一般化**が引き続き核心。

### 4) RL / エージェント / 安全性・制御

* **自己対戦ファインチューニングによる弱LLMの強化**（`.../自己対戦...`、year_guess=2023）：**自己対戦（self‑play）**で**RL的な圧力**を与える路線。
* **Evaluating LLM Agent Control: A Trajectory to Superintelligence**（`.../Evaluating LLM Agent Control...`、year_guess=2025）：**エージェント制御**/ガバナンスの**評価軌跡**。
* **Survey of LLM‑Driven AI Agent Communication**（`.../LLMエージェント通信のセキュリティサーベイ/...`、year_guess=2025）：**エージェント間通信プロトコル/標準**、セキュリティ的視点。
* **ImpossibleBench: Measuring LLMs’ Propensity of Exploiting Test Cases**（`.../ImpossibleBench...`、year_guess=2025）：**テストケースの抜け道**活用傾向を計測（安全性/評価健全性）。

**示唆**：

* LLMエージェントは**通信・協調**と**制御**が核。通信は**脅威モデル**を含め標準化が走りつつある。
* **自己対戦・RLHF・DPO系**は、**好ましい方策**を形成する再帰的訓練で、本Zip内にもその片鱗がある。

---

## 重要な個別項目（上位より抜粋・短評）

> 相対パスはZip内の実体です。タイトル/年は自動推定です。

1. `NotebookLM/Many-Shot In-Context Learning/Sources/https_arxiv.org_pdf_2404.11018.html`（ICL, 2024）
   多ショット ICL の挙動・スケーリング。**ショット数増**と**誤謬/脆性**の兼ね合いを検証する素材。

2. `NotebookLM/LLMエージェント通信のセキュリティサーベイ/Sources/https_arxiv.org_pdf_2506.19676.html`（Agent通信, 2025）
   LLM駆動エージェントの**通信プロトコル/セキュリティ**俯瞰。**多エージェント連携**の要点整理。

3. `NotebookLM/LLM Long Horizon Execution and Self-Conditioning/Sources/The Illusion of Diminishing Returns_ Measuring.html`（長期遂行, 2025）
   **長地平タスク**における伸び鈍化を**計測と定義**から捉え直す試み。

4. `NotebookLM/Agentic Context Engineering for Self-Improving Lan/Sources/Agentic Context Engineering_ Evolving Contexts.html`（自己改善×文脈, 2025）
   **エージェントが自ら文脈を編成し改善**する設計論。**自己最適化ループ**の青写真。

5. `NotebookLM/The Prompting Brain_ Neurocognitive Markers of ...`（プロンプト×神経認知, 2024）
   **人間側の認知特性**と**プロンプト設計**の関係を探る方向性。**ヒト要因**の定量化を示唆。

6. `NotebookLM/Polynomial-Time Learning of Linear Attention ...`（理論, 2024）
   **線形アテンション**の**学習可能性**に理論的な光を当てる資料。

7. `NotebookLM/CoT Reasoning_ A Brittle Mirage/...` および
   `NotebookLM/Is Chain-of-Thought Reasoning a Mirage_/...`（CoT, 2025）
   **CoTの脆性**・**一般化**の限界を問い直し、安定化条件や**代替推論**戦略の検討を促す。

8. `NotebookLM/DeepSeek-OCR_ Contexts Optical Compression for LLM/...`（圧縮, 2025）
   **長文脈圧縮**による**可読性/保持率/計算コスト**の最適点探索。

9. `NotebookLM/Early Experience for Language Agent Learning/...`（エージェント初期経験, 2025）
   **初期経験（カリキュラム/前学習）**が**エージェント学習**に与える影響。

10. `NotebookLM/ドラッグ＆ドロップLLM_ プロンプト・トゥ・ウェイト/Sources/[2506.16...].html`（Prompt→Weights, 2025）
    **ICL的誘導**を**パラメータ更新**へ直写する新トレンド。**“文脈の一回性”の限界突破**を狙う。

---

## どのように結論に至ったか（実務向け・監査可能性担保）

**チェックリスト駆動の処理系**

1. **解凍**：Zipを `/mnt/data/NotebookLM_extracted_final` に展開。
2. **インベントリ化**：全ファイルの相対パス/拡張子/サイズを列挙。
3. **候補抽出**：ファイル名ベースで（llm, gpt, transformer, rl, icl, prompt, rag, rope, alibi…など）一次フィルタ。
4. **軽量スキャン**：候補の**先頭数ページ/数十KB**のみ全文検索し、「LLM / RL / ICL / ContextEng」のヒット数を計上。
5. **上位選別**：総ヒットで順位付けし、**タイトル・年の推定**と**アブストラクト/リード抜粋**を付与。
6. **成果物化**：インベントリ/候補/関連上位/要約の各CSV & Markdownを**ダウンロード可能**に出力。

   * 上位30件要約: [notebooklm_top30_summary.md](sandbox:/mnt/data/notebooklm_top30_summary.md)

**留保**

* HTML保存由来でタイトルが崩れる箇所あり（例：「Skip to main content…」）。
* PDFテキスト抽出は先頭数ページに限定。**画像埋め込みPDFはOCRしていない**ため、拾い漏れ可能性あり。
* **年号はテキスト上の最新年を推定**。最終版の厳密化は DOI/arXiv 突合が必要。

---

## 代替視点・作業仮説（創発的だが検証可能）

* **ICL→Weights**（Drag‑and‑Drop系）：ICLの**“一時的文脈最適化”**を**“永続的パラメータ最適化”**へ短絡する潮流。
  **仮説**：ICLで成立する表現整形は**低秩更新**や**LoRA/Adapters**と等価変換可能な部分がある。
* **自己文脈最適化ループ**（Agentic Context Engineering）：**評価→文脈再配置→再試行**のループで**外部メモリ＋RAG圧縮**を組み合わせると、**計算予算一定下でも性能単調増加**を期待できる。
* **CoT脆性を跨ぐ設計原理**：**self‑consistency**（多数決）や**program‑of‑thought**（実行可能表現）で、単一CoTの脆性を**分散化**して吸収。
* **長期遂行評価の再設計**：逓減はモデル限界ではなく**評価系の非線形性**説。**報酬設計/観測設計**の見直しで“伸び”を回復し得る。

---

## 次の実務アクション（具体で、小さく早く回せる順）

1. **正規メタデータ付与（10分割バッチ）**

   * 上位30件の **タイトル/著者/年/会議・ジャーナル/URL/DOI** を外部照合してCSV拡張。
   * 目的：**検索性 & 引用性**の確保。
2. **評価観点タグ付け**

   * 列：`Task(推論/計画/協調)`, `ICL型(例示/CoT/ToT)`, `Context(圧縮/長文脈/位置埋込)`, `RL型(RLHF/DPO/自己対戦/報酬設計)` などを**二値/カテゴリ**で付与。
3. **設計チェックリスト（運用用1枚）**

   * **ICL安定化**（例示配置/ノイズ耐性/自己整合）、**長文脈**（圧縮/メモリ/再配置）、**RL**（目的関数/好み/安全性）、**評価**（長期タスク/脱テストケース流用）。
4. **ギャップ検知**

   * RLHF/DPO等の**比較実験**系、RAG圧縮の**情報理論的評価**、エージェント通信の**攻撃面**など、**Zip外の必読古典/最新**を差分洗い出し。
5. **再走査（必要時）**

   * OCR/全文展開/多言語正規化で**取りこぼし**最小化。

---

## 補足：今回生成した成果物

* インベントリ: [notebooklm_inventory.csv](sandbox:/mnt/data/notebooklm_inventory.csv)
* 候補一覧: [notebooklm_candidates.csv](sandbox:/mnt/data/notebooklm_candidates.csv)
* 関連候補（高速）: [notebooklm_relevant_fast.csv](sandbox:/mnt/data/notebooklm_relevant_fast.csv)
* 上位30件の詳細レポート（CSV）: [notebooklm_relevant_report_top30.csv](sandbox:/mnt/data/notebooklm_relevant_report_top30.csv)
* 上位30件の要約（Markdown）: [notebooklm_top30_summary.md](sandbox:/mnt/data/notebooklm_top30_summary.md)

---

### 3ステップの論理

1. **論理抽出**：Zip全体→テキスト化→LLM/RL/ICL/Context関連の**語彙マッチ**→上位候補を抽出。
2. **論理拡張**：各候補の**要旨/先頭**から**テーマ/位置づけ**を推定し、**カテゴリ別の含意**を整理。
3. **論理翻訳**：実務投入できる形（**設計チェックリストと次アクション**）に落とし込み、**成果物（CSV/MD）**を提供。

---

必要なら、**DOI/arXiv突合でメタデータを厳密化**し、**研究分野マップ（ICL↔RL↔Context設計）**を図解化・俯瞰化まで拡張できます。上記CSVを土台に、レビュー/精読の優先度付けもすぐ作れます。



```mermaid
flowchart TB

  %% ===== 入力・正規化 =====
  U["ユーザ / 外界"] --> N0["目標・拘束条件 正規化器\nTaskSpec: Goal, Constraints, KPIs, Budget, Safety, Deadline, Eval"]

  %% ===== (1) 計画ループ（Inner-Loop） =====
  subgraph L1["(1) 計画ループ（Inner-Loop）"]
    direction LR
    P["プランナー\n計画プロンプト + Many-Shot ICL"]
    C["文脈管理子（ACE）\nWM / Episodic / Semantic(RAG) / Playbook"]
    E["実行者\nTool / Code / API\n長文脈圧縮(DeepSeek-OCR 等)"]
    V["評価者\nRubric / Spec vs Test / ImpossibleBench / 摂動ロバスト性"]
    R["リファイナ\n差分パッチ / 次試行A/B"]
    AO["Artifacts Orchestrator (AO)\n出力標準化/整合"]
    RAS["Rubric Auto Synthesis (RAS)\n自動生成/ブラッシュアップ"]

    N0 --> P --> C --> E --> V --> R --> C
    E --> AO --> V
    R --> RAS
  end

  %% ===== メモリ / 知識ストア =====
  subgraph Stores["メモリ / 知識ストア"]
    direction TB
    WM["Task WM"]
    EP["Episodic Memory"]
    SEM["Semantic / RAG Index"]
    PB["Playbook Store"]
    EE["Early Experience DB"]
  end

  C --- WM
  C --- EP
  C --- SEM
  C --- PB
  E --> EE

  %% ===== (3) モデル適応（Outer-Loop） =====
  subgraph L3["(3) モデル適応（Outer-Loop）"]
    direction TB
    Base["基盤 LLM"]
    AM["Adapter / LoRA Manager"]
    Pref["Preference データ"]
    DPO["DPO / RLHF 学習"]

    Pref --> DPO --> AM
    Base --> AM
  end

  M["LLM サービス"]
  AM --> M
  P --> M
  C --> M
  E --> M
  V --> M

  %% ===== (2) 自己改良（Middle-Loop） =====
  subgraph L2["(2) 自己改良（Middle-Loop）"]
    direction LR
    FX["失敗解析"]
    DnD["Prompt → LoRA 生成（Drag-and-Drop）"]

    R --> FX
    FX --> PB
    FX --> EE
    R --> DnD
    DnD --> AM
  end

  %% ===== 外部ツール / データ源 =====
  subgraph Tools["外部ツール / データ源"]
    direction TB
    APIs["外部 API / 関数呼出"]
    Docs["コーパス / ウェブ / DB"]
    OCR["文脈圧縮 / OCR"]
  end

  E --> APIs
  C --> Docs
  E --> OCR
  OCR -. "要約 / 抽出" .-> SEM

  %% ===== 通信 / 標準 / 安全 =====
  subgraph Sec["通信 / 標準 / 安全"]
    direction TB
    Proto["エージェント通信プロトコル / 標準"]
    Threat["脅威モデル / 監査ログ"]
  end

  C --- Proto
  E --- Proto
  Proto --> Threat
  V --- Threat

  %% ===== 観測 / 可視化 =====
  D["観測: ダッシュボード / リプレイ"]
  E -. "実行ログ / コスト" .-> D
  V -. "スコア / 欠陥 / CheatingRisk" .-> D
```

## 3つの改善ループの違いと本質

自己改善型AIエージェントは、3つの階層ループ（Inner-Loop、Middle-Loop、Outer-Loop）で構成されています。各ループは異なる時間スケールと対象で改善を行い、階層的に連携してエージェントの能力を向上させます。

### 改善の「時間スケール」と「対象」の違い

| ループ | 時間スケール | 改善対象 | 改善の本質 |
|--------|------------|---------|-----------|
| **Inner-Loop** | **秒〜分単位**（単一タスク内） | **実行計画・文脈・行動** | **現在のタスクを完了させるための即時改善** |
| **Middle-Loop** | **タスク〜日単位**（タスク間） | **知識・テンプレート・手順** | **過去の経験から学び、将来のタスクに活かす知識改善** |
| **Outer-Loop** | **週〜月単位**（長期的） | **モデル・プロンプト設計** | **全タスクに通用する基礎能力の改善** |

### Inner-Loop（計画ループ）の本質

**「現在のタスクを完了させるための即時改善」**

- **スコープ**: 単一タスク内での実行サイクル
- **改善サイクル**: 計画 → 実行 → 評価 → リファイン → 再試行（同一タスク内で繰り返し）
- **改善手段**:
  - 実行計画の修正（プランナー）
  - 文脈の動的調整（ACE）
  - 評価結果に基づく再試行（リファイナ）
  - 差分パッチの適用
- **改善の範囲**: タスク固有の文脈・状態・実行計画
- **例**: 「コード生成が失敗 → エラー解析 → 計画修正 → 再実行」

### Middle-Loop（自己改良ループ）の本質

**「過去の経験から学び、将来のタスクに活かす知識改善」**

- **スコープ**: タスク間での知識伝達と再利用
- **改善サイクル**: 失敗解析 → 知識抽出 → テンプレート/Playbook更新 → 次回タスクで活用
- **改善手段**:
  - 失敗パターンの抽出とPlaybook化
  - 成功プロンプトのテンプレート化・バージョン管理
  - Early Experience DBへの蓄積
  - プロンプトテンプレートの最適化（A/Bテスト）
- **改善の範囲**: 再利用可能な知識・手順・テンプレート
- **例**: 「過去10回のコード生成タスクで、エラーハンドリングを追加する成功率が高い → Playbookに追加 → 今後のタスクで自動適用」

### Outer-Loop（モデル適応ループ）の本質

**「全タスクに通用する基礎能力の改善」**

- **スコープ**: 全タスクに通用する能力の向上
- **改善サイクル**: 好みデータ収集 → 学習（DPO/RLHF） → モデル更新 → 全タスクに反映
- **改善手段**（CLI環境では代替）:
  - プロンプトテンプレートの最適化（Few-shot/Many-shot例の最適化）
  - コンテキストエンジニアリング（文脈設計の最適化）
  - ルーブリックの改善（評価基準の最適化）
- **改善の範囲**: モデル自体の能力（CLI環境ではテンプレート設計）
- **例**: 「全タスクで成功例をMany-Shot ICLに追加 → プランナーの基本能力向上 → 全タスクの成功率向上」

### 階層的な改善の関係

3つのループは階層的に連携し、段階的な能力向上を実現します：

```
Outer-Loop（基礎能力）
    ↓ （全タスクに影響）
Middle-Loop（知識・テンプレート）
    ↓ （再利用可能な知識）
Inner-Loop（タスク実行）
    ↓ （個別タスクの成功）
```

**改善の流れ**:
1. **Outer-Loop**: 全タスクに通用する基礎能力を向上（プロンプトテンプレートの最適化、Many-Shot ICL例の精選）
2. **Middle-Loop**: 過去の経験から学び、再利用可能な知識を蓄積（Playbook、テンプレート、Early Experience）
3. **Inner-Loop**: 現在のタスクに対して、改善された基礎能力と知識を活用して即座に改善（計画修正、文脈調整、再試行）

### 具体例で理解する

**シナリオ**: 「Pythonコード生成タスク」

#### Inner-Loop（1回のタスク実行中）
1. 1回目の生成でインポートエラー → 評価者検出
2. リファイナがインポートを修正 → 再実行
3. 成功まで繰り返し（同一タスク内）

#### Middle-Loop（複数タスク後）
1. 過去5回のPythonタスクで`typing`モジュールの使用が有効
2. Playbook Storeに「Pythonコード生成時は`typing`を推奨」を追加
3. 次のタスクで自動適用

#### Outer-Loop（長期運用後）
1. Many-Shot ICL例を最適化（成功例50件を精選）
2. プランナーのプロンプトテンプレートを改善
3. 全タスクの初期成功率が向上

### 本質的な違いのまとめ

- **Inner-Loop**: その場その場での即時改善（リアクティブ）
  - 現在のタスク完了を最優先
  - 失敗に対して即座に対応
  - タスク固有の文脈・状態を改善

- **Middle-Loop**: 経験から学ぶ知識改善（プロアクティブ）
  - 過去の経験を将来に活かす
  - 再利用可能な知識を蓄積
  - タスク間での知識伝達

- **Outer-Loop**: 基礎能力の段階的向上（エボリューション）
  - 全タスクに通用する能力を改善
  - 長期的な能力向上
  - モデル自体の能力向上（CLI環境ではテンプレート設計）

この3層構造により、**即時対応 → 経験学習 → 基礎能力向上**の多層的な改善を実現し、エージェントは継続的に自己改善を行います。

## 評価健全性ガイドライン（抜粋）
- 評価者（V）は Rubric/Spec 準拠、摂動ロバスト性、ImpossibleBench 類似の抜け道検知を備える
- 既定では RAS による AutoRubric を入力とし、明示の Rubric 指定があればそれを優先
- 昇格（テンプレ更新）はプロモーション・ゲートを通過（回帰/ロバスト/コスト/ホールドアウト/監査/HITL）
- 監査ログ必須: 入力ハッシュ・rubric_id・template_id・スコア・根拠・コスト/レイテンシ・モデル情報
- 可視化: スコア推移・失敗分布・コスト時系列・CheatingRisk をダッシュボードで監視

参考: `docs/auto-refine-agents/evaluation-governance.md`

### 補足（正典 / ランタイム / RAG 対象）
- 共有正典（Git）: `agent/registry/`（prompts/playbooks/rubrics/config/*.defaults.yaml）。再利用資産はここで管理し、PR昇格で更新。
- ランタイム（非Git）: `.agent/`（worktree専用の実行状態、RAG DB含む）。
- RAG対象: `docs/**.md`, `memory-bank/**.md`。`agent/registry/**` は RAG の対象外。

