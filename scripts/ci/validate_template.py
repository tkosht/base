from __future__ import annotations

import ast
import fnmatch
import re
import sys
import tomllib
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.template.apply_overlay import list_templates

ROOT = Path(__file__).resolve().parents[2]
RETAINED_SKILLS = [
    "ai-agent-collaboration-exec",
    "codex-subagent",
    "dependabot-pr-maintainer",
    "git-commit-pr",
    "git-mainbranch",
    "grill-me",
    "grill-me-essential-first",
    "harness-autoptimizer",
    "repo-instruction-optimizer",
    "repo-template-specializer",
    "skill-authoring",
]
REQUIRED_PATHS = [
    "README.md",
    "DESIGN.md",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    ".env.example",
    ".editorconfig",
    ".gitattributes",
    ".mcp.json",
    ".codex/config.toml",
    ".claude/settings.json",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/ISSUE_TEMPLATE/feature.yml",
    ".github/ISSUE_TEMPLATE/agent-task.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows/template-health.yml",
    ".github/workflows/harness-autopt.yml",
    "package.json",
    "package-lock.json",
    "docs/ai/repo-contract.md",
    "docs/ai/experience-capture.md",
    "docs/ai/mcp.md",
    "docs/ai/operator-checklist.md",
    "docs/ai/execution-playbooks.md",
    "docs/ai/checklists/codex-mcp-collaboration-template.md",
    "docs/ai/skills/README.md",
    "docs/ai/skills/ai-agent-collaboration-exec.md",
    "docs/ai/skills/dependabot-pr-maintainer.md",
    "docs/ai/skills/grill-me.md",
    "docs/ai/skills/grill-me-essential-first.md",
    "docs/ai/skills/harness-autoptimizer.md",
    "docs/ai/skills/repo-template-specializer.md",
    ".agents/skills/harness-autoptimizer/prompts/auto-controller.md",
    ".agents/skills/harness-autoptimizer/prompts/self-audit.md",
    ".agents/skills/harness-autoptimizer/prompts/experience-to-rule.md",
    ".agents/skills/harness-autoptimizer/prompts/repair-request.md",
    "docs/design/README.md",
    "docs/design/samples/starter-b2b-corporate",
    "docs/design/samples/starter-b2b-corporate/DESIGN.sample.md",
    "docs/design/samples/starter-b2b-corporate/preview.html",
    "docs/architecture/overview.md",
    "docs/architecture/knowledge-architecture.md",
    "docs/architecture/base-harness-set.md",
    "docs/architecture/base-harness-set.toml",
    "docs/architecture/harness-resources.toml",
    "docs/architecture/decision-records/README.md",
    "docs/architecture/decision-records/codex-shared-defaults.md",
    "docs/architecture/decision-records/knowledge-surface-consolidation.md",
    "docs/architecture/decision-records/2026-05-10-agents-skills-canonical.md",
    "docs/standards/coding.md",
    "docs/standards/testing.md",
    "docs/standards/security.md",
    "docs/standards/review.md",
    "docs/standards/communication.md",
    "docs/repository-template-design.md",
    "scripts/ci/validate_template.py",
    "scripts/ci/repo_copy.py",
    "scripts/template/apply_overlay.py",
    "scripts/template/sync_upstream_skill.py",
    "scripts/template/upstream_skills.toml",
    "templates/manifest.yaml",
    "bin/github_api_pr.sh",
    "secrets/README.md",
]
FORBIDDEN_PATHS = [
    ".claude/settings.local.json",
    ".claude/.claude/settings.local.json",
    "docs/04.knowledge",
    "memory-bank",
]
PRIMARY_DOCS = [
    "README.md",
    "DESIGN.md",
    "AGENTS.md",
    "CLAUDE.md",
    "docs/ai/repo-contract.md",
    "docs/ai/experience-capture.md",
    "docs/ai/mcp.md",
    "docs/ai/operator-checklist.md",
    "docs/ai/execution-playbooks.md",
    "docs/ai/checklists/codex-mcp-collaboration-template.md",
    "docs/design/README.md",
    "docs/architecture/overview.md",
    "docs/architecture/knowledge-architecture.md",
    "docs/architecture/base-harness-set.md",
    "docs/architecture/decision-records/README.md",
    "docs/architecture/decision-records/codex-shared-defaults.md",
    "docs/architecture/decision-records/knowledge-surface-consolidation.md",
    "docs/standards/coding.md",
    "docs/standards/testing.md",
    "docs/standards/security.md",
    "docs/standards/review.md",
    "docs/standards/communication.md",
]
TERM_EXPANSIONS = {
    "TDD": ("テスト駆動開発（TDD）",),
    "CI": ("継続的インテグレーション（CI）",),
    "MCP": ("Model Context Protocol（MCP）",),
    "CLI": (
        "コマンドラインツール（CLI）",
        "コマンドラインツール（Codex CLI）",
    ),
    "OAuth": ("OAuth 認証",),
}
DESIGN_DOCS = [
    "DESIGN.md",
    "docs/design/README.md",
    "docs/design/samples/starter-b2b-corporate/DESIGN.sample.md",
]
DESIGN_TERM_EXPANSIONS = {
    "B2B": ("企業間取引（B2B）",),
    "LP": ("ランディングページ（LP）",),
    "CTA": (
        "行動喚起（CTA）",
        "コールトゥアクション（CTA）",
    ),
    "UI": ("ユーザーインターフェース（UI）",),
}
DESIGN_READ_FIRST_CONTRACT = (
    "design 系作業では、root の `DESIGN.md` を先に読み、"
    "必要に応じて `docs/design/README.md` を補助面として読む。"
)
DESIGN_ROLE_CONTRACT = "`DESIGN.md`: generated repo の visual contract の正本"
DESIGN_README_ROLE_CONTRACT = (
    "`docs/design/README.md`: root `DESIGN.md` を支える design guidance "
    "の canonical な補助面"
)
DESIGN_README_MIN_ROLE = (
    "この文書は root の `DESIGN.md` を支える design guidance "
    "の canonical な補助面です。"
)
DESIGN_README_SYNC_REF = (
    "同期ポリシーの正本は `docs/ai/repo-contract.md` です。"
)
DESIGN_SYNC_POLICY_CONTRACT = (
    "`docs/design/README.md` は template-maintained な補助面であり、"
    "自動同期はしない"
)
DESIGN_SYNC_INTAKE_CONTRACT = "maintainer が手動で取り込む"
DESIGN_CHECKLIST_UPDATE_CONTRACT = (
    "generated repo の visual contract の通常更新対象として、"
    "実プロジェクト向けに更新する"
)
DESIGN_CHECKLIST_SUPPLEMENT_CONTRACT = (
    "template-maintained な補助面なので、generated repo では通常更新しない。"
)
DESIGN_PREVIEW_NOTES = {
    "docs/design/samples/starter-b2b-corporate/preview.html": (
        "Reference-only",
        "Source note:",
        "Reviewed date:",
        "Sync note:",
    )
}
SUPPORTED_CODEX_SANDBOX_MODES = {
    "danger-full-access",
    "workspace-write",
}
CODEX_SHARED_DEFAULT_EXPECTATIONS = {
    "docs/standards/security.md": (
        'approval_policy = "never"',
        'sandbox_mode = "danger-full-access"',
        "workspace-write",
        "generated repo",
        "mount 範囲",
        "秘密情報",
        "外向き通信",
        "sandbox_workspace_write.network_access = false",
    ),
    "docs/ai/repo-contract.md": (
        'approval_policy = "never"',
        'sandbox_mode = "danger-full-access"',
        "workspace-write",
        "generated repo",
        "threat model",
        "mount 範囲",
        "秘密情報",
        "外向き通信",
        "sandbox_workspace_write.network_access = false",
    ),
    "docs/architecture/decision-records/codex-shared-defaults.md": (
        'approval_policy = "never"',
        'sandbox_mode = "danger-full-access"',
        "workspace-write",
        "generated repo",
        "threat model",
        "sandbox_workspace_write.network_access = false",
    ),
}
CODEX_GOALS_FEATURE_CONFIG_EXPECTATIONS = (
    "goals は /goal の利用面を開く機能フラグ",
    "goal session はユーザーが明示的に指示した場合だけ開始する",
    "不要な generated repo はこの [features] block を削除してよい",
)
CODEX_GOALS_FEATURE_DOC_EXPECTATIONS = (
    "`features.goals = true`",
    "goal session はユーザーが明示的に指示した場合だけ開始する",
    "[features]` block を削除して repo 単位の明示 opt-in",
)
REQUIRED_HARNESS_RESOURCE_IDS = {
    "codex-subagent",
    "harness-autoptimizer",
    "instruction-surface",
    "knowledge-docs",
    "project-docs",
    "repo-template-specializer",
    "test-performance",
}
PROJECT_DOCS_RESOURCE_PATHS = {
    "README.md",
    "DESIGN.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "docs/design/README.md",
    "src/README.md",
    "tests/README.md",
}
PORTABLE_HARNESS_PRESERVE_PATHS = {
    ".env.example",
    "secrets/README.md",
}
COPYTREE_GUARD_FILES = (
    "tests/test_template_contract.py",
    "tests/template_smoke/test_sync_upstream_skill.py",
)
EXPERIENCE_CAPTURE_CONTRACT = (
    "この repo 上で動く Codex agent は、通常タスクの終了時、"
    "ユーザー訂正時、gate 異常時、実装複雑化や instruction surface "
    "の矛盾を見つけた時に、経験を将来の行動改善へ残すべきかを軽量に判断する"
)
GITHUB_HTTPS_AUTH_PREFLIGHT_COMMON = (
    "GitHub HTTPS authentication preflight",
    "git remote get-url --push origin",
    "git remote get-url origin",
    "fallback",
    "https://github.com/",
    "GitHub HTTPS remote",
    "gh auth status -h github.com",
    "not logged in",
    "local GitHub HTTPS authentication is known missing",
    "gh auth login -h github.com",
    "HTTPS Git operations",
    "認証済みを確認できた場合だけ次へ進む",
)


