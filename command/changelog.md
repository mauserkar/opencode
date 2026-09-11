---
description: "Update CHANGELOG.md, bump the semantic version, and commit the release"
---

You are going to document and version the recent changes in this repository. Argument received (optional: change scope/summary, or empty to infer from the diff): $ARGUMENTS

Steps to follow:

1. **Inspect what changed:**
   - Run `git status` and `git diff` (staged and unstaged) to see what was modified.
   - If $ARGUMENTS was provided, use it as context for the scope/intent of the change; otherwise infer the summary from the diff itself.

2. **Locate the changelog:**
   - Check if `CHANGELOG.md` exists in the root directory.
   - **If it exists:** identify the correct section to append to, following [Keep a Changelog](https://keepachangelog.com/) categories (`Added`, `Changed`, `Fixed`, `Deprecated`, `Removed`).
   - **If it does not exist:** create `CHANGELOG.md` with a standard title/header, then document the change.

3. **Determine the version bump (SemVer: MAJOR.MINOR.PATCH):**
   - Read the current version from the latest `CHANGELOG.md` entry, or from a manifest file if present (`package.json`, `pyproject.toml`, `Cargo.toml`, etc.).
   - Classify the change:
     - **MAJOR** — breaking changes, incompatible API changes, removed functionality.
     - **MINOR** — new backward-compatible functionality (`Added`).
     - **PATCH** — backward-compatible fixes (`Fixed`, minor `Changed`, `Deprecated`).
   - If multiple types apply, use the highest-priority bump (MAJOR > MINOR > PATCH).
   - Increment accordingly, resetting lower-order numbers to 0 (e.g. `1.2.3` → `2.0.0`, `1.3.0`, or `1.2.4`).

4. **Update version references:**
   - Add the new version and date as the `CHANGELOG.md` heading (e.g. `## [1.3.0] - 2026-09-10`).
   - Update the version field in the manifest file, if one exists.

5. **Show a summary before committing:**
   - Print the proposed `CHANGELOG.md` diff and the computed version bump.
   - Do not commit yet — wait for confirmation in the same turn unless the user has explicitly asked to skip confirmation.

6. **Commit the changes:**
   - Stage `CHANGELOG.md` and any updated manifest/version files, plus the code changes made in this task.
   - Create a commit with a message following the pattern:
      release: vX.Y.Z
      <short summary of changes>
   - Do not push automatically — leave the push step to the user unless explicitly instructed otherwise.
