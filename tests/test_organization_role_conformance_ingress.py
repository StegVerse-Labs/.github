"""An organization-role conformance request is admitted by the existing manifest ingress.

`STEGDB-ORGANIZATION-ROLE-VERSION-PROPAGATION-002` issues one manifest-bound
request per stale adopter. This organization receives it on
`organization_manifest_ingress.receive`; the boundary selects
`stegverse-labs.organization-role-conformance` by the manifest's declared
capability and route, the adapter evaluates this organization's own source
against the target digests, and the ingress commits ALLOW, DENY or actionable
FAIL_CLOSED in the organization receipt, under the organization ledger lock.

The SDK is the real pinned SDK (`StegVerse-org/StegVerse-SDK@c30dc34`), never a
stub: manifests are built by its Manifest Builder, which declares
`stegverse.route.organization-role-conformance.v1` in
`extensions.stegverse_route` and carries the request in
`extensions.stegverse_organization_role_conformance_request`; validation, route
resolution and request derivation are the SDK's own. Only this repository's
crossing subprocess and closure reconstruction are replaced by fixed values in
the disposition cases, as in `test_manifest_ingress_idempotent`, so the
adapter evaluates a temporary git source root; one case drives the real
crossing end to end. Ledgers are temporary roots. No production receipt is
written or claimed.

Source validation only. No authority effect is claimed.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# The pinned SDK is required, never stubbed. Where it is not installed (the
# whole-suite ratchet) the module is skipped, as the Experiment 3 wire binding
# is; `org-runtime-boundary.yml` installs the pin and sets
# STEGVERSE_SDK_REQUIRED=1, so there an absent SDK is an error, not a skip.
try:
    from stegverse.manifest_builder import build_manifest
    from stegverse.organization_role_conformance_processor import (
        PROCESSING_CAPABILITY as SDK_CAPABILITY,
        REQUEST_EXTENSION as SDK_REQUEST_EXTENSION,
        REQUEST_SCHEMA as SDK_REQUEST_SCHEMA,
        ROUTE_ID as SDK_ROUTE_ID,
    )
    from stegverse.route_resolution import (
        ECOSYSTEM_DIAGNOSTIC_ROUTE_ID,
        PUBLISHED_ROUTES,
        ROUTE_DECLARATION_EXTENSION as SDK_ROUTE_EXTENSION,
        _ROUTE_FIELDS,
    )
except ImportError as exc:
    if os.environ.get("STEGVERSE_SDK_REQUIRED") == "1":
        raise
    raise unittest.SkipTest(f"requires the pinned StegVerse SDK: {exc}") from exc

ROOT = Path(__file__).resolve().parents[1]
REVISION = "0123456789abcdef0123456789abcdef01234567"
CREATED_AT = "2026-10-09T00:00:00Z"

_fixture_spec = importlib.util.spec_from_file_location(
    "manifest_ingress_rule_ref_fixture_conformance",
    ROOT / "tests/test_organization_manifest_ingress_rule_ref.py")
fixture = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(fixture)
ingress = fixture.ingress
conformance = ingress.role_conformance
organization_ledger = ingress.organization_ledger

ROLE_FILES = (
    "resident-runtime/organization_egress_boundary.py",
    "resident-runtime/ledger_store.py",
    "resident-runtime/aggregate_repo_transition.py",
    ".stegverse/transition-ledger/emit.py",
)
DIFFERING = ["resident-runtime/aggregate_repo_transition.py",
             "resident-runtime/organization_egress_boundary.py"]


def sha256_uri(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def sdk_manifest(request: dict) -> dict:
    """The manifest the pinned SDK's own builder emits for this request."""
    return build_manifest(data={"source": "role-version-propagation"},
                          processor_request=json.loads(json.dumps(request)),
                          source_framework="StegDB", source_output_id="role-conformance-1",
                          process=SDK_CAPABILITY, egress_surface="sdk-manifest-ingress",
                          created_at=CREATED_AT)


def target_version(root: Path, version_id: str = "org-role-test") -> dict:
    """A target version whose recorded digests are exactly `root`'s role files."""
    files = []
    for path in ROLE_FILES:
        raw = (root / path).read_bytes()
        files.append({"path": path, "blob_sha": conformance.git_blob_sha(raw),
                      "byte_count": len(raw), "contract_digest": sha256_uri(raw)})
    return {"version_id": version_id, "contract_digest": sha256_uri(conformance.canon(files)),
            "reference": {"repository": "StegVerse-org/.github", "ref": "f" * 40},
            "files": files, "digest_scope": "SHA256_OF_CANONICAL_JSON_OF_FILES_LIST"}


