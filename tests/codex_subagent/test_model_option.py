import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "codex-subagent" / "scripts"
sys.path.append(str(SCRIPTS))

import codex_exec  # noqa: E402


def test_run_codex_exec_passes_model_and_records_metadata(monkeypatch):
    captured_cmd: list[str] = []

    class DummyProc:
        def __init__(self, cmd):
            self.cmd = cmd
            self.returncode = 0

        def communicate(self, timeout=None):
            return ("ok", "")

    def fake_popen(cmd, **kwargs):
        del kwargs
        captured_cmd.extend(cmd)
        return DummyProc(cmd)

    monkeypatch.setattr(codex_exec.subprocess, "Popen", fake_popen)

    result = codex_exec.run_codex_exec(
        prompt="hello",
        model="gpt-5.3-codex-spark",
    )

    assert "--model" in captured_cmd
    model_index = captured_cmd.index("--model")
    assert captured_cmd[model_index + 1] == "gpt-5.3-codex-spark"
    assert result.success is True
    assert result.metadata["model"] == "gpt-5.3-codex-spark"


def test_execute_parallel_propagates_model(monkeypatch):
    seen_models: list[str | None] = []

    async def fake_run_codex_exec_async(
        prompt,
        sandbox,
        timeout,
        agent_id,
        workdir,
        profile,
        model,
    ):
        del prompt, sandbox, timeout, workdir, profile
        seen_models.append(model)
        return codex_exec.CodexResult(
            agent_id=agent_id,
            output="ok",
            success=True,
            metadata={"model": model},
        )

    monkeypatch.setattr(
        codex_exec, "run_codex_exec_async", fake_run_codex_exec_async
    )

    results = asyncio.run(
        codex_exec.execute_parallel(
            prompts=["a", "b", "c"],
            model="gpt-5.3-codex",
        )
    )

    assert seen_models == [
        "gpt-5.3-codex",
        "gpt-5.3-codex",
        "gpt-5.3-codex",
    ]
    assert [r.metadata.get("model") for r in results] == seen_models
