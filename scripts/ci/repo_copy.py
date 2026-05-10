from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

TOP_LEVEL_COPY_EXCLUDES = frozenset(
    {
        ".git",
        ".npm-global",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "node_modules",
        "worker",
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
