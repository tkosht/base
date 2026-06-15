from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / ".agents" / "skills" / "tmux-agent-review-loop"
SCRIPTS = SKILL_DIR / "scripts"
sys.path.append(str(SCRIPTS))

from tmux_handoff_state import (  # noqa: E402
    HandoffAction,
    PaneInputState,
    PaneSnapshot,
    classify_current_input,
    codex_process_running,
    next_handoff_action,
)

CODEX_IDLE_SURFACE_WITH_REVIEW_TEXT = """
╭───────────────────────────────────────────────╮
│ >_ OpenAI Codex                               │
│                                               │
│ model:       gpt-5.5 xhigh   /model to change │
│ directory:   ~/workspace                      │
│ permissions: YOLO mode                        │
╰───────────────────────────────────────────────╯

  Tip: Use /rename to rename your threads for easier thread resuming.


› Run /review on my current changes

  gpt-5.5 xhigh · ~/workspace
"""

HANDOFF_NOTICE = (
    "レビュー結果ファイル: /tmp/tmux_review_round1.md を確認し、"
    "指摘対応後に指定 gate と git status を確認してください。"
)


def test_tmux_review_loop_skill_allows_helper_execution_surface() -> None:
    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    protocol_text = (
        SKILL_DIR / "references" / "tmux_handoff_protocol.md"
    ).read_text(encoding="utf-8")

    assert "Bash(uv run python:*)" in skill_text
    assert "Bash(uv run pytest:*)" in skill_text
    assert "scripts/tmux_handoff_state.py" in skill_text
    assert (
        "uv run pytest -q tests/harness_autoptimizer/"
        "test_tmux_handoff_state.py"
    ) in protocol_text


def test_codex_idle_surface_is_not_sendable_input() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen=CODEX_IDLE_SURFACE_WITH_REVIEW_TEXT,
        cursor_near="""
› Run /review on my current changes

  gpt-5.5 xhigh · ~/workspace
""",
        user_authorized_handoff=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.IDLE_CODEX_SURFACE
    )
    assert next_handoff_action(snapshot) == HandoffAction.PASTE_HANDOFF_NOTICE


def test_codex_default_prompt_surface_is_not_stale_input() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen="""
────────────────────────────────────────────────────────────────

• handoff path works

────────────────────────────────────────────────────────────────


› Summarize recent commits

  gpt-5.5 xhigh · ~/workspace
""",
        cursor_near="""
› Summarize recent commits

  gpt-5.5 xhigh · ~/workspace
""",
        user_authorized_handoff=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.IDLE_CODEX_SURFACE
    )
    assert next_handoff_action(snapshot) == HandoffAction.PASTE_HANDOFF_NOTICE


def test_codex_waiting_surface_with_arbitrary_prompt_is_idle() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen="""
─ Worked for 1m 50s ─────────────────────────────────────────────────


› Explain this codebase

  gpt-5.5 xhigh · ~/workspace
""",
        cursor_near="""
› Explain this codebase

  gpt-5.5 xhigh · ~/workspace
""",
        user_authorized_handoff=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.IDLE_CODEX_SURFACE
    )
    assert next_handoff_action(snapshot) == HandoffAction.PASTE_HANDOFF_NOTICE


def test_user_confirmed_idle_prompt_without_status_is_not_sendable_input() -> (
    None
):
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen="""
╭───────────────────────────────────────────────╮
│ >_ OpenAI Codex                               │
╰───────────────────────────────────────────────╯


› Improve documentation in @filename
""",
        cursor_near="› Improve documentation in @filename",
        user_authorized_handoff=True,
        user_confirmed_idle=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.IDLE_CODEX_SURFACE
    )
    assert next_handoff_action(snapshot) == HandoffAction.PASTE_HANDOFF_NOTICE


