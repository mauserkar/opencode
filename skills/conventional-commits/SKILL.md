---
name: conventional-commits
description: Analyze git diff workspace changes and formulate structured commit messages following the Conventional Commits specification.
metadata:
  opencode/slash: "true"
---

# Skill: Conventional Commits & Scope Inspector

## Trigger
Execute this skill prior to staging commits or during the release packaging phase to inspect workspace modifications (`git diff`) and generate standardized commit headers.

## Instructions

1. **Analyze Diff Scope:**
   - Run `git diff --cached` or `git diff` to evaluate all modified, added, or deleted files.
   - Determine the primary impact area (e.g., component name, module, or file path as scope).

2. **Classify Change Type:**
   Map the primary intent of the modifications to the appropriate prefix:
   - **`feat:`** New backward-compatible functionality (corresponds to a MINOR version bump).
   - **`fix:`** Backward-compatible bug fixes (corresponds to a PATCH version bump).
   - **`refactor:`** Code changes that neither fix a bug nor add a feature.
   - **`docs:`** Documentation-only changes.
   - **`perf:`** Code changes that improve performance.
   - **`chore:`** Maintenance tasks, dependency updates, build processes, or auxiliary tool modifications.
   - *Note:* Append an exclamation mark (`feat!:`, `refactor!:`) if the change introduces breaking alterations (MAJOR version bump).

3. **Construct Commit Message:**
   - Format: `<type>(<scope>): <short description>`
   - Keep the description imperative, concise, and lowercase (e.g., `feat(auth): add JWT expiration validation`).
   - Add an optional body for complex technical context if needed.

4. **Apply and Stage:**
   - Use the generated message for the final commit or provide it to the orchestration agent for verification.