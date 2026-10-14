#!/usr/bin/env python3
"""Standalone CLI to create/get/update Jira issues and their comments, for
use by opencode commands.

This script is fully self-contained: it does NOT import anything from this
project's own `app/` package or `main.py`, and it has ZERO third-party
dependencies — only the Python standard library (`urllib`, `argparse`,
`json`). This single file can be copied to another repo and run as-is with
any Python 3 interpreter, no `pip install` required.

Usage:
    jira.py create --project <PROJECT_KEY> --summary "..." --description "..." \
                          [--issuetype "..."] [--labels "..." "..."] [--priority "..."] \
                          [--epic "..."]
    jira.py get --issue-key KEY-123
    jira.py update --issue-key KEY-123 [--project <PROJECT_KEY>] [--summary "..."] \
                          [--description "..."] [--issuetype "..."] [--labels "..." "..."] \
                          [--priority "..."] [--epic "..."]
    jira.py comment-add --issue-key KEY-123 --body "..."
    jira.py comment-list --issue-key KEY-123
    jira.py comment-update --issue-key KEY-123 --comment-id 12345 --body "..."
    jira.py comment-delete --issue-key KEY-123 --comment-id 12345
    jira.py search [--project <PROJECT_KEY>] [--summary "..."] [--epic "..."] [--max-results N]
    jira.py list [--project <PROJECT_KEY>] [--status "..."] [--max-results N]

Reads configuration from environment variables, falling back to a `.env`
file (KEY=VALUE per line) in the current working directory if they aren't
already set:
    JIRA_TOKEN          Jira Bearer token (required, no default).
    JIRA_BASE_URL       Jira base URL (required, no default — e.g.
                         "https://your-company.atlassian.net" or
                         "https://jira.your-company.com"). This script is
                         meant to be portable across organizations, so no
                         instance-specific URL is baked in.
    JIRA_PROJECT_ID     Default Jira project key (no default; must be given
                         via env var or --project).
    JIRA_ISSUE_TYPE     Default issue type (default: "Task").
    JIRA_ISSUE_LABELS    Default labels, comma-separated (default: none).
    JIRA_ISSUE_PRIORITY Default priority (default: "Medium").
    JIRA_ISSUE_EPIC     Default epic key to link the issue to (default: none).
    JIRA_EPIC_FIELD     Jira custom field id used for the epic link
                         (required only if you use --epic / JIRA_ISSUE_EPIC;
                         no default — must be set explicitly, e.g.
                         "customfield_10014").
    JIRA_TIMEOUT        HTTP request timeout in seconds (default: 10).
    JIRA_MAX_RESULTS    Default page size for `search`/`list` (default: 50).
                         Can be overridden per-call via --max-results.
Any of these (except JIRA_TOKEN and JIRA_BASE_URL) can be overridden
per-call via CLI flags where a flag exists.

Always prints one line of JSON to stdout. For `create`/`update`:
    {"success": true, "url": "https://your-company.atlassian.net/browse/KEY-123"}
    {"success": false, "error": "..."}
For `get`:
    {"success": true, "issue": {"key": "...", "project": "...", "summary": "...",
                                 "description": "...", "issuetype": "...",
                                 "labels": [...], "priority": "...", "status": "...",
                                 "epic": "...", "url": "..."}}
    {"success": false, "error": "..."}
For `comment-add`/`comment-update`:
    {"success": true, "comment": {"id": "...", "body": "...", "author": "...",
                                   "created": "...", "updated": "..."}}
    {"success": false, "error": "..."}
For `comment-list`:
    {"success": true, "comments": [{"id": "...", "body": "...", "author": "...",
                                     "created": "...", "updated": "..."}, ...]}
    {"success": false, "error": "..."}
For `comment-delete`:
    {"success": true}
    {"success": false, "error": "..."}
For `search` (at least one of `--summary`/`--epic` is required; both together are AND'd):
    {"success": true, "issues": [{"key": "...", "project": "...", "summary": "...",
                                   "description": "...", "issuetype": "...",
                                   "labels": [...], "priority": "...", "status": "...",
                                   "epic": "...", "url": "..."}, ...],
     "total": 3, "truncated": false}
    {"success": false, "error": "..."}
For `list` (no filter is required; `--status` narrows to an exact status match):
    {"success": true, "issues": [{"key": "...", "project": "...", "summary": "...",
                                   "description": "...", "issuetype": "...",
                                   "labels": [...], "priority": "...", "status": "...",
                                   "epic": "...", "url": "..."}, ...],
     "total": 3, "truncated": false}
    {"success": false, "error": "..."}
Exit code is 0 on success, 1 on failure.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import traceback
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


def load_dotenv(path: str = ".env") -> None:
    """Minimal `.env` loader (no third-party dependency). Does not override
    variables already present in the environment."""
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def _get_nonempty_env(name: str) -> Optional[str]:
    """Read an env var, treating an unset OR empty-string value as absent.
    Used for config that must be either a real value or explicitly missing
    (e.g. JIRA_BASE_URL, JIRA_PROJECT_ID) so a blank env var doesn't silently
    satisfy an `is None` check and slip an empty value through to the API."""
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value if value else None


load_dotenv()
JIRA_TOKEN = _get_nonempty_env("JIRA_TOKEN")
# No hardcoded default: this script is meant to be copied to any repo/org
# as-is, so silently pointing at one specific company's Jira instance when
# JIRA_BASE_URL is unset would be a portability trap (fix #1).
JIRA_BASE_URL = _get_nonempty_env("JIRA_BASE_URL")
DEFAULT_PROJECT = _get_nonempty_env("JIRA_PROJECT_ID")
DEFAULT_ISSUETYPE = os.getenv("JIRA_ISSUE_TYPE", "Task")
DEFAULT_LABELS = [
    label.strip()
    for label in os.getenv("JIRA_ISSUE_LABELS", "").split(",")
    if label.strip()
]
DEFAULT_PRIORITY = os.getenv("JIRA_ISSUE_PRIORITY", "Medium")
DEFAULT_EPIC = os.getenv("JIRA_ISSUE_EPIC")
EPIC_FIELD = os.getenv("JIRA_EPIC_FIELD")


def _require_base_url() -> str:
    """Return JIRA_BASE_URL, raising a clear error if it isn't configured."""
    if not JIRA_BASE_URL:
        raise ValueError(
            "JIRA_BASE_URL environment variable is not set. Set it to your "
            "Jira instance's base URL (e.g. "
            "'https://your-company.atlassian.net')."
        )
    return JIRA_BASE_URL


