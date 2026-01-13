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
    repro_command: str = ""


@dataclass(frozen=True)
class DrillResult:
    rule_id: str
    passed: bool
    evidence: str | None


@dataclass(frozen=True)
class AttackCard:
    rule_id: str
    adversary_class: tuple[str, ...]
    surface: str
    attack_vector: str
    repro_command: str
    evidence: str | None


@dataclass(frozen=True)
class Report:
    rules: tuple[Rule, ...]
    results: tuple[DrillResult, ...]

    def failures(self) -> tuple[DrillResult, ...]:
        return tuple(result for result in self.results if not result.passed)

    def attack_cards(self) -> tuple[AttackCard, ...]:
        rule_map = {rule.rule_id: rule for rule in self.rules}
        cards: list[AttackCard] = []
        for result in self.failures():
            rule = rule_map.get(result.rule_id)
            if rule is None:
                continue
            cards.append(
                AttackCard(
                    rule_id=rule.rule_id,
                    adversary_class=rule.adversary_class,
                    surface=rule.surface,
                    attack_vector=rule.attack_vector,
                    repro_command=rule.repro_command,
                    evidence=result.evidence,
                )
            )
        return tuple(cards)
