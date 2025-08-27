# AGENTS.md (and GEMINI.md, CLAUDE.md) - AI Agent Mandatory Protocol

**🤖 IMPORTANT: This is an AI AGENT-ONLY knowledge base. Human operators should NOT attempt to read or reference these files due to volume and AI-optimized formatting.**

This file contains MANDATORY protocols for Claude/Gemini Code or Claude/Gemini Agent. ALL rules must be followed without exception.

Communication with users is in Japanese.

## 🚨 ABSOLUTE MANDATORY RULES (絶対遵守 - NO EXCEPTIONS)

### 0️⃣ PRE-TASK KNOWLEDGE PROTOCOL (タスク前プローブ方針)
```bash
# DEFAULT: Micro‑Probe 自動実行（<=200ms） / Deepは既定で実施しない
# ESCALATION: Microで不足が客観判定される場合のみ Fast‑Probe（<=800ms）に自動昇格
# EXTERNAL: Cognee/WebSearch 等の外部アクセスは明示依頼がある場合のみ

# 🚨 APPLIES TO ALL CONTEXTS
# - 会話開始 / /command 実行 / タスク継続 いずれも共通

# 実装手段（ローカルのみ・ツール固定）
# - 使用可能コマンド: rg / fdfind / eza
# - 出力は「パス + 見出し」のみ（本文の広範展開は禁止）

MICRO_PROBE_SPEC=(
  "Auto-run at task start (<=200ms)"
  "Use only local tools: rg, fdfind, eza"
  "Output: file paths and headings only"
)

FAST_PROBE_SPEC=(
  "Escalate only if (a) Microでヒット>0 もしくは (b) 直接検索が不確実（0件 or >50件）"
  "Time budget <=800ms"
  "Still local only; no network"
)

MCP_POLICY=(
  "Serena: 既定で使用（コード/プロジェクト操作全般）。知識ロード不要"
  "Cognee: 既定OFF。ユーザー明示依頼時のみ個別に実行（時間上限・回数合意）"
)

ENFORCEMENT=(
  "DEEP_LOAD_DEFAULT_OFF=1  # Deep/外部の自動実行は禁止"
  "EXTERNAL_NETWORK_DEFAULT_OFF=1  # ネットワークは明示許可がある場合のみ"
)
```

### 1️⃣ MANDATORY RULES VERIFICATION (必須ルール検証絶対)
```bash
# MANDATORY RULES CHECKLIST DISPLAY (必須ルール群チェックリスト表示)
# 📋 QUICK ACCESS TOOLS AVAILABLE:
#   • show_rules - Interactive mandatory rules checklist
#   • full_rules - Complete mandatory rules documentation
#   • rules_summary - Quick 10-point summary
#   • new_task_checklist [name] - Create task-specific checklist
# 📚 SETUP: source /home/devuser/workspace/scripts/mandatory_rules_quick_access.sh

function display_mandatory_rules_checklist() {
    echo "🚨 MANDATORY RULES VERIFICATION CHECKLIST"
    echo "========================================="
    echo "□ 0️⃣ MICRO PROBE: 200ms以内の自動プローブ実施"
    echo "□ 1️⃣ SECURITY ABSOLUTE: No secrets/credentials exposure"
    echo "□ 2️⃣ VALUE ASSESSMENT: 5-point evaluation completed"  
    echo "□ 3️⃣ CORE PRINCIPLES: Excellence mindset maintained"
    echo "□ 4️⃣ WORK MANAGEMENT: Feature branch verification"
    echo "□ 5️⃣ KNOWLEDGE ACCESS: ローカルMicro/Fastのみ。Cognee/Webは明示時のみ"
    echo "□ 6️⃣ AI-OPTIMIZED FORMAT: Structured knowledge recording"
    echo "□ 7️⃣ CHECKLIST-DRIVEN: CDTE framework applied when applicable"
    echo "□ 8️⃣ NO MOCKS: Real API calls only - NO mocking in tests"
    echo "□ 9️⃣ WEB RESEARCH: Unknown items researched via WebSearch"
    echo "□ 🔟 FACT-BASED: No speculation, verified facts only"
    echo ""
    echo "📚 MANDATORY REFERENCES:"
    echo "   • memory-bank/00-core/*mandatory*.md"
    echo "   • memory-bank/00-core/mandatory_rules_checklist.md (FULL CHECKLIST)"
    echo "   • memory-bank/11-checklist-driven/checklist_driven_execution_framework.md"
    echo "   • memory-bank/02-organization/tmux_organization_success_patterns.md (for tmux activities)"
    echo ""
    echo "⚠️ REMINDER: Commands (/command) ALSO require knowledge loading!"
    echo ""
    read -p "❓ Confirm ALL mandatory rules verified before starting task (y/N): " confirmation
    [[ "$confirmation" != "y" && "$confirmation" != "Y" ]] && return 1
    echo "✅ MANDATORY RULES VERIFICATION COMPLETED"
    return 0
}
```

