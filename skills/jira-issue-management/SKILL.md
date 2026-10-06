---
name: jira-issue-management
description: Create, look up, update, search, list, or comment on Jira issues. Use whenever the user mentions a Jira issue, ticket, epic, or issue key (e.g. PROJ-123), or asks to create, update, find, list, check the status of, or comment on an issue, even if they don't say "Jira".
compatibility: Requires Python 3 (stdlib only), a resolvable jira.py, and JIRA_TOKEN and JIRA_BASE_URL exported in the environment. The `jira` command (.opencode/commands/jira.md) documents the exact flags.
metadata:
  version: "1.1"
---

# Skill: jira-issue-management

Manage Jira issues and comments with the resolved `jira.py`. An agent runs it
directly through the `bash` tool; the `jira` command
(`.opencode/commands/jira.md`) is the manual `/jira` entry point. Either way,
that command file is the source of truth for exact flags and per-action
fields — read it before running anything.

This skill says **when** to act and **which action** to pick.

## Prerequisites

### Environment variables

Load them from `.env` (copy `.env.example`, which is tracked; `.env` is
gitignored) or export them in the shell. Never put real values in
`.env.example`.

| Variable              | Required                                     | Default  | Purpose                                                     |
| --------------------- | -------------------------------------------- | -------- | ----------------------------------------------------------- |
| `JIRA_TOKEN`          | Yes                                          | none     | Authentication                                              |
| `JIRA_BASE_URL`       | Yes                                          | none     | Instance URL, e.g. `https://your-company.atlassian.net`     |
| `JIRA_PROJECT_ID`     | For create/search/list (or pass `--project`) | none     | Default project key                                         |
| `JIRA_ISSUE_TYPE`     | No                                           | `Task`   | Default issue type                                          |
| `JIRA_ISSUE_LABELS`   | No                                           | none     | Default labels, comma-separated                             |
| `JIRA_ISSUE_PRIORITY` | No                                           | `Medium` | Default priority                                            |
| `JIRA_ISSUE_EPIC`     | No                                           | none     | Default epic key for create/update                          |
| `JIRA_EPIC_FIELD`     | Only if an epic is used                      | none     | Custom field id for the epic link, e.g. `customfield_10014` |
| `JIRA_TIMEOUT`        | No                                           | `10`     | HTTP timeout in seconds                                     |
| `JIRA_MAX_RESULTS`    | No                                           | `50`     | Page size for search/list (override with `--max-results`)   |

Check that secrets are set **without printing them**:

```bash
[ -n "$JIRA_TOKEN" ] && [ -n "$JIRA_BASE_URL" ] && echo "ok" || echo "missing JIRA_TOKEN or JIRA_BASE_URL"
```

### Script resolution

Resolve `jira.py` once, in this order (repository-local wins):

1. `.opencode/scripts/jira.py`
2. `$HOME/.config/opencode/scripts/jira.py`

If neither exists, report that `jira.py` was not found and list both
locations checked.

## Actions

| Action                                                               | Purpose                         | Required input                                                                                                       |
| -------------------------------------------------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `create`                                                             | Open a new issue                | `summary`, `description`                                                                                             |
| `get`                                                                | Look up one issue               | `issue-key`                                                                                                          |
| `update`                                                             | Change fields on an issue       | `issue-key` plus only the fields being changed (`summary`, `description`, `issuetype`, `labels`, `priority`, `epic`) |
| `search`                                                             | Find issues by text and/or epic | at least one of `summary`, `epic`                                                                                    |
| `list`                                                               | List issues in the project      | none; optional exact-match `status`                                                                                  |
| `comment-add` / `comment-list` / `comment-update` / `comment-delete` | Manage comments on an issue     | `issue-key`, plus `body` (add/update) or `comment-id` (update/delete)                                                |
| `help`                                                               | Summarize what is available     | none; answer directly, run nothing                                                                                   |

`project` is also required for `create`, `search`, and `list` when
`JIRA_PROJECT_ID` is not set.

## Procedure

1. Verify the environment and resolve `jira.py` (see Prerequisites).
2. Identify the action from the request. If it is genuinely ambiguous
   (`search` vs `list`, `get` vs `comment-list`), ask the user.
3. If a required input is missing, ask for it. Never guess a `summary`,
   `description`, `issue-key`, `project`, comment `body`, or `comment-id`.
   A missing `status` on `list` means "unfiltered", not "ask".
4. Run the resolved `jira.py` (see Script resolution) with the `bash` tool,
   using only the flags the user provided or that were clearly extracted.
   Never invent values for fields the user did not mention; on `update`,
   touch only the fields explicitly mentioned.
5. Report the result (see Output).

## Rules

- **`comment-delete` is destructive:** show the target issue and comment,
  and require explicit user confirmation before running it.
- Never print, log, or echo `JIRA_TOKEN`, and never include it in
  commands shown to the user.
- On `{"success": false, "error": "..."}`, report the message verbatim and
  do not retry silently. This includes the "set `JIRA_EPIC_FIELD`" error:
  relay it as-is.

## Output

- `create` / `update`: the issue URL.
- `get`: the issue details (summary, description, status, labels).
- `search` / `list`: the matching issues, or "no issues found". If
  `truncated` is `true`, say so and suggest a narrower filter.
- Comment actions: the comment result.