def _require_epic_field() -> str:
    """Return EPIC_FIELD, raising a clear error if it isn't configured.
    Call this at every point epic is actually about to be used (not at
    import time), so commands that don't touch epics still work fine
    without JIRA_EPIC_FIELD set."""
    if not EPIC_FIELD:
        raise ValueError(
            "--epic / JIRA_ISSUE_EPIC was given but JIRA_EPIC_FIELD is not "
            "set. Set the JIRA_EPIC_FIELD environment variable to your "
            "Jira instance's epic-link custom field id (e.g. "
            "'customfield_10014')."
        )
    return EPIC_FIELD


def _epic_field_cf_id(epic_field: Optional[str] = None) -> str:
    """Return the numeric id portion of a Jira custom field id (e.g.
    'customfield_10014' -> '10014') for use inside a JQL `cf[...]` clause.
    Fix #3: rather than blindly stripping a literal 'customfield_' prefix
    (which silently produces a malformed JQL clause if the configured field
    doesn't follow that exact convention), extract the trailing digits and
    fail loudly if none are found.
    """
    field_id = epic_field or _require_epic_field()
    match = re.search(r"(\d+)\s*$", field_id)
    if not match:
        raise ValueError(
            f"JIRA_EPIC_FIELD ('{field_id}') doesn't look like a Jira custom "
            "field id (expected something like 'customfield_10014'). Cannot "
            "build a JQL cf[...] clause from it."
        )
    return match.group(1)


