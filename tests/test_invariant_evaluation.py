"""RT-INVARIANT-EVALUATION-001: scripts/invariant_evaluation.py.

Every disposition, every six-field refusal path, UNDECIDABLE idempotency,
citation lines against the real Labs invariants file, and the absence of
network, subprocess and unbounded loops.
"""
from __future__ import annotations

import ast
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts import invariant_evaluation as ie
from scripts.validate_transition_disposition import NON_ALLOW, NON_ALLOW_REQUIRED, non_allow_missing

ROOT = Path(__file__).resolve().parents[1]
INVARIANTS_PATH = "data/task-registry-global-invariants.json"
INVARIANTS = (ROOT / INVARIANTS_PATH).read_bytes()
REPO, REV = "StegVerse-Labs/.github", "main"


def source(data: bytes = INVARIANTS, path: str = INVARIANTS_PATH, **overrides):
    row = {"repo": REPO, "rev": REV, "path": path, "sha256": hashlib.sha256(data).hexdigest(), "data": data}
    row.update(overrides)
    return row


def question(pointer: str = "/invariants/second_user_operated_device_allowed", value=False, **overrides) -> bytes:
    body = {"schema": ie.QUESTION_SCHEMA, "question_id": "Q-1", "invariant_pointer": pointer, "asserted_value": value}
    body.update(overrides)
    return json.dumps(body).encode()


def quoted(text: str) -> str:
    return '"' + text + '"'


def line_of(needle: str) -> int:
    for number, line in enumerate(INVARIANTS.decode().splitlines(), 1):
        if needle in line:
            return number
    raise AssertionError(needle)


class Dispositions(unittest.TestCase):
    def assert_six_fields(self, answer):
        self.assertIn(answer["disposition"], NON_ALLOW)
        self.assertEqual(non_allow_missing(answer), [])
        for key in NON_ALLOW_REQUIRED:
            self.assertIn(key, answer)
        self.assertEqual(answer["authority_effect"], "NONE_ANSWER_ONLY")
        self.assertIs(answer["consequence_committed"], False)

    def test_allow_when_assertion_matches_declared_value(self):
        answer = ie.evaluate(question(), [source()])
        self.assertEqual(answer["disposition"], "ALLOW")
        self.assertEqual(answer["schema"], "stegverse.invariant-evaluation/v1")
        self.assertEqual(answer["authority_effect"], "NONE_ANSWER_ONLY")
        self.assertNotIn("failure_code", answer)

    def test_deny_when_assertion_contradicts(self):
        answer = ie.evaluate(question(value=True), [source()])
        self.assertEqual(answer["disposition"], "DENY")
        self.assertEqual(answer["failure_code"], "INVARIANT_ASSERTION_CONTRADICTED")
        self.assert_six_fields(answer)

    def test_type_is_part_of_equality(self):
        # True == 1 in Python; a JSON boolean is not a JSON number.
        doc = b'{"invariants": {"flag": true}}'
        answer = ie.evaluate(question("/invariants/flag", 1), [source(doc, "x.json")])
        self.assertEqual(answer["disposition"], "DENY")

    def test_undecidable_when_no_source_declares_pointer(self):
        answer = ie.evaluate(question("/invariants/not_declared_anywhere", True), [source()])
        self.assertEqual(answer["disposition"], "UNDECIDABLE")
        self.assertEqual(answer["failure_code"], "INVARIANT_NOT_DECLARED_IN_SUPPLIED_SOURCES")
        self.assert_six_fields(answer)
        entry = answer["relay_queue_entry"]
        self.assertEqual(entry["entry_id"], answer["evaluation_key"])
        self.assertEqual(entry["queue_disposition"], "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION")

    def test_conflicting_sources_fail_closed(self):
        a = source(b'{"k": 1}', "a.json")
        b = source(b'{"k": 2}', "b.json")
        answer = ie.evaluate(question("/k", 1), [a, b])
        self.assertEqual(answer["disposition"], "FAIL_CLOSED")
        self.assertEqual(answer["failure_code"], "SOURCES_CONFLICT")
        self.assert_six_fields(answer)

    def test_validator_vocabulary_accepts_undecidable_as_non_allow(self):
        self.assertIn("UNDECIDABLE", NON_ALLOW)
        self.assertNotIn("ALLOW", NON_ALLOW)


