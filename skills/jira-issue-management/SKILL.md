---
name: jira-issue-management
description: Create, look up, update, search for, list, or comment on Jira issues during a session. Use when the user asks to create, update, search for, list, comment on, or check the status of a Jira issue.
compatibility: Requires jira.py (Python 3, stdlib only) available either in the repository's .opencode/scripts/ directory or the global OpenCode scripts directory ($HOME/.config/opencode/scripts/), plus JIRA_TOKEN and JIRA_BASE_URL exported in the environment.
---

# Skill: jira-issue-management

Manage Jira issues and their comments in your project by delegating to the
single `jira` opencode command, which wraps the resolved `jira.py`
implementation.

The Jira script may be provided at repository or global OpenCode scope.
Repository-local configuration takes precedence over the global configuration.

This skill is procedural — it says when to use the command and which action to
pick, not how the script talks to Jira.

Before running anything, ensure `JIRA_TOKEN` and `JIRA_BASE_URL` are set: both
are required, with no built-in default. Copy `.env.example` to `.env`
(gitignored) and set your variables there, or export them directly in your
shell — never add a real value to the tracked `.env.example`.

## Environment Variables (.env Verification)

If a `.env` file exists, verify that the following variables are available or
properly defaulted in the environment:

- `JIRA_TOKEN`: Required for authentication. No default.
- `JIRA_BASE_URL`: Required — the Jira instance base URL (e.g.
  `https://your-company.atlassian.net`). No default; the script refuses to
  guess an org-specific URL.
- `JIRA_PROJECT_ID`: Default Jira project key. No default — required (via
  `.env` or `--project`) for `create`, `search`, and `list`.
- `JIRA_ISSUE_TYPE`: Default issue type. Defaults to `Task`.
- `JIRA_ISSUE_LABELS`: Default comma-separated labels. Defaults to none.
- `JIRA_ISSUE_PRIORITY`: Default priority. Defaults to `Medium`.
- `JIRA_ISSUE_EPIC`: Default epic key to link on `create`/`update`. No
  default.
- `JIRA_EPIC_FIELD`: Jira custom field id used for the epic link (e.g.
  `customfield_10014`). No default — required only if `--epic` /
  `JIRA_ISSUE_EPIC` is actually used; if needed but unset, the script fails
  with `{"success": false, "error": "..."}` explaining what to set. Relay
  that error as-is rather than treating it as unexpected.
- `JIRA_TIMEOUT`: HTTP request timeout in seconds. Defaults to `10`.
- `JIRA_MAX_RESULTS`: Default page size for `search`/`list`. Defaults to
  `50`; can be overridden per-call with `--max-results`.

## When to invoke this skill

- Creating a new Jira issue for work about to start or already agreed on.
- Looking up an existing issue's summary, description, status, or labels.
- Updating an existing issue's fields as work progresses.
- Finding an issue by summary text or by the epic it belongs to, when its
  key isn't already known.
- Listing issues in the project, with or without a status filter.
- Adding, listing, updating, or deleting a comment on an issue — e.g.
  recording progress, a decision, or a link back to a merge request.

## Script Resolution

The Jira implementation may exist at either repository or global OpenCode
scope.

Resolve `jira.py` in this order:

1. Repository-local:
   `.opencode/scripts/jira.py`

2. Global OpenCode:
   `$HOME/.config/opencode/scripts/jira.py`

If both exist, the repository-local implementation takes precedence.

If neither exists, report that `jira.py` could not be found and include the
locations that were checked.

## How dispatch works

There is a single `jira` opencode command that wraps the resolved script — it takes the raw
request as `$ARGUMENTS`, figures out which action is intended (`create`,
`get`, `update`, `list`, `search`, `comment-add`, `comment-list`,
`comment-update`, `comment-delete`, or `help`), gathers only the fields that
action needs, and runs:

```
<python> <resolved-jira-script> <action> [flags...]
```
The `jira` command is responsible for resolving the script location according
to the Script Resolution rules.

The command's own file is the source of truth for exact flag names, which
fields are required per action, and how results are reported — read it
before running anything. It documents each action in one place rather than
one file per action.

## Which action to use

| Action | Purpose | Required input |
| --- | --- | --- |
| `create` | Open a new issue | `summary`, `description` (plus `project` only if `JIRA_PROJECT_ID` isn't set) |
| `get` | Look up one issue | `issue-key` (e.g. `PROJECT-123`) |
| `update` | Change fields on an existing issue | `issue-key`, plus only the fields being changed (`summary`, `description`, `issuetype`, `labels`, `priority`, `epic`) — only fields explicitly mentioned are touched |
| `search` | Find issues by summary text and/or epic | at least one of `summary`, `epic`, plus `project` only if `JIRA_PROJECT_ID` isn't set |
| `list` | List issues in the project | none required; optional exact-match `status`, plus `project` only if `JIRA_PROJECT_ID` isn't set |
| `comment-add` / `comment-list` / `comment-update` / `comment-delete` | Manage comments on an issue | `issue-key`, plus `body` (add/update) or `comment-id` (update/delete) |
| `help` | Summarize what's available | none — answered directly, nothing is run |

## Procedure

1. Verify environment configuration: ensure `.env` is loaded or the
   environment variables above (`JIRA_TOKEN`, `JIRA_BASE_URL`,
   `JIRA_PROJECT_ID`, etc.) are accessible. Also ensure that a `jira.py`
   implementation can be resolved according to the Script Resolution rules.
2. Identify the action (`create`, `get`, `update`, `list`, `search`, one of
   the comment sub-actions, or `help`) from the request. If it's genuinely
   ambiguous (e.g. `search` vs `list`, or `get` vs `comment-list`), ask the
   user to clarify before proceeding.
3. If any required input for that action is missing, ask the user for it —
   do not guess a `summary`, `description`, `issue-key`, `project` (when
   `JIRA_PROJECT_ID` is unset), or comment `body`/`comment-id`. A missing
   `status` on `list` is not ambiguous: it means "list unfiltered," not "ask
   the user."
4. Run the `jira` command with the identified action and only the flags
   that were actually provided or extracted — never invent values for
   fields the user didn't mention.
5. Report the result to the user: the issue URL for `create`/`update`, the
   issue details for `get`, the matching issues (or "no issues found") for
   `search`/`list` (and mention if `truncated` is `true`, suggesting a
   narrower filter), or the comment result for comment actions. On
   `{"success": false, "error": "..."}`, report the error message verbatim
   rather than retrying silently.

## Defaults & Environment Fallbacks

If optional arguments are omitted, the script falls back dynamically to the
values defined in the environment:

- **Base URL**: `JIRA_BASE_URL` — required, no fallback; `create`/`get`/
  `update`/`search`/`list` all fail loudly if it's unset.
- **Project ID**: `DEFAULT_PROJECT` (`JIRA_PROJECT_ID`)
- **Issue Type**: `DEFAULT_ISSUETYPE` (defaults to `"Task"`)
- **Labels**: `DEFAULT_LABELS` (parsed from comma-separated
  `JIRA_ISSUE_LABELS`)
- **Priority**: `DEFAULT_PRIORITY` (defaults to `"Medium"`)
- **Epic**: `DEFAULT_EPIC` (`JIRA_ISSUE_EPIC`)
- **Epic Field**: `EPIC_FIELD` (`JIRA_EPIC_FIELD`) — only required if an
  epic is actually being set or searched on
- **Timeout**: `DEFAULT_TIMEOUT` (`JIRA_TIMEOUT`, defaults to `10` seconds)
- **Max results**: `DEFAULT_MAX_RESULTS` (`JIRA_MAX_RESULTS`, defaults to
  `50`; overridable per-call with `--max-results` on `search`/`list`)