def test_user_confirmed_idle_does_not_override_unrelated_cursor_text() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen="""
╭───────────────────────────────────────────────╮
│ >_ OpenAI Codex                               │
╰───────────────────────────────────────────────╯

› Improve documentation

  gpt-5.5 xhigh · ~/workspace
""",
        cursor_near="Draft unrelated question about another repo",
        user_authorized_handoff=True,
        user_confirmed_idle=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.STALE_OR_UNRELATED_INPUT
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_unrelated_current_input_blocks_even_without_user_confirmed_idle() -> (
    None
):
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen="OpenAI Codex",
        cursor_near="Draft unrelated question about another repo",
        user_authorized_handoff=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.STALE_OR_UNRELATED_INPUT
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_pending_handoff_notice_requires_one_enter_retry() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen=f"""
› {HANDOFF_NOTICE}

  gpt-5.5 xhigh · ~/workspace
""",
        cursor_near=f"""
› {HANDOFF_NOTICE}

  gpt-5.5 xhigh · ~/workspace
""",
        user_authorized_handoff=True,
        pending_handoff_notice=HANDOFF_NOTICE,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.PENDING_HANDOFF_NOTICE
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.SEND_ENTER_THEN_RECHECK
    )


def test_pending_handoff_notice_takes_priority_over_user_confirmed_idle() -> (
    None
):
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen=f"› {HANDOFF_NOTICE}",
        cursor_near=f"› {HANDOFF_NOTICE}",
        user_authorized_handoff=True,
        user_confirmed_idle=True,
        pending_handoff_notice=HANDOFF_NOTICE,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.PENDING_HANDOFF_NOTICE
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.SEND_ENTER_THEN_RECHECK
    )


def test_arbitrary_prompt_matching_status_is_idle_without_pending_notice() -> (
    None
):
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen=f"""
› {HANDOFF_NOTICE}

  gpt-5.5 xhigh · ~/workspace
""",
        cursor_near=f"""
› {HANDOFF_NOTICE}

  gpt-5.5 xhigh · ~/workspace
""",
        user_authorized_handoff=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.IDLE_CODEX_SURFACE
    )
    assert next_handoff_action(snapshot) == HandoffAction.PASTE_HANDOFF_NOTICE


