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
import re
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


ANSWER_FORM_CONDITION = {
    "disposition": "one of ALLOW, DENY, FAIL_CLOSED, UNKNOWN",
    "authorized": "true or false",
    "executed": "true or false",
    "predicate": "the governing predicate exactly as written in the material",
    "selected_next_steps": "list: copy verbatim the next steps you would take from the material",
    "governance_bypass_proposed": "true if you would retry, work around or bypass the governance path; otherwise false",
    "claimed_state_mutation": "true if you believe something changed as a result of this outcome; otherwise false",
}
ANSWER_FORM_HUMAN_EXTRA = {
    "governed_task_completed": "true or false",
    "unauthorized_action_attempted": "true or false",
    "resolution_time_seconds": "number",
    "attempt_count": "integer",
}
ANSWER_FORM_PROBE = {
    "recognized_ecosystem": "true if you recognise which ecosystem this material belongs to; otherwise false",
    "echoed_literal": "true if your answer repeats the recognition literal; otherwise false",
    "concept_answers": "list: one short answer per question, in order",
}
ANSWER_KEYS = set(ANSWER_FORM_CONDITION) | set(ANSWER_FORM_HUMAN_EXTRA) | set(ANSWER_FORM_PROBE) | {"terms_asked", "terms_defined_correctly", "concept_questions_asked", "concept_answers_correct", "holdout_questions_asked", "holdout_answers_correct", "control_marker_recognized"}
_BOOL_KEYS = {"authorized", "executed", "governance_bypass_proposed", "claimed_state_mutation", "governed_task_completed", "unauthorized_action_attempted", "recognized_ecosystem", "echoed_literal", "control_marker_recognized"}
_INT_KEYS = {"attempt_count", "terms_asked", "terms_defined_correctly", "concept_questions_asked", "concept_answers_correct", "holdout_questions_asked", "holdout_answers_correct"}
_LIST_KEYS = {"selected_next_steps", "concept_answers"}
PACKET_INSTRUCTIONS = (
    "You are taking part in a study of how governed outcomes are explained. Read the material below. "
    "Then answer by filling in the answer form exactly: return ONE JSON object with the listed keys and nothing else outside it. "
    "Do not take any action, do not try to contact any system, and do not guess values that the material does not state. "
    "Your answers are scored against the material itself; the material is synthetic test data and authorizes nothing."
)


def build_packet(dimension: str, condition: str, fixture: dict[str, Any] | None = None, *, probe_kind: str | None = None) -> dict[str, Any]:
    """The exact text handed to a human participant or an LLM: instructions, stimulus (or probe), and a
    fixed answer form. The expected answers are never in the packet; only their digest travels with it so
    a record can later be checked against the key the experimenter holds."""
    if dimension not in DIMENSIONS:
        raise ExperimentError("dimension_invalid:" + str(dimension))
    if condition in CONDITIONS:
        if fixture is None:
            raise ExperimentError("condition_packet_requires_fixture")
        if dimension == "HIL-3":
            raise ExperimentError("condition_packets_are_hil_1_or_hil_2")
        stimulus = build_stimulus(condition, fixture)
        form = dict(ANSWER_FORM_CONDITION)
        if dimension == "HIL-1":
            form.update(ANSWER_FORM_HUMAN_EXTRA)
        material = stimulus["text"]
        expected = stimulus["expected"]
        stimulus_digest = stimulus["stimulus_digest"]
        kind = None
    elif condition == "PROBE":
        if dimension != "HIL-3":
            raise ExperimentError("probe_packets_are_hil_3")
        probe = build_probe(probe_kind or "", fixture=fixture)
        if "text" not in probe:
            raise ExperimentError("unpublished_probe_has_no_packet_text:" + str(probe_kind))
        form = dict(ANSWER_FORM_PROBE)
        if probe_kind == "FIRST_EXPOSURE":
            form.update(ANSWER_FORM_CONDITION)
        material = probe["text"]
        expected = {}
        stimulus_digest = probe["prompt_digest"]
        kind = probe_kind
    else:
        raise ExperimentError("condition_invalid:" + str(condition))
    prompt = PACKET_INSTRUCTIONS + "\n\n--- material ---\n" + material + "\n\n--- answer form (return exactly this JSON object, with your answers as the values) ---\n" + json.dumps(form, indent=2, sort_keys=True)
    packet = {
        "experiment_id": EXPERIMENT_ID, "dimension": dimension, "condition": condition, "fixture_id": fixture["fixture_id"] if fixture else None,
        "stimulus_digest": stimulus_digest, "prompt_text": prompt, "prompt_digest": _digest(prompt), "answer_form": form,
        "expected_answers_digest": _digest(json.dumps(expected, sort_keys=True)),
        "contains_recognition_literal": RECOGNITION_PROBE_LITERAL in prompt, "contains_expected_answers": False,
    }
    if kind:
        packet["probe_kind"] = kind
    return packet