def _get_int_env(name: str, default: int) -> int:
    """Read an int env var, falling back to `default` if unset or invalid."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


DEFAULT_TIMEOUT = _get_int_env("JIRA_TIMEOUT", 10)
DEFAULT_MAX_RESULTS = _get_int_env("JIRA_MAX_RESULTS", 50)


def build_payload(
    project: str,
    summary: str,
    description: str,
    issuetype: str,
    labels: List[str],
    priority: str,
    epic: Optional[str] = None,
) -> Dict[str, Any]:
    fields = {
        "project": {"key": project},
        "summary": summary,
        "labels": labels,
        "description": description,
        "issuetype": {"name": issuetype},
        "priority": {"name": priority},
    }
    if epic:
        fields[_require_epic_field()] = epic
    return {"fields": fields}


# --- Jira HTTP calls (stdlib urllib, no `requests` dependency) --------------
def jira_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = DEFAULT_TIMEOUT,
):
    if not JIRA_TOKEN:
        return {"error": "JIRA_TOKEN environment variable is not set"}
    base_url = _require_base_url()

    # Fix #5: normalize away any leading/trailing slashes on both sides of
    # the join so every call point produces the same URL shape, regardless
    # of whether the endpoint string happens to include a trailing slash.
    url = f"{base_url.rstrip('/')}/{endpoint.strip('/')}"
    body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(
        url,
        data=body_bytes,
        method=method,
        headers={
            "Authorization": f"Bearer {JIRA_TOKEN}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                # Fix #2: a non-JSON response body (e.g. an HTML error page
                # from a proxy in front of Jira) shouldn't raise all the way
                # out of jira_request; report it through the normal error
                # channel instead.
                return {
                    "status_code": response.status,
                    "error": f"Non-JSON response from Jira: {raw[:500]!r}",
                }
            return {"status_code": response.status, "response": parsed}
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")
        return {"status_code": err.code, "error": detail}
    except urllib.error.URLError as err:
        return {"error": str(err.reason)}


def create_issue(
    project: str,
    summary: str,
    description: str,
    issuetype: str,
    labels: List[str],
    priority: str,
    epic: Optional[str] = None,
) -> Dict[str, Any]:
    payload = build_payload(
        project, summary, description, issuetype, labels, priority, epic
    )
    result = jira_request("POST", "rest/api/2/issue", payload)

    if result.get("status_code") == 201:
        key = result["response"]["key"]
        return {"success": True, "url": f"{_require_base_url()}/browse/{key}"}
    return {"success": False, "error": result.get("error", result)}


def _format_issue(raw_issue: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the fields common to `get` and `search` results from a raw Jira issue
    object (one that has top-level `key` and `fields`)."""
    fields = raw_issue.get("fields", {})
    key = raw_issue.get("key")
    return {
        "key": key,
        "project": fields.get("project", {}).get("key"),
        "summary": fields.get("summary"),
        "description": fields.get("description"),
        "issuetype": fields.get("issuetype", {}).get("name"),
        "labels": fields.get("labels", []),
        "priority": fields.get("priority", {}).get("name"),
        "status": fields.get("status", {}).get("name"),
        "epic": fields.get(EPIC_FIELD) if EPIC_FIELD else None,
        "url": f"{_require_base_url()}/browse/{key}",
    }


def get_issue(issue_key: str) -> Dict[str, Any]:
    result = jira_request("GET", f"rest/api/2/issue/{issue_key}")
    if "response" not in result:
        return {"success": False, "error": result.get("error", result)}
    return {"success": True, "issue": _format_issue(result["response"])}


def _escape_jql(value: str) -> str:
    """Escape a value for embedding inside a double-quoted JQL string literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_search_jql(
    project: str,
    summary: Optional[str] = None,
    epic: Optional[str] = None,
    epic_field: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Build a JQL query scoped to `project`, AND-ing in a `summary` text match and/or an
    exact match on the `epic_field` custom field for `epic`. At least one of `summary`/`epic`
    is required. Returns `(jql, None)` on success or `(None, error)` if neither is given.
    `epic_field` defaults to the configured EPIC_FIELD (validated only if `epic` is given).
    """
    if not summary and not epic:
        return None, "At least one of --summary or --epic is required for search."

    clauses = [f'project = "{_escape_jql(project)}"']
    if summary:
        clauses.append(f'summary ~ "{_escape_jql(summary)}"')
    if epic:
        field_id = _epic_field_cf_id(epic_field)
        clauses.append(f'cf[{field_id}] = "{_escape_jql(epic)}"')
    return " AND ".join(clauses), None


def _execute_jql_search(
    jql: str, max_results: int = DEFAULT_MAX_RESULTS
) -> Dict[str, Any]:
    """Run a JQL query against `rest/api/2/search` and map the results through
    `_format_issue`, capped at `max_results` with a `truncated` flag. Shared by `search`
    and `list` so the two cannot independently drift in field names, pagination cap, or
    `truncated` semantics."""
    fields = [
        "summary",
        "description",
        "issuetype",
        "labels",
        "priority",
        "status",
        "project",
    ]
    if EPIC_FIELD:
        fields.append(EPIC_FIELD)
    payload = {
        "jql": jql,
        "maxResults": max_results,
        "fields": fields,
    }
    result = jira_request("POST", "rest/api/2/search", payload)
    if "response" not in result:
        return {"success": False, "error": result.get("error", result)}

    response = result["response"]
    issues = [_format_issue(raw) for raw in response.get("issues", [])]
    total = response.get("total", len(issues))
    return {
        "success": True,
        "issues": issues,
        "total": total,
        "truncated": total > len(issues),
    }


