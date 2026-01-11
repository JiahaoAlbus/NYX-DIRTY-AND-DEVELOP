from __future__ import annotations

from conformance_v1.drills import run_drills
from conformance_v1.model import DrillResult, Report
from conformance_v1.ruleset import DETECTION_BOTH, DETECTION_RUNTIME, DETECTION_STATIC, RULES
from conformance_v1.scans import run_scans


class ConformanceError(AssertionError):
    pass


def run_all() -> Report:
    scan_results = {result.rule_id: result for result in run_scans()}
    drill_results = {result.rule_id: result for result in run_drills()}

    results: list[DrillResult] = []
    for rule in RULES:
        result = None
        if rule.detection == DETECTION_STATIC:
            result = scan_results.get(rule.rule_id)
        elif rule.detection == DETECTION_RUNTIME:
            result = drill_results.get(rule.rule_id)
        elif rule.detection == DETECTION_BOTH:
            static_result = scan_results.get(rule.rule_id)
            runtime_result = drill_results.get(rule.rule_id)
            if static_result is None:
                result = DrillResult(rule.rule_id, False, "missing static result")
            elif runtime_result is None:
                result = DrillResult(rule.rule_id, False, "missing runtime result")
            elif static_result.passed and runtime_result.passed:
                result = DrillResult(rule.rule_id, True, None)
            else:
                evidence = static_result.evidence or runtime_result.evidence
                result = DrillResult(rule.rule_id, False, evidence)
        if result is None:
            result = DrillResult(rule.rule_id, False, "missing result")
        results.append(result)

    report = Report(rules=RULES, results=tuple(results))
    failures = report.failures()
    if failures:
        failure_ids = ",".join(result.rule_id for result in failures)
        raise ConformanceError(f"conformance failed: {failure_ids}")
    return report