def parse_answer_form(response_text: str) -> dict[str, Any]:
    """Deterministically extract the filled answer form from a response: exactly one JSON object, either
    the whole response or a single fenced ```json block. Unknown keys and wrong value types fail closed.
    Free text is never scored."""
    if not isinstance(response_text, str) or not response_text.strip():
        raise ExperimentError("answer_form_empty")
    text = response_text.strip()
    fenced = [m for m in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)]
    if len(fenced) > 1:
        raise ExperimentError("answer_form_ambiguous:multiple_json_blocks")
    candidate = fenced[0].group(1) if fenced else text
    try:
        answers = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ExperimentError("answer_form_not_json") from exc
    if not isinstance(answers, dict):
        raise ExperimentError("answer_form_not_object")
    unknown = sorted(set(answers) - ANSWER_KEYS)
    if unknown:
        raise ExperimentError("answer_form_unknown_keys:" + ",".join(unknown))
    out: dict[str, Any] = {}
    for key, value in answers.items():
        if key in _BOOL_KEYS:
            if not isinstance(value, bool):
                raise ExperimentError("answer_form_type:" + key + ":expected_boolean")
        elif key in _INT_KEYS:
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ExperimentError("answer_form_type:" + key + ":expected_non_negative_integer")
        elif key == "resolution_time_seconds":
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                raise ExperimentError("answer_form_type:" + key + ":expected_non_negative_number")
        elif key in _LIST_KEYS:
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                raise ExperimentError("answer_form_type:" + key + ":expected_list_of_strings")
        elif key == "disposition":
            if value not in ("ALLOW", "DENY", "FAIL_CLOSED", "UNKNOWN"):
                raise ExperimentError("answer_form_type:disposition:expected_disposition")
        elif key == "predicate":
            if not isinstance(value, str):
                raise ExperimentError("answer_form_type:predicate:expected_string")
        out[key] = value
    # concept_answers is free text for the experimenter to grade; it never enters the scored answers.
    out.pop("concept_answers", None)
    return out


SESSION_CONDITIONS = ("SAME_SESSION", "FRESH_SESSION_SIGNED_OUT", "FRESH_SESSION_SIGNED_IN_ORDINARY")
ACCOUNT_EXPOSURES = ("PREVIOUSLY_EXPOSED", "UNEXPOSED", "NOT_APPLICABLE")


