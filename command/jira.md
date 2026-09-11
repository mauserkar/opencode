---
description: Create, get, update, list, or search Jira issues, or manage their comments, using .opencode/scripts/jira.py
---

Manage Jira issues and comments by running `.opencode/scripts/jira.py` with the `bash` tool. This script is fully self-contained: no imports from this project's `app/` package, and zero third-party dependencies (pure Python stdlib, no `pip install` needed). It needs the `JIRA_TOKEN` environment variable (required), loaded from the `.env` file in the project root.

The following are also configurable via `.env`, each with a default except `JIRA_PROJECT_ID`:

- `JIRA_PROJECT_ID`: Jira project id/key. No default — required (via `.env` or `--project`) for `create`, `search`, and `list`.
- `JIRA_ISSUE_TYPE`: issue type for `create`. Default `Task`.
- `JIRA_ISSUE_LABELS`: comma-separated labels for `create`. No default (no labels if omitted).
- `JIRA_ISSUE_PRIORITY`: priority for `create`. Default `Medium`.
- `JIRA_ISSUE_EPIC`: epic key to link on `create`/`update`. No default (no epic link if omitted).
- `JIRA_EPIC_FIELD`: Jira custom field id used for the epic link and for `search --epic`. No default — required only if `--epic`/`JIRA_ISSUE_EPIC` is used; if it's needed but not set, the script fails with `{"success": false, "error": "..."}` explaining that `JIRA_EPIC_FIELD` must be set (e.g. to `customfield_10014`, the standard "Epic Link" field id on Jira Server/Data Center). Relay that error as-is rather than treating it as unexpected.

Request: $ARGUMENTS

## Step 1 — Identify the action

From the request above, determine which action is intended:

| Action | Typical phrasing |
| --- | --- |
| `create` | "create/open/file a new issue/ticket/bug/task" |
| `get` | "show/get/look up issue KEY", "what's the status of KEY" |
| `update` | "update/change/edit issue KEY", "move KEY to project X", "relabel KEY" |
| `list` | "list issues in PROJECT", "what's in progress in PROJECT" |
| `search` | "find issues about X", "search for issues under epic Y" |
| `comment-add` | "comment on KEY", "add a note to KEY" |
| `comment-list` | "show comments on KEY" |
| `comment-update` | "edit/update comment on KEY" |
| `comment-delete` | "delete/remove comment on KEY" |
| `help` | "jira help", "what can you do with jira", "how does this work" |

