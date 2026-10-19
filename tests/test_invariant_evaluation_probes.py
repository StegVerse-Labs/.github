"""RT-INVARIANT-EVALUATION-001 spec guard: the B-P6 probe set as data.

Each tests/fixtures/invariant_evaluation_probes/P<NN>.json holds one probe:
P01-P15 are the B-P6 cross-check, P16-P21 the B-P14 refusal citations, P22-P26
the B-P16 declared bounds. A probe
holds the question (JSON, or raw bytes for a question that does not parse), the source bytes (a Labs data/ file named
by path, or synthetic bytes held in the fixture) and the expected answer
fields. Every expected field cites the spec line it derives from as
RT-INVARIANT-EVALUATION-001.json:<line> plus a quote that must appear on that
line, so a spec edit that moves or drops the rule fails here.

Each run calls the CLI, scripts/invariant_evaluation.py, exactly as the spec's
reuse_instructions name it, with one relay queue directory per probe so
write-once behaviour across runs is observed on disk. Source validation only:
nothing here admits, authorizes or commits.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_transition_disposition import NON_ALLOW, NON_ALLOW_REQUIRED, non_allow_missing

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "invariant_evaluation_probes"
SPEC_NAME = "RT-INVARIANT-EVALUATION-001.json"
SPEC_LINES = (ROOT / "source-bundles" / "reusable-task-registry.d" / SPEC_NAME).read_text(encoding="utf-8").splitlines()
EVALUATOR = ROOT / "scripts" / "invariant_evaluation.py"
PROBE_SCHEMA = "stegverse.invariant-evaluation-probe/v1"
B_P6_PROBES = set(range(1, 16))
B_P14_PROBES = set(range(16, 22))
B_P16_PROBES = set(range(22, 27))
EXPECTED_PROBES = B_P6_PROBES | B_P14_PROBES | B_P16_PROBES
SPEC_BOUNDS = json.loads("\n".join(SPEC_LINES))["bounds"]
SPEC_REF = re.compile(re.escape(SPEC_NAME) + r":(\d+)")
PLACEHOLDER = re.compile(r"^\$\{(ref|ref_full|sha256|sha256_full):([a-z0-9_]+)\}$")
EXPECT_KEYS = {"disposition", "failure_code", "citations", "six_fields", "queue",
               "authority_effect", "owning_existing_goal", "retry_entrypoint"}
QUEUE_VALUES = {"created", "not_created", "write_once_repeat"}


def load_probes() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(FIXTURES.glob("P*.json"))]


def source_bytes(spec: dict) -> tuple[bytes, bytes]:
    """(supplied bytes, untruncated bytes) of one fixture source."""
    recipe = spec["bytes"]
    if "labs_file" in recipe:
        path = recipe["labs_file"]
        assert path.startswith("data/") and ".." not in path, path
        full = (ROOT / path).read_bytes()
    elif "json" in recipe:
        full = json.dumps(recipe["json"], indent=2).encode("utf-8")
    elif "hex" in recipe:
        full = bytes.fromhex(recipe["hex"])
    elif "text" in recipe:
        full = recipe["text"].encode("utf-8")
    else:
        full = b"".join(part["text"].encode("utf-8") * part.get("times", 1) for part in recipe["parts"])
    if "truncate_before" in recipe:
        return full[:full.index(recipe["truncate_before"].encode("utf-8"))], full
    return full, full


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ProbeRunner:
    def __init__(self, probe: dict, workdir: Path):
        self.probe = probe
        self.workdir = workdir
        self.queue = workdir / "relay-queue"
        self.bytes = {sid: source_bytes(spec) for sid, spec in probe["sources"].items()}

    def ref(self, sid: str, full: bool) -> dict:
        spec = self.probe["sources"][sid]
        data = self.bytes[sid][1 if full else 0]
        return {"repository": spec["repo"], "path": spec["path"], "revision": spec["rev"], "digest": "sha256:" + digest(data)}

    def fill(self, value):
        if isinstance(value, dict):
            return {k: self.fill(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.fill(v) for v in value]
        match = PLACEHOLDER.match(value) if isinstance(value, str) else None
        if not match:
            return value
        kind, sid = match.groups()
        if kind.startswith("ref"):
            return self.ref(sid, kind == "ref_full")
        return "sha256:" + digest(self.bytes[sid][1 if kind == "sha256_full" else 0])

    def citation(self, want: dict, question_sha256: str) -> str:
        if want.get("question"):
            return f"question@{question_sha256}:question:{want['line']}"
        spec = self.probe["sources"][want["source"]]
        if "line" in want:
            return f"{spec['repo']}@{spec['rev']}:{spec['path']}:{want['line']}"
        text = self.bytes[want["source"]][0].decode("utf-8")
        if want.get("line_at_end"):
            line = text.count("\n") + 1
        else:
            line = next(n for n, row in enumerate(text.splitlines(), 1) if want["line_of"] in row)
        return f"{spec['repo']}@{spec['rev']}:{spec['path']}:{line}"

    def run(self, index: int, run: dict) -> tuple[dict, bytes]:
        recipe = run["question"]
        if "json" in recipe:
            question = json.dumps(self.fill(recipe["json"]), indent=2).encode("utf-8")
        else:
            question = source_bytes({"bytes": recipe})[0]
        qfile = self.workdir / f"question-{index}.json"
        qfile.write_bytes(question)
        args = [sys.executable, "-I", str(EVALUATOR), "--question", str(qfile), "--relay-queue-dir", str(self.queue)]
        for row in run["supply"]:
            sid = row["source"]
            spec = self.probe["sources"][sid]
            data, full = self.bytes[sid]
            sfile = self.workdir / f"source-{index}-{sid}.bin"
            sfile.write_bytes(data)
            sha = digest(full if row.get("sha256") == "full" else data)
            args += ["--source", spec["repo"], spec["rev"], spec["path"], sha, str(sfile)]
        done = subprocess.run(args, cwd=self.workdir, capture_output=True, text=True, timeout=120)
        if done.returncode not in (0, 2) or "Traceback" in done.stderr:
            raise AssertionError(f"evaluator crashed: rc={done.returncode} {done.stderr[-2000:]}")
        return json.loads(done.stdout), question

    def queue_files(self) -> list[Path]:
        return sorted(self.queue.glob("*.json")) if self.queue.is_dir() else []


class SpecGuardFixtures(unittest.TestCase):
    """The fixtures themselves: complete, data only, each expectation spec-cited."""

    def test_one_probe_per_b_p6_row_b_p14_refusal_and_b_p16_bound(self):
        probes = load_probes()
        self.assertEqual({p["probe"] for p in probes}, EXPECTED_PROBES)
        self.assertEqual(len(probes), len(EXPECTED_PROBES))
        for probe in probes:
            self.assertEqual(probe["schema"], PROBE_SCHEMA)
            self.assertEqual(probe["reusable_task_id"], "RT-INVARIANT-EVALUATION-001")
            self.assertEqual(probe["authority_effect"], "NONE_TEST_FIXTURE")
            if probe["probe"] in B_P6_PROBES:
                self.assertEqual(probe["derived_from"]["b_p6_row"], probe["probe"])
            elif probe["probe"] in B_P16_PROBES:
                # Every B-P16 probe names the declared bound it pins, and every refusal its citations.
                self.assertIsInstance(SPEC_BOUNDS[probe["derived_from"]["b_p16_bound"]], dict)
                for run in probe["runs"]:
                    if run["expect"]["disposition"]["value"] == "FAIL_CLOSED":
                        self.assertIn("citations", run["expect"])
            else:
                self.assertIn("b_p14_refusal", probe["derived_from"])
                # Every B-P14 run pins the refusal's exact citations.
                for run in probe["runs"]:
                    self.assertIn("citations", run["expect"])

    def test_every_expectation_cites_a_spec_line_that_carries_its_quote(self):
        for probe in load_probes():
            for index, run in enumerate(probe["runs"]):
                expect = run["expect"]
                self.assertLessEqual(set(expect), EXPECT_KEYS, (probe["probe"], index))
                # Every run pins the answer's authority effect and the queue behaviour.
                self.assertIn("authority_effect", expect)
                self.assertIn("queue", expect)
                if expect["disposition"]["value"] in NON_ALLOW:
                    self.assertTrue(expect["six_fields"]["value"])
                for name, want in expect.items():
                    where = (probe["probe"], index, name)
                    match = SPEC_REF.fullmatch(want["spec_ref"])
                    self.assertIsNotNone(match, where)
                    line = int(match.group(1))
                    self.assertLessEqual(line, len(SPEC_LINES), where)
                    self.assertIn(want["spec_quote"], SPEC_LINES[line - 1], where)

    def test_sources_are_labs_data_files_or_synthetic_bytes(self):
        for probe in load_probes():
            for sid, spec in probe["sources"].items():
                recipe = spec["bytes"]
                if "labs_file" in recipe:
                    self.assertEqual((spec["repo"], spec["path"]), ("StegVerse-Labs/.github", recipe["labs_file"]))
                    self.assertTrue((ROOT / recipe["labs_file"]).is_file(), recipe["labs_file"])
                else:
                    self.assertTrue(spec["repo"].startswith("synthetic/"), (probe["probe"], sid))


class SpecGuardProbes(unittest.TestCase):
    """Run every probe through the CLI and assert each expected field."""

    def check(self, runner: ProbeRunner, index: int, run: dict) -> None:
        before = {p.name: p.read_bytes() for p in runner.queue_files()}
        answer, question = runner.run(index, run)
        expect = run["expect"]
        label = f"P{runner.probe['probe']:02d} run {index}"
        self.assertEqual(answer["disposition"], expect["disposition"]["value"], label)
        self.assertEqual(answer["authority_effect"], expect["authority_effect"]["value"], label)
        self.assertIs(answer["consequence_committed"], False, label)
        if "failure_code" in expect:
            self.assertEqual(answer["failure_code"], expect["failure_code"]["value"], label)
        if "citations" in expect:
            wanted = {runner.citation(c, digest(question)) for c in expect["citations"]["value"]}
            self.assertEqual(set(answer["citations"]), wanted, label)
        if "six_fields" in expect:
            self.assertEqual(non_allow_missing(answer), [], label)
            for field in NON_ALLOW_REQUIRED:
                self.assertTrue(answer[field], (label, field))
        for field in ("owning_existing_goal", "retry_entrypoint"):
            if field in expect:
                self.assertEqual(answer[field], expect[field]["value"], (label, field))

        queue = expect["queue"]
        after = runner.queue_files()
        self.assertEqual(len(after), queue["files_after"], label)
        if queue["value"] == "not_created":
            self.assertNotIn("relay_queue_ref", answer, label)
            self.assertEqual({p.name: p.read_bytes() for p in after}, before, label)
            return
        ref = answer["relay_queue_ref"]
        path = Path(ref["path"])
        self.assertEqual(path.name, f"{answer['evaluation_key']}.json", label)
        self.assertIs(ref["created"], queue["value"] == "created", label)
        if queue["value"] == "write_once_repeat":
            self.assertEqual(path.read_bytes(), before[path.name], label)
        else:
            self.assertNotIn(path.name, before, label)
        entry = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(entry["citations"], answer["citations"], label)
        if "relay_to" in queue:
            self.assertEqual(entry["relay_to"], queue["relay_to"], label)

    def test_probes(self):
        for probe in load_probes():
            with self.subTest(probe=probe["probe"]), tempfile.TemporaryDirectory() as tmp:
                runner = ProbeRunner(probe, Path(tmp))
                for index, run in enumerate(probe["runs"]):
                    self.check(runner, index, run)


if __name__ == "__main__":
    unittest.main()
