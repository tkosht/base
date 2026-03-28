import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "codex-subagent" / "scripts"
sys.path.append(str(SCRIPTS))

import codex_query  # noqa: E402


def _sample_logs():
    return [
        {
            "run_id": "run-codex",
            "timestamp": "2026-02-14T00:00:00+00:00",
            "execution": {
                "mode": "single",
                "task_type": "analysis",
                "model": "gpt-5.3-codex",
                "prompt": "task-a",
            },
            "results": [{"success": True, "execution_time": 10.0}],
            "evaluation": {"heuristic": {"combined_score": 4.2}},
        },
        {
            "run_id": "run-spark",
            "timestamp": "2026-02-14T00:01:00+00:00",
            "execution": {
                "mode": "single",
                "task_type": "analysis",
                "model": "gpt-5.3-codex-spark",
                "prompt": "task-b",
            },
            "results": [{"success": True, "execution_time": 8.5}],
            "evaluation": {"heuristic": {"combined_score": 4.0}},
        },
    ]


def test_filter_logs_by_model():
    logs = _sample_logs()
    filtered = list(
        codex_query.filter_logs(
            iter(logs),
            model="gpt-5.3-codex-spark",
        )
    )
    assert len(filtered) == 1
    assert filtered[0]["execution"]["model"] == "gpt-5.3-codex-spark"


def test_format_log_row_contains_model():
    row = codex_query.format_log_row(_sample_logs()[0])
    assert row["model"] == "gpt-5.3-codex"


def test_print_stats_includes_model_section(capsys):
    codex_query.print_stats(_sample_logs())
    out = capsys.readouterr().out
    assert "By Model:" in out
    assert "gpt-5.3-codex: 1" in out
    assert "gpt-5.3-codex-spark: 1" in out
