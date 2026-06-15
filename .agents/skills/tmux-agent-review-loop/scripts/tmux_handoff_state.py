from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

_CODEX_COMMANDS = {"codex", "node"}
_SHELL_COMMANDS = {"bash", "fish", "pwsh", "sh", "zsh"}
_CODEX_MODEL_FOOTER_RE = re.compile(r"^gpt-[^\s·]+(?:\s+[^·]+)?\s+·\s+\S")
_BUSY_STATUS_RE = re.compile(
    r"^(?:[·•◦]\s*)?Working(?:\s*(?:[.…]+|\([^)]*\)))?(?:\s+·\s+.+)?$"
)
_POSIX_SHELL_PROMPT_RE = re.compile(
    r"^(?:\([^)]+\)\s*)?(?:[\w.\-]+@[\w.\-]+(?::[^#$]*)?\s*)?[$#]\s*$"
)
_ZSH_PROMPT_RE = re.compile(
    r"^(?:\([^)]+\)\s*)?(?:[\w.\-]+@[\w.\-]+(?::[^%]*)?\s*)?%\s*$"
)
_ZSH_HOST_PROMPT_RE = re.compile(r"^(?:\([^)]+\)\s*)?[A-Za-z][\w.\-]*%\s*$")
_FISH_PROMPT_RE = re.compile(
    r"^(?:>|(?:[~/]|\.)(?:[/\w.\-]*)(?:\s+\([^)]*\))?>|"
    r"[\w.\-]+@[\w.\-]+\s+(?:[~/]|\.)(?:[/\w.\-]*)(?:\s+\([^)]*\))?>)\s*$"
)
_POWERSHELL_PROMPT_RE = re.compile(r"^PS(?:\s+.+)?>\s*$")


class PaneInputState(StrEnum):
    BUSY_OR_RUNNING = "busy_or_running"
    IDLE_EMPTY = "idle_empty"
    IDLE_CODEX_SURFACE = "idle_codex_surface"
    PENDING_HANDOFF_NOTICE = "pending_handoff_notice"
    SELF_HANDOFF_BLOCKED = "self_handoff_blocked"
    SENDABLE_CURRENT_INPUT = "sendable_current_input"
    STALE_OR_UNRELATED_INPUT = "stale_or_unrelated_input"


class HandoffAction(StrEnum):
    PASTE_HANDOFF_NOTICE = "paste_handoff_notice"
    SEND_ENTER_THEN_RECHECK = "send_enter_then_recheck"
    START_CODEX_THEN_SEND = "start_codex_then_send"
    WAIT_OR_REPORT_BLOCKER = "wait_or_report_blocker"


@dataclass(frozen=True)
class PaneSnapshot:
    current_command: str
    current_screen: str
    cursor_near: str
    user_authorized_handoff: bool = False
    user_confirmed_idle: bool = False
    user_permits_start_codex: bool = False
    pending_handoff_notice: str | None = None
    handoff_enter_retry_sent: bool = False
    target_pane_id: str | None = None
    controller_pane_id: str | None = None
    controller_recent_markers: tuple[str, ...] = ()


def _normalize_visible_text(value: str) -> str:
    return " ".join(value.split())


def _compact_visible_text(value: str) -> str:
    return "".join(value.split())


def _last_codex_prompt_index(lines: list[str]) -> int | None:
    for index in range(len(lines) - 1, -1, -1):
        if lines[index].strip().startswith("›"):
            return index
    return None


def _current_codex_prompt_block(text: str) -> str:
    lines = text.splitlines()
    prompt_index = _last_codex_prompt_index(lines)
    if prompt_index is None:
        return ""
    return "\n".join(lines[prompt_index:])


def _pending_handoff_notice_visible(snapshot: PaneSnapshot) -> bool:
    if not snapshot.pending_handoff_notice:
        return False

    expected_notice = _compact_visible_text(snapshot.pending_handoff_notice)
    if not expected_notice:
        return False

    return expected_notice in _compact_visible_text(
        _current_codex_prompt_block(snapshot.cursor_near)
    )


def _codex_prompt_visible(text: str) -> bool:
    return any(line.strip().startswith("›") for line in text.splitlines())


def _codex_model_footer_line(line: str) -> bool:
    return _CODEX_MODEL_FOOTER_RE.match(line.strip()) is not None


def _codex_model_footer_visible(text: str) -> bool:
    return any(_codex_model_footer_line(line) for line in text.splitlines())


def _codex_top_chrome_visible(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines()]
    has_model = any(line.startswith("model:") for line in lines)
    has_directory = any(line.startswith("directory:") for line in lines)
    has_permissions = any(line.startswith("permissions:") for line in lines)
    has_chrome = any(
        line.startswith(("╭", "╰", "│")) or ">_ OpenAI Codex" in line
        for line in lines
    )
    return has_model and has_directory and has_permissions and has_chrome


