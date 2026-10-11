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
        "answers": {}, "scores": {"scored": False}, "evidence_locator": "fixture://trials/0001", "privacy": {"opt_in": True, "pii_present": False, "raw_text_stored_in_repository": False},
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
        s = H.summarize([t, trial(scores={"scored": True, "interpretation_accuracy": 1.0})])
        self.assertEqual(s["state"], "MEASURED_SYNTHETIC")
        self.assertEqual(s["cells"]["HIL-2/C"], {"n": 2, "metrics": {"interpretation_accuracy": 0.75, "governance_fidelity": 1.0}})

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
        kw = dict(trial_id="HIL-SE-R-0001", dimension="HIL-2", condition="C", fixture_id=DENIED["fixture_id"], subject=self.SUBJECT, session_condition="FRESH_SESSION_SIGNED_OUT", account_exposure="UNEXPOSED", session_ref="session-ref-secret", prompt_text=stim["text"], response_text="the response text", answers=H.oracle_answers(stim["expected"]), evidence_locator="owner://trials/0001", observed_at="2026-10-11T18:50:00Z")
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
        self.assertEqual(rec["evidence_class"], "ACTUAL_OBSERVATION")
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
            spec = {"trial_id": "HIL-SE-CLI-0001", "dimension": "HIL-2", "condition": "A", "fixture_id": DENIED["fixture_id"], "subject": self.SUBJECT, "session_condition": "FRESH_SESSION_SIGNED_IN_ORDINARY", "account_exposure": "UNEXPOSED", "session_ref": "s", "prompt_file": str(d / "prompt.txt"), "response_file": str(d / "response.txt"), "answers": H.oracle_answers(stim["expected"]), "evidence_locator": "owner://x", "observed_at": "2026-10-11T18:50:00Z"}
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
        rec = H.record_trial(trial_id="HIL-SE-PK-0001", dimension="HIL-2", condition="C", fixture_id=DENIED["fixture_id"], subject={"subject_class": "LLM", "subject_pseudonym": "subj_00000001", "provider": "p", "model_id": "m"}, session_condition="FRESH_SESSION_SIGNED_OUT", account_exposure="UNEXPOSED", session_ref="s", prompt_text=H.build_packet("HIL-2", "C", DENIED)["prompt_text"], response_text=json.dumps(body), answers=H.parse_answer_form(json.dumps(body)), evidence_locator="owner://x", observed_at="2026-10-11T20:00:00Z")
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
            spec = {"trial_id": "HIL-SE-CLI-0002", "dimension": "HIL-1", "condition": "B", "fixture_id": DENIED["fixture_id"], "subject": {"subject_class": "HUMAN", "subject_pseudonym": "subj_00ff00ff"}, "session_condition": "FRESH_SESSION_SIGNED_OUT", "account_exposure": "NOT_APPLICABLE", "session_ref": "s", "prompt_file": str(d / "prompt.txt"), "response_file": str(d / "response.txt"), "evidence_locator": "owner://x", "observed_at": "2026-10-11T20:00:00Z"}
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
