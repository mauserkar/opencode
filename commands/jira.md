---
description: Create, get, update, list, or search Jira issues, or manage their comments, using the jira MCP server
---

Manage Jira issues and comments by calling the tools exposed by the `jira` MCP server (`mcps/jira/`), connected as `mcp.servers.jira` in the OpenCode config. Call the tools directly — do not shell out or look for a local script. The server needs `JIRA_TOKEN` and `JIRA_BASE_URL` (required) configured on its own side (`mcps/jira/.env`), not in this project's environment.

The following are also configurable server-side (`mcps/jira/.env`), each with a default except `JIRA_PROJECT_ID`, and each can be overridden per-call via the matching tool argument:

- `JIRA_PROJECT_ID`: Jira project id/key. No default — required (via server config or the `project` argument) for `create`, `search`, and `list`.
- `JIRA_ISSUE_TYPE`: issue type for `create`. Default `Task`.
- `JIRA_ISSUE_LABELS`: comma-separated labels for `create`. No default (no labels if omitted).
- `JIRA_ISSUE_PRIORITY`: priority for `create`. Default `Medium`.
- `JIRA_ISSUE_EPIC`: epic key to link on `create`/`update`. No default (no epic link if omitted).
- `JIRA_EPIC_FIELD`: Jira custom field id used for the epic link and for `search`'s `epic` argument. No default — required only if an `epic` is used; if it's needed but not set, the tool returns `{"success": false, "error": "..."}` explaining that `JIRA_EPIC_FIELD` must be set (e.g. to `customfield_10014`, the standard "Epic Link" field id on Jira Server/Data Center). Relay that error as-is rather than treating it as unexpected.

## Step 0 — Check the MCP server is available

Confirm the `jira` MCP tools (`jira_create_issue`, `jira_get_issue`, `jira_update_issue`, `jira_add_comment`, `jira_list_comments`, `jira_update_comment`, `jira_delete_comment`, `jira_search_issues`, `jira_list_issues`) are available in this session. If they are not, report that the `jira` MCP server is not connected (see `mcps/jira/README.md` to run it with `make up`) instead of trying a workaround.

Request: $ARGUMENTS

## Step 1 — Identify the action

From the request above, determine which action is intended:

| Action           | Tool                   | Typical phrasing                                                       |
| ---------------- | ----------------------- | ------------------------------------------------------------------------ |
| `create`         | `jira_create_issue`    | "create/open/file a new issue/ticket/bug/task"                         |
| `get`            | `jira_get_issue`       | "show/get/look up issue KEY", "what's the status of KEY"               |
| `update`         | `jira_update_issue`    | "update/change/edit issue KEY", "move KEY to project X", "relabel KEY" |
| `list`           | `jira_list_issues`     | "list issues in PROJECT", "what's in progress in PROJECT"              |
| `search`         | `jira_search_issues`   | "find issues about X", "search for issues under epic Y"                |
| `comment-add`    | `jira_add_comment`     | "comment on KEY", "add a note to KEY"                                  |
| `comment-list`   | `jira_list_comments`   | "show comments on KEY"                                                 |
| `comment-update` | `jira_update_comment`  | "edit/update comment on KEY"                                           |
| `comment-delete` | `jira_delete_comment`  | "delete/remove comment on KEY"                                         |
| `help`           | —                       | "jira help", "what can you do with jira", "how does this work"         |

