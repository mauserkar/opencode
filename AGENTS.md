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
