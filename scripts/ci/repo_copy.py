from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

TOP_LEVEL_COPY_EXCLUDES = frozenset(
    {
        ".benchmarks",
        ".cache",
        ".git",
        ".npm-global",
        ".npm-cache",
        ".nox",
        ".projects",
        ".pytest_cache",
        ".ruff_cache",
        ".serena",
        ".serena_home",
        ".ssh",
        ".tox",
        ".venv",
        "backup",
        "bk",
        "bkup",
        "data",
        "dist",
        "htmlcov",
        "log",
        "logs",
        "mlruns",
        "node_modules",
        "output",
        "result",
        "temp",
        "tmp",
        "wk",
        "work",
        "worker",
    }
)
TOP_LEVEL_COPY_EXCLUDE_PATTERNS = frozenset(
    {
        "*.log",
        "*logs",
    }
)
CLAUDE_COPY_EXCLUDES = frozenset(
    {
        ".claude",
        "settings.local.json",
        "settings.local.json.backup",
    }
)
CODEX_COPY_KEEP = frozenset({"config.toml", "skills", "version.json"})
SECRETS_COPY_KEEP = frozenset({"README.md"})


def _is_env_runtime_file(name: str) -> bool:
    return name == ".env" or (
        name.startswith(".env.") and name != ".env.example"
    )


def make_repo_copy_ignore(
    source_root: Path,
) -> Callable[[str, list[str]], set[str]]:
    resolved_root = source_root.resolve()

    def ignore(dir_path: str, names: list[str]) -> set[str]:
        current = Path(dir_path).resolve()
        ignored: set[str] = set()
        if current == resolved_root:
            ignored.update(
                name for name in names if name in TOP_LEVEL_COPY_EXCLUDES
            )
            ignored.update(
                name
                for name in names
                if any(
                    Path(name).match(pattern)
                    for pattern in TOP_LEVEL_COPY_EXCLUDE_PATTERNS
                )
            )
            ignored.update(
                name for name in names if _is_env_runtime_file(name)
            )
        try:
            rel = current.relative_to(resolved_root).as_posix()
        except ValueError:
            return ignored
        if rel == ".codex":
            ignored.update(
                name for name in names if name not in CODEX_COPY_KEEP
            )
        if rel == ".claude":
            ignored.update(
                name for name in names if name in CLAUDE_COPY_EXCLUDES
            )
        if rel == "secrets":
            ignored.update(
                name for name in names if name not in SECRETS_COPY_KEEP
            )
        return ignored

    return ignore


def copy_repo_for_test(source_root: Path, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    shutil.copytree(
        source_root,
        repo,
        symlinks=True,
        ignore=make_repo_copy_ignore(source_root),
    )
    return repo