If the action is genuinely ambiguous (e.g. it's unclear whether the user wants `search` vs `list`, or `get` vs `comment-list`), ask the user to clarify before proceeding. Otherwise, proceed directly to the matching branch below — do not ask just to confirm an action that's already clear from phrasing.

## Step 2 — Gather the fields for that action, then call the tool

### help

No fields to extract, and nothing to run — answer directly from this file. Reply to the user with a short summary of what's available:

- **create** — open a new issue (needs summary, description; project/issuetype/labels/priority/epic optional).
- **get** — fetch one issue by key.
- **update** — change fields on an existing issue (only the fields mentioned are touched).
- **list** — list every issue in a project, optionally filtered by exact status.
- **search** — find issues by summary text and/or epic key.
- **comment-add / comment-list / comment-update / comment-delete** — manage comments on an issue.

Mention that `project` only needs to be given if the server doesn't already have `JIRA_PROJECT_ID` set, and that `epic` needs `JIRA_EPIC_FIELD` configured server-side.

In every call below, include only the optional arguments for fields that were actually provided or extracted — never invent values for fields the user didn't mention.

### create

Extract: `summary` and `description` (required — ask if missing). Optionally extract `project`, `issuetype`, `labels`, `priority`, `epic` if mentioned; otherwise omit and let the server fall back to its own config/defaults.

Call `jira_create_issue` with `summary`, `description`, and any of the optional arguments extracted above.

Output: `{"success": true, "url": "..."}` or `{"success": false, "error": "..."}`. Report the issue URL, or the error as-is.

### get

Extract: `issue-key` (required — ask if missing).

Call `jira_get_issue` with `issue_key`.

Output: `{"success": true, "issue": {"key": "...", "project": "...", "summary": "...", "description": "...", "issuetype": "...", "labels": [...], "priority": "...", "status": "...", "epic": "...", "url": "..."}}` or `{"success": false, "error": "..."}`. Report the issue details, or the error.

### update

Extract: `issue-key` (required — ask if missing). Extract any of `project`, `summary`, `description`, `issuetype`, `labels`, `priority`, `epic` that were explicitly mentioned — omit the rest entirely (do not invent values).

Call `jira_update_issue` with `issue_key` and only the fields explicitly mentioned.

Output: `{"success": true, "url": "..."}` or `{"success": false, "error": "..."}`. If only `summary`/`description` is given, only those fields are patched directly; otherwise the full issue payload is rebuilt from the current issue + new values. Report the URL, or the error.

### list

Extract: optional `status` (exact status name, e.g. `"In Progress"`, `"Done"` — must match Jira's configured name exactly; no filter is required and no filter means "every issue in the project" — do not ask the user for one if not mentioned). Extract `project` only if the server doesn't already have `JIRA_PROJECT_ID` configured. Extract `max-results` only if the user asks for a specific count; otherwise omit it.

Call `jira_list_issues` with the optional arguments gathered above.

Output: `{"success": true, "issues": [...], "total": N, "truncated": false}` or `{"success": false, "error": "..."}`. Report matching issues (key, summary, status, url each), "no issues found" if empty (an unmatched `status` returns zero results, not an error), or the error. If `truncated` is `true`, say more results exist and suggest narrowing with `status`.

### search

Extract: `summary` (text to match) and/or `epic` (epic key, e.g. `PRJ_MRDN-5`) — at least one is required; ask if neither can be identified. Extract `project` only if the server doesn't already have `JIRA_PROJECT_ID` configured. Extract `max-results` only if the user asks for a specific count; otherwise omit it.

Call `jira_search_issues` with the arguments gathered above.

Output: `{"success": true, "issues": [...], "total": N, "truncated": false}` or `{"success": false, "error": "..."}`. Report matching issues (key, summary, status, url each), "no issues found" if empty, or the error. If `truncated` is `true`, say more results exist and suggest narrowing (add `epic`, or a more specific `summary`).

### comment-add

Extract: `issue-key` (required) and `body` (the comment text — ask if missing).

Call `jira_add_comment` with `issue_key` and `body`.

Output: `{"success": true, "comment": {"id": "...", "body": "...", "author": "...", "created": "...", "updated": "..."}}` or `{"success": false, "error": "..."}`. Report the result, or the error.

### comment-list

Extract: `issue-key` (required — ask if missing). No other fields needed.

Call `jira_list_comments` with `issue_key`.

Output: `{"success": true, "comments": [{"id": "...", "body": "...", "author": "...", "created": "...", "updated": "..."}, ...]}` or `{"success": false, "error": "..."}`. Report the comments, or the error.

### comment-update

Extract: `issue-key` (required), `comment-id`, and the new `body`. If `comment-id` is missing, first run `comment-list` to help identify it, or ask the user directly.

Call `jira_update_comment` with `issue_key`, `comment_id`, and `body`.

Output: `{"success": true, "comment": {...}}` or `{"success": false, "error": "..."}`. Report the result, or the error.

### comment-delete

Extract: `issue-key` (required) and `comment-id`. If `comment-id` is missing, first run `comment-list` to help identify it, or ask the user directly.

Call `jira_delete_comment` with `issue_key` and `comment_id`.

Output: `{"success": true}` or `{"success": false, "error": "..."}`. Report success, or the error.
