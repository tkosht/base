from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "templates" / "manifest.yaml"


class OverlayConflictError(RuntimeError):
    """Raised when an overlay would overwrite existing files."""


@dataclass(frozen=True)
class TemplateSpec:
    template_id: str
    description: str
    root_copy_from: Path
    validation: list[dict[str, str]]


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or "templates" not in data:
        raise ValueError("templates/manifest.yaml is invalid")
    return data


def list_templates(path: Path = MANIFEST_PATH) -> list[TemplateSpec]:
    manifest = load_manifest(path)
    entries = manifest.get("templates")
    if not isinstance(entries, list):
        raise ValueError("manifest templates must be a list")

    specs: list[TemplateSpec] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("template entry must be a mapping")
        template_id = entry["id"]
        description = entry["description"]
        root_copy_from = entry["root_copy_from"]
        validation = entry.get("validation", [])
        if not isinstance(template_id, str):
            raise ValueError("template id must be a string")
        if not isinstance(description, str):
            raise ValueError("template description must be a string")
        if not isinstance(root_copy_from, str):
            raise ValueError("template root_copy_from must be a string")
        if not isinstance(validation, list):
            raise ValueError("template validation must be a list")
        specs.append(
            TemplateSpec(
                template_id=template_id,
                description=description,
                root_copy_from=REPO_ROOT / root_copy_from,
                validation=validation,
            )
        )
    return specs


def get_template(template_id: str, path: Path = MANIFEST_PATH) -> TemplateSpec:
    for spec in list_templates(path):
        if spec.template_id == template_id:
            return spec
    raise KeyError(f"unknown template id: {template_id}")


def iter_source_files(source_root: Path) -> list[Path]:
    return sorted(path for path in source_root.rglob("*") if path.is_file())


def collect_conflicts(spec: TemplateSpec, target_root: Path) -> list[Path]:
    conflicts: list[Path] = []
    for src in iter_source_files(spec.root_copy_from):
        rel = src.relative_to(spec.root_copy_from)
        dest = target_root / rel
        if dest.exists():
            conflicts.append(dest)
    return conflicts


def apply_template(spec: TemplateSpec, target_root: Path) -> list[Path]:
    if not spec.root_copy_from.exists():
        raise FileNotFoundError(spec.root_copy_from)

    conflicts = collect_conflicts(spec, target_root)
    if conflicts:
        joined = ", ".join(
            str(path.relative_to(target_root)) for path in conflicts
        )
        raise OverlayConflictError(
            f"overlay would overwrite existing files: {joined}"
        )

    copied: list[Path] = []
    for src in iter_source_files(spec.root_copy_from):
        rel = src.relative_to(spec.root_copy_from)
        dest = target_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied.append(dest)
    return copied


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply a starter overlay to a repo"
    )
    parser.add_argument(
        "--template",
        required=True,
        help="Template id from templates/manifest.yaml",
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Target repository root. Defaults to the current directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show conflicts and copy plan without writing files.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    target_root = Path(args.target).resolve()
    spec = get_template(args.template)
    conflicts = collect_conflicts(spec, target_root)
    if conflicts:
        raise OverlayConflictError(
            "overlay would overwrite existing files: "
            + ", ".join(
                str(path.relative_to(target_root)) for path in conflicts
            )
        )
    if args.dry_run:
        for src in iter_source_files(spec.root_copy_from):
            rel = src.relative_to(spec.root_copy_from)
            print(rel.as_posix())
        return 0

    copied = apply_template(spec, target_root)
    print(f"Applied {spec.template_id} to {target_root}")
    for path in copied:
        print(path.relative_to(target_root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