def _command_name(command: str) -> str:
    return command.rsplit("/", maxsplit=1)[-1].lower()


def _lines_after_pending_notice(text: str, expected_notice: str) -> list[str]:
    normalized_notice = _compact_visible_text(expected_notice)
    if not normalized_notice:
        return []

    lines = text.splitlines()
    for start_index in range(len(lines)):
        accumulated: list[str] = []
        for end_index in range(start_index, len(lines)):
            accumulated.append(lines[end_index])
            if normalized_notice in _compact_visible_text(
                "\n".join(accumulated)
            ):
                return lines[end_index + 1 :]
    return []


def _status_or_chrome_line(line: str) -> bool:
    stripped = line.strip()
    return (
        not stripped
        or stripped.startswith(
            ("gpt-", "model:", "directory:", "permissions:")
        )
        or stripped.startswith(("Tip:", "╭", "╮", "╰", "╯", "│", "─"))
    )


def _cursor_near_allows_user_confirmed_idle(text: str) -> bool:
    return all(
        line.startswith("›") or _status_or_chrome_line(line)
        for line in (item.strip() for item in text.splitlines())
    )


def _handoff_ack_evidence_after_notice(snapshot: PaneSnapshot) -> bool:
    if not snapshot.pending_handoff_notice:
        return False

    for line in _lines_after_pending_notice(
        snapshot.cursor_near, snapshot.pending_handoff_notice
    ):
        stripped = line.strip()
        if _status_or_chrome_line(stripped):
            continue
        if stripped.startswith("›"):
            continue
        return True
    return False


def codex_tui_visible(snapshot: PaneSnapshot) -> bool:
    return "OpenAI Codex" in snapshot.current_screen


def _codex_surface_visible(snapshot: PaneSnapshot) -> bool:
    visible_text = f"{snapshot.current_screen}\n{snapshot.cursor_near}"
    return (
        codex_tui_visible(snapshot)
        or (
            _codex_prompt_visible(visible_text)
            and _codex_model_footer_visible(visible_text)
        )
        or _codex_top_chrome_visible(visible_text)
    )


def codex_process_running(snapshot: PaneSnapshot) -> bool:
    command = _command_name(snapshot.current_command)
    return command in _CODEX_COMMANDS and _codex_surface_visible(snapshot)


def _shell_prompt_line(line: str, command: str) -> bool:
    command_name = _command_name(command)
    if command_name == "fish":
        return _FISH_PROMPT_RE.match(line) is not None
    if command_name == "pwsh":
        return _POWERSHELL_PROMPT_RE.match(line) is not None
    if command_name == "zsh":
        return (
            _ZSH_PROMPT_RE.match(line) is not None
            or _ZSH_HOST_PROMPT_RE.match(line) is not None
            or _POSIX_SHELL_PROMPT_RE.match(line) is not None
        )
    return _POSIX_SHELL_PROMPT_RE.match(line) is not None


def _shell_prompt_only(lines: list[str], command: str) -> bool:
    if not lines:
        return True
    return all(_shell_prompt_line(line, command) for line in lines)


def _last_line_is_shell_prompt(lines: list[str], command: str) -> bool:
    return bool(lines and _shell_prompt_line(lines[-1], command))


def _busy_status_visible(text: str) -> bool:
    nonempty_lines = [
        line.strip() for line in text.splitlines() if line.strip()
    ]
    if not nonempty_lines:
        return False
    return any(
        _BUSY_STATUS_RE.match(line) is not None for line in nonempty_lines[-3:]
    )


def _command_is_shell(command: str) -> bool:
    return _command_name(command) in _SHELL_COMMANDS


def _sendable_handoff_prompt_line(line: str, snapshot: PaneSnapshot) -> bool:
    prompt = line.removeprefix("›").strip()
    compact_prompt = _compact_visible_text(prompt)
    if snapshot.pending_handoff_notice:
        compact_notice = _compact_visible_text(snapshot.pending_handoff_notice)
        if compact_notice and compact_notice in compact_prompt:
            return True
    return prompt.startswith(("レビュー結果ファイル:", "Review result file:"))


def should_start_codex(snapshot: PaneSnapshot) -> bool:
    if not snapshot.user_permits_start_codex or codex_process_running(
        snapshot
    ):
        return False
    if not _command_is_shell(snapshot.current_command):
        return False
    return classify_current_input(snapshot) == PaneInputState.IDLE_EMPTY


