---
name: jira-issue-management
description: Create, look up, update, search, list, or comment on Jira issues. Use whenever the user mentions a Jira issue, ticket, epic, or issue key (e.g. PROJ-123), or asks to create, update, find, list, check the status of, or comment on an issue, even if they don't say "Jira".
compatibility: Requires the `jira` MCP server (`mcps/jira/`) connected in this session, with `JIRA_TOKEN` and `JIRA_BASE_URL` configured on the server side. The `jira` command (`commands/jira.md`) documents the exact tool arguments.
metadata:
  version: "2.0"
---

# Skill: jira-issue-management

Manage Jira issues and comments by calling the tools exposed by the `jira`
MCP server. An agent calls the tools directly (no shelling out, no local
script); the `jira` command (`commands/jira.md`) is the manual `/jira`
entry point. Either way, that command file is the source of truth for
exact tool arguments and per-action fields — read it before calling
anything.

This skill says **when** to act and **which action** to pick.

## Prerequisites

### MCP server

The `jira` MCP server must be connected (see `mcp.servers.jira` in the OpenCode
config). It exposes: `jira_create_issue`, `jira_get_issue`,
`jira_update_issue`, `jira_add_comment`, `jira_list_comments`,
`jira_update_comment`, `jira_delete_comment`, `jira_search_issues`,
`jira_list_issues`.

If the tools are not available, report that the `jira` MCP server is not
connected (see `mcps/jira/README.md` to run it with `make up`) instead of
looking for a local script or working around it.

### Server configuration

`JIRA_TOKEN` and `JIRA_BASE_URL` are required and live in the server's own
`.env` (`mcps/jira/.env`, copied from `mcps/jira/env.sample`) — never in
this project's environment, and never printed or echoed.

| Variable              | Required                                   | Default  | Purpose                                                     |
| --------------------- | ------------------------------------------ | -------- | ----------------------------------------------------------- |
| `JIRA_TOKEN`          | Yes                                        | none     | Authentication                                              |
| `JIRA_BASE_URL`       | Yes                                        | none     | Instance URL, e.g. `https://your-company.atlassian.net`     |
| `JIRA_PROJECT_ID`     | For create/search/list (or pass `project`) | none     | Default project key                                         |
| `JIRA_ISSUE_TYPE`     | No                                         | `Task`   | Default issue type                                          |
| `JIRA_ISSUE_LABELS`   | No                                         | none     | Default labels, comma-separated                             |
| `JIRA_ISSUE_PRIORITY` | No                                         | `Medium` | Default priority                                            |
| `JIRA_ISSUE_EPIC`     | No                                         | none     | Default epic key for create/update                          |
| `JIRA_EPIC_FIELD`     | Only if an epic is used                    | none     | Custom field id for the epic link, e.g. `customfield_10014` |
| `JIRA_TIMEOUT`        | No                                         | `10`     | HTTP timeout in seconds                                     |
| `JIRA_MAX_RESULTS`    | No                                         | `50`     | Page size for search/list (override with `max_results`)     |

## Actions

| Action                                                               | Tool                                                                                      | Purpose                         | Required input                                                                                                       |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `create`                                                             | `jira_create_issue`                                                                       | Open a new issue                | `summary`, `description`                                                                                             |
| `get`                                                                | `jira_get_issue`                                                                          | Look up one issue               | `issue_key`                                                                                                          |
| `update`                                                             | `jira_update_issue`                                                                       | Change fields on an issue       | `issue_key` plus only the fields being changed (`summary`, `description`, `issuetype`, `labels`, `priority`, `epic`) |
| `search`                                                             | `jira_search_issues`                                                                      | Find issues by text and/or epic | at least one of `summary`, `epic`                                                                                    |
| `list`                                                               | `jira_list_issues`                                                                        | List issues in the project      | none; optional exact-match `status`                                                                                  |
| `comment-add` / `comment-list` / `comment-update` / `comment-delete` | `jira_add_comment` / `jira_list_comments` / `jira_update_comment` / `jira_delete_comment` | Manage comments on an issue     | `issue_key`, plus `body` (add/update) or `comment_id` (update/delete)                                                |
| `help`                                                               | —                                                                                         | Summarize what is available     | none; answer directly, call nothing                                                                                  |

`project` is also required for `create`, `search`, and `list` when the
server doesn't already have `JIRA_PROJECT_ID` configured.

## Procedure

1. Confirm the `jira` MCP tools are available (see Prerequisites).
2. Identify the action from the request. If it is genuinely ambiguous
   (`search` vs `list`, `get` vs `comment-list`), ask the user.
3. If a required input is missing, ask for it. Never guess a `summary`,
   `description`, `issue_key`, `project`, comment `body`, or `comment_id`.
   A missing `status` on `list` means "unfiltered", not "ask".
4. Call the matching MCP tool (see Actions / `commands/jira.md`), passing
   only the arguments the user provided or that were clearly extracted.
   Never invent values for fields the user did not mention; on `update`,
   touch only the fields explicitly mentioned.
5. Report the result (see Output).

## Rules

- **`comment-delete` is destructive:** show the target issue and comment,
  and require explicit user confirmation before calling it.
- Never print, log, or echo `JIRA_TOKEN`, and never include it in any
  output shown to the user.
- On `{"success": false, "error": "..."}`, report the message verbatim and
  do not retry silently. This includes the "set `JIRA_EPIC_FIELD`" error:
  relay it as-is.

## Output

- `create` / `update`: the issue URL.
- `get`: the issue details (summary, description, status, labels).
- `search` / `list`: the matching issues, or "no issues found". If
  `truncated` is `true`, say so and suggest a narrower filter.
- Comment actions: the comment result.
