from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    rule_id: str
    adversary_class: tuple[str, ...]
    attack_vector: str
    surface: str
    severity: str
    rationale: str
    detection: str


@dataclass(frozen=True)
class DrillResult:
    rule_id: str
    passed: bool
    evidence: str | None


@dataclass(frozen=True)
class Report:
    rules: tuple[Rule, ...]
    results: tuple[DrillResult, ...]

    def failures(self) -> tuple[DrillResult, ...]:
        return tuple(result for result in self.results if not result.passed)
