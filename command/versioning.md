---
description: Checks and adds version reporting (argument/flag or API endpoint depending on code type). Integrates with OpenSpec proposals if present.
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
     - Execute or create an `openspec propose` detailing the planned version interface implementation (endpoint or CLI argument) before or alongside making the code change.

4. **Implement Version Support (If Missing):**
   - **For CLI Apps / Scripts:** Add a `--version` / `-v` flag using the standard option parsing library for the language (e.g., `argparse`/`click` in Python, `commander`/`yargs` in Node.js, `flag` in Go).
   - **For Web APIs / HTTP Services:** Add a lightweight `/version` or `/health` GET endpoint returning a JSON payload with the current version string (e.g., `{"version": "1.0.0"}`).
   - Ensure execution returns the current version string cleanly and adheres to standard language conventions.
