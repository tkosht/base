from __future__ import annotations

from pathlib import Path

import pytest

from scripts.template.apply_overlay import (
    OverlayConflictError,
    apply_template,
    get_template,
    list_templates,
)


def test_manifest_contains_expected_template_ids() -> None:
    template_ids = sorted(spec.template_id for spec in list_templates())
    assert template_ids == ["nextjs-app", "python-minimal"]


def test_apply_python_overlay_into_empty_directory(tmp_path: Path) -> None:
    spec = get_template("python-minimal")
    apply_template(spec, tmp_path)

    assert (tmp_path / "src" / "template_python_app" / "core.py").exists()
    assert (tmp_path / "tests" / "template_python" / "test_core.py").exists()


def test_apply_nextjs_overlay_into_empty_directory(tmp_path: Path) -> None:
    spec = get_template("nextjs-app")
    apply_template(spec, tmp_path)

    assert (tmp_path / "apps" / "web" / "package.json").exists()
    assert (tmp_path / "apps" / "web" / "app" / "page.tsx").exists()


def test_overlay_fails_when_target_file_exists(tmp_path: Path) -> None:
    spec = get_template("python-minimal")
    existing = tmp_path / "src" / "template_python_app"
    existing.mkdir(parents=True)
    (existing / "core.py").write_text("already here", encoding="utf-8")

    with pytest.raises(OverlayConflictError):
        apply_template(spec, tmp_path)
