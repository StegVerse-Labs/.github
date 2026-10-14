"""PE-01..08 deterministic integrity/authority tests; bounded synthetic model, not empirical proof."""
import hashlib
import json
import unittest

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def capture(observations, receipts, start, finish, acquisition, emitter=None, clocks=None):
    edges = [{"index": i, "before": observations[i], "after": observations[i + 1]}
             for i in range(len(observations) - 1)]
    expected = [digest(edge) for edge in edges]
    valid = (len(observations) >= 2 and bool(start) and bool(finish)
             and bool(acquisition) and receipts == expected)
    return {"valid": valid, "edges": edges, "emitter": emitter,
            "acquisition": acquisition, "clocks": clocks or {}, "expected": expected}

def projection(original_ref, missing, method):
    payload = {"original_ref": original_ref, "missing": missing, "method": method,
               "original_complete": False}
    return {"identity": digest(payload), **payload}

def assess(origin_evidence, publication_authorized, execution_authorized):
    return {"origin": "ALLOW" if origin_evidence else "DENY",
            "publication": "ALLOW" if publication_authorized else "DENY",
            "execution": "ALLOW" if publication_authorized and execution_authorized else "DENY"}

class ProvenanceFixtures(unittest.TestCase):
    def setUp(self):
        self.observations = [{"hz": 100, "sample": 0}, {"hz": 110, "sample": 1},
                             {"hz": 120, "sample": 2}]
        self.edges = [{"index": i, "before": self.observations[i],
                       "after": self.observations[i + 1]} for i in range(2)]
        self.receipts = [digest(e) for e in self.edges]
        self.args = (self.observations, self.receipts, "start", "finish", "recorder-A")

    def test_PE_01_adjacency_and_tamper(self):
        original = capture(*self.args)
        self.assertTrue(original["valid"])
        self.assertEqual(len(original["edges"]), len(self.observations) - 1)
        altered = [*self.observations]
        altered[1] = {"hz": 111, "sample": 1}
        self.assertFalse(capture(altered, self.receipts, "start", "finish", "recorder-A")["valid"])
        self.assertFalse(capture(self.observations, self.receipts, None, "finish", "recorder-A")["valid"])

    def test_PE_02_unknown_emitter_not_unknown_recorder(self):
        original = capture(*self.args, emitter=None)
        self.assertTrue(original["valid"])
        self.assertEqual(original["acquisition"], "recorder-A")
        self.assertIsNone(original["emitter"])
        self.assertEqual(assess(False, True, False)["origin"], "DENY")
        self.assertFalse(capture(self.observations, self.receipts, "start", "finish", None)["valid"])

    def test_PE_03_conflicting_clocks_preserved(self):
        clocks = {"device": 100, "system": 200, "hb": 3, "uncertainty": 150}
        original = capture(*self.args, clocks=clocks)
        self.assertTrue(original["valid"])
        self.assertEqual(original["clocks"], clocks)
        self.assertNotEqual(original["clocks"]["device"], original["clocks"]["system"])

    def test_PE_04_missing_receipt_never_repaired_silently(self):
        original = capture(self.observations, self.receipts[:-1], "start", "finish", "recorder-A")
        self.assertFalse(original["valid"])
        derived = projection("original-1", [1], "interpolation")
        self.assertFalse(derived["original_complete"])

    def test_PE_05_publication_denial_does_not_mutate_capture(self):
        original = capture(*self.args)
        before = digest(original)
        self.assertEqual(assess(True, False, False)["publication"], "DENY")
        self.assertEqual(digest(original), before)
        self.assertTrue(original["valid"])

    def test_PE_06_degraded_replay_separate_identity(self):
        first = projection("original-1", [1], "interpolation")
        second = projection("original-1", [1], "interpolation")
        changed = projection("original-1", [1], "extrapolation")
        self.assertEqual(first["identity"], second["identity"])
        self.assertNotEqual(first["identity"], changed["identity"])
        self.assertNotEqual(first["identity"], first["original_ref"])
        self.assertFalse(first["original_complete"])

    def test_PE_07_common_ancestor_not_independent(self):
        left = {"identity": "L", "ancestor": "original-1"}
        right = {"identity": "R", "ancestor": "original-1"}
        independent = left["ancestor"] != right["ancestor"]
        self.assertFalse(independent)
        self.assertTrue(left["identity"] != right["identity"])

    def test_PE_08_governance_allow_not_execution(self):
        self.assertEqual(assess(True, True, False)["execution"], "DENY")
        self.assertEqual(assess(True, True, True)["execution"], "ALLOW")
        self.assertEqual(assess(True, False, True)["execution"], "DENY")

if __name__ == "__main__":
    unittest.main(verbosity=2)