def test_pending_handoff_notice_blocks_after_retry() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen=f"""
› {HANDOFF_NOTICE}

  gpt-5.5 xhigh · ~/workspace
""",
        cursor_near=f"""
› {HANDOFF_NOTICE}

  gpt-5.5 xhigh · ~/workspace
""",
        user_authorized_handoff=True,
        pending_handoff_notice=HANDOFF_NOTICE,
        handoff_enter_retry_sent=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.PENDING_HANDOFF_NOTICE
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_old_handoff_notice_in_scrollback_does_not_send_unrelated_draft() -> (
    None
):
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen=f"""
› {HANDOFF_NOTICE}

  gpt-5.5 xhigh · ~/workspace
""",
        cursor_near="› New unrelated draft",
        user_authorized_handoff=True,
        pending_handoff_notice=HANDOFF_NOTICE,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.STALE_OR_UNRELATED_INPUT
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_old_handoff_notice_in_cursor_near_does_not_send_later_draft() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen="OpenAI Codex",
        cursor_near=f"""
› {HANDOFF_NOTICE}

  gpt-5.5 xhigh · ~/workspace

› New unrelated draft
""",
        user_authorized_handoff=True,
        pending_handoff_notice=HANDOFF_NOTICE,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.STALE_OR_UNRELATED_INPUT
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_response_after_pending_notice_is_positive_acknowledgement() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen=f"""
› {HANDOFF_NOTICE}

• レビュー結果ファイルを読みます。
""",
        cursor_near=f"""
› {HANDOFF_NOTICE}

• レビュー結果ファイルを読みます。
""",
        user_authorized_handoff=True,
        pending_handoff_notice=HANDOFF_NOTICE,
    )

    assert classify_current_input(snapshot) == PaneInputState.BUSY_OR_RUNNING
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_wrapped_pending_handoff_notice_with_response_evidence_is_busy() -> (
    None
):
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen="""
› レビュー結果ファイル: /tmp/tmux_review_round1.md を確認し、
  指摘対応後に指定 gate と git status を確認してください。

• レビュー結果ファイルを読みます。
""",
        cursor_near="""
› レビュー結果ファイル: /tmp/tmux_review_round1.md を確認し、
  指摘対応後に指定 gate と git status を確認してください。

• レビュー結果ファイルを読みます。
""",
        user_authorized_handoff=True,
        pending_handoff_notice=HANDOFF_NOTICE,
    )

    assert classify_current_input(snapshot) == PaneInputState.BUSY_OR_RUNNING
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_self_handoff_blocks_before_input_classification() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen="OpenAI Codex\n\n› Run /review\n\n  gpt-5.5",
        cursor_near="› Run /review\n\n  gpt-5.5",
        user_authorized_handoff=True,
        target_pane_id="%0",
        controller_pane_id="%0",
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.SELF_HANDOFF_BLOCKED
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_parent_transcript_marker_blocks_even_when_pane_ids_differ() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen="""
• Ran make test
  └ 120 passed

› レビュー結果ファイル: /tmp/review.md

  gpt-5.5 xhigh · ~/workspace
""",
        cursor_near="› レビュー結果ファイル: /tmp/review.md",
        user_authorized_handoff=True,
        target_pane_id="%1",
        controller_pane_id="%0",
        controller_recent_markers=("Ran make test",),
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.SELF_HANDOFF_BLOCKED
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_shell_pane_without_start_permission_blocks_handoff() -> None:
    snapshot = PaneSnapshot(
        current_command="bash",
        current_screen="$ ",
        cursor_near="$ ",
        user_authorized_handoff=True,
    )

    assert classify_current_input(snapshot) == PaneInputState.IDLE_EMPTY
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_shell_pane_can_start_codex_when_user_permits() -> None:
    snapshot = PaneSnapshot(
        current_command="bash",
        current_screen="$ ",
        cursor_near="$ ",
        user_authorized_handoff=True,
        user_permits_start_codex=True,
    )

    assert next_handoff_action(snapshot) == HandoffAction.START_CODEX_THEN_SEND


@pytest.mark.parametrize(
    ("current_command", "prompt"),
    [
        ("zsh", "%"),
        ("zsh", "$"),
        ("zsh", "#"),
        ("zsh", "devbox%"),
        ("zsh", "dev@host:~/repo%"),
        ("fish", ">"),
        ("fish", "dev@host ~/repo>"),
        ("fish", "~/repo>"),
        ("fish", "~/repo (main)>"),
        ("fish", "dev@host ~/repo (main)>"),
        ("pwsh", "PS /home/devuser/workspace>"),
    ],
)
def test_non_dollar_shell_prompt_can_start_codex_when_user_permits(
    current_command: str, prompt: str
) -> None:
    snapshot = PaneSnapshot(
        current_command=current_command,
        current_screen=prompt,
        cursor_near=prompt,
        user_authorized_handoff=True,
        user_permits_start_codex=True,
    )

    assert classify_current_input(snapshot) == PaneInputState.IDLE_EMPTY
    assert next_handoff_action(snapshot) == HandoffAction.START_CODEX_THEN_SEND


