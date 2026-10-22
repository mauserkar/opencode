# OpenCode

Personal [OpenCode](https://opencode.ai) configuration plus a reproducible Docker development environment (devbox). It defines an agent-orchestrated engineering workflow: specify → implement → test → review → merge.

## Structure

```
.
├── agents/              # Agent definitions (primary and subagents)
├── commands/            # Custom slash commands
├── skills/              # Reusable skills
├── mcps/                # MCP servers (e.g. mcps/jira, dockerized)
├── opencode.jsonc       # OpenCode configuration (base)
├── cli.json             # OpenCode V2 CLI (TUI) settings
├── AGENTS.md            # Global agent rules (language, security, worktrees)
├── profiles/            # Work/personal profiles (copy examples to opencode.jsonc)
├── Dockerfile           # Devbox image
├── docker-compose.yaml  # Container orchestration (usually copied into the target repo as `docker-compose-devbox.yaml`)
├── Makefile             # Shortcuts to build/run the devbox (`make help`)
├── .env.example         # Environment variable template
└── package.json         # (gitignored) local Node dependencies
```

> **Note:** `package.json`, `package-lock.json`, and `node_modules/` are **not versioned** (they are listed in `.gitignore`). A fresh clone will not contain them, and they are not required at runtime.

## Agents (`agents/`)

The default agent is **`resolver`** (lightweight fallback). The **`spec_driven`** agent is available as the orchestrator and delegates to subagents (it never implements code itself); select it explicitly or via a profile's `default_agent`.

### Primary

| Agent         | Role                                                                                                                                                                                           |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `resolver`    | Default agent. Fast, lightweight assistant for quick questions and context clarifications. Read-only, no subagent delegation.                                                                   |
| `spec_driven` | Orchestrator. Analyzes, plans, delegates, reviews results, and makes the final integration decision. Read-only plus read-only git/openspec commands.                                           |
| `unattended`  | Engineer for autonomous runs inside an isolated container. Broad write permissions, but blocks reading/editing secrets (`.env`, `.pem`, `.key`, `.ssh`, `.kube`, etc.) and dangerous commands. |

### Subagents

| Agent               | Role                                                                                                          |
| ------------------- | ------------------------------------------------------------------------------------------------------------- |
| `researcher`        | External research (docs, APIs, libraries, best practices). Read-only.                                         |
| `spec_author`       | Authors OpenSpec artifacts (proposal → specs → design → tasks). Only writes `openspec/**`, `specs/**`.        |
| `developer`         | Repository reconnaissance and production code implementation (mode `all`: usable as primary or subagent).    |
| `tester`            | Runs tests and validation; reports failures, regressions, and coverage gaps.                                  |
| `reviewer`          | General code review plus deep Go/Python audit (concurrency, memory, async, idiomatic errors). Read-only.      |
| `security_reviewer` | Security review (authn/authz, secrets, injection, dependencies, insecure defaults). Read-only.                |

## Workflow (spec_driven)

Spec-driven pipeline with no skipped stages:

```
proposal ──▶ specs ──▶ design ──▶ tasks     (OpenSpec)
    │
    ▼
worktree                                     (isolation)
    │
    ├──▶ implement
    ├──▶ test
    └──▶ review
    │
    ▼
merge ──▶ archive                            (integration)
```

1. **Understand** — inspect repo, git, and OpenSpec state.
2. **Specify** — `spec_author` drafts proposal, specs, design, and tasks (with a gate after each artifact) and validates with `openspec validate --strict`.
3. **Worktree** — isolate the change in a `git worktree` before touching any code.
4. **Implement → Test → Review** — loop inside the worktree (`developer`, `tester`, `reviewer`, plus `security_reviewer` as needed).
5. **Merge & Archive** — squash-merge into main and `openspec archive` the change.
6. **Final response** — summary of changes, artifacts, subagents, tests, and pending decisions.

## Commands (`commands/`)

| Command       | Description                                                                                                                                               |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/changelog`  | Updates `CHANGELOG.md` (Keep a Changelog format), computes the SemVer bump, updates the manifest, and creates the release commit.                         |
| `/format`     | Formats Python (`ruff`/`black`/`isort`), Terraform (`terraform fmt`), or Go (`gofmt`/`goimports`) code and shows `git diff --stat`.                       |
| `/versioning` | Audits and implements version support (`--version`, `/version` endpoint, `__version__`, …) based on project type, integrating with OpenSpec when present. |
| `/jira`       | Creates, gets, updates, lists, or searches Jira issues and manages their comments via the `jira` MCP server (`mcps/jira/`).                                |

## Skills (`skills/`)

| Skill                   | Description                                                                                                                                                          |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `conventional-commits`  | Analyzes the `git diff` and generates commit messages following Conventional Commits (`feat`, `fix`, `refactor`, `docs`, `perf`, `chore`, `!` for breaking changes). |
| `jira-issue-management` | Creates, updates, searches, lists, or comments on Jira issues during a session (requires the `jira` MCP server running, `JIRA_TOKEN` and `JIRA_BASE_URL`).           |
| `network-proxy`         | Rules for running `curl`/`wget` behind a proxy; reads the proxy only from `HTTP_PROXY` and forbids proxy use if it isn't defined.                                    |

## OpenCode Configuration (`opencode.jsonc`)

- Uses the native OpenCode V2 schema: `agents` and an ordered `permissions` array.
- `default_agent: resolver` (base fallback; profiles can override it, e.g. `unattended`).
- `build` and `plan` agents disabled.
- The server listens on `0.0.0.0:4096` via the `opencode serve --hostname 0.0.0.0 --port 4096` command in `docker-compose.yaml`; V2 does not use the deprecated `server` config key.
- No plugins are loaded. OpenSpec integration is native (see below).
- `compaction`, `tool_output` limits and `experimental.subagent_depth` are supported but not set here; define them in `opencode.jsonc` or a profile to override the defaults.

TUI/CLI settings live in `cli.json` (V2 schema) and belong at `~/.config/opencode/cli.json`; they do not affect `opencode serve`.

## OpenSpec Integration

OpenSpec integration does **not** use the legacy `opencode-plugin-openspec` V1 plugin, which is not compatible with OpenCode V2. OpenSpec ships native OpenCode support through its CLI, which generates standard skills and commands:

```bash
openspec init --tools opencode
```

Run it once per project (the `openspec` CLI is already installed in the devbox image, see [Docker Devbox](#docker-devbox)). It writes:

- `openspec/` at the repo root (`config.yaml`, `specs/`, `changes/`).
- `.opencode/skills/openspec-*/SKILL.md` — workflow skills.
- `.opencode/commands/opsx-*.md` — the equivalent `/opsx-*` slash commands.

Re-running `openspec init` (or `openspec update`) refreshes the generated files without touching `openspec/specs/` or `openspec/changes/`. Commit the generated `.opencode/skills/openspec-*` and `.opencode/commands/opsx-*` files like any other project file.

## Profiles (`profiles/`)

Separate **work**, and **personal** configurations, each an `opencode.jsonc` that is **merged on top of** the base config (so it only needs the overrides, e.g. `model`/`small_model`):

```
profiles/
├── work/opencode.example.jsonc        # copy to opencode.jsonc (gitignored)
├── personal/opencode.example.jsonc    # copy to opencode.jsonc (gitignored)
```

Select one with the `OPENCODE_CONFIG` environment variable:

```bash
export OPENCODE_CONFIG=~/.config/opencode/profiles/work/opencode.jsonc
```

In the Docker devbox, set `OPENCODE_PROFILE` (`work`, `personal`) in `.env`; the compose file wires it to `OPENCODE_CONFIG` automatically.

## Docker Devbox

Image based on `ubuntu:24.04` with the tooling required for the workflow:

- **Go** 1.27.1
- **Node.js** 20
- **Python** 3.14 (standalone, installed via `uv`)
- **OpenTofu** 1.13.0
- **OpenCode** 2.1.2
- **OpenSpec** 1.14.3
- CLI utilities: `git`, `ripgrep`, `fd-find`, `jq`, `yq`, `curl`, `vim`, `tree`, `unzip`, `zip`, `kubectl`, `helm`, `make`, `glab` (GitLab CLI).

Tool and runtime versions are defined exclusively in `docker-compose.yaml` (`build.args`). The `Dockerfile` ARGs intentionally have no defaults, so every build must go through Compose (or pass the args explicitly).

`docker-compose.yaml` mounts:

- the working repo at `/workspace/${PROJECT_NAME}` (`PROJECT_NAME` is required; the stack fails fast if unset),
- `agents/`, `commands/`, `skills/`, `scripts/`, `opencode.jsonc`, `AGENTS.md`, and `profiles/` as configuration,
- persistent volumes for the home directory (tooling, OpenCode data/state) and the workspace (so git worktrees can be created as siblings of the repo).

The container runs `opencode serve` on port `4096`, reachable through the Traefik gateway, with hardening: non-root `ubuntu` user, `read_only` root filesystem (with writable volumes for home and workspace plus a `/tmp` tmpfs), `cap_drop: ALL`, `no-new-privileges`, `pids_limit`, and fixed `mem_limit`/`cpus`.

> **Security note:** `OPENCODE_SERVER_PASSWORD` is passed as a container environment variable and is therefore visible via `docker inspect`. OpenCode V2 uses the fixed username `opencode`; `OPENCODE_SERVER_USERNAME` is not read. Keep `.env` out of version control.

> **Naming convention:** `docker-compose.yaml` is normally copied into the target repository's path as `docker-compose-devbox.yaml` (so it doesn't collide with the repo's own `docker-compose.yaml`, if any). The `Makefile` defaults to `docker-compose.yaml`; override it with `make <target> COMPOSE_FILE=docker-compose-devbox.yaml` when using a renamed copy.

> **Build context:** the image is built from `$HOME/.config/opencode`, where the `Dockerfile` lives, not from `--project-directory`. If you copy `docker-compose-devbox.yaml` into a target repo, keep `build.context: ${HOME}/.config/opencode` (or omit the `build` section in the copy and let the base file provide it).

### Usage

```bash
cp .env.example .env      # fill in the variables
# Start the gateway once (creates the external traefik-net network)
docker compose -f docker-compose-gateway.yaml up -d
docker compose -f docker-compose-devbox.yaml up -d --build
# Server available at http://${PROJECT_NAME}.docker.localhost
```

### Makefile

Shortcuts for the commands above (defaults `PROJECT_NAME` to the current directory name; override with `make <target> PROJECT_NAME=foo`):

| Target                 | Description                                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------------------------- |
| `make help`            | Lists all available targets.                                                                                  |
| `make gateway-up`      | Starts the Traefik gateway (creates the external `traefik-net` network).                                      |
| `make gateway-down`    | Stops the Traefik gateway.                                                                                    |
| `make build`           | Rebuilds the devbox image for the host's native architecture (amd64/arm64), no manual platform config needed. |
| `make build-multiarch` | Builds `amd64`+`arm64` from the Compose config with `buildx`; requires the Docker buildx plugin and `PUSH=1` to push a multi-arch manifest. |

```bash
make help
make build-multiarch            # build amd64+arm64 (cache only)
make build-multiarch PUSH=1     # build and push the multi-arch manifest
```

### Environment Variables (`.env`)

| Variable                   | Description                                                                        |
| -------------------------- | ---------------------------------------------------------------------------------- |
| `PROJECT_NAME`             | Name used for the container and mount target (`/workspace/<PROJECT_NAME>`).       |
| `OPENCODE_PROFILE`         | Config profile to load: `work`, `personal`, or `unattended` (default: `personal`). |
| `OPENCODE_SERVER_PASSWORD` | Password to authenticate with the server (username is fixed to `opencode` in V2). |
