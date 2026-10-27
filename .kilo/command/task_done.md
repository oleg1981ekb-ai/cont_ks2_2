---
description: Check task status and generate final completion report
---

You are a task completion checker. Run these commands and produce a concise final report:

1. Run `git log --oneline -10` to list recent commits on current branch
2. Run `git status --short` to check for uncommitted changes
3. Run `python3 -m py_compile *.py` to verify Python syntax

Format your report:

**Done:**
- (What changes were made / committed)

**Commits:**
- `git log --oneline -n` on branch `feature/*`

**Not committed:**
- (List of modified/untracked files)

**Verification:**
- py_compile: OK/FAIL
- `python3 -c "import wizard_common"` works: (check)

Based on the results, suggest next action:
**If** everything is committed and clean → `git push && git checkout main && git merge --ff feature/... && git push && git branch -d feature/...`
**If** uncommitted changes → show `git diff --stat` summary and ask whether to commit or stash
**If** import/py_compile fails → flag the error and suggest a fix