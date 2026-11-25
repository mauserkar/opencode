# OpenCode

Personal [OpenCode](https://opencode.ai) configuration plus a reproducible Docker development environment (devbox). It defines an agent-orchestrated engineering workflow: specify → implement → test → review → merge.

## Structure

```
.
├── agents/                      # Agent definitions (primary and subagents)
├── commands/                    # Custom slash commands
├── skills/                      # Reusable skills
├── mcps/                        # MCP servers (e.g. mcps/jira, dockerized)
├── examples/                    # Starter configs to copy into target repos (Compose and sbx)
├── opencode.jsonc               # OpenCode configuration (base)
├── cli.json                     # OpenCode V2 CLI (TUI) settings
├── AGENTS.md                    # Global agent rules (language, security, worktrees)
├── profiles/                    # Work/personal profiles (copy examples to opencode.jsonc)
├── sbx/                         # Docker Sandboxes v3 kit (`opencode-devbox`)
├── sbxenv.yaml                  # Docker Sandboxes environment definition
├── VERSION                      # Tool and devbox image versions
├── Dockerfile                   # Devbox image
├── docker-compose.yaml          # Base container orchestration (included by target repos)
├── docker-compose-gateway.yaml  # Traefik gateway for routing `*.docker.localhost`
├── Makefile                     # Shortcuts to build/run the devbox (`make help`)
├── .env.example                 # Environment variable template
└── package.json                 # (gitignored) local Node dependencies
```

> **Note:** `package.json`, `package-lock.json`, and `node_modules/` are **not versioned** (they are listed in `.gitignore`). A fresh clone will not contain them, and they are not required at runtime.

## Agents (`agents/`)

The default agent is **`resolver`** (lightweight fallback). The **`spec_driven`** agent is available as the orchestrator and delegates to subagents (it never implements code itself); select it explicitly or via a profile's `default_agent`.

### Primary

| Agent         | Role                                                                                                                                                                                           |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `resolver`    | Default agent. Fast, lightweight assistant for quick questions and context clarifications. Read-only, no subagent delegation.                                                                  |
| `spec_driven` | Orchestrator. Analyzes, plans, delegates, reviews results, and makes the final integration decision. Read-only plus read-only git/openspec commands.                                           |
| `unattended`  | Engineer for autonomous runs inside an isolated container. Broad write permissions, but blocks reading/editing secrets (`.env`, `.pem`, `.key`, `.ssh`, `.kube`, etc.) and dangerous commands. |

### Subagents

| Agent               | Role                                                                                                      |
| ------------------- | --------------------------------------------------------------------------------------------------------- |
| `researcher`        | External research (docs, APIs, libraries, best practices). Read-only.                                     |
| `spec_author`       | Authors OpenSpec artifacts (proposal → specs → design → tasks). Only writes `openspec/**`, `specs/**`.    |
| `developer`         | Repository reconnaissance and production code implementation (mode `all`: usable as primary or subagent). |
| `tester`            | Runs tests and validation; reports failures, regressions, and coverage gaps.                              |
| `reviewer`          | General code review plus deep Go/Python audit (concurrency, memory, async, idiomatic errors). Read-only.  |
| `security_reviewer` | Security review (authn/authz, secrets, injection, dependencies, insecure defaults). Read-only.            |

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
| `/jira`       | Creates, gets, updates, lists, or searches Jira issues and manages their comments via the `jira` MCP server (`mcps/jira/`).                               |

## Skills (`skills/`)

| Skill                   | Description                                                                                                                                                          |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `conventional-commits`  | Analyzes the `git diff` and generates commit messages following Conventional Commits (`feat`, `fix`, `refactor`, `docs`, `perf`, `chore`, `!` for breaking changes). |
| `jira-issue-management` | Creates, updates, searches, lists, or comments on Jira issues during a session (requires the `jira` MCP server running, `JIRA_TOKEN` and `JIRA_BASE_URL`).           |
| `network-proxy`         | Rules for running `curl`/`wget` behind a proxy; reads the proxy only from `HTTP_PROXY` and forbids proxy use if it isn't defined.                                    |

## OpenCode Configuration (`opencode.jsonc`)

- Uses the native OpenCode V2 schema: `agents` and an ordered `permissions` array.
- `default_agent: resolver` (base fallback; profiles can override it).
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

Image based on `ubuntu:26.04` with the tooling required for the workflow:

- **Go** 1.27.1
- **Node.js** 20
- **Python** 3.15 (standalone, installed via `uv` 0.13.10)
- **OpenTofu** 1.13.0
- **OpenCode** 2.4.1
- **OpenSpec** 2.2.0
- CLI utilities: `git`, `ripgrep`, `fd-find`, `jq`, `yq` (4.54.3), `curl`, `less`, `vim-tiny`, `tree`, `unzip`, `zip`, `kubectl` (1.37.2), `helm` (4.3.1), `make`, `glab` (GitLab CLI).

Tool and runtime versions (along with `DEVBOX_VERSION` for the image tag `opencode-devbox:${DEVBOX_VERSION}`) are defined in `VERSION` and exported by the `Makefile` into `docker-compose.yaml` (`build.args`). The `Dockerfile` ARGs intentionally have no defaults, so every build must go through Compose / `make` (or pass the args explicitly).

`docker-compose.yaml` mounts:

- the working repo at `/workspace/${PROJECT_NAME}` (`PROJECT_NAME` is required; the stack fails fast if unset),
- `agents/`, `commands/`, `skills/`, `scripts/`, `opencode.jsonc`, `AGENTS.md`, and `profiles/` read-only into `/home/agent/.config/opencode/`,
- persistent volumes for `/home/agent` (tooling, OpenCode data/state) and `/workspace` (so git worktrees can be created as siblings of the repo).

The container runs `opencode serve` on port `4096`, reachable through the Traefik gateway, with hardening: non-root `agent` user (UID/GID `1000`), `read_only` root filesystem (with writable volumes for home and workspace plus a `/tmp` tmpfs), `cap_drop: ALL`, `no-new-privileges`, `pids_limit`, and fixed `mem_limit: 8g` / `cpus: 4.0`.

> **Security note:** `OPENCODE_SERVER_PASSWORD` is passed as a container environment variable and is therefore visible via `docker inspect`. OpenCode V2 uses the fixed username `opencode`; `OPENCODE_SERVER_USERNAME` is not read. Keep `.env` out of version control.

> **Using in a target repository:** copy `examples/docker-compose-devbox.yaml` into the target repository as `docker-compose-devbox.yaml`. It uses Compose `include:` to inherit `${HOME}/.config/opencode/docker-compose.yaml` (with `project_directory: .`) and overrides only project-specific settings (`working_dir`, `image`, `OPENCODE_PROFILE`, extra volumes/ports/env). When using `make` with a renamed file, pass `COMPOSE_FILE=docker-compose-devbox.yaml`.

> **Build context:** `docker-compose.yaml` builds from `.` (this repository), so build the image here with `make build` (or `make build-multiarch`) before starting a target repository's `docker-compose-devbox.yaml`.

### Usage

From this repository (gateway + image build):

```bash
cp .env.example .env      # fill in the variables
# Start the gateway once (creates the external traefik-net network)
make gateway-up
# Build the devbox image tagged with VERSION
make build
```

In a target repository (using `examples/docker-compose-devbox.yaml` copied as `docker-compose-devbox.yaml`):

```bash
PROJECT_NAME=$(basename "$PWD") docker compose -f docker-compose-devbox.yaml up -d
# Server available at http://${PROJECT_NAME}.docker.localhost
```

Or directly from this repository:

```bash
set -a && . ./VERSION && set +a
PROJECT_NAME=$(basename "$PWD") docker compose -f docker-compose.yaml up -d
```

### Makefile

Shortcuts for the commands above (defaults `PROJECT_NAME` to the current directory name and reads package versions and `DEVBOX_VERSION` from `VERSION`; override with `make <target> PROJECT_NAME=foo`):

| Target                 | Description                                                                                                                                 |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `make help`            | Lists all available targets.                                                                                                                |
| `make gateway-up`      | Starts the Traefik gateway (creates the external `traefik-net` network).                                                                    |
| `make gateway-down`    | Stops the Traefik gateway.                                                                                                                  |
| `make build`           | Rebuilds the devbox image for the host's native architecture (amd64/arm64), tagged with `VERSION`.                                          |
| `make build-multiarch` | Builds `amd64`+`arm64` from the Compose config with `buildx`; requires the Docker buildx plugin and `PUSH=1` to push a multi-arch manifest. |
| `make sbx-build`       | Builds the devbox image (`make build`) and loads it into Docker Sandboxes via `sbx template load`.                                          |
| `make sbx-plan`        | Shows the Docker Sandboxes environment plan.                                                                                                |
| `make sbx-run`         | Creates or attaches the Docker Sandboxes devbox (uses the current directory as workspace).                                                  |
| `make sbx-stop`        | Stops the Docker Sandboxes devbox.                                                                                                          |
| `make sbx-rm`          | Removes the Docker Sandboxes devbox and its state.                                                                                          |
| `make sbx-ports`       | Shows published ports of the Docker Sandboxes devbox.                                                                                       |
| `make sbx-shell`       | Opens a shell inside the Docker Sandboxes devbox.                                                                                           |

```bash
make help
make build-multiarch            # build amd64+arm64 (cache only)
make build-multiarch PUSH=1     # build and push the multi-arch manifest
```

### Environment Variables (`.env`)

| Variable                   | Description                                                                                      |
| -------------------------- | ------------------------------------------------------------------------------------------------ |
| `PROJECT_NAME`             | Name used for the container and mount target (`/workspace/<PROJECT_NAME>`).                      |
| `OPENCODE_PROFILE`         | Config profile to load: `work` or `personal` (default: `personal`).                              |
| `OPENCODE_SERVER_PASSWORD` | Password to authenticate with the server (username is fixed to `opencode` in V2).                |
| `DEVBOX_VERSION`           | Image tag for `docker-compose.yaml` (set automatically from `VERSION` by `make`, or explicitly). |

## Docker Sandboxes Devbox

An alternative to Compose, using [`sbx`](https://docs.docker.com/ai/sandboxes/) (Docker Sandboxes). Instead of a container it runs a microVM sandbox with its own Docker daemon, and it publishes the OpenCode server on a host loopback port rather than through Traefik.

- `sbxenv.yaml` defines the environment: `projectName`, `workspace`, `configDir`, `devboxVersion` (from `VERSION`), `profile` (`personal`/`work`), `serverPassword`, port `4096`, and `2` CPUs / `4g` memory (`sandboxOptions`).
- `sbx/opencode-devbox/opencode-devbox.yaml` is a v3 sandbox kit (`schemaVersion: "3"`, `kind: workload`) that builds on top of the local `opencode-devbox:${DEVBOX_VERSION}` image (`FROM opencode-devbox:${DEVBOX_VERSION}`), reusing the exact same pre-baked toolchain as the Compose devbox, and runs `opencode serve` on `0.0.0.0:4096`.
- Run `make sbx-build` on first setup (and after `VERSION`/image updates) to build `opencode-devbox:<VERSION>` and load it into Docker Sandboxes via `sbx template load`.
- The config directory (`$HOME/.config/opencode` by default) is mounted read-only via `additionalWorkspaces` and symlinked into `/home/agent/.config/opencode` by the kit's `lifecycle@1` `install` hook, so the same `opencode.jsonc`, agents, commands, skills, and profiles are used. Changes to the config require recreating the sandbox.
- Provider credentials (`com.docker.sandbox/credential@1`) are injected by the sandbox proxy. Store them on the host with `sbx secret set anthropic` or `sbx secret set openai`; every credential in the kit is optional, so the sandbox starts even without them.
- For target repositories, copy `examples/sbxenv-devbox.yaml` as `sbxenv.yaml` (unlike Compose, `sbxenv.yaml` has no `include:` keyword, so it points directly to the v3 kit at `${{ env.args.configDir }}/sbx/opencode-devbox` and inherits image, toolchain, default env, credentials, network policy, and CPU/RAM resources).

Prerequisites: `sbx` installed and signed in (`sbx login`). On Linux, local sandboxes also need KVM and membership in the `kvm` group; see the [installation guide](https://docs.docker.com/ai/sandboxes/install/).

```bash
make sbx-build                       # build devbox image and load into sbx
make sbx-plan                        # review the environment plan
make sbx-run                         # create/attach with $PWD as workspace
make sbx-shell                       # shell inside the sandbox
make sbx-ports                       # show the published port
make sbx-stop                        # stop it
make sbx-rm                          # remove sandbox and its state
```

The server is available at `http://localhost:4096` (username `opencode`). Keep `make sbx-run` attached: the sandbox stops after its last session disconnects. Override defaults with `SBX_CONFIG_DIR`, `SBX_PROFILE`, `SBX_SERVER_PASSWORD`, `SBX_ENV_FILE`, or `SBX=...`.

> **Differences from Compose:** no Traefik gateway or `traefik-net` (publish is loopback-only; use `sbx ports`), no named volumes (the sandbox persists until `sbx rm`, the workspace is a direct host mount), default resources are `2` CPUs / `4g` memory (vs. `4` CPUs / `8g` in Compose), and no container-level `read_only`/`cap_drop` hardening (isolation is the microVM boundary). Network egress is open (`**`) to match the Compose setup; narrow it in `sbx/opencode-devbox/opencode-devbox.yaml` if needed.
