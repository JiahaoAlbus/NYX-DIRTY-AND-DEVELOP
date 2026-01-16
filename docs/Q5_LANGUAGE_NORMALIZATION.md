# Q5 Language Normalization

## Purpose
Record the Week 00 language normalization scan and outcomes.

## Scope
- Scan of docs/, packages/, and conformance/ for CJK characters.

## Non-Scope
- Modifying sealed frozen manifests and locked artifacts.

## MUST
- Q5 deliverables MUST be English only.
- Any non-English text in mutable files MUST be translated with no semantic change.

## MUST NOT
- Do not alter sealed frozen manifests or locked artifacts.

## Evidence / Verification
- Scan command: `rg -n "[\p{Han}]" docs packages conformance -S`
- Finding: `conformance/frozen-manifest.sha256` contains a sealed filename entry.

## Freeze & Change Control
- Follow `docs/CHANGE_CONTROL.md`.