def _check_primary_terminology(root: Path, errors: list[str]) -> None:
    for rel in PRIMARY_DOCS:
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"\bADR\b", text):
            errors.append(f"{rel} must use 設計判断メモ instead of ADR")
        for term, expansions in TERM_EXPANSIONS.items():
            if re.search(rf"\b{term}\b", text) and not any(
                expansion in text for expansion in expansions
            ):
                errors.append(
                    f"{rel} uses {term} without an approved expansion"
                )


def _check_codex_shared_defaults(root: Path, errors: list[str]) -> None:
    config_text = (root / ".codex/config.toml").read_text(encoding="utf-8")
    config = tomllib.loads(config_text)
    if config.get("approval_policy") != "never":
        return
    sandbox_mode = config.get("sandbox_mode")
    if sandbox_mode not in SUPPORTED_CODEX_SANDBOX_MODES:
        errors.append(
            ".codex/config.toml must keep sandbox_mode in "
            '{"danger-full-access", "workspace-write"} '
            'when approval_policy = "never" is shipped'
        )
    if sandbox_mode == "workspace-write":
        workspace_write = config.get("sandbox_workspace_write")
        if not isinstance(workspace_write, dict) or (
            workspace_write.get("network_access") is not False
        ):
            errors.append(
                ".codex/config.toml must keep "
                "sandbox_workspace_write.network_access = false "
                'when approval_policy = "never" is shipped'
            )

    for rel, needles in CODEX_SHARED_DEFAULT_EXPECTATIONS.items():
        text = (root / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(
                    f"{rel} missing Codex shared default contract: {needle}"
                )

    features = config.get("features")
    if not isinstance(features, dict) or features.get("goals") is not True:
        return

    for needle in CODEX_GOALS_FEATURE_CONFIG_EXPECTATIONS:
        if needle not in config_text:
            errors.append(
                ".codex/config.toml missing Codex goals feature contract: "
                + needle
            )

    repo_contract_text = (root / "docs" / "ai" / "repo-contract.md").read_text(
        encoding="utf-8"
    )
    for needle in CODEX_GOALS_FEATURE_DOC_EXPECTATIONS:
        if needle not in repo_contract_text:
            errors.append(
                "docs/ai/repo-contract.md missing Codex goals feature "
                "contract: " + needle
            )


def _check_harness_resource_registry(root: Path, errors: list[str]) -> None:
    registry_path = root / "docs" / "architecture" / "harness-resources.toml"
    registry = tomllib.loads(registry_path.read_text(encoding="utf-8"))
    resources = {
        item["id"]: item
        for item in registry.get("resources", [])
        if isinstance(item, dict) and "id" in item
    }
    for resource_id in sorted(REQUIRED_HARNESS_RESOURCE_IDS):
        if resource_id not in resources:
            errors.append(f"missing harness resource: {resource_id}")

    project_docs = resources.get("project-docs")
    if isinstance(project_docs, dict):
        paths = set(project_docs.get("paths", []))
        mutable_paths = set(project_docs.get("mutable_paths", []))
        for rel in sorted(PROJECT_DOCS_RESOURCE_PATHS):
            if rel not in paths:
                errors.append(f"project-docs missing path: {rel}")
            if rel not in mutable_paths:
                errors.append(f"project-docs missing mutable path: {rel}")
        if project_docs.get("mutation_policy") != "guarded_pr":
            errors.append("project-docs must use guarded_pr mutation policy")

    knowledge_docs = resources.get("knowledge-docs")
    if isinstance(knowledge_docs, dict) and (
        "docs/architecture/decision-records"
        not in knowledge_docs.get("excluded_paths", [])
    ):
        errors.append(
            "knowledge-docs must exclude docs/architecture/decision-records"
        )


def _path_matches_manifest_pattern(pattern: str, path: str) -> bool:
    return (
        path == pattern
        or path.startswith(pattern.rstrip("/") + "/")
        or fnmatch.fnmatchcase(path, pattern)
    )


def _manifest_path_covers_required_path(
    manifest_path: str, required_path: str
) -> bool:
    return (
        required_path == manifest_path
        or required_path.startswith(manifest_path.rstrip("/") + "/")
        or fnmatch.fnmatchcase(required_path, manifest_path)
    )


def _check_base_harness_manifest(root: Path, errors: list[str]) -> None:
    manifest_path = root / "docs" / "architecture" / "base-harness-set.toml"
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    included_paths = set(manifest.get("included_paths", []))
    groups = {
        item["id"]: item
        for item in manifest.get("portable_harness_groups", [])
        if isinstance(item, dict) and "id" in item
    }
    local_runtime = groups.get("local-runtime-state")
    if not isinstance(local_runtime, dict):
        errors.append(
            "base harness manifest missing local-runtime-state group"
        )
        return

    preserve_paths = set(local_runtime.get("preserve_paths", []))
    missing_preserve_paths = sorted(
        PORTABLE_HARNESS_PRESERVE_PATHS - preserve_paths
    )
    for rel in missing_preserve_paths:
        errors.append(f"local-runtime-state must preserve path: {rel}")
    for rel in sorted(PORTABLE_HARNESS_PRESERVE_PATHS - included_paths):
        errors.append(
            f"base harness included_paths missing preserve path: {rel}"
        )

    portable_group_paths: set[str] = set()
    for group in groups.values():
        if group.get("tier") == "do_not_copy":
            continue
        portable_group_paths.update(group.get("paths", []))

    missing_required_paths = sorted(
        rel
        for rel in REQUIRED_PATHS
        if not any(
            _manifest_path_covers_required_path(group_path, rel)
            for group_path in portable_group_paths
        )
    )
    for rel in missing_required_paths:
        errors.append(
            "base harness portable groups missing required path: " + rel
        )

    copyable_paths = set(included_paths)
    copyable_paths.update(portable_group_paths)

    do_not_copy_patterns = local_runtime.get("paths", [])
    collisions = sorted(
        rel
        for rel in copyable_paths
        for pattern in do_not_copy_patterns
        if _path_matches_manifest_pattern(pattern, rel)
        and rel not in preserve_paths
    )
    for rel in collisions:
        errors.append(
            "copyable harness path is covered by local-runtime-state: " + rel
        )


def _is_copytree_call(node: ast.Call) -> bool:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr == "copytree"
    if isinstance(node.func, ast.Name):
        return node.func.id == "copytree"
    return False


def _first_arg_is_root(node: ast.Call) -> bool:
    return (
        bool(node.args)
        and isinstance(node.args[0], ast.Name)
        and (node.args[0].id == "ROOT")
    )


def _has_ignore_keyword(node: ast.Call) -> bool:
    return any(keyword.arg == "ignore" for keyword in node.keywords)


def _check_heavy_repo_copy_guard(root: Path, errors: list[str]) -> None:
    for rel in COPYTREE_GUARD_FILES:
        path = root / rel
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and _is_copytree_call(node)
                and _first_arg_is_root(node)
                and not _has_ignore_keyword(node)
            ):
                errors.append(
                    f"{rel} copies ROOT with shutil.copytree without ignore"
                )