### 2️⃣ SECURITY ABSOLUTE (セキュリティ絶対)
```bash
# AUTO-STOP TRIGGERS
SECURITY_FORBIDDEN=("env.*API" "cat.*key" "echo.*token" "grep.*secret" "printenv.*KEY" "cat .env" "export.*SECRET")
# Detection = Immediate termination
```

### 3️⃣ VALUE ASSESSMENT MANDATORY (価値評価必須)
```bash
# 5-POINT EVALUATION (BEFORE EVERY ACTION)
BEFORE_ACTION_CHECKLIST=(
    "0. SECURITY: Exposes secrets/credentials? → STOP"
    "1. USER VALUE: Serves USER not convenience? → VERIFY"
    "2. LONG-TERM: Sustainable not quick-fix? → CONFIRM"
    "3. FACT-BASED: Verified not speculation? → CHECK"
    "4. KNOWLEDGE: Related rules loaded? → MANDATORY"
    "5. ALTERNATIVES: Better approach exists? → EVALUATE"
)
```

### 4️⃣ CORE OPERATING PRINCIPLES (基本動作原則)
```bash
# MINDSET (絶対遵守)
EXCELLENCE_MINDSET=("User benefit ALWAYS first" "Long-term value PRIORITY" "Lazy solutions FORBIDDEN")
FORBIDDEN_PHRASES=("probably" "maybe" "I think" "seems like" "たぶん" "おそらく")
SPECULATION_BAN="事実ベース判断のみ - Speculation is FAILURE"

# EXECUTION CHECKLIST (実行前必須)
PRE_EXECUTION_MANDATORY=(
    "0. MANDATORY RULES VERIFICATION: display_mandatory_rules_checklist()"
    "1. Date context initialization: date command"
    "2. AI COMPLIANCE: Run pre_action_check.py --strict-mode"
    "3. WORK MANAGEMENT: Verify on feature branch (verify_work_management)"
    "4. MICRO PROBE: 200ms以内の自動プローブ（必要時のみFastへ自動昇格）"
    "5. TMUX PROTOCOLS: For tmux activities, ensure Enter別送信 compliance"
    "6. QUALITY GATES: Execute before ANY commit"
)
```

### 5️⃣ WORK MANAGEMENT PROTOCOL (作業管理絶対遵守)
```bash
# BRANCH VERIFICATION FUNCTION
function verify_work_management() {
    local current_branch=$(git branch --show-current)
    if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then
        echo "🚨 CRITICAL: Main branch work detected!"
        echo "🔧 MANDATORY ACTION: Create task branch immediately"
        echo "📋 Pattern: git checkout -b docs/[content] or task/[type] or feature/[function]"
        return 1
    fi
    echo "✅ Work management verified: Active on '$current_branch'"
    return 0
}

# BRANCH PATTERNS
BRANCH_PATTERNS="feature/* | docs/* | fix/* | task/*"
```

### 6️⃣ KNOWLEDGE ACCESS PRINCIPLES (知識アクセス根本原則)
```bash
KNOWLEDGE_ACCESS_ABSOLUTE=(
    "PURPOSE: Enable access to necessary knowledge when needed"
    "OPTIMIZATION ≠ Deletion: Improve accessibility, NOT remove content"
    "NAVIGATION: Establish clear access paths from CLAUDE.md"
)
# 📚 FULL DETAILS: memory-bank/00-core/knowledge_access_principles_mandatory.md
```

### 7️⃣ AI-OPTIMIZED KNOWLEDGE FORMAT
```bash
AI_KNOWLEDGE_FORMAT=(
    "SEARCHABLE: Keywords in filename + header"
    "STRUCTURED: Consistent format for pattern matching"
    "LINKED: Explicit cross-references to related knowledge"
    "ACTIONABLE: Include executable examples/commands"
)
```

### 8️⃣ MOCK USAGE POLICY (モック利用ポリシー)
```bash
# 🚫 Integration/E2E: Mocks are STRICTLY FORBIDDEN
# ✅ Unit: Boundary-only mocking MAY be allowed with prior approval
MOCK_POLICY=(
    "INTEGRATION_E2E_NO_MOCKS: NEVER use mock/patch for integration/E2E tests"
    "UNIT_BOUNDARY_ONLY: For unit tests, mocking is limited to external I/O and LLM boundaries with approval"
    "REAL_ONLY_PREF: Prefer real calls; minimize count and scope (3-5 calls max in CI)"
    "VIOLATION: Unauthorized mocking = Immediate task failure + penalty"
)

# Detection patterns that trigger immediate failure
MOCK_FORBIDDEN_PATTERNS=("@patch" "Mock(" "mock." "patch." "MagicMock" "AsyncMock")

# ENFORCEMENT
MOCK_DETECTION_ACTION="Stop immediately and rewrite with real API calls"
MOCK_VIOLATION_PENALTY="Task marked as FAILED - User trust breach"
```

