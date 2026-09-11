# opencode-devbox

Personal [OpenCode](https://opencode.ai) configuration plus a reproducible Docker development environment (devbox). It defines an agent-orchestrated engineering workflow: specify → implement → test → review → merge.

## Structure

```
.
├── agents/              # Agent definitions (primary and subagents)
├── command/             # Custom slash commands
├── skills/              # Reusable skills
├── opencode.jsonc       # OpenCode configuration
├── Dockerfile           # Devbox image
├── docker-compose.yaml  # Container orchestration
├── .env.example         # Environment variable template
└── package.json         # OpenCode plugin dependency
```

## Agents (`agents/`)

The default agent is **`architect`**, which orchestrates the work and delegates to subagents (it never implements code itself). `subagent_depth: 1` prevents a subagent from launching further subagents.

### Primary

| Agent | Role |
|-------|------|
| `architect` | Principal architect and orchestrator. Analyzes, plans, delegates, reviews results, and makes the final integration decision. Read-only plus read-only git/openspec commands. |
| `unattended` | Engineer for autonomous runs inside an isolated container. Broad write permissions, but blocks reading/editing secrets (`.env`, `.pem`, `.key`, `.ssh`, `.kube`, etc.) and dangerous commands. |

### Subagents

| Agent | Role |
|-------|------|
| `explorer` | Read-only repository reconnaissance: architecture, relevant files, dependencies, patterns, and impact. |
| `researcher` | External research (docs, APIs, libraries, best practices). Read-only. |
| `spec_author` | Authors OpenSpec artifacts (proposal → specs → design → tasks). Only writes `openspec/**`, `specs/**`, `project.md`, `AGENTS.md`. |
| `developer` | Production code implementation. Writes only inside its assigned worktree/scope. |
| `tester` | Runs tests and validation; reports failures, regressions, and coverage gaps. |
| `reviewer` | General code review (correctness, regressions, maintainability, tests). Read-only. |
| `security_reviewer` | Security review (authn/authz, secrets, injection, dependencies, insecure defaults). Read-only. |
| `bug_hunter` | Deep bug and concurrency audit for Go and Python. Read-only. |
| `resolver` | Quick questions and context clarifications. Lightweight and read-only. |

## Workflow (architect)

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
4. **Implement → Test → Review** — loop inside the worktree (`developer`, `tester`, `reviewer`, plus `security_reviewer`/`bug_hunter` as needed).
5. **Merge & Archive** — squash-merge into main and `openspec archive` the change.
6. **Final response** — summary of changes, artifacts, subagents, tests, and pending decisions.

## Commands (`command/`)

| Command | Description |
|---------|-------------|
| `/changelog` | Updates `CHANGELOG.md` (Keep a Changelog format), computes the SemVer bump, updates the manifest, and creates the release commit. |
| `/format` | Formats Python (`ruff`/`black`/`isort`), Terraform (`terraform fmt`), or Go (`gofmt`/`goimports`) code and shows `git diff --stat`. |
| `/versioning` | Audits and implements version support (`--version`, `/version` endpoint, `__version__`, …) based on project type, integrating with OpenSpec when present. |

## Skills (`skills/`)

| Skill | Description |
|-------|-------------|
| `conventional-commits` | Analyzes the `git diff` and generates commit messages following Conventional Commits (`feat`, `fix`, `refactor`, `docs`, `perf`, `chore`, `!` for breaking changes). |

## OpenCode Configuration (`opencode.jsonc`)

- `default_agent: architect`, `subagent_depth: 1`.
- `build` and `plan` agents disabled.
- Server listening on `0.0.0.0:4096`.
- Plugin: `opencode-plugin-openspec`.
- Automatic compaction with pruning (`reserved: 10000`).
- Tool output limits: 500 lines / 20000 bytes.

## Docker Devbox

Image based on `ubuntu:24.04` with the tooling required for the workflow:

- **Go** 1.27.1
- **Node.js** 20
- **Python** 3.14 (+ pip, venv)
- **OpenTofu** 1.12.6
- **OpenCode** 1.18.27 and **OpenSpec** 1.12.0
- CLI utilities: `git`, `ripgrep`, `fd-find`, `jq`, `yq`, `curl`, `vim`, `htop`, `tree`, etc.

`docker-compose.yaml` mounts:

- the working repo at `/workspace/${REPO_NAME}`,
- `agents/`, `command/`, `skills/`, and `opencode.jsonc` as configuration,
- persistent volumes for OpenCode data and state.

The container runs `opencode serve` on port `4096` (mapped to the host), with a healthcheck and `no-new-privileges`.

### Usage

```bash
cp .env.example .env      # fill in the variables
docker compose up -d --build
# Server available at http://localhost:${OPENCODE_HOST_PORT:-4096}
```

### Environment Variables (`.env`)

| Variable | Description |
|----------|-------------|
| `REPO_NAME` | Name of the repo to mount (`$HOME/repos/<REPO_NAME>`). |
| `OPENCODE_HOST_PORT` | Host port to expose the server on. |
| `OPENCODE_SERVER_USERNAME` | Username to authenticate with the server. |
| `OPENCODE_SERVER_PASSWORD` | Password to authenticate with the server. |