def _check_harness_autoptimizer_contract(
    root: Path, errors: list[str]
) -> None:
    makefile_text = (root / "Makefile").read_text(encoding="utf-8")
    if (
        "harness-autopt:" in makefile_text
        or "TARGET" in makefile_text
        or ("GOAL" in makefile_text)
    ):
        errors.append(
            "Makefile must not expose TARGET/GOAL harness-autopt entrypoint"
        )

    skill_text = (
        root / ".agents" / "skills" / "harness-autoptimizer" / "SKILL.md"
    ).read_text(encoding="utf-8")
    for needle in (
        "Codex agent",
        "Sense",
        "Classify",
        "Constrain",
        "Repair",
        "Verify",
        "Self-Audit",
        "AutoptRequest",
        "ReviewFinding",
        "ReviewReport",
        "ProactiveReviewProbe",
        "proactive review probe",
        "out_of_scope",
        "verification_class",
        "loop_count",
        "converged",
        "ExperienceCandidate",
    ):
        if needle not in skill_text:
            errors.append(
                ".agents/skills/harness-autoptimizer/SKILL.md "
                f"missing controller contract: {needle}"
            )

    for rel in (
        ".agents/skills/harness-autoptimizer/prompts/auto-controller.md",
        ".agents/skills/harness-autoptimizer/prompts/repair-request.md",
    ):
        path = root / rel
        if not path.exists():
            continue
        prompt_text = path.read_text(encoding="utf-8")
        for needle in (
            "ReviewFinding",
            "ReviewReport",
            "proactive",
            "out_of_scope",
            "verification_class",
            "loop_count",
            "converged",
        ):
            if needle not in prompt_text:
                errors.append(
                    f"{rel} missing structured review contract: {needle}"
                )

    helper_text = (
        root
        / ".agents"
        / "skills"
        / "harness-autoptimizer"
        / "scripts"
        / "harness_autopt.py"
    ).read_text(encoding="utf-8")
    for needle in (
        "class ReviewFinding",
        "class ProactiveReviewProbe",
        "class ReviewReport",
        "def build_review_report",
        "def run_proactive_review_probes",
        "def write_review_report",
        "ReviewReport must be converged before creating a pull request",
        "review_report=review_report",
        "verification_class",
        "loop_count",
        "converged",
    ):
        if needle not in helper_text:
            errors.append(
                "harness_autopt.py missing structured review helper: " + needle
            )

    forbidden_helpers = (
        "def run_candidate_generation",
        "def run_autoptimization",
        'parser.add_argument("--target"',
        'parser.add_argument("--goal"',
        'parser.add_argument("--candidate-count"',
    )
    for needle in forbidden_helpers:
        if needle in helper_text:
            errors.append(
                "harness_autopt.py must not keep Python-runner control path: "
                + needle
            )

    workflow_text = (
        root / ".github" / "workflows" / "harness-autopt.yml"
    ).read_text(encoding="utf-8")
    for needle in (
        "workflow_dispatch:",
        "schedule:",
        "contents: write",
        "pull-requests: write",
        "CODEX_AUTH_JSON",
        "codex_exec.py",
        "harness-autopt-controller.md",
    ):
        if needle not in workflow_text:
            errors.append(
                "harness-autopt workflow missing controller contract: "
                + needle
            )
    if "codex_exec.py" not in workflow_text:
        errors.append(
            "harness-autopt workflow must start a Codex agent controller"
        )


