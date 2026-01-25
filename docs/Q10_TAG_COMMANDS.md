# Q10 Tag Commands (Maintainer-Executed)

## Purpose
Provide exact, reproducible tag commands for the Q10 Testnet Beta RC.

## Scope
Tag creation only; no code changes.

## Non-Scope
- Mainnet tagging.
- Any force push or history rewrite.

## RC Tag (Testnet Beta)
Execute from a clean, up-to-date main branch after all Q10 PRs are merged:

1) Ensure clean state
- git checkout main
- git pull
- git status

2) Create annotated tag
- git tag -a q10-rc1 -m "NYX Q10 Testnet Beta RC1"

3) Push tag
- git push origin q10-rc1

## Verification
- git show q10-rc1

## Freeze / Change Control
Tagging MUST happen only after Go criteria in Q10 Go/No-Go are satisfied.
