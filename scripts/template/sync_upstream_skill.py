from __future__ import annotations

import argparse
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "scripts" / "template" / "upstream_skills.toml"


class SyncError(RuntimeError):
    """Raised when an upstream skill sync cannot complete safely."""


class UnknownSkillError(SyncError):
    """Raised when the requested skill is not registered for syncing."""


@dataclass(frozen=True)
class UpstreamSkillSpec:
    skill_name: str
    repo: str
    ref: str
    source: str
    target: str


@dataclass(frozen=True)
class SyncResult:
    skill_name: str
    ref: str
    url: str
    target: Path


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, UpstreamSkillSpec]:
    with path.open("rb") as fh:
        data = tomllib.load(fh)

    skills = data.get("skills")
    if not isinstance(skills, dict):
        raise ValueError("upstream skill catalog is invalid")

    specs: dict[str, UpstreamSkillSpec] = {}
    for skill_name, entry in skills.items():
        if not isinstance(skill_name, str):
            raise ValueError("skill name must be a string")
        if not isinstance(entry, dict):
            raise ValueError(f"{skill_name} entry must be a table")

        repo = entry.get("repo")
        ref = entry.get("ref")
        source = entry.get("source")
        target = entry.get("target")
        if not all(
            isinstance(value, str) for value in (repo, ref, source, target)
        ):
            raise ValueError(f"{skill_name} entry is missing string fields")

        specs[skill_name] = UpstreamSkillSpec(
            skill_name=skill_name,
            repo=repo,
            ref=ref,
            source=source,
            target=target,
        )
    return specs


def get_skill_spec(
    skill_name: str,
    path: Path = CATALOG_PATH,
) -> UpstreamSkillSpec:
    specs = load_catalog(path)
    try:
        return specs[skill_name]
    except KeyError as exc:
        available = ", ".join(sorted(specs)) or "none"
        raise UnknownSkillError(
            f"unknown skill: {skill_name} (registered: {available})"
        ) from exc


def build_raw_url(
    spec: UpstreamSkillSpec, ref_override: str | None = None
) -> str:
    ref = ref_override or spec.ref
    return f"https://raw.githubusercontent.com/{spec.repo}/{ref}/{spec.source}"


def fetch_remote_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "codex"})
    try:
        with urlopen(request, timeout=30) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset)
    except (HTTPError, URLError) as exc:
        raise SyncError(f"failed to download {url}: {exc}") from exc


def ensure_relative_symlink(link_path: Path, target: str) -> None:
    link_path.parent.mkdir(parents=True, exist_ok=True)

    if link_path.is_symlink():
        if link_path.readlink() == Path(target):
            return
        link_path.unlink()
    elif link_path.exists():
        raise SyncError(f"refusing to replace non-symlink path: {link_path}")

    link_path.symlink_to(target)


def sync_skill(
    skill_name: str,
    *,
    root: Path = ROOT,
    ref_override: str | None = None,
    fetch_text=fetch_remote_text,
) -> SyncResult:
    catalog_path = root / "scripts" / "template" / "upstream_skills.toml"
    spec = get_skill_spec(skill_name, catalog_path)
    ref = ref_override or spec.ref
    url = build_raw_url(spec, ref_override=ref_override)
    target = root / spec.target

    text = fetch_text(url)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")

    ensure_relative_symlink(
        root / ".claude" / "skills" / skill_name,
        f"../../.agents/skills/{skill_name}",
    )
    ensure_relative_symlink(
        root / ".codex" / "skills" / skill_name,
        f"../../.agents/skills/{skill_name}",
    )

    return SyncResult(
        skill_name=skill_name,
        ref=ref,
        url=url,
        target=target,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync a vendored upstream skill into this repo"
    )
    parser.add_argument(
        "--skill",
        required=True,
        help="Registered skill name from scripts/template/upstream_skills.toml",
    )
    parser.add_argument(
        "--ref",
        help="Optional git ref override. Defaults to the catalog ref.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = sync_skill(args.skill, ref_override=args.ref)
    except SyncError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(
        f"Synced {result.skill_name} from {result.url} "
        f"to {result.target.relative_to(ROOT).as_posix()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
