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
        # At least one selected step is required in every dimension: an empty selection is not a valid
        # remediation (all([]) is vacuously true). "No action" is a valid answer only where the artifact's
        # safe list offers it explicitly as a step, as the verified-success fixture does.
        scores["remediation_validity"] = 1.0 if selected and valid else 0.0
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
    if trial["evidence_class"] == "ACTUAL_OBSERVATION" and trial["response_digest"] not in trial["evidence_locator"]:
        raise ExperimentError("HIL_EVIDENCE_LOCATOR_NOT_BOUND_TO_RESPONSE")
    return trial


def _model_key(trial: dict[str, Any]) -> str | None:
    subject = trial.get("subject", {})
    if subject.get("subject_class") != "LLM":
        return None
    return str(subject.get("provider", "")) + "/" + str(subject.get("model_id", ""))


def _require_ticket_binding(trial: dict[str, Any], tickets_dir: Path | None) -> None:
    """An ACTUAL_OBSERVATION counts only when its ticket exists, is RECORDED (not withdrawn) and
    names this exact record by digest. A copied or hand-made record has no such ticket."""
    if tickets_dir is None:
        raise _refuse("HIL_SUMMARY_TICKETS_REQUIRED_FOR_ACTUAL_OBSERVATIONS")
    path = Path(tickets_dir) / (trial["trial_id"] + ".json")
    ticket = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if ticket.get("schema") != SUBMISSION_TICKET_SCHEMA or ticket.get("trial_id") != trial["trial_id"] or ticket.get("state") != "RECORDED" or ticket.get("record_digest") != _digest(json.dumps(trial, sort_keys=True)):
        raise _refuse("HIL_SUMMARY_RECORD_NOT_BOUND_TO_TICKET", trial["trial_id"])


