from __future__ import annotations

import json

from conformance_v1.model import Report


def report_to_json(report: Report) -> str:
    payload = {
        "rules": [
            {
                "rule_id": rule.rule_id,
                "adversary_class": list(rule.adversary_class),
                "attack_vector": rule.attack_vector,
                "surface": rule.surface,
                "severity": rule.severity,
                "rationale": rule.rationale,
                "detection": rule.detection,
            }
            for rule in report.rules
        ],
        "results": [
            {
                "rule_id": result.rule_id,
                "passed": result.passed,
                "evidence": result.evidence,
            }
            for result in report.results
        ],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
