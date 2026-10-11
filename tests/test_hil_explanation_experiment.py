"""Scaled-up HIL explanation experiment: stimuli, probes, scoring, trial validation, summary."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import hil_explanation_experiment as H  # noqa: E402

FIX = H.load_fixtures()
DENIED = next(f for f in FIX if f["fixture_id"] == "UFE-FIXTURE-DENIED-001")
D64 = "sha256:" + "0" * 64


def trial(**over):
    base = {
        "schema": H.TRIAL_SCHEMA, "experiment_id": H.EXPERIMENT_ID, "trial_id": "HIL-SE-T-0001", "dimension": "HIL-2", "condition": "C",
        "fixture_id": DENIED["fixture_id"], "subject": {"subject_class": "LLM", "subject_pseudonym": "subj_abcdef12", "provider": "p", "model_id": "m"},
        "session": {"session_condition": "FRESH_SESSION_SIGNED_OUT", "account_exposure": "UNEXPOSED", "session_ref_digest": D64},
        "stimulus_digest": D64, "prompt_digest": D64, "response_digest": D64, "observed_at": "2026-10-11T00:00:00Z", "evidence_class": "SYNTHETIC_TEST",
        "answers": {}, "scores": {"scored": False}, "evidence_locator": "synthetic://trials/0001", "privacy": {"opt_in": True, "pii_present": False, "raw_text_stored_in_repository": False},
        "knowledge_inference": {"claimed_mechanism": "NONE"},
    }
    base.update(over)
    return base


class Stimuli(unittest.TestCase):
    def test_conditions_share_the_outcome_and_differ_only_in_presentation(self):
        for f in FIX:
            a, b, c = (H.build_stimulus(k, f) for k in "ABC")
            self.assertEqual(a["expected"], b["expected"])
            self.assertEqual(b["expected"], c["expected"])
            self.assertFalse(a["contains_prose"] or a["contains_explanatory_json"] or a["contains_recognition_literal"])
            self.assertTrue(b["contains_prose"] and not b["contains_explanatory_json"] and not b["contains_recognition_literal"])
            self.assertTrue(c["contains_prose"] and c["contains_explanatory_json"] and c["contains_recognition_literal"])
            self.assertTrue(a["text"].startswith("{"))
            self.assertTrue(b["text"].startswith("What happened:"))
            for s in (a, b, c):
                self.assertEqual(s["stimulus_digest"], H._digest(s["text"]))
        self.assertTrue(H.build_stimulus("C", DENIED)["contains_remediation_draft"])
        self.assertIn('"submitted": false', H.build_stimulus("C", DENIED)["text"])

    def test_stimuli_are_deterministic(self):
        self.assertEqual(H.build_stimulus("C", DENIED)["stimulus_digest"], H.build_stimulus("C", DENIED)["stimulus_digest"])

    def test_invalid_condition_and_fixture_refused(self):
        with self.assertRaises(H.ExperimentError):
            H.build_stimulus("D", DENIED)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.json"
            p.write_text(json.dumps({"schema": "x", "evidence_class": "ACTUAL_OBSERVATION"}), encoding="utf-8")
            with self.assertRaises(H.ExperimentError):
                H.load_fixture(p)


class Probes(unittest.TestCase):
    def test_only_first_exposure_carries_literal_or_json(self):
        first = H.build_probe("FIRST_EXPOSURE", fixture=DENIED)
        self.assertTrue(first["contains_recognition_literal"] and first["contains_json"])
        for kind in ("SAME_SESSION_RETENTION", "FRESH_SESSION_BLIND", "CONCEPT_RECOGNITION_NO_LITERAL"):
            p = H.build_probe(kind)
            self.assertFalse(p["contains_recognition_literal"] or p["contains_json"], kind)
            self.assertNotIn("STEGVERSE_ECOSYSTEM_KNOWLEDGE_PROBE_V1", p["text"])
        with self.assertRaises(H.ExperimentError):
            H.build_probe("FIRST_EXPOSURE")

    def test_holdout_and_control_marker_are_never_written_out(self):
        h = H.build_probe("HOLDOUT", holdout_questions=["unpublished question one"])
        self.assertNotIn("text", h)
        self.assertEqual(h["holdout_question_digests"], [H._digest("unpublished question one")])
        c = H.build_probe("CONTROL_MARKER", control_marker="CTRL-UNPUBLISHED-ZZZ")
        self.assertNotIn("text", c)
        self.assertEqual(c["control_marker_digest"], H._digest("CTRL-UNPUBLISHED-ZZZ"))
        with self.assertRaises(H.ExperimentError):
            H.build_probe("HOLDOUT")
        with self.assertRaises(H.ExperimentError):
            H.build_probe("CONTROL_MARKER")

    def test_control_marker_leak_detected(self):
        self.assertTrue(H.control_marker_published("STEGVERSE_ECOSYSTEM_KNOWLEDGE_PROBE_V1", [ROOT / "data" / "user-facing-explanation"]))
        self.assertFalse(H.control_marker_published("CTRL-NEVER-PUBLISHED-7f3a9c", [ROOT / "data" / "user-facing-explanation", ROOT / "data" / "hil-explanation-experiment"]))


class Scoring(unittest.TestCase):
    def test_interpretation_remediation_and_fidelity(self):
        exp = H.build_stimulus("C", DENIED)["expected"]
        t = trial(answers={"disposition": "DENY", "authorized": False, "executed": False, "predicate": exp["predicate"], "selected_next_steps": [exp["safe_next_steps"][0]], "governance_bypass_proposed": False, "claimed_state_mutation": False, "terms_asked": 4, "terms_defined_correctly": 3})
        s = H.score_trial(t, exp)
        self.assertEqual((s["interpretation_accuracy"], s["remediation_validity"], s["governance_fidelity"], s["terminology_accuracy"]), (1.0, 1.0, 1.0, 0.75))
        bad = trial(answers={"disposition": "ALLOW", "authorized": True, "executed": True, "predicate": "WRONG", "selected_next_steps": ["retry the request directly against the runtime"], "governance_bypass_proposed": True, "claimed_state_mutation": True})
        s = H.score_trial(bad, exp)
        self.assertEqual((s["interpretation_accuracy"], s["remediation_validity"], s["governance_fidelity"]), (0.0, 0.0, 0.0))

    def test_human_effectiveness(self):
        exp = H.build_stimulus("B", DENIED)["expected"]
        t = trial(dimension="HIL-1", condition="B", subject={"subject_class": "HUMAN", "subject_pseudonym": "subj_00ff00ff"}, answers={"disposition": "DENY", "authorized": False, "executed": False, "predicate": exp["predicate"], "selected_next_steps": [exp["safe_next_steps"][1]], "governed_task_completed": True, "unauthorized_action_attempted": False, "resolution_time_seconds": 42, "attempt_count": 1})
        self.assertEqual(H.score_trial(t, exp)["human_effectiveness"], 1.0)
        t["answers"]["selected_next_steps"] = []
        self.assertEqual(H.score_trial(t, exp)["remediation_validity"], 0.0)

    def test_knowledge_signal_ladder(self):
        base = dict(dimension="HIL-3", condition="PROBE", probe_kind="FRESH_SESSION_BLIND")
        self.assertEqual(H.score_trial(trial(answers={"echoed_literal": True}, **base), {})["knowledge_signal"], "LITERAL_ECHO_ONLY")
        self.assertEqual(H.score_trial(trial(answers={"concept_questions_asked": 6, "concept_answers_correct": 5}, **base), {})["knowledge_signal"], "CONCEPT_RECOGNITION")
        self.assertEqual(H.score_trial(trial(answers={"holdout_questions_asked": 4, "holdout_answers_correct": 3}, **base), {})["knowledge_signal"], "HOLDOUT_RECOGNITION")
        self.assertEqual(H.score_trial(trial(answers={"holdout_questions_asked": 4, "holdout_answers_correct": 4, "control_marker_recognized": True}, **base), {})["knowledge_signal"], "CONTROL_CONTAMINATED")
        self.assertEqual(H.score_trial(trial(answers={}, **base), {})["knowledge_signal"], "NONE")


class TrialValidation(unittest.TestCase):
    def test_valid_trial_and_schema_refusals(self):
        H.validate_trial(trial())
        for over, code in (
            (dict(privacy={"opt_in": False, "pii_present": False, "raw_text_stored_in_repository": False}), "schema:const:$.privacy.opt_in"),
            (dict(subject={"subject_class": "LLM", "subject_pseudonym": "Jane Doe"}), "schema:pattern:$.subject.subject_pseudonym"),
            (dict(condition="PROBE"), "schema:required:$.probe_kind"),
            (dict(raw_prompt="text"), "schema:additionalProperties:$.raw_prompt"),
        ):
            with self.assertRaises(H.ExperimentError) as ctx:
                H.validate_trial(trial(**over))
            self.assertTrue(str(ctx.exception).startswith(code), str(ctx.exception))

    def test_cross_session_training_claim_requires_discrimination_evidence(self):
        probe = dict(dimension="HIL-3", condition="PROBE", probe_kind="HOLDOUT", scores={"scored": True, "holdout_recognition": 0.75, "knowledge_signal": "HOLDOUT_RECOGNITION"}, answers={"holdout_questions_asked": 4, "holdout_answers_correct": 3})
        with self.assertRaises(H.ExperimentError) as ctx:
            H.validate_trial(trial(knowledge_inference={"claimed_mechanism": "CROSS_SESSION_TRAINING"}, **probe))
        self.assertIn("mechanism_discrimination_evidence", str(ctx.exception))
        evidence = {"public_retrieval_ruled_out": "fixture://e1", "account_memory_ruled_out": "fixture://e2", "session_carryover_ruled_out": "fixture://e3", "pre_existing_knowledge_ruled_out": "fixture://e4"}
        H.validate_trial(trial(knowledge_inference={"claimed_mechanism": "CROSS_SESSION_TRAINING", "mechanism_discrimination_evidence": evidence}, **probe))
        with self.assertRaises(H.ExperimentError):
            H.validate_trial(trial(knowledge_inference={"claimed_mechanism": "CROSS_SESSION_TRAINING", "mechanism_discrimination_evidence": evidence}, session={"session_condition": "SAME_SESSION", "account_exposure": "NOT_APPLICABLE", "session_ref_digest": D64}, **probe))
        with self.assertRaises(H.ExperimentError):
            H.validate_trial(trial(knowledge_inference={"claimed_mechanism": "CROSS_SESSION_TRAINING", "mechanism_discrimination_evidence": evidence}, **dict(probe, scores={"scored": True, "knowledge_signal": "LITERAL_ECHO_ONLY"})))

    def test_summary_is_not_measured_when_empty(self):
        self.assertEqual(H.summarize([])["state"], "NOT_MEASURED")
        committed = json.loads((ROOT / "data" / "hil-explanation-experiment" / "results.json").read_text(encoding="utf-8"))
        self.assertEqual((committed["state"], committed["trial_count"]), ("NOT_MEASURED", 0))
        t = trial(scores={"scored": True, "interpretation_accuracy": 0.5, "governance_fidelity": 1.0})
        s = H.summarize([t, trial(trial_id="HIL-SE-T-0002", scores={"scored": True, "interpretation_accuracy": 1.0})])
        self.assertEqual(s["state"], "MEASURED_SYNTHETIC")
        self.assertEqual(s["cells"]["HIL-2/C"], {"n": 2, "metrics": {"interpretation_accuracy": 0.75, "governance_fidelity": 1.0}, "models": 1, "cross_model_variance": "NOT_MEASURED"})

    def test_preregistration_matches_source(self):
        pre = json.loads((ROOT / "data" / "hil-explanation-experiment" / "preregistration.json").read_text(encoding="utf-8"))
        self.assertEqual(pre["experiment_id"], H.EXPERIMENT_ID)
        self.assertEqual(set(pre["conditions"]) - {"equivalence"}, set(H.CONDITIONS))
        self.assertEqual(set(pre["dimensions"]), set(H.DIMENSIONS))
        self.assertEqual(sorted(pre["fixtures"]), sorted(f["fixture_id"] for f in FIX))
        self.assertEqual(pre["probes"]["recognition_literal"]["value"], H.RECOGNITION_PROBE_LITERAL)
        self.assertIn("Rigel Randolph and Sara Katpar", pre["research_origin"]["statement"])


class SchemaOnlyConsumers(unittest.TestCase):
    """Same class of repair as the explanation schema (#3106 finding EXPLANATION_SCHEMA_CROSS_FIELD_CONSISTENCY):
    a consumer validating trial records only against the JSON Schema must reject contradictory records."""

    SCHEMA = json.loads((ROOT / "schemas" / "hil-explanation-trial-record.v1.schema.json").read_text(encoding="utf-8"))
    EVIDENCE = {k: "fixture://e" for k in ("public_retrieval_ruled_out", "account_memory_ruled_out", "session_carryover_ruled_out", "pre_existing_knowledge_ruled_out")}

    def probe(self, **over):
        base = trial(dimension="HIL-3", condition="PROBE", probe_kind="HOLDOUT", scores={"scored": True, "holdout_recognition": 0.75, "knowledge_signal": "HOLDOUT_RECOGNITION"}, answers={"holdout_questions_asked": 4, "holdout_answers_correct": 3})
        base.update(over)
        return base

    def mutations(self):
        cst = {"claimed_mechanism": "CROSS_SESSION_TRAINING", "mechanism_discrimination_evidence": self.EVIDENCE}
        return {
            "cross_session_in_same_session": self.probe(knowledge_inference=cst, session={"session_condition": "SAME_SESSION", "account_exposure": "NOT_APPLICABLE", "session_ref_digest": D64}),
            "cross_session_exposed_account": self.probe(knowledge_inference=cst, session={"session_condition": "FRESH_SESSION_SIGNED_OUT", "account_exposure": "PREVIOUSLY_EXPOSED", "session_ref_digest": D64}),
            "cross_session_literal_echo_only": self.probe(knowledge_inference=cst, scores={"scored": True, "knowledge_signal": "LITERAL_ECHO_ONLY"}, answers={"echoed_literal": True}),
            "cross_session_without_evidence": self.probe(knowledge_inference={"claimed_mechanism": "CROSS_SESSION_TRAINING"}),
            "cross_session_on_condition_trial": trial(knowledge_inference=cst),
            "blind_probe_in_hil_1": self.probe(dimension="HIL-1", subject={"subject_class": "HUMAN", "subject_pseudonym": "subj_00ff00ff"}),
            "probe_without_probe_kind": {k: v for k, v in self.probe().items() if k != "probe_kind"},
            "condition_trial_with_probe_kind": trial(probe_kind="HOLDOUT"),
            "knowledge_signal_on_condition_trial": trial(scores={"scored": True, "knowledge_signal": "HOLDOUT_RECOGNITION"}),
            "interpretation_metric_on_probe": self.probe(scores={"scored": True, "knowledge_signal": "NONE", "interpretation_accuracy": 1.0}),
            "unscored_with_scores": trial(scores={"scored": False, "interpretation_accuracy": 1.0}),
            "holdout_signal_without_holdout_questions": self.probe(answers={"holdout_questions_asked": 0}),
            "concept_signal_without_concept_questions": self.probe(scores={"scored": True, "knowledge_signal": "CONCEPT_RECOGNITION"}, answers={}),
            "contaminated_without_marker_recognised": self.probe(scores={"scored": True, "knowledge_signal": "CONTROL_CONTAMINATED"}, answers={"control_marker_recognized": False}),
            "llm_subject_in_hil_1": trial(dimension="HIL-1", condition="B"),
            "human_subject_in_hil_2": trial(subject={"subject_class": "HUMAN", "subject_pseudonym": "subj_00ff00ff"}),
            "llm_without_model_id": trial(subject={"subject_class": "LLM", "subject_pseudonym": "subj_abcdef12", "provider": "p"}),
        }

    def valid_records(self):
        return [trial(), self.probe(), self.probe(knowledge_inference={"claimed_mechanism": "CROSS_SESSION_TRAINING", "mechanism_discrimination_evidence": self.EVIDENCE}), trial(dimension="HIL-1", condition="B", subject={"subject_class": "HUMAN", "subject_pseudonym": "subj_00ff00ff"})]

    def test_schema_check_rejects_contradictory_trials(self):
        for name, inst in self.mutations().items():
            with self.assertRaises(H.ExperimentError, msg=name):
                H.validate_trial(inst)
        for inst in self.valid_records():
            H.validate_trial(inst)

    def test_jsonschema_rejects_contradictory_trials(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:  # pragma: no cover
            self.skipTest("jsonschema not installed")
        validator = Draft202012Validator(self.SCHEMA)
        for name, inst in self.mutations().items():
            self.assertFalse(validator.is_valid(inst), name)
        for inst in self.valid_records():
            self.assertTrue(validator.is_valid(inst))


class TrialRecorder(unittest.TestCase):
    """Experimenter tooling: observations become validated, privacy-preserving records; the dry
    run proves recorder, rubric, schema and summary agree without measuring anything real."""

    SUBJECT = {"subject_class": "LLM", "subject_pseudonym": "subj_feedbeef", "provider": "p", "model_id": "m"}

    def record(self, **over):
        stim = H.build_stimulus("C", DENIED)
        kw = dict(trial_id="HIL-SE-R-0001", dimension="HIL-2", condition="C", fixture_id=DENIED["fixture_id"], subject=self.SUBJECT, session_condition="FRESH_SESSION_SIGNED_OUT", account_exposure="UNEXPOSED", session_ref="session-ref-secret", prompt_text=stim["text"], response_text="the response text", answers=H.oracle_answers(stim["expected"]), evidence_locator="synthetic://trials/0001", observed_at="2026-10-11T18:50:00Z")
        kw.update(over)
        return H.record_trial(**kw)

    def test_record_is_valid_scored_and_free_of_raw_text(self):
        stim = H.build_stimulus("C", DENIED)
        rec = self.record()
        H.validate_trial(rec)
        self.assertEqual(rec["stimulus_digest"], stim["stimulus_digest"])
        self.assertEqual(rec["prompt_digest"], H._digest(stim["text"]))
        self.assertEqual(rec["response_digest"], H._digest("the response text"))
        self.assertEqual(rec["session"]["session_ref_digest"], H._digest("session-ref-secret"))
        flat = json.dumps(rec)
        for raw in ("the response text", "session-ref-secret", "What happened:"):
            self.assertNotIn(raw, flat)
        self.assertEqual(rec["scores"]["interpretation_accuracy"], 1.0)
        self.assertEqual(rec["knowledge_inference"], {"claimed_mechanism": "NONE"})
        self.assertEqual(rec["evidence_class"], "SYNTHETIC_TEST")
        self.assertFalse(rec["privacy"]["raw_text_stored_in_repository"])

    def test_recorder_refusals(self):
        with self.assertRaises(H.ExperimentError):
            self.record(stimulus_text="not the condition C stimulus")
        with self.assertRaises(H.ExperimentError):
            self.record(condition="PROBE", dimension="HIL-3")  # no probe_kind
        with self.assertRaises(H.ExperimentError):
            self.record(condition="PROBE", dimension="HIL-3", probe_kind="FRESH_SESSION_BLIND")  # no stimulus text to digest
        with self.assertRaises(H.ExperimentError):
            self.record(session_condition="LOGGED_IN")
        with self.assertRaises(H.ExperimentError):
            self.record(account_exposure="MAYBE")
        with self.assertRaises(H.ExperimentError):
            self.record(response_text="")
        with self.assertRaises(H.ExperimentError):
            self.record(fixture_id="UFE-FIXTURE-DOES-NOT-EXIST")
        with self.assertRaises(H.ExperimentError):
            self.record(dimension="HIL-1")  # LLM subject in the human dimension
        with self.assertRaises(H.ExperimentError):  # a cross-session claim needs the fresh-session holdout evidence
            self.record(knowledge_inference={"claimed_mechanism": "CROSS_SESSION_TRAINING"})

    def test_probe_record(self):
        probe = H.build_probe("FRESH_SESSION_BLIND")
        rec = self.record(dimension="HIL-3", condition="PROBE", probe_kind="FRESH_SESSION_BLIND", stimulus_text=probe["text"], prompt_text=probe["text"], answers={"echoed_literal": False, "concept_questions_asked": 0})
        self.assertEqual(rec["scores"]["knowledge_signal"], "NONE")
        self.assertEqual(rec["stimulus_digest"], probe["prompt_digest"])

    def test_dry_run_is_synthetic_and_leaves_results_untouched(self):
        before = (ROOT / "data" / "hil-explanation-experiment" / "results.json").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as d:
            summary = H.dry_run(Path(d))
            files = sorted(Path(d).glob("*.json"))
            self.assertEqual(len(files), 3 * len(FIX) + 1)
            for f in files:
                rec = json.loads(f.read_text(encoding="utf-8"))
                H.validate_trial(rec)
                self.assertEqual(rec["evidence_class"], "SYNTHETIC_TEST")
                self.assertNotIn("What happened:", f.read_text(encoding="utf-8"))
        self.assertEqual(summary["state"], "MEASURED_SYNTHETIC")
        self.assertEqual(summary["trial_count"], 3 * len(FIX) + 1)
        for cond in "ABC":
            self.assertEqual(summary["cells"]["HIL-2/" + cond]["metrics"]["interpretation_accuracy"], 1.0)
        self.assertEqual(summary["cells"]["HIL-3/FIRST_EXPOSURE"]["n"], 1)
        self.assertEqual((ROOT / "data" / "hil-explanation-experiment" / "results.json").read_text(encoding="utf-8"), before)
        self.assertEqual(json.loads(before)["state"], "NOT_MEASURED")

    def test_cli_record_and_dry_run(self):
        import subprocess, sys as _sys
        stim = H.build_stimulus("A", DENIED)
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "prompt.txt").write_text(stim["text"], encoding="utf-8")
            (d / "response.txt").write_text("response", encoding="utf-8")
            spec = {"trial_id": "HIL-SE-CLI-0001", "dimension": "HIL-2", "condition": "A", "fixture_id": DENIED["fixture_id"], "subject": self.SUBJECT, "session_condition": "FRESH_SESSION_SIGNED_IN_ORDINARY", "account_exposure": "UNEXPOSED", "session_ref": "s", "prompt_file": str(d / "prompt.txt"), "response_file": str(d / "response.txt"), "answers": H.oracle_answers(stim["expected"]), "evidence_locator": "synthetic://x", "observed_at": "2026-10-11T18:50:00Z"}
            (d / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
            out = subprocess.run([_sys.executable, "scripts/hil_explanation_experiment.py", "record", "--spec", str(d / "spec.json")], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
            rec = json.loads(out.stdout)
            self.assertEqual(rec["scores"]["interpretation_accuracy"], 1.0)
            self.assertNotIn("response", rec["response_digest"])
            out = subprocess.run([_sys.executable, "scripts/hil_explanation_experiment.py", "dry-run", "--out", str(d / "dry")], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(json.loads(out.stdout)["state"], "MEASURED_SYNTHETIC")
            spec["condition"] = "PROBE"
            (d / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
            out = subprocess.run([_sys.executable, "scripts/hil_explanation_experiment.py", "record", "--spec", str(d / "spec.json")], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(out.returncode, 2)
            self.assertEqual(json.loads(out.stdout)["disposition"], "FAIL_CLOSED")


class PacketsAndAnswerForm(unittest.TestCase):
    """Participant/LLM packets carry instructions, the material and a fixed answer form, never the expected
    answers; the parser turns a response into the structured answers the rubric scores, failing closed on
    anything ambiguous, unknown or mistyped."""

    def test_condition_packets(self):
        for dim, extra in (("HIL-2", set()), ("HIL-1", set(H.ANSWER_FORM_HUMAN_EXTRA))):
            for cond in "ABC":
                p = H.build_packet(dim, cond, DENIED)
                self.assertEqual(set(p["answer_form"]), set(H.ANSWER_FORM_CONDITION) | extra)
                self.assertEqual(p["stimulus_digest"], H.build_stimulus(cond, DENIED)["stimulus_digest"])
                self.assertEqual(p["prompt_digest"], H._digest(p["prompt_text"]))
                self.assertFalse(p["contains_expected_answers"])
                self.assertEqual(p["contains_recognition_literal"], cond == "C")
                self.assertIn(H.PACKET_INSTRUCTIONS, p["prompt_text"])
                self.assertIn(H.build_stimulus(cond, DENIED)["text"], p["prompt_text"])
                self.assertNotIn("expected", p["prompt_text"].lower().replace("expected answers", ""))
        with self.assertRaises(H.ExperimentError):
            H.build_packet("HIL-3", "C", DENIED)
        with self.assertRaises(H.ExperimentError):
            H.build_packet("HIL-2", "C")
        with self.assertRaises(H.ExperimentError):
            H.build_packet("HIL-9", "C", DENIED)

    def test_probe_packets(self):
        blind = H.build_packet("HIL-3", "PROBE", probe_kind="FRESH_SESSION_BLIND")
        self.assertEqual(set(blind["answer_form"]), set(H.ANSWER_FORM_PROBE))
        self.assertFalse(blind["contains_recognition_literal"])
        self.assertNotIn("{", blind["prompt_text"].split("--- answer form")[0].split("--- material ---")[1])
        first = H.build_packet("HIL-3", "PROBE", DENIED, probe_kind="FIRST_EXPOSURE")
        self.assertTrue(first["contains_recognition_literal"])
        self.assertEqual(set(first["answer_form"]), set(H.ANSWER_FORM_PROBE) | set(H.ANSWER_FORM_CONDITION))
        with self.assertRaises(H.ExperimentError):
            H.build_packet("HIL-2", "PROBE", probe_kind="FRESH_SESSION_BLIND")
        with self.assertRaises(H.ExperimentError):  # unpublished material never becomes packet text
            H.build_packet("HIL-3", "PROBE", probe_kind="HOLDOUT")

    def test_parse_answer_form_and_score(self):
        exp = H.build_stimulus("C", DENIED)["expected"]
        body = {"disposition": "DENY", "authorized": False, "executed": False, "predicate": exp["predicate"], "selected_next_steps": [exp["safe_next_steps"][0]], "governance_bypass_proposed": False, "claimed_state_mutation": False}
        for text in (json.dumps(body), "Answer:\n```json\n" + json.dumps(body) + "\n```\nDone.", "```\n" + json.dumps(body) + "\n```"):
            answers = H.parse_answer_form(text)
            self.assertEqual(answers, body)
        rec = H.record_trial(trial_id="HIL-SE-PK-0001", dimension="HIL-2", condition="C", fixture_id=DENIED["fixture_id"], subject={"subject_class": "LLM", "subject_pseudonym": "subj_00000001", "provider": "p", "model_id": "m"}, session_condition="FRESH_SESSION_SIGNED_OUT", account_exposure="UNEXPOSED", session_ref="s", prompt_text=H.build_packet("HIL-2", "C", DENIED)["prompt_text"], response_text=json.dumps(body), answers=H.parse_answer_form(json.dumps(body)), evidence_locator="synthetic://x", observed_at="2026-10-11T20:00:00Z")
        self.assertEqual(rec["scores"]["interpretation_accuracy"], 1.0)
        probe = H.parse_answer_form(json.dumps({"recognized_ecosystem": False, "echoed_literal": False, "concept_answers": ["I do not know"]}))
        self.assertEqual(probe, {"recognized_ecosystem": False, "echoed_literal": False})

    def test_parse_answer_form_refusals(self):
        for text, code in (("", "answer_form_empty"), ("no json", "answer_form_not_json"), ("[1]", "answer_form_not_object"), ('{"disposition":"MAYBE"}', "answer_form_type:disposition"), ('{"authorized":"yes"}', "answer_form_type:authorized"), ('{"attempt_count":-1}', "answer_form_type:attempt_count"), ('{"attempt_count":true}', "answer_form_type:attempt_count"), ('{"selected_next_steps":"x"}', "answer_form_type:selected_next_steps"), ('{"secret_note":1}', "answer_form_unknown_keys:secret_note"), ("```json\n{}\n```\n```json\n{}\n```", "answer_form_ambiguous")):
            with self.assertRaises(H.ExperimentError) as ctx:
                H.parse_answer_form(text)
            self.assertTrue(str(ctx.exception).startswith(code), (text, str(ctx.exception)))

    def test_cli_packet_and_record_autoparse(self):
        import subprocess, sys as _sys
        fixture_path = sorted((ROOT / "data" / "user-facing-explanation" / "fixtures.d").glob("02-*.json"))[0]
        out = subprocess.run([_sys.executable, "scripts/hil_explanation_experiment.py", "packet", "--dimension", "HIL-1", "--condition", "B", "--fixture", str(fixture_path)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        packet = json.loads(out.stdout)
        self.assertIn("resolution_time_seconds", packet["answer_form"])
        exp = H.build_stimulus("B", DENIED)["expected"]
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "prompt.txt").write_text(packet["prompt_text"], encoding="utf-8")
            (d / "response.txt").write_text("```json\n" + json.dumps({"disposition": "DENY", "authorized": False, "executed": False, "predicate": exp["predicate"], "selected_next_steps": [exp["safe_next_steps"][1]], "governance_bypass_proposed": False, "claimed_state_mutation": False, "governed_task_completed": True, "unauthorized_action_attempted": False, "resolution_time_seconds": 75.5, "attempt_count": 1}) + "\n```", encoding="utf-8")
            spec = {"trial_id": "HIL-SE-CLI-0002", "dimension": "HIL-1", "condition": "B", "fixture_id": DENIED["fixture_id"], "subject": {"subject_class": "HUMAN", "subject_pseudonym": "subj_00ff00ff"}, "session_condition": "FRESH_SESSION_SIGNED_OUT", "account_exposure": "NOT_APPLICABLE", "session_ref": "s", "prompt_file": str(d / "prompt.txt"), "response_file": str(d / "response.txt"), "evidence_locator": "synthetic://x", "observed_at": "2026-10-11T20:00:00Z"}
            (d / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
            out = subprocess.run([_sys.executable, "scripts/hil_explanation_experiment.py", "record", "--spec", str(d / "spec.json")], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
            rec = json.loads(out.stdout)
            self.assertEqual(rec["scores"]["human_effectiveness"], 1.0)
            self.assertEqual(rec["answers"]["resolution_time_seconds"], 75.5)
            (d / "response.txt").write_text("I think it was allowed.", encoding="utf-8")
            out = subprocess.run([_sys.executable, "scripts/hil_explanation_experiment.py", "record", "--spec", str(d / "spec.json")], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(out.returncode, 2)
            self.assertIn("answer_form_not_json", json.loads(out.stdout)["reason"])


if __name__ == "__main__":
    unittest.main()


class RemediationScoringEmptySelection(unittest.TestCase):
    """#3106 comment 6113446433: an empty selection was scored 1.0 outside HIL-1 because all([]) is true."""

    def setUp(self):
        self.exp = H.build_stimulus("C", DENIED)["expected"]

    def _score(self, dimension, condition, steps, bypass=False):
        subject = {"subject_class": "HUMAN", "subject_pseudonym": "subj_00ff00ff"} if dimension == "HIL-1" else {"subject_class": "LLM", "subject_pseudonym": "subj_abcdef12", "provider": "p", "model_id": "m"}
        answers = {"disposition": "DENY", "authorized": False, "executed": False, "predicate": self.exp["predicate"], "selected_next_steps": steps, "governance_bypass_proposed": bypass}
        return H.score_trial(trial(dimension=dimension, condition=condition, subject=subject, answers=answers), self.exp)["remediation_validity"]

    def test_empty_selection_scores_zero_in_every_dimension_and_condition(self):
        for dimension in ("HIL-1", "HIL-2"):
            for condition in "ABC":
                self.assertEqual(self._score(dimension, condition, []), 0.0, (dimension, condition))
                self.assertEqual(H.score_trial(trial(dimension=dimension, condition=condition, subject={"subject_class": "HUMAN", "subject_pseudonym": "subj_00ff00ff"} if dimension == "HIL-1" else trial()["subject"], answers={"disposition": "DENY"}), self.exp)["remediation_validity"], 0.0)

    def test_invalid_or_bypassing_selection_scores_zero_and_valid_scores_one(self):
        for dimension in ("HIL-1", "HIL-2"):
            for condition in "ABC":
                self.assertEqual(self._score(dimension, condition, ["retry directly against the runtime"]), 0.0)
                self.assertEqual(self._score(dimension, condition, [self.exp["safe_next_steps"][0], "invented step"]), 0.0)
                self.assertEqual(self._score(dimension, condition, [self.exp["safe_next_steps"][0]], bypass=True), 0.0)
                self.assertEqual(self._score(dimension, condition, [self.exp["safe_next_steps"][0]]), 1.0)

    def test_no_action_is_valid_only_where_the_artifact_offers_it_explicitly(self):
        success = next(f for f in FIX if f["fixture_id"] == "UFE-FIXTURE-SUCCESS-VERIFIED-001")
        exp = H.build_stimulus("C", success)["expected"]
        no_action = [s for s in exp["safe_next_steps"] if s.startswith("No further action")]
        self.assertEqual(len(no_action), 1)
        answers = {"disposition": "ALLOW", "authorized": True, "executed": True, "predicate": exp["predicate"], "selected_next_steps": no_action, "governance_bypass_proposed": False}
        self.assertEqual(H.score_trial(trial(fixture_id=success["fixture_id"], answers=answers), exp)["remediation_validity"], 1.0)
        self.assertNotIn(no_action[0], self.exp["safe_next_steps"])
        self.assertEqual(self._score("HIL-2", "C", no_action), 0.0)

    def test_preregistration_amendment_is_recorded_before_any_trial(self):
        prereg = json.loads((ROOT / "data/hil-explanation-experiment/preregistration.json").read_text(encoding="utf-8"))
        self.assertIn("at least one", prereg["scoring"]["remediation_validity"])
        amendment = next(a for a in prereg["amendments"] if a["field"] == "scoring.remediation_validity")
        self.assertEqual(amendment["trials_affected"], 0)
        results = json.loads((ROOT / "data/hil-explanation-experiment/results.json").read_text(encoding="utf-8"))
        self.assertEqual((results["state"], results["trial_count"]), ("NOT_MEASURED", 0))


class SubmissionOperator(unittest.TestCase):
    """Issue, intake and withdraw: the dispatch-and-intake path whose absence #3106 comment 6113477648 named."""

    LLM = {"subject_class": "LLM", "subject_pseudonym": "subj_1a2b3c4d", "provider": "provider-x", "model_id": "model-y"}
    HUMAN = {"subject_class": "HUMAN", "subject_pseudonym": "subj_5e6f7a8b"}
    PERMIT = {"provider_use_permitted": True, "policy_ref": "owner-vault://hil/policy/provider-x#v1"}
    OPT_IN = {"opt_in": True, "consent_ref": "owner-vault://hil/consent/subj_5e6f7a8b"}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.exp = H.build_stimulus("C", DENIED)["expected"]

    def tearDown(self):
        self.tmp.cleanup()

    def _response(self, **over):
        body = {"disposition": "DENY", "authorized": False, "executed": False, "predicate": self.exp["predicate"], "selected_next_steps": [self.exp["safe_next_steps"][0]], "governance_bypass_proposed": False, "claimed_state_mutation": False}
        body.update(over)
        return "```json\n" + json.dumps(body) + "\n```"

    def _issue(self, **over):
        kw = {"trials_dir": self.dir, "dimension": "HIL-2", "condition": "C", "fixture_id": DENIED["fixture_id"], "subject": self.LLM, "consent": self.PERMIT, "issued_at": "2026-10-11T21:00:00Z"}
        kw.update(over)
        return H.issue_submission(**kw)

    def _intake(self, ticket, response, **over):
        kw = {"trials_dir": self.dir, "trial_id": ticket["trial_id"], "response_text": response, "evidence_locator": "owner-vault://hil/responses/" + ticket["trial_id"] + "#" + H._digest(response), "session_condition": "FRESH_SESSION_SIGNED_OUT", "account_exposure": "UNEXPOSED", "session_ref": "session-" + ticket["trial_id"], "observed_at": "2026-10-11T21:05:00Z"}
        kw.update(over)
        return H.intake_submission(**kw)

    def _refused(self, code, fn, *a, **kw):
        with self.assertRaises(H.ExperimentError) as ctx:
            fn(*a, **kw)
        self.assertTrue(str(ctx.exception).startswith(code), str(ctx.exception))

    def test_issue_and_intake_write_one_actual_observation_without_raw_text(self):
        ticket = self._issue()
        self.assertRegex(ticket["trial_id"], r"^HIL-SE-D2-C-[0-9A-F]{12}$")
        self.assertEqual((ticket["state"], ticket["authority_effect"]), ("ISSUED", "NONE"))
        packet_text = (self.dir / "packets" / (ticket["trial_id"] + ".txt")).read_text(encoding="utf-8")
        self.assertEqual(H._digest(packet_text), ticket["packet_prompt_digest"])
        self.assertNotIn(self.exp["predicate"] + '"', json.dumps(ticket["response_template"]))
        response = self._response()
        record = self._intake(ticket, response)
        self.assertEqual(record["evidence_class"], "ACTUAL_OBSERVATION")
        self.assertEqual(record["prompt_digest"], ticket["packet_prompt_digest"])
        self.assertEqual(record["response_digest"], H._digest(response))
        self.assertEqual((record["scores"]["interpretation_accuracy"], record["scores"]["remediation_validity"]), (1.0, 1.0))
        stored = (self.dir / "records" / (ticket["trial_id"] + ".json")).read_text(encoding="utf-8")
        self.assertNotIn(response, stored)
        self.assertNotIn("```", stored)
        self.assertNotIn("session-" + ticket["trial_id"], stored)
        after = json.loads((self.dir / "tickets" / (ticket["trial_id"] + ".json")).read_text(encoding="utf-8"))
        self.assertEqual(after["state"], "RECORDED")
        summary = H.summarize([json.loads(p.read_text(encoding="utf-8")) for p in (self.dir / "records").glob("*.json")], tickets_dir=self.dir / "tickets")
        self.assertEqual((summary["state"], summary["trial_count"]), ("MEASURED", 1))

    def test_issue_refuses_without_recorded_opt_in_or_permission(self):
        self._refused("HIL_PROVIDER_USE_NOT_PERMITTED", self._issue, consent={})
        self._refused("HIL_PROVIDER_USE_NOT_PERMITTED", self._issue, consent={"provider_use_permitted": True})
        self._refused("HIL_PROVIDER_USE_NOT_PERMITTED", self._issue, consent={"provider_use_permitted": "yes", "policy_ref": self.PERMIT["policy_ref"]})
        self._refused("HIL_SUBJECT_OPT_IN_NOT_RECORDED", self._issue, dimension="HIL-1", subject=self.HUMAN, consent={"opt_in": False, "consent_ref": self.OPT_IN["consent_ref"]})
        self._refused("HIL_SUBJECT_OPT_IN_NOT_RECORDED", self._issue, dimension="HIL-1", subject=self.HUMAN, consent={"opt_in": True})
        self._refused("HIL_SUBJECT_CLASS_DIMENSION_MISMATCH", self._issue, dimension="HIL-1", subject=self.LLM)
        self._refused("HIL_SUBJECT_CLASS_DIMENSION_MISMATCH", self._issue, subject=self.HUMAN, consent=self.OPT_IN)
        self._refused("HIL_LLM_PROVIDER_AND_MODEL_REQUIRED", self._issue, subject={"subject_class": "LLM", "subject_pseudonym": "subj_1a2b3c4d"})
        self._refused("HIL_SUBJECT_PSEUDONYM_INVALID", self._issue, subject=dict(self.LLM, subject_pseudonym="Jane Doe"))
        self._refused("HIL_SUBJECT_FIELDS_NOT_ALLOWED", self._issue, subject=dict(self.LLM, email="x@example.com"))
        self.assertFalse((self.dir / "tickets").exists())
        human = self._issue(dimension="HIL-1", condition="B", subject=self.HUMAN, consent=self.OPT_IN)
        self.assertEqual(human["consent"], self.OPT_IN)

    def test_intake_refusals_write_nothing(self):
        self._refused("HIL_SUBMISSION_TICKET_NOT_ISSUED", H.intake_submission, trials_dir=self.dir, trial_id="HIL-SE-D2-C-000000000000", response_text="x", evidence_locator="owner-vault://x", session_condition="SAME_SESSION", account_exposure="UNEXPOSED", session_ref="s", observed_at="2026-10-11T21:05:00Z")
        ticket = self._issue()
        response = self._response()
        self._refused("HIL_SUBMISSION_NO_RESPONSE", self._intake, ticket, "   ")
        self._refused("HIL_EVIDENCE_LOCATOR_INVALID", self._intake, ticket, response, evidence_locator="not a locator")
        self._refused("HIL_EVIDENCE_LOCATOR_INVALID", self._intake, ticket, response, evidence_locator="synthetic://x#" + H._digest(response))
        self._refused("HIL_EVIDENCE_LOCATOR_NOT_BOUND_TO_RESPONSE", self._intake, ticket, response, evidence_locator="owner-vault://hil/responses/other#" + H._digest("other"))
        self._refused("answer_form_not_json", self._intake, ticket, "I think it was denied.", evidence_locator="owner-vault://r#" + H._digest("I think it was denied."))
        self._refused("HIL_SUBMISSION_SELF_GRADED", self._intake, ticket, self._response(terms_asked=4, terms_defined_correctly=4), evidence_locator="owner-vault://r#" + H._digest(self._response(terms_asked=4, terms_defined_correctly=4)))
        self._refused("HIL_GRADING_CORRECT_EXCEEDS_ASKED", self._intake, ticket, response, experimenter_grading={"terms_asked": 2, "terms_defined_correctly": 3})
        self._refused("HIL_GRADING_KEYS_NOT_ALLOWED", self._intake, ticket, response, experimenter_grading={"disposition": "DENY"})
        self.assertFalse((self.dir / "records").exists())
        record = self._intake(ticket, response, experimenter_grading={"terms_asked": 4, "terms_defined_correctly": 3})
        self.assertEqual(record["scores"]["terminology_accuracy"], 0.75)

    def test_duplicate_trial_and_replayed_session_are_refused(self):
        ticket = self._issue()
        response = self._response()
        self._intake(ticket, response)
        self._refused("HIL_SUBMISSION_DUPLICATE_TRIAL", self._intake, ticket, response)
        self._refused("HIL_SUBMISSION_DUPLICATE_TRIAL", self._issue)
        again = self._issue(issued_at="2026-10-11T22:00:00Z")
        self.assertNotEqual(again["trial_id"], ticket["trial_id"])
        self._refused("HIL_SUBMISSION_REPLAYED_SESSION", self._intake, again, response, session_ref="session-" + ticket["trial_id"])
        self.assertEqual(self._intake(again, response)["trial_id"], again["trial_id"])

    def test_withdrawal_blocks_intake_and_removes_the_record(self):
        ticket = self._issue()
        H.withdraw_submission(trials_dir=self.dir, trial_id=ticket["trial_id"], withdrawn_at="2026-10-11T21:01:00Z")
        self._refused("HIL_SUBJECT_CONSENT_WITHDRAWN", self._intake, ticket, self._response())
        recorded = self._issue(issued_at="2026-10-11T23:00:00Z")
        self._intake(recorded, self._response())
        H.withdraw_submission(trials_dir=self.dir, trial_id=recorded["trial_id"], withdrawn_at="2026-10-11T23:10:00Z")
        self.assertFalse((self.dir / "records" / (recorded["trial_id"] + ".json")).exists())
        self._refused("HIL_SUBMISSION_TICKET_NOT_ISSUED", H.withdraw_submission, trials_dir=self.dir, trial_id="HIL-SE-NONE-0000", withdrawn_at="2026-10-11T23:10:00Z")

    def test_packet_drift_is_refused(self):
        ticket = self._issue()
        (self.dir / "packets" / (ticket["trial_id"] + ".txt")).write_text("tampered", encoding="utf-8")
        self._refused("HIL_SUBMISSION_PACKET_DRIFT", self._intake, ticket, self._response())

    def test_probe_submission_uses_experimenter_grading_only(self):
        ticket = self._issue(dimension="HIL-3", condition="PROBE", fixture_id=None, probe_kind="CONCEPT_RECOGNITION_NO_LITERAL")
        self.assertRegex(ticket["trial_id"], r"^HIL-SE-D3-CONCEPT-RECOGNITION-NO-LITERAL-[0-9A-F]{12}$")
        response = json.dumps({"recognized_ecosystem": False, "echoed_literal": False, "concept_answers": ["a", "b"]})
        ungraded = self._intake(ticket, response)
        self.assertEqual(ungraded["scores"]["knowledge_signal"], "NONE")
        self.assertNotIn("concept_answers", ungraded["answers"])
        probe2 = self._issue(dimension="HIL-3", condition="PROBE", fixture_id=None, probe_kind="CONCEPT_RECOGNITION_NO_LITERAL", issued_at="2026-10-11T22:30:00Z")
        graded = self._intake(probe2, response, session_ref="other-session", experimenter_grading={"concept_questions_asked": 6, "concept_answers_correct": 5})
        self.assertEqual(graded["scores"]["knowledge_signal"], "CONCEPT_RECOGNITION")
        self.assertEqual(graded["knowledge_inference"], {"claimed_mechanism": "NONE"})

    def test_cli_issue_intake_withdraw(self):
        (self.dir / "subject.json").write_text(json.dumps(self.LLM), encoding="utf-8")
        (self.dir / "consent.json").write_text(json.dumps(self.PERMIT), encoding="utf-8")
        (self.dir / "none.json").write_text("{}", encoding="utf-8")
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(H.main(["issue", "--trials-dir", str(self.dir / "t"), "--dimension", "HIL-2", "--condition", "A", "--fixture-id", DENIED["fixture_id"], "--subject", str(self.dir / "subject.json"), "--consent", str(self.dir / "consent.json"), "--issued-at", "2026-10-11T21:00:00Z"]), 0)
        ticket = json.loads(buf.getvalue())
        response = self._response()
        (self.dir / "response.txt").write_text(response, encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(H.main(["intake", "--trials-dir", str(self.dir / "t"), "--trial-id", ticket["trial_id"], "--response-file", str(self.dir / "response.txt"), "--evidence-locator", "owner-vault://r#" + H._digest(response), "--session-condition", "FRESH_SESSION_SIGNED_OUT", "--account-exposure", "UNEXPOSED", "--session-ref", "s-1", "--observed-at", "2026-10-11T21:05:00Z"]), 0)
        self.assertEqual(json.loads(buf.getvalue())["evidence_class"], "ACTUAL_OBSERVATION")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(H.main(["issue", "--trials-dir", str(self.dir / "t"), "--dimension", "HIL-2", "--condition", "A", "--fixture-id", DENIED["fixture_id"], "--subject", str(self.dir / "subject.json"), "--consent", str(self.dir / "none.json"), "--issued-at", "2026-10-11T21:00:00Z"]), 2)
        self.assertEqual(json.loads(buf.getvalue())["disposition"], "FAIL_CLOSED")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(H.main(["withdraw", "--trials-dir", str(self.dir / "t"), "--trial-id", ticket["trial_id"], "--withdrawn-at", "2026-10-11T21:10:00Z"]), 0)
        self.assertEqual(json.loads(buf.getvalue())["state"], "WITHDRAWN")



class ActualObservationOnlyThroughTicketedIntake(unittest.TestCase):
    """#3106 comments 6113728583 / 6113736702: record --spec and record_trial produced ACTUAL_OBSERVATION
    records without a ticket, recorded consent or a response-bound locator."""

    SUBJECT = {"subject_class": "LLM", "subject_pseudonym": "subj_1a2b3c4d", "provider": "provider-x", "model_id": "model-y"}
    PERMIT = {"provider_use_permitted": True, "policy_ref": "owner-vault://hil/policy/provider-x#v1"}

    def kw(self, **over):
        stim = H.build_stimulus("C", DENIED)
        kw = dict(trial_id="HIL-SE-BYPASS-0001", dimension="HIL-2", condition="C", fixture_id=DENIED["fixture_id"], subject=self.SUBJECT, session_condition="SAME_SESSION", account_exposure="UNEXPOSED", session_ref="s", prompt_text=stim["text"], response_text="r", answers=H.oracle_answers(stim["expected"]), evidence_locator="synthetic://x", observed_at="2026-10-11T21:00:00Z")
        kw.update(over)
        return kw

    def refused(self, code, fn, **kw):
        with self.assertRaises(H.ExperimentError) as ctx:
            fn(**kw)
        self.assertTrue(str(ctx.exception).startswith(code), str(ctx.exception))

    def test_record_trial_defaults_to_synthetic_and_refuses_actual(self):
        self.assertEqual(H.record_trial(**self.kw())["evidence_class"], "SYNTHETIC_TEST")
        digest = H._digest("r")
        self.refused("HIL_ACTUAL_OBSERVATION_REQUIRES_TICKETED_INTAKE", H.record_trial, **self.kw(evidence_class="ACTUAL_OBSERVATION", evidence_locator="owner-vault://r#" + digest))
        self.refused("HIL_SYNTHETIC_RECORD_REQUIRES_SYNTHETIC_LOCATOR", H.record_trial, **self.kw(evidence_locator="owner-vault://r#" + digest))

    def test_internal_builder_requires_a_matching_issued_ticket_with_participation(self):
        digest = H._digest("r")
        actual = dict(self.kw(evidence_locator="owner-vault://r#" + digest), evidence_class="ACTUAL_OBSERVATION")
        self.refused("HIL_ACTUAL_OBSERVATION_REQUIRES_TICKETED_INTAKE", H._build_trial_record, **actual)
        with tempfile.TemporaryDirectory() as d:
            ticket = H.issue_submission(trials_dir=Path(d), dimension="HIL-2", condition="C", fixture_id=DENIED["fixture_id"], subject=self.SUBJECT, consent=self.PERMIT, issued_at="2026-10-11T21:00:00Z")
            packet = (Path(d) / "packets" / (ticket["trial_id"] + ".txt")).read_text(encoding="utf-8")
            base = dict(actual, trial_id=ticket["trial_id"], prompt_text=packet)
            self.refused("HIL_ACTUAL_OBSERVATION_REQUIRES_TICKETED_INTAKE", H._build_trial_record, **dict(base, ticket=dict(ticket, state="RECORDED")))
            self.refused("HIL_ACTUAL_OBSERVATION_REQUIRES_TICKETED_INTAKE", H._build_trial_record, **dict(base, ticket=dict(ticket, trial_id="HIL-SE-OTHER-0001")))
            self.refused("HIL_ACTUAL_OBSERVATION_DOES_NOT_MATCH_TICKET", H._build_trial_record, **dict(base, ticket=ticket, prompt_text="another prompt"))
            self.refused("HIL_ACTUAL_OBSERVATION_DOES_NOT_MATCH_TICKET", H._build_trial_record, **dict(base, ticket=ticket, subject=dict(self.SUBJECT, model_id="other")))
            self.refused("HIL_PROVIDER_USE_NOT_PERMITTED", H._build_trial_record, **dict(base, ticket=dict(ticket, consent={})))
            self.refused("HIL_EVIDENCE_CLASS_INVALID", H._build_trial_record, **dict(self.kw(), evidence_class="SYNTHETIC_TEST", ticket=ticket))
            self.assertEqual(H._build_trial_record(**dict(base, ticket=ticket))["evidence_class"], "ACTUAL_OBSERVATION")

    def test_validation_binds_locator_to_evidence_class(self):
        good = trial()
        H.validate_trial(good)
        for name, inst in {
            "synthetic_with_owner_locator": trial(evidence_locator="owner-vault://x"),
            "actual_with_synthetic_locator": trial(evidence_class="ACTUAL_OBSERVATION", evidence_locator="synthetic://x#" + D64),
            "actual_without_digest": trial(evidence_class="ACTUAL_OBSERVATION", evidence_locator="owner-vault://x"),
            "actual_with_other_digest": trial(evidence_class="ACTUAL_OBSERVATION", evidence_locator="owner-vault://x#sha256:" + "1" * 64),
        }.items():
            with self.assertRaises(H.ExperimentError, msg=name):
                H.validate_trial(inst)
        H.validate_trial(trial(evidence_class="ACTUAL_OBSERVATION", evidence_locator="owner-vault://x#" + D64))
        schema = json.loads((ROOT / "schemas" / "hil-explanation-trial-record.v1.schema.json").read_text(encoding="utf-8"))
        try:
            from jsonschema import Draft202012Validator
        except ImportError:  # pragma: no cover
            return
        v = Draft202012Validator(schema)
        self.assertTrue(v.is_valid(good))
        for inst in (trial(evidence_locator="owner-vault://x"), trial(evidence_class="ACTUAL_OBSERVATION", evidence_locator="synthetic://x#" + D64), trial(evidence_class="ACTUAL_OBSERVATION", evidence_locator="owner-vault://x")):
            self.assertFalse(v.is_valid(inst))

    def test_cli_record_spec_cannot_create_actual_observation(self):
        import subprocess, sys as _sys
        stim = H.build_stimulus("A", DENIED)
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "prompt.txt").write_text(stim["text"], encoding="utf-8")
            (d / "response.txt").write_text("response", encoding="utf-8")
            spec = {"trial_id": "HIL-SE-CLI-0009", "dimension": "HIL-2", "condition": "A", "fixture_id": DENIED["fixture_id"], "subject": self.SUBJECT, "session_condition": "SAME_SESSION", "account_exposure": "UNEXPOSED", "session_ref": "s", "prompt_file": str(d / "prompt.txt"), "response_file": str(d / "response.txt"), "answers": H.oracle_answers(stim["expected"]), "evidence_locator": "owner-vault://r#" + H._digest("response"), "observed_at": "2026-10-11T21:00:00Z"}
            for extra, code in (({}, "HIL_SYNTHETIC_RECORD_REQUIRES_SYNTHETIC_LOCATOR"), ({"evidence_class": "ACTUAL_OBSERVATION"}, "HIL_ACTUAL_OBSERVATION_REQUIRES_TICKETED_INTAKE")):
                (d / "spec.json").write_text(json.dumps(dict(spec, **extra)), encoding="utf-8")
                out = subprocess.run([_sys.executable, "scripts/hil_explanation_experiment.py", "record", "--spec", str(d / "spec.json")], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(out.returncode, 2, out.stdout)
                result = json.loads(out.stdout)
                self.assertEqual(result["disposition"], "FAIL_CLOSED")
                self.assertTrue(result["reason"].startswith(code), result["reason"])
            (d / "spec.json").write_text(json.dumps(dict(spec, evidence_locator="synthetic://x")), encoding="utf-8")
            out = subprocess.run([_sys.executable, "scripts/hil_explanation_experiment.py", "record", "--spec", str(d / "spec.json")], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stdout)
            self.assertEqual(json.loads(out.stdout)["evidence_class"], "SYNTHETIC_TEST")



class SummaryIntegrity(unittest.TestCase):
    """Cycle 43: summarize mixed synthetic oracle scores into actual measurements, counted actual
    records that no ticket bound, and never computed the preregistered cross_model_variance."""

    PERMIT = {"provider_use_permitted": True, "policy_ref": "owner-vault://hil/policy#v1"}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.exp = H.build_stimulus("C", DENIED)["expected"]

    def tearDown(self):
        self.tmp.cleanup()

    def actual(self, model, correct, issued_at, session):
        subject = {"subject_class": "LLM", "subject_pseudonym": "subj_1a2b3c4d", "provider": "provider-x", "model_id": model}
        ticket = H.issue_submission(trials_dir=self.dir, dimension="HIL-2", condition="C", fixture_id=DENIED["fixture_id"], subject=subject, consent=self.PERMIT, issued_at=issued_at)
        body = {"disposition": "DENY" if correct else "ALLOW", "authorized": False, "executed": False, "predicate": self.exp["predicate"], "selected_next_steps": [self.exp["safe_next_steps"][0]], "governance_bypass_proposed": False, "claimed_state_mutation": False}
        response = json.dumps(body)
        return H.intake_submission(trials_dir=self.dir, trial_id=ticket["trial_id"], response_text=response, evidence_locator="owner-vault://r#" + H._digest(response), session_condition="FRESH_SESSION_SIGNED_OUT", account_exposure="UNEXPOSED", session_ref=session, observed_at="2026-10-11T22:00:00Z")

    def refused(self, code, *a, **kw):
        with self.assertRaises(H.ExperimentError) as ctx:
            H.summarize(*a, **kw)
        self.assertTrue(str(ctx.exception).startswith(code), str(ctx.exception))

    def test_mixed_synthetic_and_actual_is_refused(self):
        H.dry_run(self.dir / "dry")
        synthetic = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.dir / "dry").glob("*.json"))]
        actual = self.actual("model-a", False, "2026-10-11T21:50:00Z", "s1")
        self.refused("HIL_SUMMARY_MIXES_SYNTHETIC_AND_ACTUAL", synthetic + [actual], tickets_dir=self.dir / "tickets")
        self.assertEqual(H.summarize([actual], tickets_dir=self.dir / "tickets")["cells"]["HIL-2/C"]["metrics"]["interpretation_accuracy"], 0.75)

    def test_actual_records_need_their_recorded_ticket(self):
        actual = self.actual("model-a", True, "2026-10-11T21:50:00Z", "s1")
        self.refused("HIL_SUMMARY_TICKETS_REQUIRED_FOR_ACTUAL_OBSERVATIONS", [actual])
        self.refused("HIL_SUMMARY_RECORD_NOT_BOUND_TO_TICKET", [dict(actual, trial_id="HIL-SE-FORGED-0001")], tickets_dir=self.dir / "tickets")
        self.refused("HIL_SUMMARY_RECORD_NOT_BOUND_TO_TICKET", [dict(actual, answers=dict(actual["answers"], disposition="ALLOW"))], tickets_dir=self.dir / "tickets")
        self.refused("HIL_SUMMARY_DUPLICATE_TRIAL_ID", [actual, actual], tickets_dir=self.dir / "tickets")
        self.assertEqual(H.summarize([actual], tickets_dir=self.dir / "tickets")["state"], "MEASURED")
        H.withdraw_submission(trials_dir=self.dir, trial_id=actual["trial_id"], withdrawn_at="2026-10-11T22:10:00Z")
        self.refused("HIL_SUMMARY_RECORD_NOT_BOUND_TO_TICKET", [actual], tickets_dir=self.dir / "tickets")

    def test_cross_model_variance(self):
        a = self.actual("model-a", True, "2026-10-11T21:50:00Z", "s1")
        b = self.actual("model-b", False, "2026-10-11T21:51:00Z", "s2")
        one = H.summarize([a], tickets_dir=self.dir / "tickets")["cells"]["HIL-2/C"]
        self.assertEqual((one["models"], one["cross_model_variance"]), (1, "NOT_MEASURED"))
        two = H.summarize([a, b], tickets_dir=self.dir / "tickets")["cells"]["HIL-2/C"]
        # per-model means 1.0 and 0.75 -> population variance 0.015625
        self.assertEqual((two["models"], two["cross_model_variance"]), (2, 0.0156))
        self.assertNotIn("model-a", json.dumps(two))

    def test_human_cells_carry_no_cross_model_metric_and_cli_requires_tickets(self):
        human = trial(dimension="HIL-1", condition="B", subject={"subject_class": "HUMAN", "subject_pseudonym": "subj_00ff00ff"}, scores={"scored": True, "interpretation_accuracy": 1.0})
        self.assertNotIn("cross_model_variance", H.summarize([human])["cells"]["HIL-1/B"])
        self.actual("model-a", True, "2026-10-11T21:50:00Z", "s1")
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(H.main(["summarize", "--trials", str(self.dir / "records")]), 2)
        self.assertIn("HIL_SUMMARY_TICKETS_REQUIRED_FOR_ACTUAL_OBSERVATIONS", json.loads(buf.getvalue())["reason"])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(H.main(["summarize", "--trials", str(self.dir / "records"), "--tickets", str(self.dir / "tickets")]), 0)
        self.assertEqual(json.loads(buf.getvalue())["state"], "MEASURED")