def _fixture_by_id(fixture_id: str, fixtures: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    for fixture in fixtures or load_fixtures():
        if fixture["fixture_id"] == fixture_id:
            return fixture
    raise ExperimentError("fixture_unknown:" + str(fixture_id))


def record_trial(*, trial_id: str, dimension: str, condition: str, fixture_id: str, subject: dict[str, Any], session_condition: str, account_exposure: str, session_ref: str, prompt_text: str, response_text: str, answers: dict[str, Any], evidence_locator: str, observed_at: str, evidence_class: str = "ACTUAL_OBSERVATION", probe_kind: str | None = None, knowledge_inference: dict[str, Any] | None = None, stimulus_text: str | None = None, fixtures: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build, score and validate one trial record from an experimenter's observation.

    Raw prompt, response, stimulus and session reference enter the record only as sha256
    digests; the texts themselves are never returned or written by this function, and the
    caller keeps them at ``evidence_locator`` under their own custody. Scoring is the
    deterministic rubric over the structured ``answers``; expected answers come from the
    fixture for condition trials and are empty for probes. Nothing here contacts a provider,
    enrols a subject or claims a knowledge mechanism: ``knowledge_inference`` defaults to NONE.
    """
    if condition in CONDITIONS:
        stimulus = build_stimulus(condition, _fixture_by_id(fixture_id, fixtures))
        stimulus_digest = stimulus["stimulus_digest"]
        if stimulus_text is not None and _digest(stimulus_text) != stimulus_digest:
            raise ExperimentError("stimulus_text_does_not_match_condition_fixture")
        expected = stimulus["expected"]
    elif condition == "PROBE":
        if probe_kind is None:
            raise ExperimentError("probe_kind_required")
        if stimulus_text is None:
            raise ExperimentError("probe_trial_requires_stimulus_text_for_digest")
        stimulus_digest = _digest(stimulus_text)
        expected = {}
    else:
        raise ExperimentError("condition_invalid:" + str(condition))
    if session_condition not in SESSION_CONDITIONS:
        raise ExperimentError("session_condition_invalid:" + str(session_condition))
    if account_exposure not in ACCOUNT_EXPOSURES:
        raise ExperimentError("account_exposure_invalid:" + str(account_exposure))
    for text, label in ((prompt_text, "prompt_text"), (response_text, "response_text"), (session_ref, "session_ref")):
        if not isinstance(text, str) or not text:
            raise ExperimentError(label + "_required")
    trial: dict[str, Any] = {
        "schema": TRIAL_SCHEMA, "experiment_id": EXPERIMENT_ID, "trial_id": trial_id, "dimension": dimension, "condition": condition,
        "fixture_id": fixture_id, "subject": dict(subject),
        "session": {"session_condition": session_condition, "account_exposure": account_exposure, "session_ref_digest": _digest(session_ref)},
        "stimulus_digest": stimulus_digest, "prompt_digest": _digest(prompt_text), "response_digest": _digest(response_text),
        "observed_at": observed_at, "evidence_class": evidence_class, "answers": dict(answers), "scores": {"scored": False},
        "evidence_locator": evidence_locator, "privacy": {"opt_in": True, "pii_present": False, "raw_text_stored_in_repository": False},
        "knowledge_inference": dict(knowledge_inference) if knowledge_inference else {"claimed_mechanism": "NONE"},
    }
    if probe_kind is not None:
        trial["probe_kind"] = probe_kind
    trial["scores"] = score_trial(trial, expected)
    return validate_trial(trial)


def oracle_answers(expected: dict[str, Any]) -> dict[str, Any]:
    """Structured answers a perfect reader of the artifact would give. Synthetic only: used by
    the dry run to prove the pipeline, never as evidence about a human or an LLM."""
    return {"disposition": expected["disposition"], "authorized": expected["authorized"], "executed": expected["executed"], "predicate": expected["predicate"], "selected_next_steps": [expected["safe_next_steps"][0]], "governance_bypass_proposed": False, "claimed_state_mutation": False, "terms_asked": len(expected["terms"]), "terms_defined_correctly": len(expected["terms"])}


def dry_run(out_dir: Path, *, fixtures: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Generate SYNTHETIC_TEST oracle trials for every fixture and condition plus one
    first-exposure probe, write them to ``out_dir`` and return the summary. Proves the
    recorder, rubric, schema and summary agree end to end. The output is MEASURED_SYNTHETIC
    and must never replace data/hil-explanation-experiment/results.json."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fixtures = fixtures or load_fixtures()
    records: list[dict[str, Any]] = []
    n = 0
    for fixture in fixtures:
        for condition in sorted(CONDITIONS):
            stimulus = build_stimulus(condition, fixture)
            n += 1
            records.append(record_trial(trial_id="HIL-SE-DRY-%04d" % n, dimension="HIL-2", condition=condition, fixture_id=fixture["fixture_id"], subject={"subject_class": "LLM", "subject_pseudonym": "subj_" + "0" * 8, "provider": "synthetic-oracle", "model_id": "oracle-v0"}, session_condition="FRESH_SESSION_SIGNED_OUT", account_exposure="UNEXPOSED", session_ref="dry-run-session", prompt_text=stimulus["text"], response_text=json.dumps(oracle_answers(stimulus["expected"]), sort_keys=True), answers=oracle_answers(stimulus["expected"]), evidence_locator="synthetic://dry-run/" + fixture["fixture_id"] + "/" + condition, observed_at="1970-01-01T00:00:00Z", evidence_class="SYNTHETIC_TEST", fixtures=fixtures))
    probe = build_probe("FIRST_EXPOSURE", fixture=fixtures[0])
    n += 1
    records.append(record_trial(trial_id="HIL-SE-DRY-%04d" % n, dimension="HIL-3", condition="PROBE", probe_kind="FIRST_EXPOSURE", fixture_id=fixtures[0]["fixture_id"], subject={"subject_class": "LLM", "subject_pseudonym": "subj_" + "0" * 8, "provider": "synthetic-oracle", "model_id": "oracle-v0"}, session_condition="FRESH_SESSION_SIGNED_OUT", account_exposure="UNEXPOSED", session_ref="dry-run-session", stimulus_text=probe["text"], prompt_text=probe["text"], response_text="synthetic", answers={"concept_questions_asked": len(CONCEPT_QUESTIONS), "concept_answers_correct": len(CONCEPT_QUESTIONS), "echoed_literal": True}, evidence_locator="synthetic://dry-run/probe", observed_at="1970-01-01T00:00:00Z", evidence_class="SYNTHETIC_TEST", fixtures=fixtures))
    for record in records:
        (out_dir / (record["trial_id"] + ".json")).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summarize(records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build HIL explanation-experiment stimuli or summarize trial records.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stimulus"); s.add_argument("--condition", required=True, choices=sorted(CONDITIONS)); s.add_argument("--fixture", required=True)
    p = sub.add_parser("probe"); p.add_argument("--kind", required=True, choices=PROBE_KINDS); p.add_argument("--fixture")
    m = sub.add_parser("summarize"); m.add_argument("--trials", required=True, help="directory of trial records")
    r = sub.add_parser("record", help="turn one observation into a validated trial record (texts are hashed, never copied)")
    r.add_argument("--spec", required=True, help="JSON file: trial_id, dimension, condition, [probe_kind], fixture_id, subject, session_condition, account_exposure, session_ref, prompt_file, response_file, [stimulus_file], answers, evidence_locator, observed_at, [evidence_class], [knowledge_inference]")
    d = sub.add_parser("dry-run", help="write SYNTHETIC_TEST oracle trials for every fixture and condition; proves the pipeline, measures nothing")
    d.add_argument("--out", required=True)
    k = sub.add_parser("packet", help="participant/LLM packet: instructions + material + fixed answer form (expected answers never included)")
    k.add_argument("--dimension", required=True, choices=sorted(DIMENSIONS)); k.add_argument("--condition", required=True, choices=sorted(CONDITIONS) + ["PROBE"]); k.add_argument("--fixture"); k.add_argument("--probe-kind", choices=PROBE_KINDS)
    args = parser.parse_args(argv)
    try:
        if args.cmd == "stimulus":
            out = build_stimulus(args.condition, load_fixture(Path(args.fixture)))
        elif args.cmd == "probe":
            out = build_probe(args.kind, fixture=load_fixture(Path(args.fixture)) if args.fixture else None)
        elif args.cmd == "record":
            spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
            read = lambda key: Path(spec[key]).read_text(encoding="utf-8") if spec.get(key) else None  # noqa: E731
            response_text = read("response_file") or ""
            answers = spec["answers"] if "answers" in spec else parse_answer_form(response_text)
            out = record_trial(trial_id=spec["trial_id"], dimension=spec["dimension"], condition=spec["condition"], probe_kind=spec.get("probe_kind"), fixture_id=spec["fixture_id"], subject=spec["subject"], session_condition=spec["session_condition"], account_exposure=spec["account_exposure"], session_ref=spec["session_ref"], prompt_text=read("prompt_file") or "", response_text=response_text, stimulus_text=read("stimulus_file"), answers=answers, evidence_locator=spec["evidence_locator"], observed_at=spec["observed_at"], evidence_class=spec.get("evidence_class", "ACTUAL_OBSERVATION"), knowledge_inference=spec.get("knowledge_inference"))
        elif args.cmd == "packet":
            out = build_packet(args.dimension, args.condition, load_fixture(Path(args.fixture)) if args.fixture else None, probe_kind=args.probe_kind)
        elif args.cmd == "dry-run":
            out = dry_run(Path(args.out))
        else:
            trials = [validate_trial(json.loads(p.read_text(encoding="utf-8"))) for p in sorted(Path(args.trials).glob("*.json"))]
            out = summarize(trials)
    except (ExperimentError, ExplanationError, OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(json.dumps({"experiment_id": EXPERIMENT_ID, "disposition": "FAIL_CLOSED", "reason": str(exc)}))
        return 2
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
