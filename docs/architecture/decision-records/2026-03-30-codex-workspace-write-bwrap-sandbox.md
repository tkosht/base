# Codex `workspace-write` Sandbox Fails in Docker Due to `bwrap`

## Status

Accepted

## Date

2026-03-30

## Context

When running Codex inside the current Ubuntu-based Docker container, all `exec_command` calls fail in `workspace-write` mode before the target command starts.

Observed error:

```text
bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted
```

This failure reproduces even for trivial commands such as `true`, `ls`, and `sed`.

The same environment works in `danger-full-access` mode.

Additional observations:

- Removing the `bubblewrap` package from the container image does not fix `workspace-write`.
- `danger-full-access` works after the package removal.
- `danger-full-access` also works with `/usr/bin/bwrap` present in the container image.
- `workspace-write` still fails after the package removal.
- In the container, Codex runs as `devuser` with `CapEff=0`.
- `kernel.apparmor_restrict_unprivileged_userns = 1` in the current environment.
- Manual `bwrap` execution as `devuser` fails with `setting up uid map: Permission denied`.
- Manual `bwrap --unshare-net` execution as `devuser` fails with `loopback: Failed RTM_NEWADDR: Operation not permitted`.
- Manual `bwrap` execution as `root` succeeds, including `--unshare-net`.
- The failure is therefore tied to Codex's internal sandbox path for `workspace-write`, not to repository file permissions or the mere presence of the `bubblewrap` package in the image.
- This was reproduced after container rebuild and restart.

## Decision

Treat this as an environment limitation of the current Docker-based execution environment.

Until a host-level or Codex-runtime-level fix is available:

- keep Codex running as non-root `devuser`
- use `danger-full-access` as the practical operating mode for this container
- use this observation as rationale for shipping `danger-full-access` as the template default, while still allowing generated repos to tighten to `workspace-write` when their environment supports it
- do not assume repository permission changes are the cause of this failure
- do not spend further time tuning `compose.yml` for this specific `RTM_NEWADDR` failure unless the Docker or host security model changes
- do not switch the default operating mode to `root` plus `workspace-write` unless the risk trade-off is explicitly re-evaluated
- if `workspace-write` must be restored, first prefer changing the host-level AppArmor / user namespace policy for the non-root execution path; treat running Codex as `root` as a fallback, not the default

## Consequences

- `workspace-write` is currently not a usable sandbox mode in this environment.
- Normal repository work can continue as `devuser` in `danger-full-access`.
- If `workspace-write` becomes a hard requirement, investigate the Docker host / nested sandbox interaction rather than repo-local permissions.
- This memo records environment evidence. It does not claim that `workspace-write` is universally unusable across all generated repos.

## Assumptions

- Codex in this container runs as non-root `devuser`.
- `devuser` has no effective Linux capability at runtime (`CapEff=0`).
- The current host keeps `kernel.apparmor_restrict_unprivileged_userns = 1`.
- The active trade-off prefers non-root execution stability over restoring `workspace-write` immediately.

## Revisit Conditions

Re-evaluate this decision if any of the following becomes true:

- Codex `workspace-write` succeeds as `devuser` in this environment for trivial commands such as `true`, `ls`, and `sed`.
- The Ubuntu host AppArmor or unprivileged user namespace policy changes so that non-root `bwrap` succeeds.
- Codex changes its `workspace-write` sandbox implementation and no longer depends on the failing `bwrap` path in this environment.
- The repository threat model changes and `danger-full-access` for `devuser` becomes unacceptable.
- A reviewed, lower-risk non-root path becomes available, such as a host policy change or supported sandbox configuration that preserves `workspace-write`.

## Evidence

Reproduced outcomes:

- `danger-full-access`: commands execute successfully
- `danger-full-access` with `bubblewrap 0.9.0` installed: commands execute successfully
- `workspace-write`: `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`
- manual `bwrap` as `devuser`: fails
- manual `bwrap --unshare-net` as `devuser`: fails
- manual `bwrap` as `root`: succeeds
- manual `bwrap --unshare-net` as `root`: succeeds

Tested after:

- container restart
- container recreation
- removing `bubblewrap` from the image
