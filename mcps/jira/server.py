#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import List, Optional

import jira as jira_lib
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "jira",
    host=os.getenv("MCP_HOST", "0.0.0.0"),
    port=int(os.getenv("MCP_PORT", "8000")),
)


@mcp.tool()
def jira_create_issue(
    summary: str,
    description: str,
    project: Optional[str] = None,
    issuetype: Optional[str] = None,
    labels: Optional[List[str]] = None,
    priority: Optional[str] = None,
    epic: Optional[str] = None,
) -> dict:
    """Create a Jira issue. `project`/`issuetype`/`labels`/`priority`/`epic`
    fall back to their JIRA_* environment variable defaults when omitted."""
    return jira_lib.create_issue(
        project or jira_lib.DEFAULT_PROJECT,
        summary,
        description,
        issuetype or jira_lib.DEFAULT_ISSUETYPE,
        labels if labels is not None else jira_lib.DEFAULT_LABELS,
        priority or jira_lib.DEFAULT_PRIORITY,
        epic or jira_lib.DEFAULT_EPIC,
    )


@mcp.tool()
def jira_get_issue(issue_key: str) -> dict:
    """Fetch a single Jira issue by key (e.g. "PROJ-123")."""
    return jira_lib.get_issue(issue_key)


@mcp.tool()
def jira_update_issue(
    issue_key: str,
    project: Optional[str] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    issuetype: Optional[str] = None,
    labels: Optional[List[str]] = None,
    priority: Optional[str] = None,
    epic: Optional[str] = None,
) -> dict:
    """Update an existing Jira issue. Only the fields provided are changed."""
    if not any(
        v is not None for v in (project, summary, description, issuetype, labels, priority, epic)
    ):
        return {"success": False, "error": "No fields provided for update."}
    return jira_lib.update_issue(
        issue_key, project, summary, description, issuetype, labels, priority, epic
    )


@mcp.tool()
def jira_add_comment(issue_key: str, body: str) -> dict:
    """Add a comment to a Jira issue."""
    return jira_lib.add_comment(issue_key, body)


@mcp.tool()
def jira_list_comments(issue_key: str) -> dict:
    """List all comments on a Jira issue."""
    return jira_lib.list_comments(issue_key)


@mcp.tool()
def jira_update_comment(issue_key: str, comment_id: str, body: str) -> dict:
    """Update an existing comment on a Jira issue."""
    return jira_lib.update_comment(issue_key, comment_id, body)


@mcp.tool()
def jira_delete_comment(issue_key: str, comment_id: str) -> dict:
    """Delete a comment from a Jira issue."""
    return jira_lib.delete_comment(issue_key, comment_id)


@mcp.tool()
def jira_search_issues(
    project: Optional[str] = None,
    summary: Optional[str] = None,
    epic: Optional[str] = None,
    max_results: Optional[int] = None,
) -> dict:
    """Search issues in a project by summary text and/or epic key. At least
    one of `summary`/`epic` is required."""
    return jira_lib.search_issues(
        project or jira_lib.DEFAULT_PROJECT,
        summary,
        epic,
        max_results if max_results is not None else jira_lib.DEFAULT_MAX_RESULTS,
    )


@mcp.tool()
def jira_list_issues(
    project: Optional[str] = None,
    status: Optional[str] = None,
    max_results: Optional[int] = None,
) -> dict:
    """List issues in a project, optionally filtered by an exact status match."""
    return jira_lib.list_issues(
        project or jira_lib.DEFAULT_PROJECT,
        status,
        max_results if max_results is not None else jira_lib.DEFAULT_MAX_RESULTS,
    )


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    mcp.run(transport=transport)
