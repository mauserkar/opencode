# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.8.0] - 2026-10-07

### Added

- `glab` (GitLab CLI) to the Docker devbox image, documented in the OCI image
  label and the README tooling list.
- `Makefile` with shortcuts for the devbox workflow: `help`, `gateway-up`,
  `gateway-down`, `build`, and `build-multiarch` (native and cross-arch
  builds via `buildx`). Defaults `PROJECT_NAME` to the current directory
  name and `COMPOSE_FILE` to `docker-compose.yaml` (overridable for renamed
  copies, e.g. `docker-compose-devbox.yaml`).
- README sections documenting the `Makefile` targets and the convention of
  copying `docker-compose.yaml` into the target repository as
  `docker-compose-devbox.yaml`.

### Changed

- Removed the hardcoded `platform: linux/amd64` from `docker-compose.yaml`
  so the devbox builds natively for the host's architecture (amd64 or
  arm64) without per-environment configuration.
- Dropped the `amd64` default from `ARG TARGETARCH` in the `Dockerfile` so a
  missing BuildKit platform arg fails the build explicitly instead of
  silently producing amd64 binaries on non-amd64 hosts.

## [1.7.1] - 2026-10-06

### Added

- `docs(agents)`: conciseness and precision rules across all agent task
  definitions.

### Changed

- `fix(config)`: allowed `.env.example` and synced docs with tooling.
- `refactor(config)`: renamed the `command/` directory to `commands/`.
- `fix(config)`: restricted config mounts, hardened env denies, and deduped
  the work profile.
- `fix(infra)`: hardened the Traefik gateway and corrected the README config
  note.
- `fix(skills)`: made the Jira skill executable by agents.

### Fixed

- `fix(config)`: removed a redundant force-push rule and hardened the `yq`
  checksum verification.
- `fix(skills)`: dropped undocumented `opencode`/`slash` metadata from the
  conventional-commits skill.
- `fix`: corrected container path and permissions issues.

## [1.7.0] - 2026-10-05

### Added

- `network-proxy` skill with rules for running `curl`/`wget` behind a proxy.

### Changed

- Reformatted and tightened the `conventional-commits`, `jira-issue-management`,
  and `network-proxy` skills.
- Reduced Docker image size by streamlining and reordering the `Dockerfile`
  build stages.

### Fixed

- Fixed git worktree handling in the `developer` and `spec_driven` agents.

## [1.6.0] - 2026-10-02

### Added

- `helm` and `make` to the Docker devbox image.

## [1.5.1] - 2026-10-02

### Changed

- Renamed `docker-compose-gateway.yaml` resources for consistency.
- Fixed agent permissions and model configuration.

### Fixed

- Updated the `kubectl` version pin in the `Dockerfile`.

## [1.5.0] - 2026-10-01

### Added

- `kubectl` to the Docker devbox image.
- Jira issue management: `jira.md` command, `scripts/jira.py` CLI, and the
  `jira-issue-management` skill.
- OpenCode profiles (`work`, `personal`, `unattended`) with dedicated
  `opencode.jsonc` files and `docker-compose.yaml` wiring.
- `AGENTS.md` and `SECURITY.md` global guidance documents.
- `docker-compose-gateway.yaml` for the Traefik gateway.
- Unattended profile with its own `docker-compose.yaml` and `opencode.jsonc`
  (later merged back into the root compose file).
- Go modules path configuration in `opencode.jsonc`.
- `AGENTS.md` git-worktree default folder convention.
- OpenSpec permissions for the `spec_author`, `spec_driven`, and `unattended`
  agents.

### Changed

- Renamed the `architect` agent to `spec_driven` and moved agent permissions
  into `opencode.jsonc`.
- Reduced verbosity of the `developer` and `tester` agent prompts.
- Reformatted README, agent definitions, and skills for consistency.
- Updated the `versioning` command and personal profile model settings.

### Removed

- `bug_hunter` and `explorer` agents (functionality folded into other
  agents).
- `resolver` agent from the spec-driven flow.

## [1.4.0] - 2026-09-28

### Added

- Initial `Dockerfile` and `docker-compose.yaml` devbox setup (Go, OpenTofu,
  Node.js, Python, OpenCode, OpenSpec).
- Initial set of agents: `architect`, `bug_hunter`, `developer`, `explorer`,
  `researcher`, `resolver`, `reviewer`, `security_reviewer`, `spec_author`,
  `tester`, `unattended`.
- Initial `README.md` documentation.
- `.dockerignore` and hardened `.env.example`.

### Changed

- Security hardening of the `Dockerfile`, `docker-compose.yaml`, and
  `.env.example` (non-root user, read-only filesystem, capability drops).

### Fixed

- Corrected the `unattended` agent configuration.
