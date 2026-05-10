#!/usr/bin/env python3
"""
codex_query.py - ログ検索・分析CLI

使用例:
    # 最新10件をリスト
    python codex_query.py --list --limit 10

    # 日付範囲で検索
    python codex_query.py --from 2025-12-20 --to 2025-12-22

    # タスク種別で検索
    python codex_query.py --task-type code_gen

    # スコア範囲で検索
    python codex_query.py --min-score 4.0

    # CSV エクスポート
    python codex_query.py --export csv > analysis.csv

    # 統計サマリー
    python codex_query.py --stats
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

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


def iter_logs(
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> Iterator[dict[str, Any]]:
    """ログを順次読み込み"""
    if not LOG_DIR.exists():
        return

    log_files = sorted(LOG_DIR.rglob("run-*.jsonl"), reverse=True)

    for log_file in log_files:
        try:
            with open(log_file, encoding="utf-8") as f:
                for line in f:
                    log = json.loads(line)

                    # 日付フィルタ
                    if from_date or to_date:
                        ts_str = log.get("timestamp", "")
                        try:
                            ts = datetime.fromisoformat(
                                ts_str.replace("Z", "+00:00")
                            )
                            ts = ts.replace(
                                tzinfo=None
                            )  # naive datetime に変換
                            if from_date and ts < from_date:
                                continue
                            if to_date and ts > to_date:
                                continue
                        except Exception:
                            continue

                    yield log

        except Exception:
            continue


def filter_logs(
    logs: Iterator[dict[str, Any]],
    task_type: str | None = None,
    mode: str | None = None,
    model: str | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
    has_human_feedback: bool | None = None,
    has_llm_eval: bool | None = None,
    timed_out: bool | None = None,
) -> Iterator[dict[str, Any]]:
    """ログをフィルタリング"""
    for log in logs:
        exec_data = log.get("execution", {})
        eval_data = log.get("evaluation", {})
        results = log.get("results", []) or []
        any_timed_out = any(r.get("timed_out") for r in results)

        if task_type and exec_data.get("task_type") != task_type:
            continue

        if mode and exec_data.get("mode") != mode:
            continue

        if model and exec_data.get("model") != model:
            continue

        heuristic = eval_data.get("heuristic") or {}
        score = heuristic.get(
            "combined_score", heuristic.get("average_score", 0)
        )

        if min_score is not None and score < min_score:
            continue

        if max_score is not None and score > max_score:
            continue

        if has_human_feedback is not None:
            human = eval_data.get("human")
            if has_human_feedback and not human:
                continue
            if not has_human_feedback and human:
                continue

        if has_llm_eval is not None:
            llm = eval_data.get("llm")
            if has_llm_eval and not llm:
                continue
            if not has_llm_eval and llm:
                continue

        if timed_out is not None and any_timed_out != timed_out:
            continue

        yield log


def format_log_row(log: dict[str, Any]) -> dict[str, Any]:
    """ログをフラットな辞書に変換"""
    exec_data = log.get("execution", {})
    eval_data = log.get("evaluation", {})
    heuristic = eval_data.get("heuristic") or {}
    human = eval_data.get("human") or {}
    llm = eval_data.get("llm") or {}
    results = log.get("results", [{}])

    # pipeline モードは results[].exec に実行結果がある
    mode = exec_data.get("mode", "")
    if mode == "pipeline" and results:
        first_exec = results[0].get("exec", {}) if results else {}
        any_timed_out = any(
            r.get("exec", {}).get("timed_out") for r in results
        )
    else:
        first_exec = results[0] if results else {}
        any_timed_out = any(r.get("timed_out") for r in (results or []))

    return {
        "run_id": log.get("run_id", "")[:8],
        "timestamp": log.get("timestamp", ""),
        "mode": mode,
        "model": exec_data.get("model", ""),
        "task_type": exec_data.get("task_type", ""),
        "prompt": exec_data.get("prompt", "")[:50],
        "success": first_exec.get("success", False),
        "timed_out": any_timed_out,
        "execution_time": first_exec.get("execution_time", 0),
        "heuristic_score": heuristic.get(
            "combined_score",
            heuristic.get("average_score", 0),
        ),
        "human_score": human.get("score", ""),
        "llm_score": llm.get("correctness", "") if llm else "",
    }


def print_table(logs: list[dict[str, Any]], limit: int = 10) -> None:
    """ログをテーブル形式で出力"""
    if not logs:
        print("No logs found.")
        return

    # ヘッダー
    header = (
        f"{'Run ID':<10} {'Timestamp':<25} {'Mode':<12} {'Model':<22} "
        f"{'Task':<15} {'TO':<3} {'Score':<8} {'Human':<6} {'LLM':<6}"
    )
    print(header)
    print("-" * 120)

    for i, log in enumerate(logs):
        if i >= limit:
            break

        row = format_log_row(log)
        human_score = str(row["human_score"]) if row["human_score"] else "-"
        llm_score = str(row["llm_score"]) if row["llm_score"] else "-"
        timed_out = "Y" if row.get("timed_out") else "-"

        print(
            f"{row['run_id']:<10} "
            f"{row['timestamp'][:23]:<25} "
            f"{row['mode']:<12} "
            f"{(row['model'] or '-'): <22} "
            f"{row['task_type']:<15} "
            f"{timed_out:<3} "
            f"{row['heuristic_score']:<8.2f} "
            f"{human_score:<6} "
            f"{llm_score:<6}"
        )

    total = len(logs)
    if total > limit:
        print(f"\n... and {total - limit} more (use --limit to show more)")


def export_csv(logs: list[dict[str, Any]], output=sys.stdout) -> None:
    """CSV形式でエクスポート"""
    if not logs:
        return

    fieldnames = [
        "run_id",
        "timestamp",
        "mode",
        "model",
        "task_type",
        "prompt",
        "success",
        "timed_out",
        "execution_time",
        "heuristic_score",
        "human_score",
        "llm_score",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for log in logs:
        row = format_log_row(log)
        writer.writerow(row)


def export_json(logs: list[dict[str, Any]], output=sys.stdout) -> None:
    """JSON形式でエクスポート"""
    json.dump(logs, output, ensure_ascii=False, indent=2)


def print_stats(logs: list[dict[str, Any]]) -> None:
    """統計サマリーを出力"""
    if not logs:
        print("No logs found.")
        return

    total = len(logs)
    scores = []
    human_scores = []
    llm_scores = []
    modes = {}
    models = {}
    task_types = {}

    for log in logs:
        exec_data = log.get("execution", {})
        eval_data = log.get("evaluation", {})
        heuristic = eval_data.get("heuristic") or {}

        score = heuristic.get(
            "combined_score", heuristic.get("average_score", 0)
        )
        if score:
            scores.append(score)

        human = eval_data.get("human", {}) or {}
        if human.get("score"):
            human_scores.append(human["score"])

        llm = eval_data.get("llm") or {}
        if llm.get("correctness"):
            llm_scores.append(llm["correctness"])

        mode = exec_data.get("mode", "unknown")
        modes[mode] = modes.get(mode, 0) + 1

        model = exec_data.get("model", "unknown") or "unknown"
        models[model] = models.get(model, 0) + 1

        task_type = exec_data.get("task_type", "unknown")
        task_types[task_type] = task_types.get(task_type, 0) + 1

    print("=" * 50)
    print("CODEX EXEC LOG STATISTICS")
    print("=" * 50)
    print(f"\nTotal Runs: {total}")

    if scores:
        print("\nHeuristic Scores:")
        print(f"  Average: {sum(scores) / len(scores):.2f}")
        print(f"  Min: {min(scores):.2f}")
        print(f"  Max: {max(scores):.2f}")

    if human_scores:
        print(f"\nHuman Feedback ({len(human_scores)} entries):")
        print(f"  Average: {sum(human_scores) / len(human_scores):.2f}")
    else:
        print("\nHuman Feedback: None")

    if llm_scores:
        print(f"\nLLM Evaluations ({len(llm_scores)} entries):")
        print(f"  Average: {sum(llm_scores) / len(llm_scores):.2f}")
    else:
        print("\nLLM Evaluations: None")

    print("\nBy Mode:")
    for mode, count in sorted(modes.items(), key=lambda x: -x[1]):
        print(f"  {mode}: {count}")

    print("\nBy Model:")
    for model, count in sorted(models.items(), key=lambda x: -x[1]):
        print(f"  {model}: {count}")

    print("\nBy Task Type:")
    for task_type, count in sorted(task_types.items(), key=lambda x: -x[1]):
        print(f"  {task_type}: {count}")


def main():
    parser = argparse.ArgumentParser(description="codex exec ログの検索・分析")

    # 出力モード
    parser.add_argument(
        "--list",
        action="store_true",
        help="ログをリスト表示",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="統計サマリーを表示",
    )
    parser.add_argument(
        "--export",
        choices=["csv", "json"],
        help="エクスポート形式",
    )

    # フィルタ
    parser.add_argument(
        "--from",
        dest="from_date",
        type=str,
        help="開始日 (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--to",
        dest="to_date",
        type=str,
        help="終了日 (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--task-type",
        type=str,
        choices=["code_gen", "code_review", "analysis", "documentation"],
        help="タスク種別",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["single", "parallel", "competition", "pipeline"],
        help="実行モード",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="モデル名（execution.model と一致するもの）",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        help="最小スコア",
    )
    parser.add_argument(
        "--max-score",
        type=float,
        help="最大スコア",
    )
    parser.add_argument(
        "--has-human",
        action="store_true",
        help="人間フィードバックあり",
    )
    parser.add_argument(
        "--has-llm",
        action="store_true",
        help="LLM評価あり",
    )
    parser.add_argument(
        "--timed-out",
        action="store_true",
        help="タイムアウトあり（results 内に timed_out=true が存在）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="表示件数（デフォルト: 10）",
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
        help="ログ分類（既定: env CODEX_SUBAGENT_LOG_SCOPE / 未設定: all）",
    )

    args = parser.parse_args()

    env_scope = os.environ.get("CODEX_SUBAGENT_LOG_SCOPE")
    if args.scope is None:
        effective_scope = (
            env_scope if env_scope in {"human", "auto"} else "all"
        )
    else:
        effective_scope = args.scope

    global LOG_DIR
    LOG_DIR = resolve_log_dir(
        args.log_dir,
        None if effective_scope == "all" else effective_scope,
    )

    # 日付パース
    from_date = None
    to_date = None
    if args.from_date:
        from_date = datetime.strptime(args.from_date, "%Y-%m-%d")
    if args.to_date:
        to_date = datetime.strptime(args.to_date, "%Y-%m-%d")

    # ログ取得
    logs = iter_logs(from_date, to_date)

    # フィルタ適用
    logs = filter_logs(
        logs,
        task_type=args.task_type,
        mode=args.mode,
        model=args.model,
        min_score=args.min_score,
        max_score=args.max_score,
        has_human_feedback=args.has_human if args.has_human else None,
        has_llm_eval=args.has_llm if args.has_llm else None,
        timed_out=True if args.timed_out else None,
    )

    # リストに変換
    logs_list = list(logs)

    # 出力
    if args.stats:
        print_stats(logs_list)
    elif args.export == "csv":
        export_csv(logs_list)
    elif args.export == "json":
        export_json(logs_list)
    else:
        print_table(logs_list, limit=args.limit)


if __name__ == "__main__":
    main()