class ConformanceIngressCase(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        base = Path(self._temp.name)
        self.repo_root, self.org_root = base / "repo-ledger", base / "org-ledger"
        self.durable = base / "durable"
        self.source = base / "source"
        self.make_source(self.source)
        self.target = target_version(self.source)
        self.env = {"GITHUB_SHA": REVISION,
                    "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root),
                    "STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root)}

        patches = [
            mock.patch.dict(os.environ, self.env),
            mock.patch.object(ingress.crossing_module, "cross", self.cross),
            mock.patch.object(ingress, "reconstruct_closures",
                              lambda c: [{"transition_id": "t-1", "receipt_sha256": "c" * 64}]),
            mock.patch.object(ingress, "admit_runtime_result",
                              lambda *a: self.fail("conformance is not admitted through the SDK result")),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def make_source(self, root: Path) -> None:
        """This organization's own source, as a git checkout: boundary, record, role files."""
        for relative in ("org-runtime/interlock-intr.json", conformance.BINDING_PATH, *ROLE_FILES):
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, root / relative)
        git(root.parent, "init", "-q", str(root))
        git(root, "add", "-A")
        git(root, "-c", "user.name=test", "-c", "user.email=test@example.invalid",
            "commit", "-q", "-m", "source")
        self.commit = git(root, "rev-parse", "HEAD")

    def binding(self, **override) -> dict:
        raw = (self.source / conformance.BINDING_PATH).read_bytes()
        return {"repository": conformance.BINDING_REPOSITORY, "path": conformance.BINDING_PATH,
                "commit": self.commit, "sha256": sha256_uri(raw), **override}

    def request(self, **override) -> dict:
        return {"schema": conformance.REQUEST_SCHEMA,
                "issuer": {"repository": conformance.AUTHORIZED_ISSUER_REPOSITORY,
                           "owner_task_id": conformance.AUTHORIZED_ISSUER_TASK_ID},
                "destination_organization": "StegVerse-Labs",
                "manifest_binding": self.binding(),
                "target_role_version": self.target, **override}

    def manifest(self, **override) -> dict:
        """The SDK-built manifest carrying this request in its admitted extension."""
        return sdk_manifest(self.request(**override))

    def cross(self, manifest, *, registry, standing=None, packet_id="p"):
        manifest_sha256 = "sha256:" + ingress.sha(manifest)
        packet = {"packet_id": packet_id,
                  "payload": {"manifest": manifest, "manifest_sha256": manifest_sha256}}
        return {"crossing_completed": True, "resolved_service_id": conformance.SERVICE_ID,
                "ingress_packet_id": packet_id, "egress_packet_id": packet_id + "-egress",
                "manifest_sha256": manifest_sha256,
                "application_result": conformance.respond(packet, root=self.source)}

    def receive(self, manifest=None, **options):
        return ingress.receive(manifest or self.manifest(), registry={}, **options)

    def receipts(self, root):
        directory = root / "receipts"
        return [json.loads(p.read_text()) for p in sorted(directory.glob("*.json"))] \
            if directory.is_dir() else []

    def committed(self, result):
        """The organization receipt this result names, read back from the ledger."""
        digest = result["organization_receipt_sha256"].split(":", 1)[-1]
        row = json.loads((self.org_root / "receipts" / (digest + ".json")).read_text())
        return row["boundary_evidence"]


class DispositionTests(ConformanceIngressCase):
    def test_authorized_request_on_matching_source_is_allow(self):
        result = self.receive()
        self.assertEqual(result["disposition"], "ALLOW", result.get("detail"))
        self.assertIsNone(result["failed_predicate"])
        self.assertEqual(result["differing_files"], [])
        self.assertEqual(result["compared_files"], sorted(ROLE_FILES))
        self.assertIs(result["source_mutated"], False)
        evidence = self.committed(result)
        self.assertEqual(evidence["role_conformance_disposition"], "ALLOW")
        self.assertEqual(evidence["role_conformance_target_role_version_id"], "org-role-test")
        self.assertEqual(len(self.receipts(self.org_root)), 1)
        self.assertEqual(len(self.receipts(self.repo_root)), 1)

    def test_digest_mismatch_is_fail_closed_naming_exactly_the_differing_files(self):
        before = {}
        for path in DIFFERING:
            (self.source / path).write_text((self.source / path).read_text() + "# labs-only O1\n")
        for path in ROLE_FILES:
            before[path] = (self.source / path).read_bytes()
        result = self.receive(self.manifest(target_role_version=self.target))
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failed_predicate"],
                         "REFERENCE_ADOPTION_PARITY_WITH_RECORDED_FILE_DIGESTS")
        self.assertEqual([row["path"] for row in result["differing_files"]], DIFFERING)
        for row in result["differing_files"]:
            self.assertNotEqual(row["observed"]["contract_digest"], row["recorded"]["contract_digest"])
        self.assertTrue(result["required_evidence_or_repair"])
        self.assertEqual(result["retry_entrypoint"], ingress.RETRY_ENTRYPOINT)
        self.assertIs(result["next_attempt"]["awaits_an_external_machine"], False)
        evidence = self.committed(result)
        self.assertEqual(evidence["role_conformance_disposition"], "FAIL_CLOSED")
        self.assertEqual(evidence["role_conformance_differing_files"], DIFFERING)
        # The ingress evaluates; it does not re-adopt.
        for path in ROLE_FILES:
            self.assertEqual((self.source / path).read_bytes(), before[path], path)

    def test_a_missing_role_file_is_a_differing_file(self):
        (self.source / ROLE_FILES[1]).unlink()
        result = self.receive()
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["differing_files"][0]["path"], ROLE_FILES[1])
        self.assertEqual(result["differing_files"][0]["observed"], "ABSENT")

    def assertDenied(self, manifest, predicate):
        result = self.receive(manifest)
        self.assertEqual(result["disposition"], "DENY", result.get("detail"))
        self.assertEqual(result["failed_predicate"], predicate)
        self.assertEqual(self.committed(result)["role_conformance_disposition"], "DENY")
        self.assertEqual(self.committed(result)["role_conformance_failed_predicate"], predicate)
        return result

    def test_unauthorized_issuer_is_deny(self):
        for issuer in ({"repository": "StegVerse-Labs/Other", "owner_task_id": conformance.AUTHORIZED_ISSUER_TASK_ID},
                       {"repository": conformance.AUTHORIZED_ISSUER_REPOSITORY, "owner_task_id": "OTHER-TASK-001"}):
            with self.subTest(issuer=issuer):
                self.assertDenied(self.manifest(issuer=issuer), conformance.ISSUER_PREDICATE)

    def test_wrong_destination_is_deny(self):
        self.assertDenied(self.manifest(destination_organization="SV-LLM"),
                          conformance.DESTINATION_PREDICATE)

    def test_binding_mismatch_is_deny(self):
        cases = {
            "digest": self.binding(sha256="sha256:" + "0" * 64),
            "path": self.binding(path="data/canonical-task-records/OTHER.json"),
            "repository": self.binding(repository="StegVerse-org/.github"),
            "commit": self.binding(commit="abc"),
        }
        for name, binding in cases.items():
            with self.subTest(binding=name):
                self.assertDenied(self.manifest(manifest_binding=binding), conformance.BINDING_PREDICATE)

    def test_bound_record_must_name_the_issuer_repository(self):
        record_path = self.source / conformance.BINDING_PATH
        record = json.loads(record_path.read_text())
        record["repository"] = "StegVerse-Labs/Elsewhere"
        record_path.write_text(json.dumps(record))
        git(self.source, "-c", "user.name=test", "-c", "user.email=test@example.invalid",
            "commit", "-q", "-a", "-m", "record")
        self.commit = git(self.source, "rev-parse", "HEAD")
        self.assertDenied(self.manifest(), conformance.BINDING_PREDICATE)

    def test_target_version_whose_contract_digest_does_not_recompute_is_deny(self):
        forged = {**self.target, "contract_digest": "sha256:" + "1" * 64}
        self.assertDenied(self.manifest(target_role_version=forged), conformance.VERSION_PREDICATE)
        escaping = json.loads(json.dumps(self.target))
        escaping["files"][0]["path"] = "../outside.py"
        escaping["contract_digest"] = sha256_uri(conformance.canon(escaping["files"]))
        self.assertDenied(self.manifest(target_role_version=escaping), conformance.VERSION_PREDICATE)

    def test_binding_commit_absent_from_a_shallow_source_compares_the_record_bytes(self):
        absent = "e" * 40
        # The working-tree record equals the declared digest: the binding holds.
        self.assertEqual(self.receive(self.manifest(manifest_binding=self.binding(commit=absent)))
                         ["disposition"], "ALLOW")
        # It does not: actionable FAIL_CLOSED, not a DENY this source cannot show.
        result = self.receive(self.manifest(manifest_binding=self.binding(
            commit=absent, sha256="sha256:" + "0" * 64)))
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failed_predicate"], conformance.BINDING_SOURCE_PREDICATE)
        self.assertIn(absent, result["required_evidence_or_repair"])

    def test_an_evaluation_not_bound_to_the_manifest_is_fail_closed(self):
        original = self.cross

        def unbound(manifest, **kwargs):
            crossing = original(manifest, **kwargs)
            crossing["application_result"] = {**crossing["application_result"],
                                              "manifest_sha256": "sha256:" + "9" * 64}
            return crossing

        with mock.patch.object(ingress.crossing_module, "cross", unbound):
            result = self.receive()
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failed_predicate"],
                         "ROLE_CONFORMANCE_EVALUATION_IS_BOUND_TO_THE_SUBMITTED_MANIFEST")
        self.assertEqual(self.committed(result)["role_conformance_disposition"], "FAIL_CLOSED")


