---
name: sync-repo
description: Syncs the local repository with the remote and pushes pending commits.
---

# Sync Repository

Current remote status: !`git fetch --dry-run 2>&1`

Pending commits: !`git log origin/main..HEAD --oneline`

Push pending commits to remote: !`git push origin main`

The repository is now synchronized.
