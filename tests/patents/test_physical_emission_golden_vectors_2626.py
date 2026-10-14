"""Deterministic synthetic PEP/0.1 evidence vectors; no physical capture or authority."""
import hashlib
import json
import unittest

DOMAINS = {"OBS", "EDGE", "CAPTURE", "REPLAY", "COMPARE"}

def canonical(value):
    def reject_floats(obj):
        if isinstance(obj, float):
            raise ValueError("floating point values are not canonical")
        if isinstance(obj, dict):
            if not all(isinstance(k, str) for k in obj):
                raise ValueError("object keys must be strings")
            for child in obj.values():
                reject_floats(child)
        if isinstance(obj, list):
            for child in obj:
                reject_floats(child)
    reject_floats(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")

def digest(domain, value):
    if domain not in DOMAINS:
        raise ValueError("unsupported domain")
    return hashlib.sha256(("PEP/0.1/" + domain).encode() + b"\\x00" + canonical(value)).hexdigest()

def parse_unique(data):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError("duplicate JSON key")
            obj[key] = value
        return obj
    return json.loads(data, object_pairs_hook=pairs, parse_float=lambda _: (_ for _ in ()).throw(ValueError("float")))

def observations():
    return [
        {"capture_id": "capture-1", "index": i, "acquisition_source": "recorder-1",
         "scope": "synthetic", "measurement": {"value": str(100 + 10*i) + ".000", "unit": "Hz"},
         "clock_coordinates": {"device": str(100+i), "system": str(200+i), "heartbeat": str(i)},
         "emitter_attribution": "UNKNOWN"} for i in range(3)
    ]

def commit(obs, *, start="start", finish="finish", missing_edge=None):
    if not start or not finish or not obs or not all(x.get("acquisition_source") for x in obs):
        return {"disposition": "FAIL_CLOSED", "reason": "ACQUISITION_BINDING_MISSING"}
    if [x["index"] for x in obs] != list(range(len(obs))):
        return {"disposition": "FAIL_CLOSED", "reason": "NONCONTIGUOUS_OBSERVATIONS"}
    hashes = [digest("OBS", x) for x in obs]
    edges = []
    previous = None
    for i in range(len(obs)-1):
        edge = {"capture_id": "capture-1", "edge_index": i,
                "before_observation_digest": hashes[i],
                "after_observation_digest": hashes[i+1],
                "previous_edge_digest": previous}
        previous = digest("EDGE", edge)
        if i != missing_edge:
            edges.append({"payload": edge, "digest": previous})
    manifest = {"capture_id": "capture-1", "start": start, "finish": finish,
                "observations": hashes, "edges": [e["digest"] for e in edges],
                "canonicalizer": "PEP/0.1"}
    return {"disposition": "ALLOW", "manifest": manifest, "manifest_digest": digest("CAPTURE", manifest),
            "edges": edges}

def verify(original, obs):
    if original.get("disposition") != "ALLOW":
        return "FAIL_CLOSED"
    rebuilt = commit(obs, start=original["manifest"]["start"], finish=original["manifest"]["finish"])
    return ("VERIFIED" if rebuilt["manifest_digest"] == original["manifest_digest"]
            and rebuilt["edges"] == original["edges"] else "FAIL_CLOSED")

def replay(original, missing, method=None):
    payload = {"original": original["manifest_digest"], "missing": missing,
               "method": method, "original_complete": not bool(missing)}
    return {"payload": payload, "digest": digest("REPLAY", payload)}

def compare(left, right, verified_left, verified_right):
    ancestry = set(left["ancestors"]) & set(right["ancestors"])
    independent = "SUPPORTED" if verified_left and verified_right and not ancestry and left["origin"] != right["origin"] else "NOT_ESTABLISHED"
    payload = {"left": left["id"], "right": right["id"], "independence": independent,
               "shared_ancestors": sorted(ancestry)}
    return {"payload": payload, "digest": digest("COMPARE", payload)}

class GoldenVectors(unittest.TestCase):
    def setUp(self):
        self.obs = observations()
        self.original = commit(self.obs)

    def test_GV_A1(self):
        self.assertEqual(verify(self.original, self.obs), "VERIFIED")
        self.assertEqual(len(self.original["edges"]), 2)
        self.assertEqual(self.obs[0]["emitter_attribution"], "UNKNOWN")

    def test_GV_A2(self):
        changed = observations()
        changed[1]["measurement"]["value"] = "111.000"
        self.assertEqual(verify(self.original, changed), "FAIL_CLOSED")

    def test_GV_A3(self):
        missing = commit(self.obs, missing_edge=1)
        self.assertEqual(verify(missing, self.obs), "FAIL_CLOSED")

    def test_GV_A4(self):
        self.assertNotEqual(digest("OBS", {"v": "1"}), digest("EDGE", {"v": "1"}))

    def test_GV_A5(self):
        coords = self.obs[0]["clock_coordinates"]
        self.assertNotEqual(coords["device"], coords["system"])
        self.assertNotEqual(coords["system"], coords["heartbeat"])
        self.assertEqual(verify(self.original, self.obs), "VERIFIED")

    def test_GV_B1(self):
        self.assertEqual(verify(self.original, self.obs), "VERIFIED")
        self.assertFalse(replay(self.original, [], None)["payload"]["missing"])

    def test_GV_B2(self):
        derived = replay(self.original, [1], "interpolation-v1")
        self.assertNotEqual(derived["digest"], self.original["manifest_digest"])
        self.assertFalse(derived["payload"]["original_complete"])

    def test_GV_C1(self):
        a = {"id": "A", "origin": "original-1", "ancestors": ["original-1"]}
        b = {"id": "B", "origin": "original-1", "ancestors": ["original-1"]}
        self.assertEqual(compare(a, b, True, True)["payload"]["independence"], "NOT_ESTABLISHED")

    def test_GV_C2(self):
        a = {"id": "A", "origin": "original-1", "ancestors": ["original-1"]}
        b = {"id": "B", "origin": "original-2", "ancestors": ["original-2"]}
        self.assertEqual(compare(a, b, True, False)["payload"]["independence"], "NOT_ESTABLISHED")

    def test_GV_C3(self):
        a = {"id": "A", "origin": "original-1", "ancestors": ["original-1"]}
        b = {"id": "B", "origin": "original-2", "ancestors": ["original-2"]}
        self.assertEqual(compare(a, b, True, True)["payload"]["independence"], "SUPPORTED")

    def test_reject_ambiguous_encoding(self):
        with self.assertRaises(ValueError):
            parse_unique('{"a":1,"a":2}')
        with self.assertRaises(ValueError):
            canonical({"v": 1.5})
        with self.assertRaises(ValueError):
            parse_unique('{"v":1.5}')

if __name__ == "__main__":
    unittest.main(verbosity=2)
