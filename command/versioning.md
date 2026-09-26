---
description: Checks and adds version reporting (argument/flag or API endpoint depending on code type) and creates/updates a VERSION file at the repo root. Integrates with OpenSpec proposals if present.
---

# Command: Add Version Support

When this command is invoked, audit the modified or main entry-point files and ensure they support version checking adapted to the application type.

## Instructions

1. **Inspect Code & Determine Type:**
   - Examine the primary files, entry points, or modules.
   - Determine whether the codebase represents a **CLI script**, a **web API/microservice**, a **library/package**, or a **background worker**.

2. **Check for Existing Version Interface:**
   - **CLI / Scripts:** Look for a `--version` / `-v` flag or argument handler.
   - **Web Services / APIs:** Look for a `/version`, `/health`, or `/info` endpoint returning the service version.
   - **Libraries / Modules:** Look for a `__version__` export, module metadata, or a programmatic version lookup interface.

3. **OpenSpec Integration:**
   - Check if the repository uses **OpenSpec** (e.g., presence of an `openspec` directory, configuration, or schema).
   - If OpenSpec is present:
     - Execute or create an OpenSpec change (`openspec new change <id>`) detailing the planned version interface implementation (endpoint or CLI argument) before or alongside making the code change, then validate it with `openspec validate --strict` and inspect it with `openspec show <id>`.

4. **Implement Version Support (If Missing):**
   - **For CLI Apps / Scripts:** Add a `--version` / `-v` flag using the standard option parsing library for the language (e.g., `argparse`/`click` in Python, `commander`/`yargs` in Node.js, `flag` in Go).
   - **For Web APIs / HTTP Services:** Add a lightweight `/version` or `/health` GET endpoint returning a JSON payload with the current version string (e.g., `{"version": "1.0.0"}`).
   - Ensure execution returns the current version string cleanly and adheres to standard language conventions.

5. **Create/Update the `VERSION` File (Always):**
   - This step runs on every invocation of the command, regardless of the earlier findings and even if version support already exists.
   - Determine the latest version, in this order of precedence:
     1. The most recent git tag: `git describe --tags --abbrev=0`.
     2. The version declared in the project manifest (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc.).
   - Create or overwrite the `VERSION` file at the repository root with exactly the version string and a single trailing newline.
   - Never invent a version: if neither a tag nor a manifest version can be determined, stop and report that no source version was found instead of writing a placeholder.