def summarize(trials: list[dict[str, Any]], *, tickets_dir: Path | None = None) -> dict[str, Any]:
    """Aggregate per dimension and condition. An empty set is NOT_MEASURED, never zero.

    Fails closed when synthetic and actual records are mixed (synthetic oracle scores would
    inflate measurements), when a trial id repeats, or when an ACTUAL_OBSERVATION is not bound to
    its RECORDED ticket in ``tickets_dir``. For LLM cells, ``cross_model_variance`` is the
    population variance across models (provider/model id) of each model's mean
    interpretation_accuracy, and NOT_MEASURED with fewer than two models."""
    classes = {t["evidence_class"] for t in trials}
    if len(classes) > 1:
        raise _refuse("HIL_SUMMARY_MIXES_SYNTHETIC_AND_ACTUAL")
    seen: set[str] = set()
    for trial in trials:
        if trial["trial_id"] in seen:
            raise _refuse("HIL_SUMMARY_DUPLICATE_TRIAL_ID", trial["trial_id"])
        seen.add(trial["trial_id"])
        if trial["evidence_class"] == "ACTUAL_OBSERVATION":
            _require_ticket_binding(trial, tickets_dir)
    summary: dict[str, Any] = {"experiment_id": EXPERIMENT_ID, "trial_count": len(trials), "state": "NOT_MEASURED" if not trials else "MEASURED_SYNTHETIC" if classes == {"SYNTHETIC_TEST"} else "MEASURED", "cells": {}}
    per_model: dict[str, dict[str, list[float]]] = {}
    for trial in trials:
        key = trial["dimension"] + "/" + (trial.get("probe_kind") if trial["condition"] == "PROBE" else trial["condition"])
        cell = summary["cells"].setdefault(key, {"n": 0, "metrics": {}})
        cell["n"] += 1
        for metric, value in trial.get("scores", {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                m = cell["metrics"].setdefault(metric, {"sum": 0.0, "n": 0})
                m["sum"] += float(value)
                m["n"] += 1
        model = _model_key(trial)
        accuracy = trial.get("scores", {}).get("interpretation_accuracy")
        if model is not None and isinstance(accuracy, (int, float)) and not isinstance(accuracy, bool):
            per_model.setdefault(key, {}).setdefault(model, []).append(float(accuracy))
    for key, cell in summary["cells"].items():
        cell["metrics"] = {k: round(v["sum"] / v["n"], 4) for k, v in cell["metrics"].items()}
        models = per_model.get(key, {})
        if models:
            means = [sum(v) / len(v) for v in models.values()]
            mean = sum(means) / len(means)
            cell["models"] = len(means)
            cell["cross_model_variance"] = round(sum((m - mean) ** 2 for m in means) / len(means), 4) if len(means) >= 2 else "NOT_MEASURED"
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


def record_trial(*, trial_id: str, dimension: str, condition: str, fixture_id: str, subject: dict[str, Any], session_condition: str, account_exposure: str, session_ref: str, prompt_text: str, response_text: str, answers: dict[str, Any], evidence_locator: str, observed_at: str, evidence_class: str = "SYNTHETIC_TEST", probe_kind: str | None = None, knowledge_inference: dict[str, Any] | None = None, stimulus_text: str | None = None, fixtures: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build, score and validate one SYNTHETIC_TEST trial record (rubric checks, oracle runs, tests).

    An ACTUAL_OBSERVATION is never produced here: it exists only through ticketed intake
    (``issue_submission`` then ``intake_submission``), which checks the issued ticket, the recorded
    opt-in or provider-use permission, packet consistency, replay and the response-bound evidence
    locator. Asking this function for ACTUAL_OBSERVATION fails closed. Synthetic records carry a
    ``synthetic://`` evidence locator so they can never be mistaken for observations.
    """
    if evidence_class != "SYNTHETIC_TEST":
        raise _refuse("HIL_ACTUAL_OBSERVATION_REQUIRES_TICKETED_INTAKE", str(evidence_class))
    if not isinstance(evidence_locator, str) or not evidence_locator.startswith("synthetic://"):
        raise _refuse("HIL_SYNTHETIC_RECORD_REQUIRES_SYNTHETIC_LOCATOR")
    return _build_trial_record(trial_id=trial_id, dimension=dimension, condition=condition, fixture_id=fixture_id, subject=subject, session_condition=session_condition, account_exposure=account_exposure, session_ref=session_ref, prompt_text=prompt_text, response_text=response_text, answers=answers, evidence_locator=evidence_locator, observed_at=observed_at, evidence_class="SYNTHETIC_TEST", probe_kind=probe_kind, knowledge_inference=knowledge_inference, stimulus_text=stimulus_text, fixtures=fixtures)


def _build_trial_record(*, trial_id: str, dimension: str, condition: str, fixture_id: str, subject: dict[str, Any], session_condition: str, account_exposure: str, session_ref: str, prompt_text: str, response_text: str, answers: dict[str, Any], evidence_locator: str, observed_at: str, evidence_class: str, probe_kind: str | None = None, knowledge_inference: dict[str, Any] | None = None, stimulus_text: str | None = None, fixtures: list[dict[str, Any]] | None = None, ticket: dict[str, Any] | None = None) -> dict[str, Any]:
    """Shared builder. Raw prompt, response, stimulus and session reference enter the record only as
    sha256 digests; the texts are never returned or written, and the caller keeps them at
    ``evidence_locator`` under their own custody. Scoring is the deterministic rubric over the
    structured ``answers``. Nothing here contacts a provider, enrols a subject or claims a
    knowledge mechanism: ``knowledge_inference`` defaults to NONE. An ACTUAL_OBSERVATION requires
    the issued ticket it answers, whose recorded participation is re-checked here."""
    if evidence_class == "ACTUAL_OBSERVATION":
        if not isinstance(ticket, dict) or ticket.get("schema") != SUBMISSION_TICKET_SCHEMA or ticket.get("state") != "ISSUED" or ticket.get("trial_id") != trial_id:
            raise _refuse("HIL_ACTUAL_OBSERVATION_REQUIRES_TICKETED_INTAKE", trial_id)
        if ticket.get("subject") != subject or ticket.get("dimension") != dimension or ticket.get("condition") != condition or ticket.get("packet_prompt_digest") != _digest(prompt_text):
            raise _refuse("HIL_ACTUAL_OBSERVATION_DOES_NOT_MATCH_TICKET", trial_id)
        _check_participation(dimension, subject, ticket.get("consent"))
    elif evidence_class != "SYNTHETIC_TEST" or ticket is not None:
        raise _refuse("HIL_EVIDENCE_CLASS_INVALID", str(evidence_class))
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


SUBMISSION_TICKET_SCHEMA = "stegverse.hil-explanation-submission-ticket/v1"
_SUBJECT_PSEUDONYM_RE = re.compile(r"^subj_[0-9a-f]{8,64}$")
_LOCATOR_RE = re.compile(r"^[a-z][a-z0-9+.-]*://\S+$")
_DIMENSION_SUBJECT = {"HIL-1": "HUMAN", "HIL-2": "LLM", "HIL-3": "LLM"}
# Counts the experimenter grades from free text; a subject's own response may never supply them.
GRADING_KEYS = {"terms_asked", "terms_defined_correctly", "concept_questions_asked", "concept_answers_correct", "holdout_questions_asked", "holdout_answers_correct", "control_marker_recognized"}


def _refuse(predicate: str, detail: str = "") -> ExperimentError:
    return ExperimentError(predicate + (":" + detail if detail else ""))


def _ticket_paths(trials_dir: Path, trial_id: str) -> tuple[Path, Path, Path]:
    root = Path(trials_dir)
    return root / "tickets" / (trial_id + ".json"), root / "packets" / (trial_id + ".txt"), root / "records" / (trial_id + ".json")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _check_participation(dimension: str, subject: dict[str, Any], consent: Any) -> None:
    """HUMAN subjects (HIL-1) need a recorded opt-in; LLM subjects (HIL-2, HIL-3) need provider and
    model id and a recorded provider-use permission. Both reference owner-custody locators."""
    if subject.get("subject_class") != _DIMENSION_SUBJECT.get(dimension):
        raise _refuse("HIL_SUBJECT_CLASS_DIMENSION_MISMATCH", str(dimension) + ":" + str(subject.get("subject_class")))
    if not isinstance(consent, dict):
        raise _refuse("HIL_CONSENT_RECORD_MISSING")
    if subject["subject_class"] == "HUMAN":
        if consent.get("opt_in") is not True or not _LOCATOR_RE.match(str(consent.get("consent_ref", ""))):
            raise _refuse("HIL_SUBJECT_OPT_IN_NOT_RECORDED")
    else:
        if not subject.get("provider") or not subject.get("model_id"):
            raise _refuse("HIL_LLM_PROVIDER_AND_MODEL_REQUIRED")
        if consent.get("provider_use_permitted") is not True or not _LOCATOR_RE.match(str(consent.get("policy_ref", ""))):
            raise _refuse("HIL_PROVIDER_USE_NOT_PERMITTED")


def issue_submission(*, trials_dir: Path, dimension: str, condition: str, subject: dict[str, Any], consent: dict[str, Any], issued_at: str, fixture_id: str | None = None, probe_kind: str | None = None, fixtures: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Issue one trial: a unique trial id, the exact packet text to hand out, and a ticket binding
    the packet digest to the subject and to the owner-held consent (HUMAN) or provider-use
    permission (LLM). Refuses before anything is written when opt-in or permission is not recorded.

    The operator never contacts a provider or a person: the experimenter delivers the packet text
    through the permitted channel and returns the response to ``intake_submission``. Tickets hold
    references and digests only; consent records stay at ``consent_ref`` under the owner's custody."""
    if dimension not in DIMENSIONS:
        raise _refuse("HIL_SUBMISSION_DIMENSION_INVALID", str(dimension))
    if not isinstance(subject, dict) or not _SUBJECT_PSEUDONYM_RE.match(str(subject.get("subject_pseudonym", ""))):
        raise _refuse("HIL_SUBJECT_PSEUDONYM_INVALID")
    if set(subject) - {"subject_class", "subject_pseudonym", "provider", "model_id"}:
        raise _refuse("HIL_SUBJECT_FIELDS_NOT_ALLOWED", ",".join(sorted(set(subject) - {"subject_class", "subject_pseudonym", "provider", "model_id"})))
    _check_participation(dimension, subject, consent)
    if not isinstance(issued_at, str) or len(issued_at) < 20:
        raise _refuse("HIL_SUBMISSION_ISSUED_AT_REQUIRED")
    fixture = _fixture_by_id(fixture_id, fixtures) if fixture_id else None
    packet = build_packet(dimension, condition, fixture, probe_kind=probe_kind)
    seed = "|".join([packet["prompt_digest"], subject["subject_pseudonym"], issued_at])
    trial_id = "HIL-SE-" + dimension.replace("HIL-", "D") + "-" + (probe_kind or condition).replace("_", "-") + "-" + _digest(seed)[7:19].upper()
    ticket_path, packet_path, record_path = _ticket_paths(trials_dir, trial_id)
    if ticket_path.exists() or record_path.exists():
        raise _refuse("HIL_SUBMISSION_DUPLICATE_TRIAL", trial_id)
    ticket = {
        "schema": SUBMISSION_TICKET_SCHEMA, "experiment_id": EXPERIMENT_ID, "trial_id": trial_id, "state": "ISSUED",
        "dimension": dimension, "condition": condition, "fixture_id": packet["fixture_id"], "subject": dict(subject),
        "consent": {k: consent[k] for k in ("opt_in", "consent_ref", "provider_use_permitted", "policy_ref") if k in consent},
        "packet_prompt_digest": packet["prompt_digest"], "stimulus_digest": packet["stimulus_digest"], "expected_answers_digest": packet["expected_answers_digest"],
        "response_template": packet["answer_form"], "issued_at": issued_at, "authority_effect": "NONE",
    }
    if probe_kind:
        ticket["probe_kind"] = probe_kind
    _write_json(ticket_path, ticket)
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(packet["prompt_text"], encoding="utf-8")
    return ticket


def withdraw_submission(*, trials_dir: Path, trial_id: str, withdrawn_at: str) -> dict[str, Any]:
    """Record a subject's withdrawal of consent: the ticket can never be taken in afterwards and an
    already-written record for it is removed (only digests were ever kept)."""
    ticket_path, _packet_path, record_path = _ticket_paths(trials_dir, trial_id)
    if not ticket_path.exists():
        raise _refuse("HIL_SUBMISSION_TICKET_NOT_ISSUED", trial_id)
    ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
    ticket.update({"state": "WITHDRAWN", "withdrawn_at": withdrawn_at})
    ticket.pop("record_digest", None)
    _write_json(ticket_path, ticket)
    if record_path.exists():
        record_path.unlink()
    return ticket


def intake_submission(*, trials_dir: Path, trial_id: str, response_text: str, evidence_locator: str, session_condition: str, account_exposure: str, session_ref: str, observed_at: str, knowledge_inference: dict[str, Any] | None = None, experimenter_grading: dict[str, Any] | None = None, fixtures: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Take in the response to an issued ticket and write one ACTUAL_OBSERVATION trial record.

    Fails closed, writing nothing, when: no ticket was issued; consent was withdrawn; the trial was
    already taken in; there is no response; the evidence locator does not name the stored response
    by its sha256 digest; the same session already answered the same packet (replay); the packet
    regenerated from source no longer matches the issued digest; the answer form does not parse; or
    the response grades itself. Graded counts (terms, concept, holdout, control marker) come only
    from ``experimenter_grading``. The response text itself is hashed, never stored."""
    ticket_path, packet_path, record_path = _ticket_paths(trials_dir, trial_id)
    if not ticket_path.exists():
        raise _refuse("HIL_SUBMISSION_TICKET_NOT_ISSUED", trial_id)
    ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
    if ticket.get("schema") != SUBMISSION_TICKET_SCHEMA or ticket.get("trial_id") != trial_id:
        raise _refuse("HIL_SUBMISSION_TICKET_INVALID", trial_id)
    if ticket.get("state") == "WITHDRAWN":
        raise _refuse("HIL_SUBJECT_CONSENT_WITHDRAWN", trial_id)
    if ticket.get("state") != "ISSUED" or record_path.exists():
        raise _refuse("HIL_SUBMISSION_DUPLICATE_TRIAL", trial_id)
    if not isinstance(response_text, str) or not response_text.strip():
        raise _refuse("HIL_SUBMISSION_NO_RESPONSE", trial_id)
    response_digest = _digest(response_text)
    if not isinstance(evidence_locator, str) or not _LOCATOR_RE.match(evidence_locator) or evidence_locator.startswith("synthetic://"):
        raise _refuse("HIL_EVIDENCE_LOCATOR_INVALID")
    if response_digest not in evidence_locator:
        raise _refuse("HIL_EVIDENCE_LOCATOR_NOT_BOUND_TO_RESPONSE")
    if not isinstance(session_ref, str) or not session_ref:
        raise _refuse("HIL_SUBMISSION_SESSION_REF_REQUIRED")
    session_digest = _digest(session_ref)
    records_dir = record_path.parent
    if records_dir.exists():
        for other in sorted(records_dir.glob("*.json")):
            prior = json.loads(other.read_text(encoding="utf-8"))
            if prior.get("prompt_digest") == ticket["packet_prompt_digest"] and prior.get("session", {}).get("session_ref_digest") == session_digest:
                raise _refuse("HIL_SUBMISSION_REPLAYED_SESSION", prior.get("trial_id", other.stem))
    fixture = _fixture_by_id(ticket["fixture_id"], fixtures) if ticket.get("fixture_id") else None
    packet = build_packet(ticket["dimension"], ticket["condition"], fixture, probe_kind=ticket.get("probe_kind"))
    if packet["prompt_digest"] != ticket["packet_prompt_digest"] or not packet_path.exists() or _digest(packet_path.read_text(encoding="utf-8")) != ticket["packet_prompt_digest"]:
        raise _refuse("HIL_SUBMISSION_PACKET_DRIFT", trial_id)
    answers = parse_answer_form(response_text)
    if GRADING_KEYS & set(answers):
        raise _refuse("HIL_SUBMISSION_SELF_GRADED", ",".join(sorted(GRADING_KEYS & set(answers))))
    if experimenter_grading:
        if set(experimenter_grading) - GRADING_KEYS:
            raise _refuse("HIL_GRADING_KEYS_NOT_ALLOWED", ",".join(sorted(set(experimenter_grading) - GRADING_KEYS)))
        graded = parse_answer_form(json.dumps(experimenter_grading))
        for asked, correct in (("terms_asked", "terms_defined_correctly"), ("concept_questions_asked", "concept_answers_correct"), ("holdout_questions_asked", "holdout_answers_correct")):
            if graded.get(correct, 0) > graded.get(asked, 0):
                raise _refuse("HIL_GRADING_CORRECT_EXCEEDS_ASKED", correct)
        answers.update(graded)
    stimulus_text = build_probe(ticket["probe_kind"], fixture=fixture)["text"] if ticket["condition"] == "PROBE" else None
    record = _build_trial_record(
        ticket=ticket, trial_id=trial_id, dimension=ticket["dimension"], condition=ticket["condition"], probe_kind=ticket.get("probe_kind"), fixture_id=ticket.get("fixture_id") or "NONE",
        subject=ticket["subject"], session_condition=session_condition, account_exposure=account_exposure, session_ref=session_ref,
        prompt_text=packet["prompt_text"], response_text=response_text, stimulus_text=stimulus_text, answers=answers,
        evidence_locator=evidence_locator, observed_at=observed_at, evidence_class="ACTUAL_OBSERVATION", knowledge_inference=knowledge_inference, fixtures=fixtures,
    )
    _write_json(record_path, record)
    ticket.update({"state": "RECORDED", "recorded_at": observed_at, "record_digest": _digest(json.dumps(record, sort_keys=True))})
    _write_json(ticket_path, ticket)
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build HIL explanation-experiment stimuli or summarize trial records.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stimulus"); s.add_argument("--condition", required=True, choices=sorted(CONDITIONS)); s.add_argument("--fixture", required=True)
    p = sub.add_parser("probe"); p.add_argument("--kind", required=True, choices=PROBE_KINDS); p.add_argument("--fixture")
    m = sub.add_parser("summarize"); m.add_argument("--trials", required=True, help="directory of trial records"); m.add_argument("--tickets", help="tickets directory; required when the records are ACTUAL_OBSERVATION")
    r = sub.add_parser("record", help="SYNTHETIC_TEST record only (rubric checks, oracle runs); actual observations go through issue then intake")
    r.add_argument("--spec", required=True, help="JSON file: trial_id, dimension, condition, [probe_kind], fixture_id, subject, session_condition, account_exposure, session_ref, prompt_file, response_file, [stimulus_file], answers, evidence_locator, observed_at, [evidence_class], [knowledge_inference]")
    d = sub.add_parser("dry-run", help="write SYNTHETIC_TEST oracle trials for every fixture and condition; proves the pipeline, measures nothing")
    d.add_argument("--out", required=True)
    k = sub.add_parser("packet", help="participant/LLM packet: instructions + material + fixed answer form (expected answers never included)")
    k.add_argument("--dimension", required=True, choices=sorted(DIMENSIONS)); k.add_argument("--condition", required=True, choices=sorted(CONDITIONS) + ["PROBE"]); k.add_argument("--fixture"); k.add_argument("--probe-kind", choices=PROBE_KINDS)
    i = sub.add_parser("issue", help="issue one trial: unique trial id, packet text and a ticket bound to recorded opt-in (HUMAN) or provider-use permission (LLM)")
    i.add_argument("--trials-dir", required=True); i.add_argument("--dimension", required=True, choices=sorted(DIMENSIONS)); i.add_argument("--condition", required=True, choices=sorted(CONDITIONS) + ["PROBE"])
    i.add_argument("--fixture-id"); i.add_argument("--probe-kind", choices=PROBE_KINDS); i.add_argument("--subject", required=True, help="JSON file: subject_class, subject_pseudonym, [provider], [model_id]"); i.add_argument("--consent", required=True, help="JSON file: HUMAN {opt_in, consent_ref} or LLM {provider_use_permitted, policy_ref}"); i.add_argument("--issued-at", required=True)
    t = sub.add_parser("intake", help="take in the response to an issued ticket and write one ACTUAL_OBSERVATION record (response hashed, never stored)")
    t.add_argument("--trials-dir", required=True); t.add_argument("--trial-id", required=True); t.add_argument("--response-file", required=True); t.add_argument("--evidence-locator", required=True, help="owner-custody locator that names the stored response by its sha256 digest")
    t.add_argument("--session-condition", required=True, choices=SESSION_CONDITIONS); t.add_argument("--account-exposure", required=True, choices=ACCOUNT_EXPOSURES); t.add_argument("--session-ref", required=True); t.add_argument("--observed-at", required=True); t.add_argument("--knowledge-inference", help="JSON file (optional)"); t.add_argument("--grading", help="JSON file (optional): experimenter-graded counts")
    w = sub.add_parser("withdraw", help="record withdrawal of consent for a ticket; its record, if any, is removed")
    w.add_argument("--trials-dir", required=True); w.add_argument("--trial-id", required=True); w.add_argument("--withdrawn-at", required=True)
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
            out = record_trial(trial_id=spec["trial_id"], dimension=spec["dimension"], condition=spec["condition"], probe_kind=spec.get("probe_kind"), fixture_id=spec["fixture_id"], subject=spec["subject"], session_condition=spec["session_condition"], account_exposure=spec["account_exposure"], session_ref=spec["session_ref"], prompt_text=read("prompt_file") or "", response_text=response_text, stimulus_text=read("stimulus_file"), answers=answers, evidence_locator=spec["evidence_locator"], observed_at=spec["observed_at"], evidence_class=spec.get("evidence_class", "SYNTHETIC_TEST"), knowledge_inference=spec.get("knowledge_inference"))
        elif args.cmd == "packet":
            out = build_packet(args.dimension, args.condition, load_fixture(Path(args.fixture)) if args.fixture else None, probe_kind=args.probe_kind)
        elif args.cmd == "issue":
            out = issue_submission(trials_dir=Path(args.trials_dir), dimension=args.dimension, condition=args.condition, fixture_id=args.fixture_id, probe_kind=args.probe_kind, subject=json.loads(Path(args.subject).read_text(encoding="utf-8")), consent=json.loads(Path(args.consent).read_text(encoding="utf-8")), issued_at=args.issued_at)
        elif args.cmd == "intake":
            out = intake_submission(trials_dir=Path(args.trials_dir), trial_id=args.trial_id, response_text=Path(args.response_file).read_text(encoding="utf-8"), evidence_locator=args.evidence_locator, session_condition=args.session_condition, account_exposure=args.account_exposure, session_ref=args.session_ref, observed_at=args.observed_at, knowledge_inference=json.loads(Path(args.knowledge_inference).read_text(encoding="utf-8")) if args.knowledge_inference else None, experimenter_grading=json.loads(Path(args.grading).read_text(encoding="utf-8")) if args.grading else None)
        elif args.cmd == "withdraw":
            out = withdraw_submission(trials_dir=Path(args.trials_dir), trial_id=args.trial_id, withdrawn_at=args.withdrawn_at)
        elif args.cmd == "dry-run":
            out = dry_run(Path(args.out))
        else:
            trials = [validate_trial(json.loads(p.read_text(encoding="utf-8"))) for p in sorted(Path(args.trials).glob("*.json"))]
            out = summarize(trials, tickets_dir=Path(args.tickets) if args.tickets else None)
    except (ExperimentError, ExplanationError, OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(json.dumps({"experiment_id": EXPERIMENT_ID, "disposition": "FAIL_CLOSED", "reason": str(exc)}))
        return 2
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