class SdkAdmissionTests(ConformanceIngressCase):
    """The pinned SDK admits the shape before any of this organization's predicates."""

    def test_the_labs_constants_are_the_sdk_published_route(self):
        self.assertEqual((conformance.CAPABILITY, conformance.ROUTE_ID, conformance.REQUEST_SCHEMA,
                          conformance.REQUEST_EXTENSION, conformance.ROUTE_DECLARATION_EXTENSION),
                         (SDK_CAPABILITY, SDK_ROUTE_ID, SDK_REQUEST_SCHEMA, SDK_REQUEST_EXTENSION,
                          SDK_ROUTE_EXTENSION))
        self.assertEqual(PUBLISHED_ROUTES[SDK_ROUTE_ID]["processor_capability"], SDK_CAPABILITY)

    def test_the_admitted_manifest_declares_the_route_and_carries_the_request_as_extensions(self):
        manifest = self.manifest()
        self.assertEqual(manifest["extensions"][SDK_ROUTE_EXTENSION]["route_id"], SDK_ROUTE_ID)
        self.assertEqual(manifest["extensions"][SDK_REQUEST_EXTENSION], self.request())
        self.assertNotIn(conformance.CAPABILITY, manifest)
        self.assertIsNone(ingress.admit_role_conformance_shape(manifest))
        derived = ingress.derive_execution_request(manifest, ingress.boundary())
        self.assertEqual((derived["route_id"], derived["processing_capability"]),
                         (SDK_ROUTE_ID, SDK_CAPABILITY))
        self.assertEqual(ingress.bound_here(derived)["operation_id"], ingress.OPERATION_ID)

    def test_the_admitted_request_is_received_on_the_durable_ledgers(self):
        result = self.receive()
        self.assertEqual(result["disposition"], "ALLOW", result.get("detail"))
        self.assertEqual((result["route_id"], result["processing_capability"]),
                         (SDK_ROUTE_ID, SDK_CAPABILITY))
        derived = ingress.derive_execution_request(self.manifest(), ingress.boundary())
        self.assertEqual(result["request_sha256"], derived["request_sha256"])
        self.assertEqual(len(self.receipts(self.org_root)), 1)
        self.assertEqual(len(self.receipts(self.repo_root)), 1)

    def assertRefusedBySdk(self, manifest, predicate, reason):
        crossed = []
        with mock.patch.object(ingress.crossing_module, "cross",
                               lambda *a, **k: crossed.append(a) or self.fail("not crossed")):
            result = self.receive(manifest)
        self.assertEqual(result["failed_predicate"], predicate, result.get("detail"))
        self.assertRegex(result["detail"], reason)
        self.assertIs(result["received"], False)
        self.assertIs(result["refusal_recorded"], True)
        refusal = [r for r in self.receipts(self.repo_root)
                   if r["transition_class"] == ingress.REFUSED_CLASS]
        self.assertEqual(len(refusal), 1)
        self.assertEqual(refusal[0]["evidence"]["disposition"], "DENY")
        self.assertEqual(refusal[0]["evidence"]["failed_predicate"], predicate)
        self.assertEqual(crossed, [])
        return result

    def test_the_request_as_a_top_level_field_is_refused(self):
        manifest = self.manifest()
        manifest[conformance.CAPABILITY] = manifest["extensions"].pop(SDK_REQUEST_EXTENSION)
        self.assertRefusedBySdk(manifest, ingress.ROLE_CONFORMANCE_SHAPE_PREDICATE,
                                "unknown top-level manifest fields: organization_role_conformance")

    def test_a_misspelled_route_is_refused(self):
        manifest = self.manifest()
        misspelled = "stegverse.route.organisation-role-conformance.v1"
        manifest["extensions"][SDK_ROUTE_EXTENSION]["route_id"] = misspelled
        manifest["processing"]["route_id"] = misspelled
        self.assertRefusedBySdk(manifest, ingress.ROLE_CONFORMANCE_ROUTE_PREDICATE,
                                "unsupported manifest route")

    def test_another_published_route_is_refused(self):
        manifest = self.manifest()
        manifest["extensions"][SDK_ROUTE_EXTENSION] = {
            field: PUBLISHED_ROUTES[ECOSYSTEM_DIAGNOSTIC_ROUTE_ID][field] for field in _ROUTE_FIELDS}
        manifest["processing"]["route_id"] = ECOSYSTEM_DIAGNOSTIC_ROUTE_ID
        self.assertRefusedBySdk(manifest, ingress.ROLE_CONFORMANCE_ROUTE_PREDICATE,
                                re.escape(ECOSYSTEM_DIAGNOSTIC_ROUTE_ID))

    def test_a_capability_mismatch_is_refused(self):
        manifest = self.manifest()
        manifest["processing"]["capability"] = "ecosystem_diagnostic"
        self.assertRefusedBySdk(manifest, ingress.ROLE_CONFORMANCE_DERIVATION_PREDICATE,
                                "does not select organization_role_conformance")

    def test_the_route_without_its_request_extension_is_refused(self):
        manifest = self.manifest()
        manifest["extensions"].pop(SDK_REQUEST_EXTENSION)
        self.assertRefusedBySdk(manifest, ingress.ROLE_CONFORMANCE_DERIVATION_PREDICATE,
                                "processor_request must be an object")

    def test_a_request_the_sdk_does_not_admit_is_refused_before_the_organization_predicates(self):
        cases = {
            "issuer absent": (lambda r: r.update(issuer=None), "issuer must be an object"),
            "binding absent": (lambda r: r.update(manifest_binding=None),
                               "manifest_binding must be an object"),
            "unknown field": (lambda r: r.update(disposition="ALLOW"),
                              "unknown organization_role_conformance request fields"),
            "schema": (lambda r: r.update(schema=SDK_REQUEST_SCHEMA.replace("/v1", "/v2")),
                       "schema must be"),
        }
        for name, (mutate, reason) in cases.items():
            with self.subTest(case=name):
                manifest = self.manifest()
                mutate(manifest["extensions"][SDK_REQUEST_EXTENSION])
                result = self.receive(manifest)
                self.assertEqual(result["failed_predicate"],
                                 ingress.ROLE_CONFORMANCE_DERIVATION_PREDICATE)
                self.assertRegex(result["detail"], reason)
                self.assertIs(result["refusal_recorded"], True)

    def test_an_exact_replay_of_a_refusal_returns_the_recorded_receipt(self):
        manifest = self.manifest()
        manifest[conformance.CAPABILITY] = manifest["extensions"].pop(SDK_REQUEST_EXTENSION)
        first, second = self.receive(manifest), self.receive(manifest)
        self.assertEqual(first["refusal_organization_receipt_sha256"],
                         second["refusal_organization_receipt_sha256"])
        self.assertEqual(len(self.receipts(self.org_root)), 1)
        self.assertEqual(len(self.receipts(self.repo_root)), 1)


