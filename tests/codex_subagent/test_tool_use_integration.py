import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / ".claude"
    / "skills"
    / "codex-subagent"
    / "scripts"
    / "codex_exec.py"
)

RUN_INTEGRATION = os.environ.get("CODEX_INTEGRATION") == "1"
HAS_CODEX = shutil.which("codex") is not None

pytestmark = pytest.mark.skipif(
    not RUN_INTEGRATION or not HAS_CODEX,
    reason="set CODEX_INTEGRATION=1 and ensure codex is on PATH",
)
TOOL_LOAD_MARKER = "TOOL_USE_LOAD_TEST_V1"


def _build_prompt() -> str:
    files = [
        "memory-bank/03-patterns/ai-agent-collaboration-exec_skill_usability_review_2026-01-05.md",
        ".claude/skills/ai-agent-collaboration-exec/SKILL.md",
        ".claude/skills/ai-agent-collaboration-exec/references/execution_framework.md",
        ".claude/skills/ai-agent-collaboration-exec/references/pipeline_spec_template.json",
        ".claude/skills/ai-agent-collaboration-exec/references/subagent_prompt_templates.md",
        ".claude/skills/ai-agent-collaboration-exec/references/contract_output.md",
    ]
    instructions = [
        "You are a skill validation agent.",
        "Use read_file to read each file in the list below exactly once.",
        "Do not use any other tools.",
        "Output JSON only with these keys:",
        "review_title, skill_role_section_title, framework_title,",
        "pipeline_stage_ids, prompt_template_title, contract_title, result.",
        'Set result to "ok".',
        'If you cannot extract a value, set it to "UNKNOWN".',
        "",
        "Files:",
    ]
    instructions.extend(f"- {path}" for path in files)
    return "\n".join(instructions)


def _build_tool_load_prompt() -> tuple[str, list[str]]:
    files = [
        "memory-bank/03-patterns/ai-agent-collaboration-exec_skill_usability_review_2026-01-05.md",
        ".claude/skills/ai-agent-collaboration-exec/SKILL.md",
        ".claude/skills/ai-agent-collaboration-exec/references/execution_framework.md",
        ".claude/skills/ai-agent-collaboration-exec/references/pipeline_spec_template.json",
        ".claude/skills/ai-agent-collaboration-exec/references/subagent_prompt_templates.md",
        ".claude/skills/ai-agent-collaboration-exec/references/contract_output.md",
        ".claude/skills/codex-subagent/SKILL.md",
        ".claude/commands/tasks/codex-subagent.md",
        "README.md",
        "pyproject.toml",
    ]
    instructions = [
        f"RUN_ID: {TOOL_LOAD_MARKER}",
        "You are a tool-load validation agent.",
        "Use read_file to read each file in the list below exactly once.",
        "Do not use any other tools.",
        "Output JSON only with these keys: files_read, result.",
        "Set files_read to the list of paths in the same order as provided.",
        'Set result to "ok".',
        'If you cannot read a file, set result to "error".',
        "",
        "Files:",
    ]
    instructions.extend(f"- {path}" for path in files)
    return "\n".join(instructions), files


def test_single_tool_use_completes_with_default_timeout():
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--mode",
        "single",
        "--task-type",
        "analysis",
        "--sandbox",
        "read-only",
        "--json",
        "--prompt",
        _build_prompt(),
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, (
        "codex_exec failed\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["timed_out"] is False
    assert payload["output"]

    output = json.loads(payload["output"])
    for key in (
        "review_title",
        "skill_role_section_title",
        "framework_title",
        "pipeline_stage_ids",
        "prompt_template_title",
        "contract_title",
        "result",
    ):
        assert key in output
        assert output[key] != "UNKNOWN"
    assert output["result"] == "ok"
    assert output["pipeline_stage_ids"] == [
        "draft",
        "execute",
        "review",
        "revise",
        "verify",
        "release",
    ]

    stderr = payload.get("stderr", "")
    assert "read_file" in stderr or "serena.read_file" in stderr


def test_tool_use_load_completes_with_default_timeout():
    prompt, files = _build_tool_load_prompt()
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--mode",
        "single",
        "--task-type",
        "analysis",
        "--sandbox",
        "read-only",
        "--json",
        "--prompt",
        prompt,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, (
        "codex_exec failed\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["timed_out"] is False
    assert payload["output"]

    output = json.loads(payload["output"])
    assert output["result"] == "ok"
    assert output["files_read"] == files

    stderr = payload.get("stderr", "") or ""
    read_calls = stderr.count("serena.read_file")
    if read_calls == 0:
        read_calls = stderr.count("read_file")
    assert read_calls >= len(files)
