from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_gpu_entrypoint_initializes_dind_before_passthrough() -> None:
    entrypoint = (ROOT / "docker" / "gpu-container-entrypoint").read_text(
        encoding="utf-8"
    )

    configure_index = entrypoint.index("sudo configure-nvidia-dind")
    start_index = entrypoint.index("sudo service docker start")
    passthrough_index = entrypoint.index('exec "$@"')
    shell_index = entrypoint.index("exec bash --login")

    assert configure_index < start_index
    assert start_index < passthrough_index
    assert start_index < shell_index


def test_make_up_delegates_dind_startup_to_entrypoint() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    up_block = makefile.split("\nactive:", 1)[0].rsplit("\nup:", 1)[1]

    assert "configure-nvidia-dind" not in up_block
    assert "service docker start" not in up_block