class RealCrossingTests(unittest.TestCase):
    """The real SDK, the real crossing subprocess and the real adapter, end to end.

    The adapter evaluates this checkout. The target version is this checkout's
    own role files, bound to the canonical task record at this checkout's HEAD,
    so the disposition is ALLOW; ledgers are temporary roots.
    """

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.org_root, self.repo_root = Path(temp.name) / "org", Path(temp.name) / "repo"
        patch = mock.patch.dict(os.environ, {"GITHUB_SHA": REVISION,
                                             "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root),
                                             "STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root)})
        patch.start()
        self.addCleanup(patch.stop)

    def test_the_admitted_request_crosses_and_commits_allow(self):
        head = git(ROOT, "rev-parse", "HEAD")
        record = subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob",
                                 f"{head}:{conformance.BINDING_PATH}"],
                                capture_output=True, check=True).stdout
        manifest = sdk_manifest({
            "schema": conformance.REQUEST_SCHEMA,
            "issuer": {"repository": conformance.AUTHORIZED_ISSUER_REPOSITORY,
                       "owner_task_id": conformance.AUTHORIZED_ISSUER_TASK_ID},
            "destination_organization": "StegVerse-Labs",
            "manifest_binding": {"repository": conformance.BINDING_REPOSITORY,
                                 "path": conformance.BINDING_PATH, "commit": head,
                                 "sha256": sha256_uri(record)},
            "target_role_version": target_version(ROOT)})
        registry = json.loads((ROOT / "org-boundary/registry/services.json").read_text())
        standing = {"mode": "ESTABLISH_GENESIS", "node_ref": "StegDB", "predecessor": None}
        result = ingress.receive(manifest, registry=registry, standing=standing,
                                 packet_id="role-conformance-real-crossing")
        self.assertEqual(result["disposition"], "ALLOW", result.get("detail"))
        self.assertEqual(result["resolved_service_id"], conformance.SERVICE_ID)
        self.assertIs(result["boundary_receipt_chain_reconstructed_independently"], True)
        self.assertIs(result["disposition_committed_in_organization_ledger"], True)
        replay = ingress.receive(manifest, registry=registry, standing=standing,
                                 packet_id="role-conformance-real-crossing")
        self.assertIs(replay["transition_replayed"], True)
        self.assertEqual(replay["organization_receipt_sha256"], result["organization_receipt_sha256"])


