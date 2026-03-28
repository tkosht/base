#!/usr/bin/env python3
"""
codex_feedback.py - 人間フィードバック追加CLI

使用例:
    # 最新の実行にフィードバック追加
    python codex_feedback.py --score 4.5 --notes "Good output"

    # 特定の run_id にフィードバック追加
    python codex_feedback.py --run-id abc123 --score 4.5

    # インタラクティブモード
    python codex_feedback.py --interactive
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[4]
LOG_ROOT_DIR = ROOT_DIR / ".codex" / "sessions" / "codex_exec"


def resolve_log_dir(
    log_dir: str | None = None,
    scope: str | None = None,
) -> Path:
    if log_dir:
        candidate = Path(log_dir)
    else:
        env_dir = os.environ.get("CODEX_SUBAGENT_LOG_DIR")
        candidate = Path(env_dir) if env_dir else LOG_ROOT_DIR

    # If the user already passed a scoped directory (e.g. ".../auto") and no
    # explicit scope override exists, treat it as the scope.
    if candidate.name in {"human", "auto"} and scope is None:
        scope = candidate.name
        candidate = candidate.parent

    if scope in {"human", "auto"}:
        candidate = candidate / scope

    if not candidate.is_absolute():
        candidate = ROOT_DIR / candidate
    return candidate


# ログディレクトリ
LOG_DIR = resolve_log_dir()


def find_latest_log() -> Path | None:
    """最新のログファイルを検索"""
    if not LOG_DIR.exists():
        return None

    # 日付ディレクトリを新しい順に探索
    log_files = list(LOG_DIR.rglob("run-*.jsonl"))
    if not log_files:
        return None

    return max(log_files, key=lambda p: p.stat().st_mtime)


def find_log_by_run_id(run_id: str) -> Path | None:
    """run_id でログファイルを検索"""
    if not LOG_DIR.exists():
        return None

    # run_id の先頭部分でファイル名検索
    for log_file in LOG_DIR.rglob(f"run-*-{run_id[:8]}*.jsonl"):
        return log_file

    # ファイル内容を検索
    for log_file in LOG_DIR.rglob("run-*.jsonl"):
        try:
            with open(log_file, encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("run_id", "").startswith(run_id):
                        return log_file
        except Exception:
            continue

    return None


def add_feedback(
    log_path: Path,
    score: float,
    notes: str = "",
    tags: list | None = None,
) -> bool:
    """ログファイルにフィードバックを追加"""
    try:
        # 既存のログを読み込み
        logs = []
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                logs.append(json.loads(line))

        if not logs:
            print("Error: Empty log file", file=sys.stderr)
            return False

        # 最後のログにフィードバックを追加
        log = logs[-1]
        log["evaluation"]["human"] = {
            "score": score,
            "notes": notes,
            "tags": tags or [],
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # ファイルを上書き
        with open(log_path, "w", encoding="utf-8") as f:
            for log_entry in logs:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return True

    except Exception as e:
        print(f"Error adding feedback: {e}", file=sys.stderr)
        return False


def show_log_summary(log_path: Path) -> None:
    """ログの概要を表示"""
    try:
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                log = json.loads(line)
                print(f"Run ID: {log.get('run_id', 'N/A')[:8]}...")
                print(f"Timestamp: {log.get('timestamp', 'N/A')}")
                print(f"Mode: {log.get('execution', {}).get('mode', 'N/A')}")
                prompt = log.get("execution", {}).get("prompt", "N/A")
                if len(prompt) > 100:
                    prompt = prompt[:100] + "..."
                print(f"Prompt: {prompt}")

                eval_data = log.get("evaluation") or {}
                heuristic = eval_data.get("heuristic") or {}
                print(
                    f"Heuristic Score: {heuristic.get('combined_score', 'N/A')}"
                )

                human = eval_data.get("human")
                if human:
                    print(f"Human Score: {human.get('score', 'N/A')}")
                    print(f"Human Notes: {human.get('notes', '')}")
                else:
                    print("Human Feedback: Not provided")

                print("-" * 40)

    except Exception as e:
        print(f"Error reading log: {e}", file=sys.stderr)


def interactive_mode() -> None:
    """インタラクティブモードでフィードバック収集"""
    log_path = find_latest_log()
    if not log_path:
        print("No log files found.", file=sys.stderr)
        return

    print("Latest log file:")
    show_log_summary(log_path)

    try:
        score_input = input("\nEnter score (1-5, or 'skip'): ").strip()
        if score_input.lower() == "skip":
            print("Skipped.")
            return

        score = float(score_input)
        if not 1 <= score <= 5:
            print("Score must be between 1 and 5", file=sys.stderr)
            return

        notes = input("Enter notes (optional): ").strip()
        tags_input = input("Enter tags (comma-separated, optional): ").strip()
        tags = (
            [t.strip() for t in tags_input.split(",") if t.strip()]
            if tags_input
            else []
        )

        if add_feedback(log_path, score, notes, tags):
            print(f"✅ Feedback added to {log_path.name}")
        else:
            print("❌ Failed to add feedback", file=sys.stderr)

    except KeyboardInterrupt:
        print("\nCancelled.")
    except ValueError as e:
        print(f"Invalid input: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="codex exec ログに人間フィードバックを追加"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        help="対象のrun_id（省略時は最新）",
    )
    parser.add_argument(
        "--score",
        type=float,
        help="評価スコア（1-5）",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="コメント",
    )
    parser.add_argument(
        "--tags",
        type=str,
        default="",
        help="タグ（カンマ区切り）",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="インタラクティブモード",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="ログの概要を表示",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="ログ保存先（既定: .codex/sessions/codex_exec）",
    )
    parser.add_argument(
        "--scope",
        "--log-scope",
        choices=["all", "human", "auto"],
        default=None,
        help="ログ分類（既定: env CODEX_SUBAGENT_LOG_SCOPE / 未設定: human）",
    )

    args = parser.parse_args()

    env_scope = os.environ.get("CODEX_SUBAGENT_LOG_SCOPE")
    if args.scope is None:
        effective_scope = (
            env_scope if env_scope in {"human", "auto"} else "human"
        )
    else:
        effective_scope = args.scope

    global LOG_DIR
    LOG_DIR = resolve_log_dir(
        args.log_dir,
        None if effective_scope == "all" else effective_scope,
    )

    if args.interactive:
        interactive_mode()
        return

    # ログファイルを検索
    if args.run_id:
        log_path = find_log_by_run_id(args.run_id)
        if not log_path:
            print(f"Log not found for run_id: {args.run_id}", file=sys.stderr)
            sys.exit(1)
    else:
        log_path = find_latest_log()
        if not log_path:
            print("No log files found.", file=sys.stderr)
            sys.exit(1)

    if args.show:
        show_log_summary(log_path)
        return

    if args.score is None:
        print(
            "Error: --score is required (or use --interactive)",
            file=sys.stderr,
        )
        sys.exit(1)

    if not 1 <= args.score <= 5:
        print("Error: score must be between 1 and 5", file=sys.stderr)
        sys.exit(1)

    tags = (
        [t.strip() for t in args.tags.split(",") if t.strip()]
        if args.tags
        else []
    )

    if add_feedback(log_path, args.score, args.notes, tags):
        print(f"✅ Feedback added to {log_path.name}")
    else:
        print("❌ Failed to add feedback", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
