from __future__ import annotations

from pathlib import Path

from scripts.ci.validate_template import run_checks

ROOT = Path(__file__).resolve().parents[1]


def test_template_contract_checks_pass() -> None:
    assert run_checks(ROOT) == []