class RetryAndLedgerRootTests(ConformanceIngressCase):
    def test_exact_retry_returns_the_recorded_receipts(self):
        # E1: the same delivery again.
        first = self.receive(packet_id="delivery-1")
        second = self.receive(packet_id="delivery-1")
        self.assertEqual(first["disposition"], "ALLOW")
        self.assertEqual(second["disposition"], "ALLOW")
        self.assertIs(first["transition_replayed"], False)
        self.assertIs(second["transition_replayed"], True)
        self.assertEqual(first["organization_receipt_sha256"], second["organization_receipt_sha256"])
        self.assertEqual(first["repository_receipt_sha256"], second["repository_receipt_sha256"])
        self.assertEqual(len(self.receipts(self.org_root)), 1)
        self.assertEqual(len(self.receipts(self.repo_root)), 1)

    def receipt_bytes(self, root):
        return {p.name: p.read_bytes() for p in sorted((root / "receipts").glob("*.json"))}

    def test_redelivery_under_another_packet_id_reuses_the_recorded_receipts(self):
        """I-10: the packet is the carrier, so a redelivery is the recorded transition."""
        first = self.receive(packet_id="delivery-1")
        repository_bytes, organization_bytes = (self.receipt_bytes(self.repo_root),
                                                self.receipt_bytes(self.org_root))
        second = self.receive(packet_id="delivery-2")
        self.assertEqual((first["disposition"], second["disposition"]), ("ALLOW", "ALLOW"))
        self.assertIs(second["transition_replayed"], True)
        self.assertEqual(first["organization_receipt_sha256"], second["organization_receipt_sha256"])
        self.assertEqual(self.receipt_bytes(self.repo_root), repository_bytes)
        self.assertEqual(self.receipt_bytes(self.org_root), organization_bytes)
        self.assertEqual(self.committed(second)["ingress_packet_id"], "delivery-1")
        self.assertEqual(second["delivery_attempt"]["ingress_packet_id"], "delivery-2")
        self.assertEqual(second["delivery_attempt"]["transition_identity_role"],
                         "NON_IDENTITY_DELIVERY_EVIDENCE")

    def assert_collides_under_one_transition_id(self, manifest):
        """Redelivered under the recorded transition id, a changed request fails closed."""
        first = self.receive(packet_id="delivery-1")
        self.assertEqual(first["disposition"], "ALLOW")
        repository_bytes, organization_bytes = (self.receipt_bytes(self.repo_root),
                                                self.receipt_bytes(self.org_root))
        with mock.patch.object(ingress, "ingress_transition_id",
                               lambda request, evaluation=None: first["organization_transition_id"]):
            refused = self.receive(manifest, packet_id="delivery-2")
        self.assertEqual(refused["disposition"], "FAIL_CLOSED")
        self.assertEqual(refused["failed_predicate"], "ONE_TRANSITION_ID_BINDS_ONE_MANIFEST")
        after = self.receipt_bytes(self.repo_root)
        self.assertTrue(set(repository_bytes.items()) <= set(after.items()))
        self.assertTrue(set(organization_bytes.items()) <= set(self.receipt_bytes(self.org_root).items()))
        self.assertEqual(sum(1 for r in self.receipts(self.repo_root)
                             if r["transition_class"] == ingress.OPERATION_ID), 1)

    def test_changed_issuer_under_one_transition_id_collides(self):
        self.assert_collides_under_one_transition_id(self.manifest(
            issuer={"repository": "StegVerse-Labs/Elsewhere",
                    "owner_task_id": conformance.AUTHORIZED_ISSUER_TASK_ID}))

    def test_changed_destination_under_one_transition_id_collides(self):
        self.assert_collides_under_one_transition_id(self.manifest(destination_organization="StegVerse-org"))

    def test_changed_binding_under_one_transition_id_collides(self):
        self.assert_collides_under_one_transition_id(self.manifest(manifest_binding=self.binding(commit="0" * 40)))

    def test_changed_target_version_under_one_transition_id_collides(self):
        self.assert_collides_under_one_transition_id(self.manifest(
            target_role_version=target_version(self.source, version_id="org-role-other")))

    def test_exact_retry_of_a_fail_closed_is_idempotent(self):
        (self.source / DIFFERING[0]).write_text("changed\n")
        first, second = self.receive(), self.receive()
        self.assertEqual(first["disposition"], "FAIL_CLOSED")
        self.assertEqual(first["organization_receipt_sha256"], second["organization_receipt_sha256"])
        self.assertIs(second["transition_replayed"], True)
        self.assertEqual(len(self.receipts(self.org_root)), 1)

    def test_resubmission_after_the_source_changed_is_a_new_transition_not_a_collision(self):
        original = (self.source / DIFFERING[0]).read_bytes()
        (self.source / DIFFERING[0]).write_text("changed\n")
        first = self.receive()
        (self.source / DIFFERING[0]).write_bytes(original)
        second = self.receive()
        self.assertEqual((first["disposition"], second["disposition"]), ("FAIL_CLOSED", "ALLOW"))
        self.assertNotEqual(first["organization_transition_id"], second["organization_transition_id"])
        self.assertEqual(len(self.receipts(self.org_root)), 2)

    def test_nothing_is_appended_to_the_organization_ledger_without_its_supplied_root(self):
        with mock.patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": ""}):
            os.environ.pop("STEGVERSE_ORG_LEDGER_ROOT")
            result = self.receive()
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failure_code"], ingress.APPEND_NOT_COMMITTED)
        self.assertIn("STEGVERSE_ORG_LEDGER_ROOT", result["required_evidence_or_repair"])
        self.assertFalse(self.org_root.exists())

    def test_nothing_is_appended_at_all_without_either_supplied_root(self):
        with mock.patch.dict(os.environ, {}):
            os.environ.pop("STEGVERSE_ORG_LEDGER_ROOT")
            os.environ.pop("STEGVERSE_REPO_LEDGER_ROOT")
            with self.assertRaisesRegex(ValueError, "ledger_location_required_from_materializer"):
                self.receive()
        self.assertFalse(self.org_root.exists())
        self.assertFalse(self.repo_root.exists())