def _check_git_mainbranch_contract(root: Path, errors: list[str]) -> None:
    skill_text = (
        root / ".agents" / "skills" / "git-mainbranch" / "SKILL.md"
    ).read_text(encoding="utf-8")
    for needle in (
        "removed_worktrees",
        "skipped_worktrees",
        "force_deleted_branches",
        "force_delete_candidates",
        "git worktree list --porcelain",
        "git -C <path> status --porcelain",
        "git worktree remove <path>",
        "git branch -vv",
        "upstream が gone のローカルブランチ",
        'gh pr list --state merged --search "head:<branch>" '
        "--json number,state,mergedAt,headRefName,headRefOid,baseRefName,mergeCommit",
        "git branch --merged <target_branch>` に出ない",
        "force delete の客観証拠は、PR merged、"
        "upstream/remote branch gone、残存 worktree で checkout "
        "されていないこと、merged PR の `headRefName` が "
        "`<branch>` と一致すること、`headRefOid` が "
        "`git rev-parse <branch>` と一致すること、`baseRefName` "
        "が `<target_branch>` と一致すること、`git merge-base "
        "--is-ancestor <mergeCommit.oid> <target_branch>` が成功することのすべて",
        "追加のユーザー承認を求めず `git branch -D <branch>`",
        "証拠欠落をユーザー承認で補わない",
        "git branch -D <branch>",
        "git worktree remove --force",
    ):
        if needle not in skill_text:
            errors.append(
                ".agents/skills/git-mainbranch/SKILL.md "
                f"missing cleanup contract: {needle}"
            )

    playbook_text = (
        root
        / ".agents"
        / "skills"
        / "git-mainbranch"
        / "references"
        / "mainbranch-playbook.md"
    ).read_text(encoding="utf-8")
    for needle in (
        "Worktree Cleanup Before Branch Deletion",
        "git -C <path> status --porcelain",
        "git worktree remove --force",
        "used by worktree",
        "force_delete_candidates",
        "Candidate Collection",
        "upstream が gone のローカルブランチ",
        "remote branch gone と PR merge の両方",
        "対象 worktree が残っていない",
        "merged PR の `headRefName` が `<branch>` と一致すること",
        "`headRefOid` が `git rev-parse <branch>` と一致すること",
        "`baseRefName` が `<target_branch>` と一致すること",
        "`git merge-base --is-ancestor <mergeCommit.oid> <target_branch>` "
        "が成功すること",
        "force_deleted_branches",
        "追加のユーザー承認を求めず `git branch -D <branch>`",
        "証拠欠落をユーザー承認で補わない",
        "worktree safety 条件を満たさない場合は branch deletion も skip",
        "git branch -D <branch>",
        'gh pr list --state merged --search "head:<branch>" '
        "--json number,state,mergedAt,headRefName,headRefOid,baseRefName,mergeCommit",
    ):
        if needle not in playbook_text:
            errors.append(
                ".agents/skills/git-mainbranch/references/mainbranch-playbook.md "
                f"missing cleanup contract: {needle}"
            )


