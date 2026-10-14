# Jira MCP

MCP server exposing Jira issue/comment operations as tools, plus a
standalone `jira.py` CLI with zero third-party dependencies.

## Contents

- `server.py` — MCP server (FastMCP) exposing the tools below over
  `streamable-http` by default.
- `jira.py` — Self-contained CLI (stdlib only: `urllib`, `argparse`,
  `json`). Can be copied to any other repo and run as-is.
- `Dockerfile` / `docker-compose.yaml` — Containerized deployment of the
  MCP server.
- `requirements.txt` — Dependencies for the MCP server only (`jira.py`
  needs none).
- `env.sample` — Template for `.env`.

## Configuration

Copy `env.sample` to `.env` in this directory and fill in the values:

```bash
cp env.sample .env
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `JIRA_TOKEN` | yes | — | Jira Bearer token. |
| `JIRA_BASE_URL` | yes | — | Jira base URL, e.g. `https://your-company.atlassian.net`. |
| `JIRA_PROJECT_ID` | no | — | Default project key. Required via env or `--project`/tool arg if omitted. |
| `JIRA_ISSUE_TYPE` | no | `Task` | Default issue type. |
| `JIRA_ISSUE_LABELS` | no | none | Default labels, comma-separated. |
| `JIRA_ISSUE_PRIORITY` | no | `Medium` | Default priority. |
| `JIRA_ISSUE_EPIC` | no | none | Default epic key to link issues to. |
| `JIRA_EPIC_FIELD` | only if using epics | — | Epic-link custom field id, e.g. `customfield_10014`. |
| `JIRA_TIMEOUT` | no | `10` | HTTP request timeout (seconds). |
| `JIRA_MAX_RESULTS` | no | `50` | Default page size for `search`/`list`. |

`MCP_TRANSPORT`/`MCP_HOST`/`MCP_PORT` only matter when running
`server.py` directly (`make run`); under Docker they're
hardcoded/defaulted in `docker-compose.yaml` and don't need to be set.

Any of these (except `JIRA_TOKEN`/`JIRA_BASE_URL`) can be overridden
per-call via CLI flags or MCP tool arguments.

## Running with Docker

The container joins the external `traefik-net` network and does **not**
publish a port to the host: it's meant to be reached by other containers
on that same network (e.g. the opencode devbox) at
`http://opencode-mcp-jira:8000` (the `container_name`; the service name
`jira-mcp` also resolves as a DNS alias on the same network),
not from the host machine.

```bash
make build   # build the image
make up      # start the server (detached)
make logs    # follow logs
make down    # stop and remove
```

## Running the CLI locally (no Docker)

Requires only a Python 3 interpreter. Reads config from the environment,
falling back to a `.env` file in the current working directory.

```bash
python jira.py create --project PROJ --summary "..." --description "..."
python jira.py get --issue-key PROJ-123
python jira.py update --issue-key PROJ-123 --summary "new summary"
python jira.py comment-add --issue-key PROJ-123 --body "..."
python jira.py comment-list --issue-key PROJ-123
python jira.py comment-update --issue-key PROJ-123 --comment-id 12345 --body "..."
python jira.py comment-delete --issue-key PROJ-123 --comment-id 12345
python jira.py search --summary "login bug"
python jira.py list --status "In Progress"
```

Always prints one line of JSON to stdout; exit code `0` on success, `1`
on failure. See the module docstring in `jira.py` for the full output
contract of each command.

## MCP tools (`server.py`)

- `jira_create_issue`
- `jira_get_issue`
- `jira_update_issue`
- `jira_add_comment`
- `jira_list_comments`
- `jira_update_comment`
- `jira_delete_comment`
- `jira_search_issues`
- `jira_list_issues`

## Running the MCP server locally (no Docker)

```bash
make install   # pip install -r requirements.txt
make run       # python server.py
```