class OutboxTests(ConformanceIngressCase):
    def put(self, name="event-1", **override):
        outbox = self.durable / "intr-outbox" / ingress.ROLE_CONFORMANCE_OUTBOX_ROUTE
        outbox.mkdir(parents=True, exist_ok=True)
        event = {"schema": ingress.OUTBOX_EVENT_SCHEMA, "route": ingress.ROLE_CONFORMANCE_OUTBOX_ROUTE,
                 "manifest": self.manifest(), "packet_id": name, **override}
        (outbox / (name + ".json")).write_text(json.dumps(event))
        return outbox / (name + ".json")

    def test_an_absent_or_empty_outbox_is_no_event(self):
        self.assertEqual(ingress.consume_outbox(self.durable, registry={})["state"], "NO_EVENT")
        (self.durable / "intr-outbox" / ingress.ROLE_CONFORMANCE_OUTBOX_ROUTE).mkdir(parents=True)
        consumed = ingress.consume_outbox(self.durable, registry={})
        self.assertEqual((consumed["state"], consumed["event_count"]), ("NO_EVENT", 0))
        self.assertFalse(self.org_root.exists())

    def test_each_event_is_received_and_redelivery_is_the_exact_retry(self):
        self.put()
        first = ingress.consume_outbox(self.durable, registry={})
        self.assertEqual(first["state"], "CONSUMED")
        self.assertEqual(first["results"][0]["disposition"], "ALLOW")
        self.assertIs(first["results"][0]["transition_replayed"], False)
        second = ingress.consume_outbox(self.durable, registry={})
        self.assertIs(second["results"][0]["transition_replayed"], True)
        self.assertEqual(first["results"][0]["organization_receipt_sha256"],
                         second["results"][0]["organization_receipt_sha256"])
        self.assertEqual(len(self.receipts(self.org_root)), 1)

    def test_events_are_not_received_until_the_ledger_roots_are_supplied(self):
        event = self.put()
        consumed = ingress.consume_outbox(self.durable, registry={}, environ={})
        self.assertEqual(consumed["state"], "FAIL_CLOSED")
        self.assertEqual(consumed["missing_ledger_roots"], list(ingress.LEDGER_ROOT_VARIABLES))
        self.assertIs(consumed["appended"], False)
        self.assertTrue(event.is_file())
        self.assertFalse(self.org_root.exists())
        self.assertFalse(self.repo_root.exists())

    def test_an_event_without_a_manifest_on_this_route_appends_nothing(self):
        self.put(route="another-route")
        consumed = ingress.consume_outbox(self.durable, registry={})
        self.assertEqual(consumed["results"][0]["failed_predicate"],
                         "OUTBOX_EVENT_CARRIES_A_MANIFEST_ON_THIS_ROUTE")
        self.assertFalse(self.org_root.exists())