def classify_current_input(snapshot: PaneSnapshot) -> PaneInputState:
    current_screen = snapshot.current_screen
    cursor_near = snapshot.cursor_near

    if (
        snapshot.target_pane_id
        and snapshot.controller_pane_id
        and snapshot.target_pane_id == snapshot.controller_pane_id
    ):
        return PaneInputState.SELF_HANDOFF_BLOCKED
    if snapshot.controller_recent_markers:
        visible_text = _normalize_visible_text(
            f"{snapshot.current_screen}\n{snapshot.cursor_near}"
        )
        for marker in snapshot.controller_recent_markers:
            if marker and _normalize_visible_text(marker) in visible_text:
                return PaneInputState.SELF_HANDOFF_BLOCKED

    if _busy_status_visible(cursor_near):
        return PaneInputState.BUSY_OR_RUNNING

    if _pending_handoff_notice_visible(snapshot):
        if _handoff_ack_evidence_after_notice(snapshot):
            return PaneInputState.BUSY_OR_RUNNING
        return PaneInputState.PENDING_HANDOFF_NOTICE

    if snapshot.user_confirmed_idle and (
        _codex_prompt_visible(cursor_near)
        or _codex_prompt_visible(current_screen)
    ):
        if _cursor_near_allows_user_confirmed_idle(cursor_near):
            return PaneInputState.IDLE_CODEX_SURFACE
        return PaneInputState.STALE_OR_UNRELATED_INPUT

    stripped_near = [line.strip() for line in cursor_near.splitlines()]
    nonempty_near = [line for line in stripped_near if line]
    prompt_lines = [line for line in nonempty_near if line.startswith("›")]
    model_status_after_prompt = False
    last_prompt_index = _last_codex_prompt_index(stripped_near)
    last_prompt_line = (
        stripped_near[last_prompt_index]
        if last_prompt_index is not None
        else None
    )
    if last_prompt_index is not None:
        later_nonempty = [
            item for item in stripped_near[last_prompt_index + 1 :] if item
        ]
        model_status_after_prompt = bool(
            later_nonempty and _codex_model_footer_line(later_nonempty[0])
        )

    if prompt_lines and model_status_after_prompt:
        return PaneInputState.IDLE_CODEX_SURFACE

    if prompt_lines:
        if not codex_process_running(snapshot):
            return PaneInputState.STALE_OR_UNRELATED_INPUT
        if (
            snapshot.user_authorized_handoff
            and last_prompt_line
            and _sendable_handoff_prompt_line(last_prompt_line, snapshot)
        ):
            return PaneInputState.SENDABLE_CURRENT_INPUT
        return PaneInputState.STALE_OR_UNRELATED_INPUT

    if nonempty_near:
        if _command_is_shell(snapshot.current_command):
            if _shell_prompt_only(
                nonempty_near, snapshot.current_command
            ) or _last_line_is_shell_prompt(
                nonempty_near, snapshot.current_command
            ):
                return PaneInputState.IDLE_EMPTY
            return PaneInputState.STALE_OR_UNRELATED_INPUT
        status_only = all(
            line.startswith(("gpt-", "model:", "directory:", "permissions:"))
            or line.startswith(("Tip:", "╭", "╰", "│"))
            for line in nonempty_near
        )
        if status_only:
            return (
                PaneInputState.IDLE_CODEX_SURFACE
                if codex_process_running(snapshot)
                else PaneInputState.IDLE_EMPTY
            )
        return PaneInputState.STALE_OR_UNRELATED_INPUT

    return PaneInputState.IDLE_EMPTY


def next_handoff_action(snapshot: PaneSnapshot) -> HandoffAction:
    state = classify_current_input(snapshot)
    if state in {
        PaneInputState.BUSY_OR_RUNNING,
        PaneInputState.SELF_HANDOFF_BLOCKED,
    }:
        return HandoffAction.WAIT_OR_REPORT_BLOCKER
    if state == PaneInputState.PENDING_HANDOFF_NOTICE:
        if snapshot.handoff_enter_retry_sent:
            return HandoffAction.WAIT_OR_REPORT_BLOCKER
        return HandoffAction.SEND_ENTER_THEN_RECHECK
    if state == PaneInputState.SENDABLE_CURRENT_INPUT:
        return HandoffAction.SEND_ENTER_THEN_RECHECK
    if state == PaneInputState.STALE_OR_UNRELATED_INPUT:
        return HandoffAction.WAIT_OR_REPORT_BLOCKER
    if should_start_codex(snapshot):
        return HandoffAction.START_CODEX_THEN_SEND
    if not codex_process_running(snapshot):
        return HandoffAction.WAIT_OR_REPORT_BLOCKER
    return HandoffAction.PASTE_HANDOFF_NOTICE
