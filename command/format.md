---
description: "Format Python, Terraform, or Go files using standard language tooling"
---

You are going to format code in the project. Argument received (file, folder, or empty for the whole repo): $ARGUMENTS

Steps to follow:

1. If no argument was passed, assume the target is the current directory (.)

2. Detect which file types are present in the target ($ARGUMENTS or .) by extension:
   - `.py` → Python
   - `.tf`, `.tfvars` → Terraform
   - `.go` → Go

3. For each file type present, run the corresponding formatter using bash:

   **Python:**
   - If `ruff` is available: !ruff format $ARGUMENTS
   - Otherwise, use black: !black $ARGUMENTS
   - Optional, if the project uses isort for imports: !isort $ARGUMENTS

   **Terraform:**
   - !terraform fmt -recursive $ARGUMENTS

   **Go:**
   - !gofmt -w $ARGUMENTS
   - If goimports is available (better, also sorts imports): !goimports -w $ARGUMENTS

4. After formatting, run `git diff --stat` to show a summary of which files changed.

5. If any formatter is not installed, let me know instead of failing silently, and suggest the install command (e.g. `pip install ruff`, `go install golang.org/x/tools/cmd/goimports@latest`).

Don't commit the changes, just format and show me the diff summary.