If the action is genuinely ambiguous (e.g. it's unclear whether the user wants `search` vs `list`, or `get` vs `comment-list`), ask the user to clarify before proceeding. Otherwise, proceed directly to the matching branch below — do not ask just to confirm an action that's already clear from phrasing.

## Step 2 — Gather the fields for that action, then run it

### help

No fields to extract, and nothing to run — answer directly from this file. Reply to the user with a short summary of what's available:

- **create** — open a new issue (needs summary, description; project/issuetype/labels/priority/epic optional).
- **get** — fetch one issue by key.
- **update** — change fields on an existing issue (only the fields mentioned are touched).
- **list** — list every issue in a project, optionally filtered by exact status.
- **search** — find issues by summary text and/or epic key.
- **comment-add / comment-list / comment-update / comment-delete** — manage comments on an issue.

Mention that `project` only needs to be given if `JIRA_PROJECT_ID` isn't already set in `.env`, and that `epic` needs `JIRA_EPIC_FIELD` configured. If the user wants the full flag-by-flag detail for a specific action instead of this overview, run:

```
<python> .opencode/scripts/jira.py <action> --help
```

and relay argparse's own usage output.

Use `python3` (any Python 3 interpreter works, e.g. `.venv/bin/python3` or the system one). Always run from the project root, so `.env` is picked up. In every command below, include only the optional (`[...]`) flags for fields that were actually provided or extracted — never invent values for fields the user didn't mention.

### create

Extract: `summary` and `description` (required — ask if missing). If `JIRA_PROJECT_ID` is not set in `.env`, also extract `project` and ask if missing/ambiguous. Optionally extract `issuetype`, `labels`, `priority`, `epic` if mentioned; otherwise omit and let the script fall back to `.env`/defaults.

```
<python> .opencode/scripts/jira.py create [--project <PROJECT>] --summary "<summary>" --description "<description>" [--issuetype "<issuetype>"] [--labels "<label1>" "<label2>" ...] [--priority "<priority>"] [--epic "<epic>"]
```

Output: `{"success": true, "url": "..."}` or `{"success": false, "error": "..."}`. Report the issue URL, or the error as-is.

### get

Extract: `issue-key` (required — ask if missing).

```
<python> .opencode/scripts/jira.py get --issue-key <KEY>
```

Output: `{"success": true, "issue": {"key": "...", "project": "...", "summary": "...", "description": "...", "issuetype": "...", "labels": [...], "priority": "...", "status": "...", "epic": "...", "url": "..."}}` or `{"success": false, "error": "..."}`. Report the issue details, or the error.

### update

Extract: `issue-key` (required — ask if missing). Extract any of `project`, `summary`, `description`, `issuetype`, `labels`, `priority`, `epic` that were explicitly mentioned — omit the rest entirely (do not invent values).

```
<python> .opencode/scripts/jira.py update --issue-key <KEY> [--project <PROJECT>] [--summary "<summary>"] [--description "<description>"] [--issuetype "<issuetype>"] [--labels "<label1>" "<label2>" ...] [--priority "<priority>"] [--epic "<epic>"]
```

Output: `{"success": true, "url": "..."}` or `{"success": false, "error": "..."}`. If only `--summary`/`--description` is given, only those fields are patched directly; otherwise the full issue payload is rebuilt from the current issue + new values. Report the URL, or the error.

### list

Extract: optional `status` (exact status name, e.g. `"In Progress"`, `"Done"` — must match Jira's configured name exactly; no filter is required and no filter means "every issue in the project" — do not ask the user for one if not mentioned). If `JIRA_PROJECT_ID` is not set in `.env`, also extract `project` and ask if missing/ambiguous. Extract `max-results` only if the user asks for a specific count; otherwise omit it.

```
<python> .opencode/scripts/jira.py list [--project <PROJECT>] [--status "<status>"] [--max-results <N>]
```

Output: `{"success": true, "issues": [...], "total": N, "truncated": false}` or `{"success": false, "error": "..."}`. Report matching issues (key, summary, status, url each), "no issues found" if empty (an unmatched `--status` returns zero results, not an error), or the error. If `truncated` is `true`, say more results exist and suggest narrowing with `--status`.

### search

Extract: `summary` (text to match) and/or `epic` (epic key, e.g. `PRJ_MRDN-5`) — at least one is required; ask if neither can be identified. If `JIRA_PROJECT_ID` is not set in `.env`, also extract `project` and ask if missing/ambiguous. Extract `max-results` only if the user asks for a specific count; otherwise omit it.

```
<python> .opencode/scripts/jira.py search [--project <PROJECT>] [--summary "<summary>"] [--epic "<epic>"] [--max-results <N>]
```

Output: `{"success": true, "issues": [...], "total": N, "truncated": false}` or `{"success": false, "error": "..."}`. Report matching issues (key, summary, status, url each), "no issues found" if empty, or the error. If `truncated` is `true`, say more results exist and suggest narrowing (add `--epic`, or a more specific `--summary`).

### comment-add

Extract: `issue-key` (required) and `body` (the comment text — ask if missing).

```
<python> .opencode/scripts/jira.py comment-add --issue-key <KEY> --body "<body>"
```

Output: `{"success": true, "comment": {"id": "...", "body": "...", "author": "...", "created": "...", "updated": "..."}}` or `{"success": false, "error": "..."}`. Report the result, or the error.

### comment-list

Extract: `issue-key` (required — ask if missing). No other fields needed.

```
<python> .opencode/scripts/jira.py comment-list --issue-key <KEY>
```

Output: `{"success": true, "comments": [{"id": "...", "body": "...", "author": "...", "created": "...", "updated": "..."}, ...]}` or `{"success": false, "error": "..."}`. Report the comments, or the error.

### comment-update

Extract: `issue-key` (required), `comment-id`, and the new `body`. If `comment-id` is missing, first run `comment-list` to help identify it, or ask the user directly.

```
<python> .opencode/scripts/jira.py comment-update --issue-key <KEY> --comment-id <ID> --body "<body>"
```

Output: `{"success": true, "comment": {...}}` or `{"success": false, "error": "..."}`. Report the result, or the error.

### comment-delete

Extract: `issue-key` (required) and `comment-id`. If `comment-id` is missing, first run `comment-list` to help identify it, or ask the user directly.

```
<python> .opencode/scripts/jira.py comment-delete --issue-key <KEY> --comment-id <ID>
```

Output: `{"success": true}` or `{"success": false, "error": "..."}`. Report success, or the error.