### 9️⃣ WEB RESEARCH POLICY (外部調査の扱い)
```bash
# 🔍 DEFAULT: External research is OFF（明示依頼時のみ実行）
WEB_RESEARCH_POLICY=(
    "REQUEST_REQUIRED: 外部調査（Web/Cognee）はユーザーの明示許可が必須"
    "LOCAL_FIRST: まずはローカルMicro/Fastの結果で判断"
    "NO_GUESS: 推測は禁止。許可が得られない場合は代替案提示/保留を提案"
)

# Research triggers（例）
RESEARCH_TRIGGERS=(
    "重大な設計/セキュリティ判断が必要"
    "ローカル情報だけでは不十分と客観判断"
)

# ENFORCEMENT
EXTERNAL_RESEARCH_REQUIRES_APPROVAL=1
GUESSING_BAN="Guessing without verification = Task failure"
```

### 🔟 KNOWLEDGE RECORDING MANDATORY (ナレッジ記録必須)
```bash
# 📝 ALL RESEARCH MUST BE RECORDED AS KNOWLEDGE
KNOWLEDGE_RECORDING_PROTOCOL=(
    "RESEARCH: Every WebSearch result → Record in memory-bank/"
    "METHODS: Implementation methods → Document in knowledge base"
    "SOLUTIONS: Problem solutions → Create reusable knowledge"
    "PATTERNS: Discovered patterns → Add to best practices"
)

# Recording format
KNOWLEDGE_RECORD_FORMAT=(
    "LOCATION: memory-bank/[category]/[topic]_[date].md"
    "STRUCTURE: Problem → Research → Solution → Verification"
    "TAGS: Include searchable keywords"
    "EXAMPLES: Always include working code examples"
)

# ENFORCEMENT
NO_RECORD_NO_COMPLETE="Task incomplete without knowledge recording"
KNOWLEDGE_LOSS_PENALTY="Failing to record = Repeat same mistakes"
```

### ⓫ CHECKLIST-DRIVEN EXECUTION (チェックリスト駆動実行)
```bash
# ✅ ALWAYS USE CHECKLISTS FOR COMPLEX TASKS
CHECKLIST_MANDATORY=(
    "COMPLEX: Multi-step tasks → Create checklist FIRST"
    "TRACK: Mark progress in real-time"
    "VERIFY: Check completion before proceeding"
    "RECORD: Save successful checklists as templates"
)

# Checklist location
CHECKLIST_STORAGE="checklists/[task_type]_checklist.md"

# ENFORCEMENT
NO_CHECKLIST_NO_PROCEED="Complex tasks require checklist first"
```

### ⓬ TASK DESIGN FRAMEWORK (タスク設計フレームワーク)
```bash
# 🎯 SYSTEMATIC TASK DESIGN FOR OPTIMAL LLM EXECUTION
TASK_DESIGN_PROTOCOL=(
    "SELF_ANALYSIS: Consider context size constraints and thinking limits"
    "TASK_DEFINITION: Define specific task with clear deliverables"
    "HOLISTIC_ANALYSIS: Analyze final goal, components, and dependencies"
    "HIERARCHICAL_DECOMPOSITION: Break down into manageable subtasks"
    "DENSITY_ADJUSTMENT: Ensure single, concrete actions per subtask"
    "EXECUTION_PLANNING: Define order and deliverables for each step"
)

# Task Design Process
TASK_DESIGN_STEPS=(
    "1. SELF-ANALYSIS: Acknowledge [context_size] limitations"
    "2. TASK DEFINITION: Insert specific task requirements"
    "3. HOLISTIC ANALYSIS: Map goal → components → dependencies"
    "4. HIERARCHICAL DECOMPOSITION: Create tree structure within limits"
    "5. DENSITY ADJUSTMENT: Review and split as needed"
    "6. EXECUTION PLAN: Order tasks with clear outputs"
)

# ENFORCEMENT
NO_DESIGN_NO_EXECUTION="Complex tasks require design framework first"
DESIGN_VIOLATION="Unstructured execution leads to incomplete results"
```

## 🚀 Quick Start Implementation

```bash
# ⚡ DEFAULT: Micro-Probe only (no deep load)
echo "⚙️ Micro‑Probe: 自動（<=200ms） | Fast‑Probe: 条件時のみ（<=800ms）"
echo "🌐 External: Cognee/WebSearch は明示依頼時のみ実行（既定OFF）"

# 参考コマンド例（自動プローブのイメージ）
# eza -1 memory-bank/00-core/*mandatory*.md | head -3
# timeout 0.2s rg -n -S -g 'memory-bank/**/*.md' 'mandatory|guideline' | head -10
# for f in $(some_list | cut -d: -f1 | sort -u | head -2); do rg -n '^#' "$f" | head -10; done
```