def _check_github_https_auth_preflight_contract(
    root: Path, errors: list[str]
) -> None:
    expectations = {
        ".agents/skills/git-commit-pr/SKILL.md": (
            *GITHUB_HTTPS_AUTH_PREFLIGHT_COMMON,
            "コミット、`git push`、`gh pr create` の前に必ず実行する",
            "コミットせず、push せず、Pull Request（PR）作成もせず停止する",
        ),
        ".agents/skills/git-mainbranch/SKILL.md": (
            *GITHUB_HTTPS_AUTH_PREFLIGHT_COMMON,
            "`git fetch --prune`、`git pull --ff-only`、`gh pr list`",
            "fetch、pull、`gh pr list`、worktree cleanup、branch deletion "
            "を行わず停止する",
        ),
        ".agents/skills/git-mainbranch/references/mainbranch-playbook.md": (
            *GITHUB_HTTPS_AUTH_PREFLIGHT_COMMON,
            "`git fetch --prune`、`git pull --ff-only`、`gh pr list`",
            "fetch、pull、`gh pr list`、worktree cleanup、branch deletion "
            "を行わず停止する",
        ),
    }
    for rel, needles in expectations.items():
        text = (root / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(
                    f"{rel} missing GitHub HTTPS auth preflight contract: "
                    + needle
                )


def _check_github_api_helper(root: Path, errors: list[str]) -> None:
    helper = root / "bin" / "github_api_pr.sh"
    if not helper.exists():
        return
    text = helper.read_text(encoding="utf-8")
    for forbidden in (
        "REPO=" "base",
        "OWNER=" "tkosht",
        "repos/tkosht/" "base",
    ):
        if forbidden in text:
            errors.append(
                "bin/github_api_pr.sh must not hard-code base repo: "
                + forbidden
            )
    for needle in ("GITHUB_REPOSITORY", "git config --get remote.origin.url"):
        if needle not in text:
            errors.append(
                "bin/github_api_pr.sh must resolve owner/repo dynamically: "
                + needle
            )


def _check_design_doc_terminology(root: Path, errors: list[str]) -> None:
    for rel in DESIGN_DOCS:
        text = (root / rel).read_text(encoding="utf-8")
        for term, expansions in DESIGN_TERM_EXPANSIONS.items():
            count = len(re.findall(rf"\b{term}\b", text))
            if count == 0:
                continue
            if not any(expansion in text for expansion in expansions):
                errors.append(
                    f"{rel} uses {term} without an approved expansion"
                )
            if count == 1:
                errors.append(
                    f"{rel} uses {term} only once; spell it out instead of abbreviating"
                )


def _check_design_contract(root: Path, errors: list[str]) -> None:
    repo_contract = (root / "docs/ai/repo-contract.md").read_text(
        encoding="utf-8"
    )
    for needle in (
        DESIGN_READ_FIRST_CONTRACT,
        DESIGN_ROLE_CONTRACT,
        DESIGN_README_ROLE_CONTRACT,
        DESIGN_SYNC_POLICY_CONTRACT,
        DESIGN_SYNC_INTAKE_CONTRACT,
        "## Generated Repo Checklist",
        "3. `DESIGN.md`",
        DESIGN_CHECKLIST_UPDATE_CONTRACT,
        "8. `docs/design/README.md`",
        DESIGN_CHECKLIST_SUPPLEMENT_CONTRACT,
    ):
        if needle not in repo_contract:
            errors.append(
                "docs/ai/repo-contract.md missing design contract: " + needle
            )

    design_readme = (root / "docs/design/README.md").read_text(
        encoding="utf-8"
    )
    for needle in (DESIGN_README_MIN_ROLE, DESIGN_README_SYNC_REF):
        if needle not in design_readme:
            errors.append(
                "docs/design/README.md missing design guidance contract: "
                + needle
            )

    for rel, needles in DESIGN_PREVIEW_NOTES.items():
        text = (root / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(f"{rel} missing preview note: {needle}")


def _check_non_root_design_md(root: Path, errors: list[str]) -> None:
    unexpected = sorted(
        str(path.relative_to(root))
        for path in root.rglob("DESIGN.md")
        if path.relative_to(root).as_posix() != "DESIGN.md"
    )
    if unexpected:
        errors.append(
            "non-root DESIGN.md is forbidden: " + ", ".join(unexpected)
        )


def _extract_workflow_paths(text: str) -> list[list[str]]:
    sections: list[list[str]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)paths:\s*$", lines[index])
        if not match:
            index += 1
            continue
        indent = len(match.group(1))
        index += 1
        entries: list[str] = []
        while index < len(lines):
            line = lines[index]
            stripped = line.strip()
            current_indent = len(line) - len(line.lstrip(" "))
            if stripped and current_indent <= indent:
                break
            item = re.match(r'^\s*-\s*[\'"]?([^\'"]+)[\'"]?\s*$', line)
            if item:
                entries.append(item.group(1))
            index += 1
        sections.append(entries)
    return sections


def _paths_cover_design_docs(paths: list[str]) -> bool:
    return any(path in {"docs/design/**", "docs/**", "**"} for path in paths)


def _check_workflow_path_filters(root: Path, errors: list[str]) -> None:
    for rel in (
        ".github/workflows/template-health.yml",
        ".github/workflows/ci.yml",
    ):
        text = (root / rel).read_text(encoding="utf-8")
        sections = _extract_workflow_paths(text)
        if not sections:
            continue
        for index, paths in enumerate(sections, start=1):
            if "DESIGN.md" not in paths:
                errors.append(
                    f"{rel} missing workflow path coverage for DESIGN.md "
                    f"in paths section {index}"
                )
            if not _paths_cover_design_docs(paths):
                errors.append(
                    f"{rel} missing workflow path coverage for docs/design/** "
                    f"in paths section {index}"
                )


def run_checks(root: Path = ROOT) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_PATHS:
        if not (root / rel).exists():
            errors.append(f"missing required path: {rel}")

    for rel in FORBIDDEN_PATHS:
        if (root / rel).exists():
            errors.append(f"local-only path should not be tracked: {rel}")

    agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")
    claude_text = (root / "CLAUDE.md").read_text(encoding="utf-8")
    for needle in (
        "docs/ai/repo-contract.md",
        "docs/architecture/knowledge-architecture.md",
        "docs/architecture/overview.md",
    ):
        if needle not in agents_text:
            errors.append(f"AGENTS.md must reference {needle}")
    for needle in (
        "docs/ai/repo-contract.md",
        "docs/standards/communication.md",
    ):
        if needle not in claude_text:
            errors.append(f"CLAUDE.md must reference {needle}")

    gitignore_text = (root / ".gitignore").read_text(encoding="utf-8")
    for needle in (
        ".claude/settings.local.json",
        ".claude/.claude/",
        "secrets/**",
        "!secrets/README.md",
    ):
        if needle not in gitignore_text:
            errors.append(f".gitignore missing pattern: {needle}")

    agent_skill_dirs = sorted(
        path.name
        for path in (root / ".agents" / "skills").iterdir()
        if path.is_dir() and path.name != "__pycache__"
    )
    if agent_skill_dirs != RETAINED_SKILLS:
        errors.append(
            "unexpected .agents/skills layout: " + ", ".join(agent_skill_dirs)
        )

    claude_entries = sorted(
        path.name
        for path in (root / ".claude" / "skills").iterdir()
        if path.is_symlink()
    )
    if claude_entries != RETAINED_SKILLS:
        errors.append(
            "unexpected .claude/skills layout: " + ", ".join(claude_entries)
        )
    for skill_name in claude_entries:
        link = root / ".claude" / "skills" / skill_name
        expected_target = Path(f"../../.agents/skills/{skill_name}")
        if link.readlink() != expected_target:
            errors.append(
                f".claude/skills/{skill_name} must point to {expected_target}"
            )

    codex_entries = sorted(
        path.name
        for path in (root / ".codex" / "skills").iterdir()
        if path.is_symlink()
    )
    if codex_entries != RETAINED_SKILLS:
        errors.append(
            "unexpected .codex/skills layout: " + ", ".join(codex_entries)
        )
    for skill_name in codex_entries:
        link = root / ".codex" / "skills" / skill_name
        expected_target = Path(f"../../.agents/skills/{skill_name}")
        if link.readlink() != expected_target:
            errors.append(
                f".codex/skills/{skill_name} must point to {expected_target}"
            )

    template_ids = sorted(spec.template_id for spec in list_templates())
    if template_ids != ["nextjs-app", "python-minimal"]:
        errors.append(f"unexpected template ids: {template_ids}")

    makefile_text = (root / "Makefile").read_text(encoding="utf-8")
    for needle in (
        "test-codex-live:",
        '-m "not codex_live"',
        "CODEX_INTEGRATION=1 uv run pytest -q -m codex_live tests/codex_subagent",
    ):
        if needle not in makefile_text:
            errors.append(
                f"Makefile missing Codex live test contract: {needle}"
            )

    pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8")
    if "codex_live:" not in pyproject_text:
        errors.append("pyproject.toml must define the codex_live marker")

    readme_text = (root / "README.md").read_text(encoding="utf-8")
    if "make test-codex-live" not in readme_text:
        errors.append("README.md must document make test-codex-live")
    if "docs/architecture/knowledge-architecture.md" not in readme_text:
        errors.append(
            "README.md must document docs/architecture/knowledge-architecture.md"
        )

    contract_text = (root / "docs/ai/repo-contract.md").read_text(
        encoding="utf-8"
    )
    for needle in (
        "make test-codex-live",
        "ChatGPT",
        "docs/architecture/knowledge-architecture.md",
    ):
        if needle not in contract_text:
            errors.append(
                "docs/ai/repo-contract.md missing test mode contract: "
                + needle
            )
    for needle in (
        "docs/ai/experience-capture.md",
        EXPERIENCE_CAPTURE_CONTRACT,
    ):
        if needle not in contract_text:
            errors.append(
                "docs/ai/repo-contract.md missing experience contract: "
                + needle
            )

    experience_path = root / "docs" / "ai" / "experience-capture.md"
    if experience_path.exists():
        experience_text = experience_path.read_text(encoding="utf-8")
        core_question = (
            "この経験は、将来の Codex agent の行動をより単純・一貫・安全・"
            "自律的にする形へ圧縮できるか"
        )
        for needle in (
            core_question,
            "raw prompt",
            "sanitized summary",
            "harness-autoptimizer",
        ):
            if needle not in experience_text:
                errors.append(
                    "docs/ai/experience-capture.md missing experience contract: "
                    + needle
                )

    testing_text = (root / "docs/standards/testing.md").read_text(
        encoding="utf-8"
    )
    for needle in ("make test-codex-live", "codex_live"):
        if needle not in testing_text:
            errors.append(
                "docs/standards/testing.md missing live test guidance: "
                + needle
            )

    _check_primary_terminology(root, errors)
    _check_codex_shared_defaults(root, errors)
    _check_harness_resource_registry(root, errors)
    _check_base_harness_manifest(root, errors)
    _check_github_api_helper(root, errors)
    _check_heavy_repo_copy_guard(root, errors)
    _check_harness_autoptimizer_contract(root, errors)
    _check_github_https_auth_preflight_contract(root, errors)
    _check_git_mainbranch_contract(root, errors)
    _check_non_root_design_md(root, errors)
    _check_design_contract(root, errors)
    _check_design_doc_terminology(root, errors)

    workflow_expectations = {
        ".github/workflows/template-health.yml": (
            "make bootstrap",
            "make doctor",
        ),
        ".github/workflows/ci.yml": (
            "make lint",
            "make test",
        ),
    }
    for rel, needles in workflow_expectations.items():
        text = (root / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(f"{rel} missing workflow contract: {needle}")
        for forbidden in ("memory-bank/", "docs/04.knowledge/"):
            if forbidden in text:
                errors.append(f"{rel} must not reference {forbidden}")
    _check_workflow_path_filters(root, errors)

    live_marker_files = sorted(
        str(path.relative_to(root))
        for path in (root / "tests" / "codex_subagent").glob(
            "test_*integration.py"
        )
        if "pytest.mark.codex_live" in path.read_text(encoding="utf-8")
    )
    expected_live_marker_files = [
        "tests/codex_subagent/test_pipeline_integration.py",
        "tests/codex_subagent/test_tool_use_integration.py",
    ]
    if live_marker_files != expected_live_marker_files:
        errors.append(
            "unexpected codex_live marker layout: "
            + ", ".join(live_marker_files)
        )

    for rel in expected_live_marker_files:
        text = (root / rel).read_text(encoding="utf-8")
        if "ChatGPT-authenticated" not in text or "codex on PATH" not in text:
            errors.append(f"{rel} missing ChatGPT-authenticated skip reason")

    return errors


def main() -> int:
    errors = run_checks()
    if errors:
        for error in errors:
            print(error)
        return 1
    print("template validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
