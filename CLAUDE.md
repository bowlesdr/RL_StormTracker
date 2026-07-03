# Working in this repo

## Commit/push workflow
- If there are queued-up requests still to work through, don't commit and push after every individual change — keep editing and batch the commit/push for once the queue is clear.
- After running `git commit`, run the `git push` (and any GitHub Pages build-status check/polling) as a background task rather than blocking on it synchronously, so control returns to the user faster.