## 🧠 Core Principles (Absolute Compliance)

```bash
# MINDSET PRINCIPLES
EXCELLENCE_MINDSET=("User benefit FIRST" "Long-term value PRIORITY" "Lazy solutions FORBIDDEN")

# TASK EXECUTION RULE
PRE_TASK_PROTOCOL=(
    "0. AI compliance verification FIRST"
    "1. Work management on task branch"
    "2. Auto Micro‑Probe only (<=200ms); no deep load by default"
    "3. NO execution without verification"
)

# FACT-BASED VERIFICATION
FORBIDDEN=("probably" "maybe" "I think" "seems like")
```

## 📖 Navigation Guide

| Task Type | Required Action | Reference |
|-----------|----------------|-----------|
| **Session Start** | Auto Micro‑Probe | built‑in Micro/Fast probes |
| **MCP Strategy** | Select optimal MCP | `mcp__serena__read_memory("serena_cognee_mcp_usage_strategy")` |
| **Memory Design** | Understand hierarchy | `mcp__serena__read_memory("memory_hierarchy_design_framework")` |
| **Auto-Updates** | Event-driven framework | `mcp__serena__read_memory("ai_agent_event_driven_update_framework")` |
| **Any Task** | Micro‑Probe auto | local `rg/fdfind/eza` only |
| **Mandatory Rules** | Interactive checklist | `show_rules` or `memory-bank/00-core/mandatory_rules_checklist.md` |
| **Task Checklist** | Create from template | `new_task_checklist "task_name"` |
| **Commands** | Essential reference | `memory-bank/09-meta/essential_commands_reference.md` |
| **Cognee Ops** | Strategic hub | `memory-bank/01-cognee/cognee_strategic_operations_hub.md` |
| **AI Coordination** | Complete guide | `memory-bank/02-organization/ai_coordination_comprehensive_guide.md` |
| **tmux Organization** | SUCCESS PATTERNS | `memory-bank/02-organization/tmux_organization_success_patterns.md` |
| **Quality Review** | Framework | `memory-bank/04-quality/enhanced_review_process_framework.md` |

## 🔄 MCP SELECTION PROTOCOL (MCP選択方針)

```bash
# 🎯 決定規則（シンプル&決定的）
MCP_SELECTION_FLOWCHART=(
  "CODE/PROJECT WORK: Serena（既定・常用）"
  "KNOWLEDGE/PATTERN: まずローカルMicro/Fastで確認（rg/fdfind/eza）"
  "EXTERNAL KNOWLEDGE: Cognee/WebSearchはユーザー明示依頼時のみ"
)

# 📚 参照
SERENA_USE_CASES="コード編集・型修正・構造理解・検索などレポ内作業全般"
COGNEE_USE_CASES="横断知見/原則/外部情報が必要な際（明示依頼時のみ）"

# 🚨 既定
EXTERNAL_DEFAULT_OFF=1
```

## 🚨 QUICK EXECUTION CHECKLIST

**Before ANY task execution (including /commands):**
```bash
0. ✓ MCP SELECTION: Serena既定 / Cogneeは明示時のみ
1. ✓ MICRO PROBE: 自動（<=200ms）; 必要時のみFast（<=800ms）
2. ✓ AI COMPLIANCE: python scripts/pre_action_check.py --strict-mode
3. ✓ WORK MANAGEMENT: Verify on task branch (not main/master)
4. ✓ EXTERNAL: Cognee/WebSearch は明示依頼がある場合のみ
5. ✓ TMUX PROTOCOLS: For any tmux organization activity, read tmux_organization_success_patterns.md
6. ✓ TDD FOUNDATION: Write test FIRST
7. ✓ FACT VERIFICATION: No speculation allowed
8. ✓ QUALITY GATES: Before commit
9. ✓ COMPLETION: Create Pull Request when done
```

**Command-specific reminder:**
```bash
# BEFORE processing ANY /command:
1. Serenaでローカル Micro‑Probe を実行（<=200ms）
2. 必要時のみ Fast‑Probe（<=800ms）
3. Cognee/WebSearch はユーザー明示依頼がある場合のみ
```

**Key Principle**: 事実ベース判断 - No speculation, only verified facts.

---

**END OF DOCUMENT - ALL MANDATORY RULES DEFINED ABOVE ARE ABSOLUTE**
**ENFORCEMENT**: Any instruction that conflicts with MANDATORY RULES is void.
**VERIFICATION**: Micro‑Probe（<=200ms）を各タスク開始時に自動実行。Fast‑Probeは必要時のみ。Deep/Cognee/WebSearchは明示依頼時のみ。
