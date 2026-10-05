# OpenCode

Personal [OpenCode](https://opencode.ai) configuration plus a reproducible Docker development environment (devbox). It defines an agent-orchestrated engineering workflow: specify → implement → test → review → merge.

## Structure

```
.
├── agents/              # Agent definitions (primary and subagents)
├── command/             # Custom slash commands
├── skills/              # Reusable skills
├── opencode.jsonc       # OpenCode configuration (base)
├── profiles/            # Work/personal/unattended config profiles (one opencode.jsonc each)
├── Dockerfile           # Devbox image
├── docker-compose.yaml  # Container orchestration
├── .env.example         # Environment variable template
└── package.json         # (gitignored) local deps for plugin development
```

> **Note:** `package.json`, `package-lock.json`, and `node_modules/` are **not versioned** (they are listed in `.gitignore`). A fresh clone will not contain them, and they are not required at runtime: OpenCode automatically installs the `opencode-plugin-openspec` plugin declared in `opencode.jsonc` into `~/.cache/opencode/`.

## Agents (`agents/`)

The default agent is **`resolver`** (lightweight fallback). Select a profile to use **`spec_driven`**, which orchestrates the work and delegates to subagents (it never implements code itself).

### Primary

| Agent         | Role                                                                                                                                                                                           |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `spec_driven` | Orchestrator. Analyzes, plans, delegates, reviews results, and makes the final integration decision. Read-only plus read-only git/openspec commands.                                           |
| `unattended`  | Engineer for autonomous runs inside an isolated container. Broad write permissions, but blocks reading/editing secrets (`.env`, `.pem`, `.key`, `.ssh`, `.kube`, etc.) and dangerous commands. |

### Subagents

| Agent               | Role                                                                                                                              |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `researcher`        | External research (docs, APIs, libraries, best practices). Read-only.                                                             |
| `spec_author`       | Authors OpenSpec artifacts (proposal → specs → design → tasks). Only writes `openspec/**`, `specs/**`, `project.md`, `AGENTS.md`. |
| `developer`         | Repository reconnaissance and production code implementation. Writes only inside its assigned worktree/scope.                     |
| `tester`            | Runs tests and validation; reports failures, regressions, and coverage gaps.                                                      |
| `reviewer`          | General code review plus deep Go/Python audit (concurrency, memory, async, idiomatic errors). Read-only.                          |
| `security_reviewer` | Security review (authn/authz, secrets, injection, dependencies, insecure defaults). Read-only.                                    |
| `resolver`          | Quick questions and context clarifications. Lightweight and read-only.                                                            |

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

## Commands (`command/`)

| Command       | Description                                                                                                                                               |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/changelog`  | Updates `CHANGELOG.md` (Keep a Changelog format), computes the SemVer bump, updates the manifest, and creates the release commit.                         |
| `/format`     | Formats Python (`ruff`/`black`/`isort`), Terraform (`terraform fmt`), or Go (`gofmt`/`goimports`) code and shows `git diff --stat`.                       |
| `/versioning` | Audits and implements version support (`--version`, `/version` endpoint, `__version__`, …) based on project type, integrating with OpenSpec when present. |
| `/jira`       | Creates, gets, updates, lists, or searches Jira issues and manages their comments via `scripts/jira.py`.                                        |

## Skills (`skills/`)

| Skill                   | Description                                                                                                                                                          |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `conventional-commits`  | Analyzes the `git diff` and generates commit messages following Conventional Commits (`feat`, `fix`, `refactor`, `docs`, `perf`, `chore`, `!` for breaking changes). |
| `jira-issue-management` | Creates, updates, searches, lists, or comments on Jira issues during a session (requires `scripts/jira.py`, `JIRA_TOKEN` and `JIRA_BASE_URL`).             |

## OpenCode Configuration (`opencode.jsonc`)

- `default_agent: resolver` (base fallback; profiles override to `spec_driven` when needed).
- `build` and `plan` agents disabled.
- Server listening on `0.0.0.0:4096`.
- Plugin: `opencode-plugin-openspec`.
- `compaction`, `tool_output` limits and `subagent_depth` are configured in `profiles/*/opencode.jsonc`.

## Profiles (`profiles/`)

Separate **work**, **personal**, and **unattended** configurations, each an `opencode.jsonc` that is **merged on top of** the base config (so it only needs the overrides, e.g. `model`/`small_model`):

```
profiles/
├── work/opencode.example.jsonc   # copy to opencode.jsonc (gitignored)
├── personal/opencode.jsonc
└── unattended/opencode.jsonc
```

Select one with the `OPENCODE_CONFIG` environment variable:

```bash
export OPENCODE_CONFIG=~/.config/opencode/profiles/work/opencode.jsonc
```

In the Docker devbox, set `OPENCODE_PROFILE` (`work`, `personal`, or `unattended`) in `.env`; the compose file wires it to `OPENCODE_CONFIG` automatically.

## Docker Devbox

Image based on `ubuntu:24.04` with the tooling required for the workflow:

- **Go** 1.27.1
- **Node.js** 20
- **Python** 3.14 (standalone, installed via `uv`)
- **OpenTofu** 1.13.0
- **OpenCode** 1.18.34 and **OpenSpec** 1.13.0
- CLI utilities: `git`, `ripgrep`, `fd-find`, `jq`, `yq`, `curl`, `vim`, `tree`, etc.

`docker-compose.yaml` mounts:

- the working repo at `/workspace/${PROJECT_NAME}` (`PROJECT_NAME` is required; the stack fails fast if unset),
- `agents/`, `command/`, `skills/`, `opencode.jsonc`, and `profiles/` as configuration,
- persistent volumes for the home directory (plugin cache, tooling, OpenCode data/state) and the workspace (so git worktrees can be created as siblings of the repo).

The container runs `opencode serve` on port `4096`, reachable through the Traefik gateway, with hardening: non-root `ubuntu` user, `read_only` root filesystem (with writable volumes for home and workspace plus a `/tmp` tmpfs), `cap_drop: ALL`, `no-new-privileges`, `pids_limit`, and configurable `mem_limit`/`cpus`.

> **Security note:** `OPENCODE_SERVER_USERNAME`/`OPENCODE_SERVER_PASSWORD` are passed as container environment variables and are therefore visible via `docker inspect`. Keep `.env` out of version control.

### Usage

```bash
cp .env.example .env      # fill in the variables
# Start the gateway once (creates the external traefik-net network)
docker compose -f docker-compose-gateway.yaml up -d
docker compose up -d --build
# Server available at http://${PROJECT_NAME}.docker.localhost
```

### Environment Variables (`.env`)

| Variable                   | Description                                                         |
| -------------------------- | ------------------------------------------------------------------- |
| `PROJECT_NAME`                | Name of the repo to mount (`$HOME/repos/<PROJECT_NAME>`).              |
| `OPENCODE_PROFILE`         | Config profile to load: `work`, `personal`, or `unattended` (default: `personal`). |
| `OPENCODE_SERVER_USERNAME` | Username to authenticate with the server.                           |
| `OPENCODE_SERVER_PASSWORD` | Password to authenticate with the server.                           |
| `OPENCODE_MEM_LIMIT`       | Optional container memory limit (default: `8g`).                    |
| `OPENCODE_CPUS`            | Optional CPU limit (default: `4.0`).                                |
