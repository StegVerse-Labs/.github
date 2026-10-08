"""StegVerse-Labs decides a governance request that crossed into it over InTr.

StegCore is a StegVerse-Labs repository, so StegVerse-Labs/.github is where a
governance request from another organization is received and decided. These
tests drive the kernel's dispatch of `stegverse-labs.governance` -- an
INTERNAL_ENDPOINT whose adapter the registry admits -- and the response the
resident cycle publishes back to the origin.

StegCore is replaced by a stub on the adapter's import path, so the decision is
deterministic and the test does not depend on which StegCore is installed. The
real evaluator is exercised wherever StegCore is materialized; without it the
adapter decides FAIL_CLOSED and says so, which is also tested.

Both ledger roots and the mesh are redirected per test.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = "stegverse-labs.governance"
STANDING = {"mode": "ESTABLISH_GENESIS", "node_ref": "StegVerse-org-test-node", "predecessor": None}
STUB = '''
class AdmissibilityRequest:
    def __init__(self, **fields):
        if "signal" not in fields:
            raise TypeError("signal required")
        self.fields = fields
class _Result:
    def __init__(self, fields):
        self.fields = fields
    def model_dump(self, mode="json"):
        return {"disposition": "DENY", "canonical_three_layer_reason": "signal.inputs_incomplete",
                "request": self.fields}
def evaluate_admissibility(request):
    return _Result(request.fields)
'''


def _kernel():
    spec = importlib.util.spec_from_file_location("labs_kernel", ROOT / "org-kernel/kernel.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


K = _kernel()


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


#: What an admitted governance manifest declares. An internal endpoint selects
#: processing only from this pair, never from the address it was sent to.
PROCESSING = {"capability": "governance", "route_id": "stegverse.route.canonical-governed.v1"}


def work_request(request, *, digest=None, processing=PROCESSING):
    payload = {
        "communication_id": "governance:" + "a" * 64,
        "message_class": "ecosystem.work.request",
        "subject": "governance.decision",
        "requested_action": "DECIDE_GOVERNANCE_ADMISSIBILITY",
        "audience": "TARGET", "target_organization": "StegVerse-Labs", "target_count": 1,
        "body": {"schema": "stegverse.org-governance-decision-request/v1",
                 "origin_organization": "StegVerse-org",
                 "sdk_request_sha256": "a" * 64,
                 "governance_request": request,
                 "governance_request_sha256": digest or hashlib.sha256(canon(request)).hexdigest()},
    }
    if processing is not None:
        payload["processing"] = dict(processing)
    return payload


def packet(payload):
    return K.build_packet(origin_org="StegVerse-org", origin_service="stegverse-org.governance",
                          destination_org="StegVerse-Labs", destination_service=SERVICE,
                          payload=payload, standing=dict(STANDING),
                          transition_reference="ecosystem.transition.governance.v1")


class GovernanceEndpointTests(unittest.TestCase):
    VARIABLES = ("STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_ROOT", "PYTHONPATH")

    def setUp(self):
        self._work = tempfile.TemporaryDirectory()
        self.addCleanup(self._work.cleanup)
        self.work = Path(self._work.name)
        previous = {name: os.environ.get(name) for name in self.VARIABLES}

        def restore():
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
        self.addCleanup(restore)
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = str(self.work / "repo-ledger")
        os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = str(self.work / "org-ledger")
        stub = self.work / "stub" / "stegcore"
        stub.mkdir(parents=True)
        (stub / "__init__.py").write_text("")
        (stub / "steggate.py").write_text(STUB)
        self.stub_path = str(self.work / "stub")

    def with_stegcore(self):
        os.environ["PYTHONPATH"] = self.stub_path

    def without_stegcore(self):
        empty = self.work / "no-stegcore"
        empty.mkdir(exist_ok=True)
        os.environ["PYTHONPATH"] = str(empty)

    def ledger(self, variable):
        return [json.loads(path.read_text())
                for path in (Path(os.environ[variable]) / "receipts").glob("*.json")]

    def test_the_governance_service_is_an_admitted_internal_endpoint(self):
        registry = K.load_registry(ROOT)
        row = next(s for s in registry["services"] if s["service_id"] == SERVICE)
        self.assertEqual(row["boundary_role"], "INTERNAL_ENDPOINT")
        self.assertEqual(row["endpoint_adapter_disposition"], "ALLOW_DECLARED_ADAPTER")
        self.assertEqual(row["decision_authority"],
                         "StegVerse-Labs/StegCore:stegcore.steggate.evaluate_admissibility")

    def test_a_crossed_request_is_decided_here_with_stegcore(self):
        self.with_stegcore()
        result = K.dispatch(ROOT, packet(work_request({"signal": {}})))
        decision = result["application_result"]
        self.assertIs(result["consumed"], True)
        self.assertEqual(result["reconstruction"]["status"], "RECONSTRUCTED")
        self.assertEqual(decision["deciding_organization"], "StegVerse-Labs")
        self.assertEqual(decision["decision_authority"], "stegcore.steggate.evaluate_admissibility")
        self.assertEqual(decision["disposition"], "DENY")
        self.assertEqual(decision["reason"], "signal.inputs_incomplete")
        self.assertEqual(decision["records_authority"], "ORGANIZATION_RECORDS_ONLY")

    def test_the_decision_is_recorded_at_both_ledger_levels_here(self):
        self.with_stegcore()
        decision = K.dispatch(ROOT, packet(work_request({"signal": {}})))["application_result"]
        repository = self.ledger("STEGVERSE_REPO_LEDGER_ROOT")
        organization = self.ledger("STEGVERSE_ORG_LEDGER_ROOT")
        self.assertEqual([r["transition_class"] for r in repository], ["ORGANIZATION_GOVERNANCE_DECISION"])
        self.assertEqual(repository[0]["repository"], "StegVerse-Labs/.github")
        self.assertEqual(repository[0]["receipt_sha256"], decision["repository_receipt_sha256"])
        self.assertEqual(len(organization), 1)
        self.assertEqual(organization[0]["repo_receipt_sha256"], decision["repository_receipt_sha256"])
        self.assertEqual(organization[0]["receipt_sha256"], decision["organization_receipt_sha256"])

    def test_without_stegcore_the_request_is_decided_fail_closed_not_guessed(self):
        self.without_stegcore()
        decision = K.dispatch(ROOT, packet(work_request({"signal": {}})))["application_result"]
        self.assertEqual(decision["disposition"], "FAIL_CLOSED")
        self.assertEqual(decision["reason"], "GOVERNANCE_RUNTIME_STEGCORE_UNAVAILABLE")
        self.assertEqual(len(self.ledger("STEGVERSE_REPO_LEDGER_ROOT")), 1)

    def test_a_request_that_does_not_recompute_is_decided_fail_closed(self):
        self.with_stegcore()
        decision = K.dispatch(ROOT, packet(work_request({"signal": {}}, digest="0" * 64)))["application_result"]
        self.assertEqual(decision["disposition"], "FAIL_CLOSED")
        self.assertEqual(decision["reason"], "GOVERNANCE_REQUEST_DIGEST_MISMATCH")

    def copied_root(self):
        """A dispatch root of its own, so the resident cycle's seen-markers land outside the checkout."""
        root = self.work / "root"
        for relative in ("org-boundary/registry/services.json", "org-boundary/runtime/node_standing.py",
                         "org-boundary/runtime/manifest_selection.py",
                         "docs/CANONICAL_NODE_INGRESS_CONTRACT_001.json",
                         "resident-runtime/governance_endpoint.py",
                         "resident-runtime/aggregate_repo_transition.py",
                         "resident-runtime/ledger_store.py",
                         "org-kernel/kernel.py", "org-kernel/node_store.py",
                         ".stegverse/transition-ledger/emit.py",
                         ".stegverse/transition-ledger/contract.json",
                         ".stegverse/transition-ledger/org-contract.json"):
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text((ROOT / relative).read_text())
        return root

    def test_the_answer_returns_to_the_origin_with_a_recomputable_chain(self):
        self.with_stegcore()
        mesh = self.work / "mesh"
        sent = packet(work_request({"signal": {}}))
        K.publish_packet(sent, root=mesh)
        # Node state and both ledgers are supplied, so the checkout is only read.
        consumed = K.consume_and_respond(ROOT, mesh_root=mesh,
                                         node_state_root=self.work / "node-state", seen=set(),
                                         repo_ledger_root=self.work / "repo-ledger",
                                         org_ledger_root=self.work / "org-ledger")
        self.assertEqual([item["result"]["status"] for item in consumed], ["CONSUMED"])
        self.assertEqual(consumed[0]["result"]["execution_result"]["processing_selection"],
                         "MANIFEST_DECLARED")
        # The decision and the crossing are each recorded at both levels.
        classes = sorted(r["transition_class"] for r in self.ledger("STEGVERSE_REPO_LEDGER_ROOT"))
        self.assertEqual(classes, ["ORGANIZATION_FEDERATION_CROSSING_CONSUMED",
                                   "ORGANIZATION_GOVERNANCE_DECISION"])
        self.assertEqual(len(self.ledger("STEGVERSE_ORG_LEDGER_ROOT")), 2)
        response = K.recover_packet(consumed[0]["response_publication"]["frame"])
        self.assertEqual(response["destination"]["org"], "StegVerse-org")
        self.assertEqual(response["payload"]["message_class"], "ecosystem.work.ack")
        body = response["payload"]["body"]
        self.assertEqual(body["request_packet_id"], sent["packet_id"])
        self.assertEqual(body["application_result"]["disposition"], "DENY")
        chain, previous = [], None
        for kind in ("INGRESS_ACCEPTED", "DISPATCHED", "CONSUMED", "RESULT_BOUND", "EGRESS_EMITTED"):
            receipt = K.receipt(kind, sent["packet_id"], SERVICE, previous,
                                {"payload_hash": K.sha(sent["payload"])})
            chain.append(receipt["receipt_id"])
            previous = receipt["receipt_id"]
        self.assertEqual(body["receipt_terminal"], chain[-1])

    def test_an_adapter_the_registry_does_not_admit_mints_no_chain(self):
        root = self.copied_root()
        registry = json.loads((root / "org-boundary/registry/services.json").read_text())
        for row in registry["services"]:
            if row["service_id"] == SERVICE:
                row["endpoint_adapter_disposition"] = "FAIL_CLOSED_ENDPOINT_ADAPTER_UNDECLARED"
        (root / "org-boundary/registry/services.json").write_text(json.dumps(registry))
        with self.assertRaises(ValueError) as raised:
            K.dispatch(root, packet(work_request({"signal": {}})))
        self.assertIn("FAIL_CLOSED_ENDPOINT_ADAPTER_UNDECLARED", str(raised.exception))

    def test_a_request_declaring_no_processing_is_refused_before_any_decision(self):
        """The address does not select processing; the admitted declaration does."""
        self.with_stegcore()
        with self.assertRaises(ValueError) as raised:
            K.dispatch(ROOT, packet(work_request({"signal": {}}, processing=None)))
        self.assertIn("PROCESSING_SELECTED_ONLY_BY_ADMITTED_PROCESSING_CAPABILITY_AND_ROUTE_ID",
                      str(raised.exception))
        self.assertEqual(self.ledger("STEGVERSE_REPO_LEDGER_ROOT")
                         if (self.work / "repo-ledger" / "receipts").is_dir() else [], [])

    def test_an_undeclared_request_crossing_is_recorded_as_deny_and_not_decided(self):
        self.with_stegcore()
        mesh = self.work / "mesh"
        K.publish_packet(packet(work_request({"signal": {}}, processing=None)), root=mesh)
        refused, = K.consume_and_respond(ROOT, mesh_root=mesh, node_state_root=self.work / "node-state",
                                         repo_ledger_root=self.work / "repo-ledger",
                                         org_ledger_root=self.work / "org-ledger")
        self.assertEqual(refused["result"]["status"], "REFUSED")
        self.assertEqual(refused["result"]["disposition"], "DENY")
        self.assertIsNone(refused["response_publication"])
        repository, = self.ledger("STEGVERSE_REPO_LEDGER_ROOT")
        self.assertEqual(repository["transition_class"], "ORGANIZATION_FEDERATION_CROSSING_REFUSED")
        organization, = self.ledger("STEGVERSE_ORG_LEDGER_ROOT")
        self.assertEqual(organization["repo_receipt_sha256"], repository["receipt_sha256"])

    def test_boundary_local_roles_are_unchanged(self):
        result = K.dispatch(ROOT, K.build_packet(
            origin_org="StegVerse-org", origin_service="stegverse-org.org-control",
            destination_org="StegVerse-Labs", destination_service="stegverse-labs.boundary-diagnostic",
            payload={"probe": 1}, standing=dict(STANDING)))
        self.assertEqual(result["application_result"], {"echo": {"probe": 1}})


if __name__ == "__main__":
    unittest.main()
