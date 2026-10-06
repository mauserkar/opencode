---
name: conventional-commits
description: Analyze git changes and write commit messages that follow the Conventional Commits specification. Use whenever the user asks to commit, write or review a commit message, prepare a release, or inspect staged/unstaged changes before committing, even if they don't mention "Conventional Commits".
metadata:
  version: "1.1"
---

# Skill: conventional-commits

Inspect the workspace changes and propose a standardized commit message.
This skill **proposes** the message; it never commits on its own.

## Prerequisites

- A git repository with at least one modified, added, or deleted file.

## Procedure

1. **Inspect the changes**
   - Run `git status --short` to see what is staged and unstaged.
   - Run `git diff --cached`; if nothing is staged, run `git diff` and tell
     the user the changes are not staged yet.
   - Determine the scope: the component, module, or top-level directory that
     concentrates most of the change. Omit the scope if the change is
     cross-cutting.

2. **Classify the change type**

   | Type       | Use for                                                 | Version bump |
   | ---------- | ------------------------------------------------------- | ------------ |
   | `feat`     | New backward-compatible functionality                   | MINOR        |
   | `fix`      | Backward-compatible bug fix                             | PATCH        |
   | `refactor` | Code change that neither fixes a bug nor adds a feature | none         |
   | `perf`     | Performance improvement                                 | PATCH        |
   | `docs`     | Documentation only                                      | none         |
   | `style`    | Formatting only, no logic change                        | none         |
   | `test`     | Adding or fixing tests                                  | none         |
   | `build`    | Build system or dependency changes                      | none         |
   | `ci`       | CI configuration and scripts                            | none         |
   | `chore`    | Other maintenance that doesn't touch src or tests       | none         |
   | `revert`   | Reverts a previous commit                               | varies       |

   **Breaking changes:** append `!` after the type/scope (`feat(api)!:`) and
   add a footer `BREAKING CHANGE: <what breaks and how to migrate>`. This
   triggers a MAJOR bump.

3. **Write the message**
   - Header format: `<type>(<scope>): <description>`
   - Description: imperative mood, lowercase, no trailing period, header
     at most 72 characters.
   - Add a body only when the *why* is not obvious from the diff; separate
     it from the header with a blank line.
   - Add footers when relevant, e.g. `Refs: PROJ-123` (Jira issue key).
   - If the diff mixes unrelated changes, suggest splitting it into several
     commits and propose one message per commit.

4. **Present and confirm**
   - Show the proposed message to the user.
   - Only run `git commit` if the user explicitly asks for it.

## Rules

- Do not invent a scope, issue key, or breaking-change note that the diff
  does not support.
- Do not run `git add`, `git commit`, or `git push` without explicit
  confirmation.

## Output

The proposed commit message in a code block, plus one line explaining why
that type and scope were chosen.

Example: `feat(auth): add jwt expiration validation`