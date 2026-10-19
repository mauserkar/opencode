# AGENTS.md (global)

Personal preferences that apply across every OpenCode project on this
machine, regardless of profile (`work` / `personal`) or repository. Loaded
automatically by OpenCode from `$XDG_CONFIG_HOME/opencode/AGENTS.md`
(normally `~/.config/opencode/AGENTS.md`) in every session, before any
project-level `AGENTS.md`.

Do not duplicate repository-specific conventions here (build commands,
architecture, OpenSpec/Jira workflow, etc.) — those belong in the project's
own root `AGENTS.md`, which is versioned with the repo.

## Language

- All files created or modified in any repository (code, comments,
  docstrings, documentation, commit messages, branch names, OpenSpec
  artifacts) MUST be written in English, regardless of the language used in
  the conversation with the user.
- Conversational replies to the user follow the user's own language; only
  the artifacts written to disk are English-only.

## Communication style

- Keep responses short and to the point; avoid restating the request back
  before answering it.
- When a task is ambiguous but low-risk, state the assumption in one line
  and proceed rather than asking first.
- When something is uncertain, missing, or genuinely ambiguous and
  high-risk (e.g. a required field, an org-specific value), ask instead of
  guessing.

## Reporting results

- After running a command, report the actual output/exit status, not a
  paraphrase of what was expected to happen.
- If a script or tool returns a structured error, relay it verbatim rather
  than rewording or silently retrying.

## Git Worktrees

- Determine the repository root with `git rev-parse --show-toplevel` and compare it against `/workspace`.
- Worktree location (check in this order):
  1. If the `/workspace` directory exists AND the repository root is NOT `/workspace` itself (e.g. the repo is `/workspace/<repo-name>`), ALWAYS create the worktree there: `/workspace/<repo-name>-<branch>`.
  2. Otherwise (no `/workspace` directory, or the repository root IS `/workspace`), create it in `/tmp/`: `/tmp/<repo-name>-<branch>`.
- Never create a worktree inside the repository's own directory tree.

## Security

Security guidance for all agents. This is a reinforcement layer, not the
enforcement mechanism: the actual technical boundaries live in each agent's
`permission` block (`opencode.jsonc` / `profiles/*/opencode.jsonc`) and in
`docker-compose.yaml`/`Dockerfile`. Nothing here overrides those — if this
file and a `permission` block ever disagree, the `permission` block wins.

### Secrets

- Never read, print, log, quote, or reconstruct the contents of `.env`,
  `.env.*` (including `.env.example`), `*.pem`, `*.key`, `*.p12`, `*.pfx`,
  or anything matching `*credential*` / `*secret*`, even indirectly (e.g.
  via `cat`, `grep`, `sed`, `head`/`tail`, a heredoc, or a script that
  shells out to print them). This applies during debugging too — report
  that a variable is missing or looks wrong instead of dumping the file to
  inspect it.
- Never run `env`, `printenv`, or `export` to enumerate the current
  environment "just to check" a value — ask the user to confirm what's set
  instead.
- Never write a real secret value into a tracked file. `.env.example` and
  similar template files must only ever contain placeholders.
- If a required credential is missing (`JIRA_TOKEN`, `JIRA_BASE_URL`,
  `JIRA_EPIC_FIELD`, cloud credentials, etc.), surface the error message
  as-is and ask the user to set it. Never invent, guess, or silently fall
  back to a hardcoded org-specific value.
- Treat `**/.ssh/**`, `**/.kube/**`, `**/.gcloud/**`, `**/.gnupg/**`, and
  `**/.docker/config.json` the same way as secrets: read-only-denied
  material, not something to work around by reading a parent directory or
  a symlink target instead.

### Git & remote actions

- Never `git push` (including `--force`) unless the user explicitly asks
  for it in that specific turn. A prior push is not blanket authorization
  for future ones.
- Never rewrite history on a shared branch (`rebase`, `reset --hard`,
  force-push) without the user asking for it explicitly.
- Never run destructive filesystem commands scoped broadly (`rm -rf /`,
  `rm -rf ~`, `rm -rf .`, `find / -delete`, `chmod -R 777 /`).

### Container & infrastructure

- Do not suggest or attempt to weaken the container's security posture as
  a workaround for a blocked action: this includes proposing
  `read_only: false`, dropping `cap_drop: ALL`, removing
  `no-new-privileges:true`, or requesting access to the Docker socket.
  If a task genuinely needs one of these, say so explicitly to the user
  and let them decide — don't silently edit `docker-compose.yaml` to
  relax it.
- Never target the cloud metadata endpoint (`169.254.169.254`) or attempt
  to reach it through a proxy, redirect, or SSRF-style request.
- Do not attempt SSH (`ssh *`, `scp *`) or Docker-in-Docker (`docker *`)
  from inside the unattended container — it has no host credentials or
  socket access, and trying to route around that is a signal to stop and
  ask, not to find another path.

### Code-level security review

When writing or reviewing code (see `agents/security_reviewer.md` for the
dedicated review checklist), always flag rather than silently work around:

- hardcoded secrets, tokens, or credentials in source, config, or tests
- string-built SQL/shell/JQL queries instead of parameterized or escaped
  ones (see `_escape_jql` in `mcps/jira/jira.py` for the pattern to follow)
- unsafe deserialization (`pickle`, `eval`, `exec` on untrusted input)
- missing input validation on anything crossing a trust boundary (API
  payloads, CLI args, file contents from outside the repo)
- overly broad permissions/scopes requested "to be safe" — request the
  minimum needed for the task
- logging of sensitive data (tokens, full request/response bodies that may
  contain secrets, PII)

### When in doubt

If an action would touch a secret, a credential, a shared branch, or the
container's security configuration, and it isn't unambiguously covered by
an explicit `allow` in the relevant agent's `permission` block: stop and
ask the user rather than finding an alternate command that achieves the
same effect.
