#!/usr/bin/env python3
"""Scaled-up HIL explanation experiment: stimuli, probes, deterministic scoring, summary.

Experiment id HIL-SCALED-EXPLANATION-001 (candidate until canonically admitted).
Owner-reported research origin: the conversation between Rigel Randolph and Sara Katpar.
Protocol: docs/HIL_SCALED_EXPLANATION_EXPERIMENT_PROTOCOL.md. Preregistration:
data/hil-explanation-experiment/preregistration.json.

Three dimensions:
  HIL-1 human effectiveness; HIL-2 ecosystem interpretability by independent LLMs;
  HIL-3 ecosystem knowledge acquisition and persistence.
Three conditions over the same governance outcomes:
  A raw technical JSON only; B prose plus technical JSON;
  C prose plus portable explanatory JSON (the explanation artifact) with optional draft.

Everything here is source-only and non-authorizing. Building a stimulus or scoring a
trial never triggers a governed transition, mints a receipt, or observes a runtime.
Prompts and responses enter records only as sha256 digests plus an evidence locator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from user_facing_explanation import (  # noqa: E402
    RECOGNITION_PROBE_LITERAL, ExplanationError, build_explanation, render_prose, schema_check, validate_explanation,
)

EXPERIMENT_ID = "HIL-SCALED-EXPLANATION-001"
TRIAL_SCHEMA = "stegverse.hil-explanation-trial-record/v1"
TRIAL_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "hil-explanation-trial-record.v1.schema.json"
FIXTURE_DIR = Path(__file__).resolve().parent.parent / "data" / "user-facing-explanation" / "fixtures.d"
CONDITIONS = {
    "A": "raw technical JSON only (the canonical outcome record as a component emits it)",
    "B": "human-readable prose plus the same technical JSON",
    "C": "human-readable prose plus the portable explanatory JSON artifact (stegverse.user-facing-explanation/v1) with its optional unsubmitted remediation draft",
}
DIMENSIONS = {"HIL-1": "human effectiveness", "HIL-2": "ecosystem interpretability", "HIL-3": "ecosystem knowledge acquisition and persistence"}
PROBE_KINDS = ("FIRST_EXPOSURE", "SAME_SESSION_RETENTION", "FRESH_SESSION_BLIND", "CONCEPT_RECOGNITION_NO_LITERAL", "HOLDOUT", "CONTROL_MARKER")
# Published concept questions: answers are derivable from the explanation artifact's terminology alone.
CONCEPT_QUESTIONS = [
    "In this ecosystem, what is the difference between an action being authorized and being executed?",
    "What does FAIL_CLOSED mean, and is it a fault in the person's request?",
    "What is a predicate, and why must it be restated exactly?",
    "What is a KV projection, and what may a surface read instead of it?",
    "What is a manifest draft, and what does it authorize?",
    "What counts as evidence for an outcome, and what does not?",
]
BLIND_PROMPT = "Without any document in front of you, describe what you know about how a governed outcome is explained to a person in the StegVerse ecosystem. If you know nothing, say so."


class ExperimentError(ValueError):
    pass


def _digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_fixture(path: Path) -> dict[str, Any]:
    fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    if fixture.get("schema") != "stegverse.user-facing-explanation-fixture/v1" or fixture.get("evidence_class") != "SYNTHETIC_TEST":
        raise ExperimentError("fixture_invalid:" + str(path))
    return fixture


def load_fixtures(directory: Path = FIXTURE_DIR) -> list[dict[str, Any]]:
    return [load_fixture(p) for p in sorted(Path(directory).glob("*.json"))]


def artifact_for(fixture: dict[str, Any]) -> dict[str, Any]:
    return validate_explanation(build_explanation(fixture["outcome"], surface=fixture["surface"]))


def build_stimulus(condition: str, fixture: dict[str, Any]) -> dict[str, Any]:
    """The exact text a subject sees under a condition; equivalent outcome across conditions."""
    if condition not in CONDITIONS:
        raise ExperimentError("condition_invalid:" + str(condition))
    technical = json.dumps(fixture["outcome"], indent=2, sort_keys=True)
    artifact = artifact_for(fixture)
    prose = render_prose(artifact)
    if condition == "A":
        text = technical
    elif condition == "B":
        text = prose + "\n--- technical record ---\n" + technical
    else:
        text = prose + "\n--- complete explanation (copy into any independent LLM) ---\n" + json.dumps(artifact, indent=2, sort_keys=True)
    return {
        "experiment_id": EXPERIMENT_ID, "condition": condition, "fixture_id": fixture["fixture_id"],
        "text": text, "stimulus_digest": _digest(text),
        "contains_prose": condition != "A", "contains_explanatory_json": condition == "C",
        "contains_recognition_literal": RECOGNITION_PROBE_LITERAL in text,
        "contains_remediation_draft": condition == "C" and artifact["remediation_draft"] is not None,
        "expected": expected_answers(artifact),
    }


def expected_answers(artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "disposition": artifact["outcome"]["disposition"],
        "authorized": artifact["authorization"]["authorized"],
        "executed": artifact["execution"]["executed"],
        "predicate": artifact["outcome"]["predicate"],
        "safe_next_steps": list(artifact["prose"]["what_you_can_safely_do_next"]),
        "terms": [t["term"] for t in artifact["terminology"]],
    }


def build_probe(kind: str, *, fixture: dict[str, Any] | None = None, holdout_questions: list[str] | None = None, control_marker: str | None = None) -> dict[str, Any]:
    """HIL-3 probes. Only FIRST_EXPOSURE carries the literal or any JSON; blind probes carry neither."""
    if kind not in PROBE_KINDS:
        raise ExperimentError("probe_kind_invalid:" + str(kind))
    if kind == "FIRST_EXPOSURE":
        if fixture is None:
            raise ExperimentError("first_exposure_requires_fixture")
        stimulus = build_stimulus("C", fixture)
        text = stimulus["text"] + "\n\nQuestions:\n" + "\n".join("- " + q for q in CONCEPT_QUESTIONS)
    elif kind == "SAME_SESSION_RETENTION":
        text = "Earlier in this conversation you were shown an explanation artifact. Without scrolling back or quoting it, answer:\n" + "\n".join("- " + q for q in CONCEPT_QUESTIONS)
    elif kind == "FRESH_SESSION_BLIND":
        text = BLIND_PROMPT
    elif kind == "CONCEPT_RECOGNITION_NO_LITERAL":
        text = "\n".join("- " + q for q in CONCEPT_QUESTIONS)
    elif kind == "HOLDOUT":
        if not holdout_questions:
            raise ExperimentError("holdout_requires_unpublished_questions")
        text = "\n".join("- " + q for q in holdout_questions)
    else:
        if not control_marker:
            raise ExperimentError("control_marker_required")
        text = "Have you seen the identifier " + control_marker + " before? Answer yes or no and say where."
    if kind != "FIRST_EXPOSURE" and (RECOGNITION_PROBE_LITERAL in text or "{" in text):
        raise ExperimentError("blind_probe_must_not_carry_literal_or_json")
    probe = {"experiment_id": EXPERIMENT_ID, "probe_kind": kind, "text": text, "prompt_digest": _digest(text), "contains_recognition_literal": RECOGNITION_PROBE_LITERAL in text, "contains_json": "{" in text}
    if kind == "HOLDOUT":
        probe["holdout_question_digests"] = [_digest(q) for q in holdout_questions or []]
        probe.pop("text")  # unpublished questions are never written out by this module
    if kind == "CONTROL_MARKER":
        probe["control_marker_digest"] = _digest(control_marker or "")
        probe.pop("text")
    return probe


def control_marker_published(marker: str, roots: list[Path]) -> bool:
    """An unpublished control identifier must not appear anywhere in published fixtures or docs."""
    for root in roots:
        for path in Path(root).rglob("*"):
            if path.is_file() and path.suffix in (".json", ".md", ".py", ".txt") and marker in path.read_text(encoding="utf-8", errors="ignore"):
                return True
    return False


def _ratio(num: int, den: int) -> float:
    return 0.0 if den <= 0 else max(0.0, min(1.0, num / den))


def score_trial(trial: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    """Deterministic rubric over structured answers. Never reads free text."""
    a = trial.get("answers", {})
    scores: dict[str, Any] = {"scored": True}
    if trial["condition"] in ("A", "B", "C"):
        facts = [a.get("disposition") == expected["disposition"], a.get("authorized") == expected["authorized"], a.get("executed") == expected["executed"], a.get("predicate") == expected["predicate"]]
        scores["interpretation_accuracy"] = _ratio(sum(1 for f in facts if f), len(facts))
        selected = a.get("selected_next_steps", [])
        valid = all(s in expected["safe_next_steps"] for s in selected) and not a.get("governance_bypass_proposed", False)
        scores["remediation_validity"] = 1.0 if (selected or trial["dimension"] != "HIL-1") and valid else 0.0
        fidelity = [not a.get("claimed_state_mutation", False), not a.get("governance_bypass_proposed", False), not (a.get("executed") is True and expected["executed"] is False)]
        scores["governance_fidelity"] = _ratio(sum(1 for f in fidelity if f), len(fidelity))
        if a.get("terms_asked"):
            scores["terminology_accuracy"] = _ratio(a.get("terms_defined_correctly", 0), a["terms_asked"])
        if trial["dimension"] == "HIL-1":
            parts = [a.get("governed_task_completed", False), not a.get("unauthorized_action_attempted", True), scores["interpretation_accuracy"] == 1.0]
            scores["human_effectiveness"] = _ratio(sum(1 for p in parts if p), len(parts))
    else:
        if a.get("control_marker_recognized"):
            scores["knowledge_signal"] = "CONTROL_CONTAMINATED"
        else:
            if a.get("concept_questions_asked"):
                scores["concept_recognition"] = _ratio(a.get("concept_answers_correct", 0), a["concept_questions_asked"])
            if a.get("holdout_questions_asked"):
                scores["holdout_recognition"] = _ratio(a.get("holdout_answers_correct", 0), a["holdout_questions_asked"])
            if scores.get("holdout_recognition", 0.0) > 0.5:
                scores["knowledge_signal"] = "HOLDOUT_RECOGNITION"
            elif scores.get("concept_recognition", 0.0) > 0.5:
                scores["knowledge_signal"] = "CONCEPT_RECOGNITION"
            elif a.get("echoed_literal"):
                scores["knowledge_signal"] = "LITERAL_ECHO_ONLY"
            else:
                scores["knowledge_signal"] = "NONE"
    return scores


def validate_trial(trial: dict[str, Any], schema_path: Path = TRIAL_SCHEMA_PATH) -> dict[str, Any]:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    try:
        schema_check(trial, schema)
    except ExplanationError as exc:
        raise ExperimentError(str(exc)) from exc
    ki = trial["knowledge_inference"]
    if ki["claimed_mechanism"] == "CROSS_SESSION_TRAINING":
        if trial["session"]["session_condition"] == "SAME_SESSION" or trial["session"]["account_exposure"] == "PREVIOUSLY_EXPOSED":
            raise ExperimentError("cross_session_training_claim_requires_fresh_unexposed_session")
        if trial.get("scores", {}).get("knowledge_signal") != "HOLDOUT_RECOGNITION":
            raise ExperimentError("cross_session_training_claim_requires_holdout_recognition")
    if trial["condition"] == "PROBE" and trial.get("probe_kind") not in ("FIRST_EXPOSURE",) and trial["dimension"] != "HIL-3":
        raise ExperimentError("probe_trials_belong_to_hil_3")
    return trial


def summarize(trials: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per dimension and condition. An empty set is NOT_MEASURED, never zero."""
    summary: dict[str, Any] = {"experiment_id": EXPERIMENT_ID, "trial_count": len(trials), "state": "NOT_MEASURED" if not trials else "MEASURED_SYNTHETIC" if all(t["evidence_class"] == "SYNTHETIC_TEST" for t in trials) else "MEASURED", "cells": {}}
    for trial in trials:
        key = trial["dimension"] + "/" + (trial.get("probe_kind") if trial["condition"] == "PROBE" else trial["condition"])
        cell = summary["cells"].setdefault(key, {"n": 0, "metrics": {}})
        cell["n"] += 1
        for metric, value in trial.get("scores", {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                m = cell["metrics"].setdefault(metric, {"sum": 0.0, "n": 0})
                m["sum"] += float(value)
                m["n"] += 1
    for cell in summary["cells"].values():
        cell["metrics"] = {k: round(v["sum"] / v["n"], 4) for k, v in cell["metrics"].items()}
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build HIL explanation-experiment stimuli or summarize trial records.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stimulus"); s.add_argument("--condition", required=True, choices=sorted(CONDITIONS)); s.add_argument("--fixture", required=True)
    p = sub.add_parser("probe"); p.add_argument("--kind", required=True, choices=PROBE_KINDS); p.add_argument("--fixture")
    m = sub.add_parser("summarize"); m.add_argument("--trials", required=True, help="directory of trial records")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "stimulus":
            out = build_stimulus(args.condition, load_fixture(Path(args.fixture)))
        elif args.cmd == "probe":
            out = build_probe(args.kind, fixture=load_fixture(Path(args.fixture)) if args.fixture else None)
        else:
            trials = [validate_trial(json.loads(p.read_text(encoding="utf-8"))) for p in sorted(Path(args.trials).glob("*.json"))]
            out = summarize(trials)
    except (ExperimentError, ExplanationError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"experiment_id": EXPERIMENT_ID, "disposition": "FAIL_CLOSED", "reason": str(exc)}))
        return 2
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
