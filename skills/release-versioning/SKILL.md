---
name: release-versioning
description: Manage project versioning and changelogs. Use whenever the user asks to update or create CHANGELOG.md, bump a SemVer version, prepare or commit a release, audit or add version reporting (--version flag, /version endpoint, __version__), or create/update the root VERSION file.
compatibility: Coordinates with `commands/changelog.md` (/changelog) and `commands/versioning.md` (/versioning), and integrates with OpenSpec when present.
metadata:
  version: "1.0"
---

# Skill: release-versioning

Handle repository versioning and release documentation across two workflows:
1. **Changelog & Release Bump** (`commands/changelog.md`) — document changes in `CHANGELOG.md`, compute the SemVer bump, update manifests, and prepare the release commit.
2. **Version Support & `VERSION` File** (`commands/versioning.md`) — audit/implement version reporting in code (`--version`, `/version`, `__version__`) and maintain the root `VERSION` file.

Pick the workflow that matches the user's request, or run both when preparing a full release that also requires version interface/file updates.

## Prerequisites

- A git repository.
- For OpenSpec integration (when auditing/adding version interfaces): the `openspec` CLI if an `openspec/` directory is present.

## Procedure

### Workflow A: Changelog & SemVer Release (`commands/changelog.md`)

1. **Inspect changes**
   - Run `git status` and `git diff` (staged and unstaged) to understand what changed.
   - Use any user-provided scope/summary as context; otherwise infer from the diff.

2. **Update or create `CHANGELOG.md`**
   - Look for `CHANGELOG.md` at the repository root (create it with a standard Keep a Changelog header if missing).
   - Classify entries under [Keep a Changelog](https://keepachangelog.com/) sections: `Added`, `Changed`, `Fixed`, `Deprecated`, `Removed`.

3. **Compute the SemVer bump (`MAJOR.MINOR.PATCH`)**
   - Read the current version from the latest `CHANGELOG.md` entry, `VERSION` file, or project manifest (`package.json`, `pyproject.toml`, `Cargo.toml`, etc.).
   - Apply the highest-priority bump that matches the changes:
     - **MAJOR** — breaking changes, incompatible API changes, removed functionality (`X.0.0`).
     - **MINOR** — new backward-compatible functionality / `Added` (`x.Y.0`).
     - **PATCH** — backward-compatible fixes / `Fixed`, minor `Changed`, `Deprecated` (`x.y.Z`).

4. **Update version references**
   - Add the new heading `## [X.Y.Z] - YYYY-MM-DD` to `CHANGELOG.md`.
   - Update the version field in the project manifest (and `VERSION` file if present).

5. **Confirm and commit**
   - Show the proposed `CHANGELOG.md` diff and computed version bump.
   - Wait for user confirmation in the current turn (unless explicitly told to skip confirmation).
   - Stage the modified files and commit with:
     ```text
     release: vX.Y.Z
     <short summary of changes>
     ```

### Workflow B: Version Reporting & `VERSION` File (`commands/versioning.md`)

1. **Inspect code & project type**
   - Identify the main entry points and classify the project: **CLI/script**, **Web API/service**, **Library/package**, or **Background worker**.

2. **Check for existing version interface**
   - **CLI / Scripts:** `--version` / `-v` flag.
   - **Web Services / APIs:** `/version`, `/health`, or `/info` GET endpoint returning the version.
   - **Libraries / Modules:** `__version__` export or module metadata lookup.

3. **OpenSpec integration (if applicable)**
   - If the repository contains an `openspec/` directory and a new version interface is needed, create or update an OpenSpec change (`openspec new change <id>`), validate with `openspec validate --strict`, and inspect with `openspec show <id>` before or alongside implementing the code change.

4. **Implement version support (if missing)**
   - **CLI:** Add `--version` / `-v` using the standard parser (`argparse`/`click` in Python, `commander`/`yargs` in Node.js, `flag` in Go).
   - **Web API:** Add a lightweight `/version` or `/health` GET endpoint returning JSON (e.g. `{"version": "1.0.0"}`).
   - **Library:** Expose `__version__` or standard package metadata.

5. **Create or update the root `VERSION` file (always)**
   - Resolve the current version in this exact precedence order:
     1. Most recent git tag: `git describe --tags --abbrev=0`.
     2. Version declared in the project manifest (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc.) or `CHANGELOG.md`.
   - Write the version string with a single trailing newline to `VERSION` at the repository root.
   - If neither a git tag nor a manifest version exists, stop and report that no source version was found.

## Rules

- Never invent or guess a version number when creating/updating `VERSION` or computing a bump without a baseline; report if no source version exists.
- Never run `git commit` without showing the proposed changelog/version diff and getting confirmation (unless the user explicitly requested committing right away).
- Never run `git push` unless the user explicitly asks for it in that turn.

## Output

- **Workflow A:** The computed SemVer bump (`old → new`), the `CHANGELOG.md` diff, the list of updated manifest files, and (after confirmation) the commit result.
- **Workflow B:** The detected project type, whether version reporting existed or was added, the OpenSpec validation status (if applicable), and the version written to `VERSION`.
