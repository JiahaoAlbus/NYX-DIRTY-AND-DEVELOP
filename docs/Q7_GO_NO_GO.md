# Q7 Go / No-Go Checklist

Purpose
- Provide objective release criteria and tag instructions for the Q7 RC.

Scope
- Applies to Q7 deliverables only.

Non-Scope
- Does not alter sealed protocol semantics.

Go Criteria (All MUST be true)
- Canonical tests pass:
  - python -m unittest discover -p "*_test.py" -v
- Evidence export is deterministic for a fixed seed.
- Conformance drills pass with no failures.

No-Go Criteria (Any MUST trigger No-Go)
- Any failing test or conformance drill.
- Missing evidence export artifacts.

Tag Instructions (Do NOT run automatically)
- git tag -a q7-rc1 -m "NYX Q7 RC1"
- git push origin q7-rc1

Freeze and Change Control
- After RC, changes MUST be docs or patch-only with regression evidence.
