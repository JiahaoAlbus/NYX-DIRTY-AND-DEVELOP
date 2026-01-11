from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from conformance_v1.model import DrillResult
from conformance_v1.ruleset import DETECTION_STATIC


@dataclass(frozen=True)
class ScanRule:
    rule_id: str
    patterns: tuple[re.Pattern, ...]


def _pattern_list(patterns: list[str]) -> tuple[re.Pattern, ...]:
    return tuple(re.compile(pattern, re.IGNORECASE) for pattern in patterns)


SCAN_RULES: tuple[ScanRule, ...] = (
    ScanRule(
        rule_id="Q1-ID-01",
        patterns=_pattern_list(
            [
                r"\baddress_as_identity\b",
                r"\baccount_as_identity\b",
                r"\bwallet_is_identity\b",
            ]
        ),
    ),
    ScanRule(
        rule_id="Q1-PRIV-01",
        patterns=_pattern_list(
            [
                r"\ballowlist\b",
                r"\bwhitelist\b",
                r"\bbypass\b",
                r"\boverride\b",
                r"\bdebug_free\b",
                r"\bfree_lane\b",
                r"\badmin_key\b",
                r"\bemergency_unlock\b",
            ]
        ),
    ),
    ScanRule(
        rule_id="Q1-PLAT-01",
        patterns=_pattern_list(
            [
                r"\bkyc\b",
                r"\baml\b",
                r"\bcompliance_gateway\b",
                r"\bforced_kyc\b",
                r"\bdeplatform\b",
                r"\bsanction\b",
                r"\bgeo_block\b",
                r"\bgeoblock\b",
                r"\bcensor\b",
                r"\bblocklist\b",
                r"\bblacklist\b",
            ]
        ),
    ),
    ScanRule(
        rule_id="Q1-ANALYTICS-01",
        patterns=_pattern_list([r"acct:[0-9a-fA-F]{64}"]),
    ),
)


def _iter_source_files(root: Path) -> list[Path]:
    packages_dir = root / "packages"
    if not packages_dir.exists():
        return []
    files: list[Path] = []
    for package_dir in packages_dir.iterdir():
        if not package_dir.is_dir():
            continue
        if package_dir.name == "conformance-v1":
            continue
        src_dir = package_dir / "src"
        if not src_dir.exists():
            continue
        for path in src_dir.rglob("*.py"):
            files.append(path)
    return files


def scan_texts(inputs: list[tuple[str, str]], rules: tuple[ScanRule, ...]) -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {rule.rule_id: [] for rule in rules}
    for path, content in inputs:
        for line_no, line in enumerate(content.splitlines(), start=1):
            for rule in rules:
                for pattern in rule.patterns:
                    if pattern.search(line):
                        findings[rule.rule_id].append(
                            f"{path}:{line_no}:{pattern.pattern}"
                        )
    return findings


def run_scans(root: Path | None = None) -> tuple[DrillResult, ...]:
    if root is None:
        root = Path(__file__).resolve().parents[4]
    inputs: list[tuple[str, str]] = []
    for path in _iter_source_files(root):
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        inputs.append((str(path), content))
    findings = scan_texts(inputs, SCAN_RULES)
    results: list[DrillResult] = []
    for rule in SCAN_RULES:
        evidence = findings.get(rule.rule_id, [])
        if evidence:
            results.append(
                DrillResult(rule_id=rule.rule_id, passed=False, evidence=evidence[0])
            )
        else:
            results.append(DrillResult(rule_id=rule.rule_id, passed=True, evidence=None))
    return tuple(results)