class RouteRegistrationTests(unittest.TestCase):
    """The capability and route are admitted by exactly one row, served by a pure adapter."""

    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "org-boundary/registry/services.json").read_text())
        spec = importlib.util.spec_from_file_location(
            "manifest_selection_conformance", ROOT / "org-boundary/runtime/manifest_selection.py")
        cls.selection = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.selection)

    def test_the_declared_pair_selects_the_conformance_endpoint_only(self):
        manifest = {"processing": {"capability": conformance.CAPABILITY, "route_id": conformance.ROUTE_ID}}
        service = ingress.crossing_module.processing_service(manifest, self.registry)
        self.assertEqual(service["service_id"], conformance.SERVICE_ID)
        self.assertEqual(service["endpoint_adapter"], "resident-runtime/organization_role_conformance.py")
        self.assertEqual(service["endpoint_adapter_effect"], "PURE")
        self.assertIs(self.selection.select_processing(service, manifest)["declared_capability_processed"], True)
        for row in self.registry["services"]:
            if row["boundary_role"] == "INTERNAL_ENDPOINT" and row is not service:
                with self.subTest(service=row["service_id"]), self.assertRaises(SystemExit):
                    self.selection.select_processing(row, manifest)

    def test_the_adapter_runs_as_the_boundary_invokes_it(self):
        packet = {"packet_id": "p-1", "payload": {"manifest_sha256": "sha256:" + "a" * 64, "manifest": {
            "extensions": {conformance.REQUEST_EXTENSION: {
                "schema": conformance.REQUEST_SCHEMA,
                "issuer": {"repository": "Elsewhere/x", "owner_task_id": "X"}}}}}}
        with tempfile.TemporaryDirectory() as temp:
            envelope, out = Path(temp) / "envelope.json", Path(temp) / "out.json"
            envelope.write_text(json.dumps(packet))
            completed = subprocess.run(
                [sys.executable, str(ROOT / "resident-runtime/organization_role_conformance.py"),
                 "--envelope", str(envelope), "--out", str(out)],
                cwd=ROOT, capture_output=True, text=True, check=False,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(out.read_text())
        self.assertEqual(result["disposition"], "DENY")
        self.assertEqual(result["failed_predicate"], conformance.ISSUER_PREDICATE)
        self.assertEqual(result["manifest_sha256"], "sha256:" + "a" * 64)


if __name__ == "__main__":
    unittest.main()
