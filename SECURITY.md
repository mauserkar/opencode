# security.md

Security guidance for all agents in this repository. This is a
reinforcement layer, not the enforcement mechanism: the actual technical
boundaries live in each agent's `permission` block (`agents/*.md`) and in
`docker-compose.yaml`/`Dockerfile`. Nothing here overrides those — if this
file and a `permission` block ever disagree, the `permission` block wins.

## Secrets

- Never read, print, log, quote, or reconstruct the contents of `.env`,
  `.env.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, or anything matching
  `*credential*` / `*secret*`, even indirectly (e.g. via `cat`, `grep`,
  `sed`, `head`/`tail`, a heredoc, or a script that shells out to print
  them). This applies during debugging too — report that a variable is
  missing or looks wrong instead of dumping the file to inspect it.
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

## Git & remote actions

- Never `git push` (including `--force`) unless the user explicitly asks
  for it in that specific turn. A prior push is not blanket authorization
  for future ones.
- Never rewrite history on a shared branch (`rebase`, `reset --hard`,
  force-push) without the user asking for it explicitly.
- Never run destructive filesystem commands scoped broadly (`rm -rf /`,
  `rm -rf ~`, `rm -rf .`, `find / -delete`, `chmod -R 777 /`).

## Container & infrastructure

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

## Code-level security review

When writing or reviewing code (see `agents/security_reviewer.md` for the
dedicated review checklist), always flag rather than silently work around:

- hardcoded secrets, tokens, or credentials in source, config, or tests
- string-built SQL/shell/JQL queries instead of parameterized or escaped
  ones (see `_escape_jql` in `scripts/jira.py` for the pattern to follow)
- unsafe deserialization (`pickle`, `eval`, `exec` on untrusted input)
- missing input validation on anything crossing a trust boundary (API
  payloads, CLI args, file contents from outside the repo)
- overly broad permissions/scopes requested "to be safe" — request the
  minimum needed for the task
- logging of sensitive data (tokens, full request/response bodies that may
  contain secrets, PII)

## When in doubt

If an action would touch a secret, a credential, a shared branch, or the
container's security configuration, and it isn't unambiguously covered by
an explicit `allow` in the relevant agent's `permission` block: stop and
ask the user rather than finding an alternate command that achieves the
same effect.