def search_issues(
    project: str,
    summary: Optional[str] = None,
    epic: Optional[str] = None,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> Dict[str, Any]:
    jql, error = build_search_jql(project, summary, epic)
    if error:
        return {"success": False, "error": error}
    return _execute_jql_search(jql, max_results)


def build_list_jql(project: str, status: Optional[str] = None) -> str:
    """Build a JQL query scoped to `project`, AND-ing in an exact `status` match when
    given. Unlike `build_search_jql`, no filter is required: `list` treats a filterless
    request ("every issue in the project") as valid."""
    clauses = [f'project = "{_escape_jql(project)}"']
    if status:
        clauses.append(f'status = "{_escape_jql(status)}"')
    return " AND ".join(clauses)


def list_issues(
    project: str,
    status: Optional[str] = None,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> Dict[str, Any]:
    jql = build_list_jql(project, status)
    return _execute_jql_search(jql, max_results)


def update_issue(
    issue_key: str,
    project: Optional[str],
    summary: Optional[str],
    description: Optional[str],
    issuetype: Optional[str],
    labels: Optional[List[str]],
    priority: Optional[str],
    epic: Optional[str] = None,
) -> Dict[str, Any]:
    if any(v is not None for v in (project, issuetype, labels, priority, epic)):
        # Building a full Jira payload requires project/summary/description/
        # issuetype/labels/priority/epic together. Fetch the current issue
        # first to fill in any gaps not explicitly provided.
        current = jira_request("GET", f"rest/api/2/issue/{issue_key}")
        if "response" not in current:
            return {"success": False, "error": current.get("error", current)}
        current_fields = current["response"]["fields"]
        summary = summary if summary is not None else current_fields.get("summary", "")
        description = (
            description
            if description is not None
            else current_fields.get("description", "")
        )
        project = project if project is not None else current_fields["project"]["key"]
        issuetype = (
            issuetype if issuetype is not None else current_fields["issuetype"]["name"]
        )
        labels = labels if labels is not None else current_fields.get("labels", [])
        priority = (
            priority
            if priority is not None
            else current_fields.get("priority", {}).get("name", DEFAULT_PRIORITY)
        )
        epic = epic if epic is not None else current_fields.get(EPIC_FIELD)
        payload = build_payload(
            project, summary, description, issuetype, labels, priority, epic
        )
    else:
        # No project/issuetype/labels/priority/epic change: only patch the
        # fields explicitly provided.
        fields: Dict[str, Any] = {}
        if summary is not None:
            fields["summary"] = summary
        if description is not None:
            fields["description"] = description
        payload = {"fields": fields}

    result = jira_request("PUT", f"rest/api/2/issue/{issue_key}", payload)

    if result.get("status_code") == 204:
        return {"success": True, "url": f"{_require_base_url()}/browse/{issue_key}"}
    return {"success": False, "error": result.get("error", result)}


# --- Comment helpers ---------------------------------------------------------
def _format_comment(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": raw.get("id"),
        "body": raw.get("body"),
        "author": raw.get("author", {}).get("displayName")
        or raw.get("author", {}).get("name"),
        "created": raw.get("created"),
        "updated": raw.get("updated"),
    }


def add_comment(issue_key: str, body: str) -> Dict[str, Any]:
    result = jira_request(
        "POST", f"rest/api/2/issue/{issue_key}/comment", {"body": body}
    )
    if result.get("status_code") == 201:
        return {"success": True, "comment": _format_comment(result["response"])}
    return {"success": False, "error": result.get("error", result)}


def list_comments(issue_key: str) -> Dict[str, Any]:
    result = jira_request("GET", f"rest/api/2/issue/{issue_key}/comment")
    if "response" not in result:
        return {"success": False, "error": result.get("error", result)}
    comments = [_format_comment(c) for c in result["response"].get("comments", [])]
    return {"success": True, "comments": comments}


def update_comment(issue_key: str, comment_id: str, body: str) -> Dict[str, Any]:
    result = jira_request(
        "PUT",
        f"rest/api/2/issue/{issue_key}/comment/{comment_id}",
        {"body": body},
    )
    if result.get("status_code") == 200:
        return {"success": True, "comment": _format_comment(result["response"])}
    return {"success": False, "error": result.get("error", result)}


def delete_comment(issue_key: str, comment_id: str) -> Dict[str, Any]:
    result = jira_request(
        "DELETE", f"rest/api/2/issue/{issue_key}/comment/{comment_id}"
    )
    if result.get("status_code") == 204:
        return {"success": True}
    return {"success": False, "error": result.get("error", result)}


# --- CLI ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create, get, update a Jira issue, or manage its comments"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument(
        "--project",
        default=DEFAULT_PROJECT,
        required=DEFAULT_PROJECT is None,
        help="Jira project key (env: JIRA_PROJECT_ID)",
    )
    create_parser.add_argument("--summary", required=True)
    create_parser.add_argument("--description", required=True)
    create_parser.add_argument(
        "--issuetype", default=DEFAULT_ISSUETYPE, help="env: JIRA_ISSUE_TYPE"
    )
    create_parser.add_argument(
        "--labels", nargs="+", default=DEFAULT_LABELS, help="env: JIRA_ISSUE_LABELS"
    )
    create_parser.add_argument(
        "--priority", default=DEFAULT_PRIORITY, help="env: JIRA_ISSUE_PRIORITY"
    )
    create_parser.add_argument(
        "--epic", default=DEFAULT_EPIC, help="env: JIRA_ISSUE_EPIC"
    )

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("--issue-key", required=True)

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--issue-key", required=True)
    update_parser.add_argument("--project", help="Jira project key")
    update_parser.add_argument("--summary")
    update_parser.add_argument("--description")
    update_parser.add_argument("--issuetype")
    update_parser.add_argument("--labels", nargs="+")
    update_parser.add_argument("--priority")
    update_parser.add_argument("--epic")

    comment_add_parser = subparsers.add_parser("comment-add")
    comment_add_parser.add_argument("--issue-key", required=True)
    comment_add_parser.add_argument("--body", required=True)

    comment_list_parser = subparsers.add_parser("comment-list")
    comment_list_parser.add_argument("--issue-key", required=True)

    comment_update_parser = subparsers.add_parser("comment-update")
    comment_update_parser.add_argument("--issue-key", required=True)
    comment_update_parser.add_argument("--comment-id", required=True)
    comment_update_parser.add_argument("--body", required=True)

    comment_delete_parser = subparsers.add_parser("comment-delete")
    comment_delete_parser.add_argument("--issue-key", required=True)
    comment_delete_parser.add_argument("--comment-id", required=True)

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument(
        "--project",
        default=DEFAULT_PROJECT,
        required=DEFAULT_PROJECT is None,
        help="Jira project key (env: JIRA_PROJECT_ID)",
    )
    search_parser.add_argument(
        "--summary", help="Text to match against the issue summary"
    )
    search_parser.add_argument("--epic", help="Epic key to filter issues by")
    search_parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help="env: JIRA_MAX_RESULTS",
    )

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument(
        "--project",
        default=DEFAULT_PROJECT,
        required=DEFAULT_PROJECT is None,
        help="Jira project key (env: JIRA_PROJECT_ID)",
    )
    list_parser.add_argument("--status", help="Exact status name to filter issues by")
    list_parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help="env: JIRA_MAX_RESULTS",
    )

    args = parser.parse_args()

    try:
        if args.command == "create":
            result = create_issue(
                args.project,
                args.summary,
                args.description,
                args.issuetype,
                args.labels,
                args.priority,
                args.epic,
            )
        elif args.command == "get":
            result = get_issue(args.issue_key)
        elif args.command == "comment-add":
            result = add_comment(args.issue_key, args.body)
        elif args.command == "comment-list":
            result = list_comments(args.issue_key)
        elif args.command == "comment-update":
            result = update_comment(args.issue_key, args.comment_id, args.body)
        elif args.command == "comment-delete":
            result = delete_comment(args.issue_key, args.comment_id)
        elif args.command == "search":
            result = search_issues(
                args.project, args.summary, args.epic, args.max_results
            )
        elif args.command == "list":
            result = list_issues(args.project, args.status, args.max_results)
        else:
            if not any(
                [
                    args.project,
                    args.summary,
                    args.description,
                    args.issuetype,
                    args.labels,
                    args.priority,
                    args.epic,
                ]
            ):
                result = {"success": False, "error": "No fields provided for update."}
            else:
                result = update_issue(
                    args.issue_key,
                    args.project,
                    args.summary,
                    args.description,
                    args.issuetype,
                    args.labels,
                    args.priority,
                    args.epic,
                )
    except ValueError as err:
        # e.g. --epic used without JIRA_EPIC_FIELD configured, or
        # JIRA_BASE_URL missing: surface it through the script's normal
        # JSON-error contract instead of a traceback, since callers only
        # read stdout JSON + exit code.
        result = {"success": False, "error": str(err)}
    except Exception as err:
        # Fix #2: catch-all so any unexpected failure (malformed API
        # response, network edge case, etc.) still honors the documented
        # "always prints one line of JSON to stdout" contract instead of
        # leaking a raw traceback to callers that only parse stdout.
        result = {
            "success": False,
            "error": f"Unexpected error: {err}",
            "traceback": traceback.format_exc(),
        }

    print(json.dumps(result))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