class Refusals(unittest.TestCase):
    def refused(self, answer, code):
        self.assertEqual(answer["disposition"], "FAIL_CLOSED")
        self.assertEqual(answer["failure_code"], code)
        self.assertEqual(non_allow_missing(answer), [])
        self.assertEqual(answer["authority_effect"], "NONE_ANSWER_ONLY")

    def test_truncated_question_json(self):
        self.refused(ie.evaluate(question()[:-7], [source()]), "JSON_TRUNCATED")

    def test_truncated_source_json(self):
        data = INVARIANTS[: len(INVARIANTS) // 2]
        self.refused(ie.evaluate(question(), [source(data)]), "JSON_TRUNCATED")

    def test_digest_mismatch_is_checked_before_parse(self):
        bad = source(sha256="0" * 64)
        self.refused(ie.evaluate(question(), [bad]), "SOURCE_DIGEST_MISMATCH")
        # Unparseable bytes with a wrong digest report the digest, not the parse.
        junk = source(b"{not json", sha256="1" * 64)
        self.refused(ie.evaluate(question(), [junk]), "SOURCE_DIGEST_MISMATCH")

    def test_over_size_question_and_source(self):
        big = b" " * (ie.MAX_QUESTION_BYTES + 1)
        self.refused(ie.evaluate(big, [source()]), "INPUT_SIZE_EXCEEDED")
        huge = b" " * (ie.MAX_SOURCE_BYTES + 1)
        self.refused(ie.evaluate(question(), [source(huge)]), "INPUT_SIZE_EXCEEDED")
        self.refused(ie.evaluate(question(), [source(path=f"p{n}.json") for n in range(ie.MAX_SOURCES + 1)]),
                     "INPUT_SIZE_EXCEEDED")

    def test_over_depth_source_and_pointer(self):
        deep = b"[" * (ie.MAX_DEPTH + 5) + b"]" * (ie.MAX_DEPTH + 5)
        self.refused(ie.evaluate(question("/0"), [source(deep, "deep.json")]), "INPUT_DEPTH_EXCEEDED")
        far = "/" + "/".join(["a"] * (ie.MAX_POINTER_TOKENS + 1))
        self.refused(ie.evaluate(question(far), [source()]), "INPUT_DEPTH_EXCEEDED")
        # Far past the interpreter recursion limit: still a refusal, never a traceback.
        abyss = b"[" * 50_000
        self.refused(ie.evaluate(question("/0"), [source(abyss, "abyss.json")]), "INPUT_DEPTH_EXCEEDED")

    def test_unhashable_and_mistyped_values(self):
        self.refused(ie.evaluate(question(), [source(repo=["not", "hashable"])]), "INPUT_FIELD_INVALID")
        self.refused(ie.evaluate(question(question_id={"a": 1}), [source()]), "INPUT_FIELD_INVALID")
        answer = ie.evaluate(question(), [{"repo": REPO, ("un", "usual"): 1}])
        self.assertEqual(answer["disposition"], "FAIL_CLOSED")
        self.assertEqual(non_allow_missing(answer), [])
        answer = ie.evaluate(question(), {"not": "a list"})
        self.assertEqual(answer["disposition"], "FAIL_CLOSED")
        self.assertEqual(non_allow_missing(answer), [])
        answer = ie.evaluate("text, not bytes", [source()])
        self.assertEqual(answer["disposition"], "FAIL_CLOSED")
        self.assertEqual(non_allow_missing(answer), [])
        answer = ie.evaluate(None, None)
        self.assertEqual(answer["disposition"], "FAIL_CLOSED")
        self.assertEqual(non_allow_missing(answer), [])

    def test_malformed_question_shapes(self):
        self.refused(ie.evaluate(b"[]", [source()]), "QUESTION_OBJECT_REQUIRED")
        self.refused(ie.evaluate(question(schema="other/v1"), [source()]), "QUESTION_SCHEMA_UNSUPPORTED")
        no_value = json.dumps({"schema": ie.QUESTION_SCHEMA, "question_id": "Q", "invariant_pointer": "/k"}).encode()
        self.refused(ie.evaluate(no_value, [source()]), "QUESTION_ASSERTION_REQUIRED")
        self.refused(ie.evaluate(question("invariants/x"), [source()]), "QUESTION_POINTER_INVALID")
        self.refused(ie.evaluate(b'{"a": 1} trailing', [source()]), "JSON_TRAILING_DATA")
        self.refused(ie.evaluate(b'{"a": 1, "a": 2}', [source()]), "JSON_DUPLICATE_KEY")
        self.refused(ie.evaluate(b"\xff\xfe", [source()]), "INPUT_NOT_UTF8")
        self.refused(ie.evaluate(question(), []), "SOURCES_REQUIRED")
        self.refused(ie.evaluate(question(), [source(), source()]), "SOURCE_DUPLICATE")
        self.refused(ie.evaluate(question(), [source(sha256=hashlib.sha256(b"text").hexdigest()) | {"data": "text"}]),
                     "INPUT_BYTES_REQUIRED")
        self.refused(ie.evaluate(question(), [source(sha256="ABC")]), "SOURCE_DIGEST_INVALID")
        self.refused(ie.evaluate(question(), [source(b"NaN", "n.json")]), "JSON_MALFORMED")


class Idempotency(unittest.TestCase):
    def test_repeat_undecidable_writes_one_entry(self):
        q = question("/invariants/not_declared_anywhere", True)
        first = ie.evaluate(q, [source()])
        second = ie.evaluate(q, [source()])
        self.assertEqual(first["evaluation_key"], second["evaluation_key"])
        self.assertEqual(first["relay_queue_entry"], second["relay_queue_entry"])
        with tempfile.TemporaryDirectory() as tmp:
            path, created = ie.enqueue(Path(tmp), first["relay_queue_entry"])
            self.assertTrue(created)
            before = path.read_bytes()
            again, created_again = ie.enqueue(Path(tmp), second["relay_queue_entry"])
            self.assertEqual(again, path)
            self.assertFalse(created_again)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(len(list(Path(tmp).iterdir())), 1)

    def test_key_ignores_source_order_but_not_content(self):
        q = question("/missing", 1)
        a, b = source(b'{"x": 1}', "a.json"), source(b'{"y": 2}', "b.json")
        self.assertEqual(ie.evaluate(q, [a, b])["evaluation_key"], ie.evaluate(q, [b, a])["evaluation_key"])
        c = source(b'{"y": 3}', "b.json")
        self.assertNotEqual(ie.evaluate(q, [a, b])["evaluation_key"], ie.evaluate(q, [a, c])["evaluation_key"])

    def test_cli_writes_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            qpath = Path(tmp) / "q.json"
            qpath.write_bytes(question("/invariants/not_declared_anywhere", True))
            args = ["--question", str(qpath), "--source", REPO, REV, INVARIANTS_PATH,
                    hashlib.sha256(INVARIANTS).hexdigest(), str(ROOT / INVARIANTS_PATH),
                    "--relay-queue-dir", str(Path(tmp) / "queue")]
            self.assertEqual(ie.main(args), 2)
            self.assertEqual(ie.main(args), 2)
            self.assertEqual(len(list((Path(tmp) / "queue").iterdir())), 1)


class Citations(unittest.TestCase):
    def test_citation_names_the_declaring_line_in_the_real_invariants_file(self):
        for key in ("second_user_operated_device_allowed", "transition_authority", "runtime_reality_lock"):
            answer = ie.evaluate(question(f"/invariants/{key}", None), [source()])
            expected = f"{REPO}@{REV}:{INVARIANTS_PATH}:{line_of(quoted(key))}"
            self.assertEqual(answer["citations"], [expected])

    def test_top_level_and_array_member_citations(self):
        answer = ie.evaluate(question("/authority_effect", "NONE_REGISTRY_INVARIANT_ONLY"), [source()])
        self.assertEqual(answer["disposition"], "ALLOW")
        line = line_of(quoted("authority_effect") + ': "NONE_REGISTRY')
        self.assertEqual(answer["citations"], [f"{REPO}@{REV}:{INVARIANTS_PATH}:{line}"])
        doc = json.loads(INVARIANTS)
        first = doc["invariants"]["runtime_substrate_review_order"][0]
        answer = ie.evaluate(question("/invariants/runtime_substrate_review_order/0", first), [source()])
        self.assertEqual(answer["disposition"], "ALLOW")
        self.assertEqual(answer["citations"], [f"{REPO}@{REV}:{INVARIANTS_PATH}:{line_of(quoted(first))}"])

    def test_parser_agrees_with_stdlib_on_the_real_file(self):
        parsed, _ = ie.parse_json(INVARIANTS, "x", ie.MAX_SOURCE_BYTES)
        self.assertEqual(parsed, json.loads(INVARIANTS))


class Boundaries(unittest.TestCase):
    def test_no_network_subprocess_or_unbounded_loop(self):
        tree = ast.parse((ROOT / "scripts" / "invariant_evaluation.py").read_text(encoding="utf-8"))
        banned = {"socket", "urllib", "http", "requests", "subprocess", "ssl", "ftplib", "smtplib", "asyncio"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn(alias.name.split(".")[0], banned)
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn((node.module or "").split(".")[0], banned)
            if isinstance(node, ast.While):
                self.assertFalse(isinstance(node.test, ast.Constant) and node.test.value, "while True")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                self.assertNotIn(node.func.attr, {"system", "popen", "urlopen", "exec"})

    def test_shard_is_registered_and_non_authorizing(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import materialize_reusable_task_construct as constructor
        definition = constructor.resolve_reusable_task(constructor.load_registry(), "RT-INVARIANT-EVALUATION-001")
        self.assertEqual(definition["authority_effect"], "NONE_ANSWER_ONLY")
        self.assertEqual(definition["runner_templates"], [])


if __name__ == "__main__":
    unittest.main()