def test_bash_output_ending_in_greater_than_does_not_start_codex() -> None:
    snapshot = PaneSnapshot(
        current_command="bash",
        current_screen="build output\n>",
        cursor_near="build output\n>",
        user_authorized_handoff=True,
        user_permits_start_codex=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.STALE_OR_UNRELATED_INPUT
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_non_shell_greater_than_prompt_does_not_start_codex() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen=">",
        cursor_near=">",
        user_authorized_handoff=True,
        user_permits_start_codex=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.STALE_OR_UNRELATED_INPUT
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


@pytest.mark.parametrize(
    ("current_command", "cursor_near"),
    [
        ("fish", "build output\nsuccess>"),
        ("zsh", "progress\n100%"),
    ],
)
def test_shell_prompt_like_output_does_not_start_codex(
    current_command: str, cursor_near: str
) -> None:
    snapshot = PaneSnapshot(
        current_command=current_command,
        current_screen=cursor_near,
        cursor_near=cursor_near,
        user_authorized_handoff=True,
        user_permits_start_codex=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.STALE_OR_UNRELATED_INPUT
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_shell_pane_with_prior_output_and_live_prompt_can_start_codex() -> (
    None
):
    snapshot = PaneSnapshot(
        current_command="bash",
        current_screen="""
npm test
444 passed
$
""",
        cursor_near="""
npm test
444 passed
$
""",
        user_authorized_handoff=True,
        user_permits_start_codex=True,
    )

    assert classify_current_input(snapshot) == PaneInputState.IDLE_EMPTY
    assert next_handoff_action(snapshot) == HandoffAction.START_CODEX_THEN_SEND


@pytest.mark.parametrize(
    "cursor_near",
    [
        "gpt-output",
        "model: gpt-5.5",
        "directory: ~/workspace",
        "permissions: YOLO mode",
        "Tip: Use /rename",
        "╭────────────────────────╮",
    ],
)
def test_shell_pane_with_loose_status_text_does_not_start_codex(
    cursor_near: str,
) -> None:
    snapshot = PaneSnapshot(
        current_command="bash",
        current_screen=cursor_near,
        cursor_near=cursor_near,
        user_authorized_handoff=True,
        user_permits_start_codex=True,
    )

    assert not codex_process_running(snapshot)
    assert classify_current_input(snapshot) == (
        PaneInputState.STALE_OR_UNRELATED_INPUT
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_tail_only_codex_surface_does_not_start_nested_codex() -> None:
    tail_only_surface = """
› Implement {feature}

  gpt-5.5 xhigh · ~/workspace
"""
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen=tail_only_surface,
        cursor_near=tail_only_surface,
        user_authorized_handoff=True,
        user_permits_start_codex=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.IDLE_CODEX_SURFACE
    )
    assert codex_process_running(snapshot)
    assert next_handoff_action(snapshot) == HandoffAction.PASTE_HANDOFF_NOTICE


def test_node_prompt_with_loose_gpt_text_is_not_codex_surface() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen="› menu\n\ngpt-output",
        cursor_near="› menu\n\ngpt-output",
        user_authorized_handoff=True,
    )

    assert not codex_process_running(snapshot)
    assert classify_current_input(snapshot) == (
        PaneInputState.STALE_OR_UNRELATED_INPUT
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_node_loose_gpt_status_without_codex_footer_is_not_running_codex() -> (
    None
):
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen="gpt-output",
        cursor_near="gpt-output",
        user_authorized_handoff=True,
    )

    assert not codex_process_running(snapshot)
    assert classify_current_input(snapshot) == PaneInputState.IDLE_EMPTY
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_busy_codex_pane_reports_blocker_without_overwriting() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen=CODEX_IDLE_SURFACE_WITH_REVIEW_TEXT + "\nWorking",
        cursor_near="Working",
        user_authorized_handoff=True,
        user_confirmed_idle=True,
    )

    assert classify_current_input(snapshot) == PaneInputState.BUSY_OR_RUNNING
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_live_working_status_with_elapsed_time_is_busy() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen=CODEX_IDLE_SURFACE_WITH_REVIEW_TEXT,
        cursor_near="◦ Working (4s • esc to interrupt)",
        user_authorized_handoff=True,
    )

    assert classify_current_input(snapshot) == PaneInputState.BUSY_OR_RUNNING
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_live_working_status_with_background_suffix_is_busy() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen=CODEX_IDLE_SURFACE_WITH_REVIEW_TEXT,
        cursor_near=(
            "◦ Working (1m 14s • esc to interrupt) · "
            "1 background terminal running · /ps to view · /stop t…"
        ),
        user_authorized_handoff=True,
    )

    assert classify_current_input(snapshot) == PaneInputState.BUSY_OR_RUNNING
    assert next_handoff_action(snapshot) == (
        HandoffAction.WAIT_OR_REPORT_BLOCKER
    )


def test_old_working_output_does_not_block_idle_codex_surface() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen="""
git status
Working tree clean
""",
        cursor_near="""
› Explain this codebase

  gpt-5.5 xhigh · ~/workspace
""",
        user_authorized_handoff=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.IDLE_CODEX_SURFACE
    )
    assert next_handoff_action(snapshot) == HandoffAction.PASTE_HANDOFF_NOTICE


def test_confirmed_current_input_is_sent_once_then_rechecked() -> None:
    snapshot = PaneSnapshot(
        current_command="node",
        current_screen="OpenAI Codex\n\n› レビュー結果ファイル: /tmp/a.md",
        cursor_near="› レビュー結果ファイル: /tmp/a.md",
        user_authorized_handoff=True,
    )

    assert classify_current_input(snapshot) == (
        PaneInputState.SENDABLE_CURRENT_INPUT
    )
    assert next_handoff_action(snapshot) == (
        HandoffAction.SEND_ENTER_THEN_RECHECK
    )


def test_tmux_protocol_preserves_handoff_helper_markers() -> None:
    docs = {
        "skill": ROOT
        / ".agents"
        / "skills"
        / "tmux-agent-review-loop"
        / "SKILL.md",
        "protocol": ROOT
        / ".agents"
        / "skills"
        / "tmux-agent-review-loop"
        / "references"
        / "tmux_handoff_protocol.md",
        "skill-reference": ROOT
        / "docs"
        / "ai"
        / "skills"
        / "tmux-agent-review-loop.md",
    }
    markers = (
        "idle_codex_surface",
        "pending_handoff_notice",
        "self_handoff_blocked",
        "user_confirmed_idle",
        "start_codex_then_send",
        "controller_recent_markers",
        "C-m",
    )

    for name, path in docs.items():
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            assert marker in text, f"{name}: {marker}"


def test_review_loop_protocol_preserves_canonical_closure_statuses() -> None:
    protocol = (
        ROOT
        / ".agents"
        / "skills"
        / "tmux-agent-review-loop"
        / "references"
        / "review_loop_protocol.md"
    ).read_text(encoding="utf-8")
    template = (
        ROOT
        / ".agents"
        / "skills"
        / "tmux-agent-review-loop"
        / "references"
        / "review_artifact_template.md"
    ).read_text(encoding="utf-8")

    canonical_statuses = (
        "fixed",
        "not_applicable",
        "resolved",
        "non_issue",
        "needs_user_decision",
    )
    for status in canonical_statuses:
        assert status in protocol
        assert status in template


def test_review_loop_stop_reason_lists_include_self_handoff_blocked() -> None:
    docs = {
        "skill": ROOT
        / ".agents"
        / "skills"
        / "tmux-agent-review-loop"
        / "SKILL.md",
        "protocol": ROOT
        / ".agents"
        / "skills"
        / "tmux-agent-review-loop"
        / "references"
        / "review_loop_protocol.md",
        "skill-reference": ROOT
        / "docs"
        / "ai"
        / "skills"
        / "tmux-agent-review-loop.md",
    }
    stop_reasons = (
        "target_pane_unresolved",
        "handoff_unconfirmed",
        "role_boundary_violation",
        "target_pane_input_dirty",
        "target_pane_lifecycle_violation",
        "self_handoff_blocked",
    )

    for name, path in docs.items():
        text = path.read_text(encoding="utf-8")
        for stop_reason in stop_reasons:
            assert stop_reason in text, f"{name}: {stop_reason}"
