"""Node registration is registrant-neutral; `web_device` in the names is historical.

A device is interchangeable and a node confers no authority, so nothing about a
registrant can distinguish it: a browser device and an external framework
present the same binding receipt and receive the same standing. This test pins
that as behaviour rather than as a claim in a document, because the claim is
only worth making if the code keeps honouring it.

What the bootstrap path actually constrains is *consistency*: the node id and
continuity id are opaque equality keys, threaded from the genesis binding
receipt through each package receipt, the aggregate receipt and the proof, and
compared only against each other. Neither is parsed.

The one place that does constrain format -
`workers/sv_dn1_browser_evidence_intr_ingress.py` requiring a `stegnode-web-`
prefix - is scoped to its own observation class,
`AUTHENTIC_ESTABLISHED_STEGVERSE_WEB_NODE`. That is a browser validator
legitimately insisting on browser identities, not a general gate, and this test
asserts that scoping so the distinction is not lost.

Non-authorizing: source validation only. No node is registered, nothing is
admitted, and registration confers no execution or verifier authority.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


m = _load("intake", "workers/bootstrap_v1_materialization_evidence_intake_worker.py")
C = list(m.COMPONENTS)

GENESIS_SCHEMA = "stegos.web_device_node_binding_receipt.v1"

#: The same registration, presented by registrants of different kinds. None of
#: these is more or less a node than the others.
REGISTRANTS = [
    ("browser device", "stegnode-web-test", "stegdevice-test"),
    ("external framework", "stegnode-framework-elyria-7f3a", "framework-continuity-elyria-7f3a"),
    ("another custody ecosystem", "stegnode-custodian-acme", "custodian-continuity-acme"),
    ("no prefix at all", "some-registrant", "some-continuity"),
]


def candidate():
    body = {
        "schema": "stegverse.bootstrap.release-candidate/v1", "candidate_version": "1.0.0-rc.1",
        "state": "FROZEN",
        "source_catalog": {"sha256": "placeholder", "source_identity_set_sha256": "placeholder"},
        "release_activated": False, "publication_performed": False, "execution_authority": "NONE",
    }
    return {**body, "candidate_identity": "sha256:" + m.digest(body)}


def make_bundle():
    ids = {c: "sha256:" + (str(i + 1) * 64)[:64] for i, c in enumerate(C)}
    catalog = {
        "schema": "stegverse.bootstrap.source-catalog/v1", "catalog_version": "1.0.0",
        "state": "FROZEN", "source_identity_scheme": "sha256-content-manifest",
        "component_count": 4,
        "components": [{"component_id": c, "source_identity": ids[c]} for c in C],
        "source_identity_set_sha256": "set-123", "github_platform_required": False,
        "specific_external_platform_required": False, "network_locator_required": False,
    }
    c = candidate()
    c["source_catalog"] = {"sha256": m.digest(catalog),
                           "source_identity_set_sha256": catalog["source_identity_set_sha256"]}
    c["candidate_identity"] = "sha256:" + m.digest(m.candidate_body(c))
    packages = [{"schema": "stegverse.source-package/v1", "package_version": "1.0.0",
                 "component_id": x, "source_identity": ids[x]} for x in C]
    body = {
        "schema": "stegverse.bootstrap.bundle/v1", "bundle_version": "1.0.0-rc.1", "state": "BUILT",
        "release_candidate": c, "source_catalog": catalog, "packages": packages,
        "component_order": C, "component_count": 4,
        "source_identity_scheme": "sha256-content-manifest", "github_platform_required": False,
        "specific_external_platform_required": False, "network_locator_required": False,
        "transport_implementation_required": False, "credential_required": False,
        "bundle_integrity_confers_execution_authority": False, "release_activated": False,
        "publication_performed": False, "execution_authority": "NONE",
        "authority_effect": "NONE_BUNDLE_BUILD_ONLY",
    }
    return c, {**body, "bundle_identity": "sha256:" + m.digest(body)}, ids


def entry(receipt, seq, prev):
    body = {"schema": "stegos.web_bootstrap_journal_entry.v1", "sequence": seq,
            "previous_entry_sha256": prev, "receipt": receipt,
            "receipt_sha256": m.digest(receipt)}
    return {**body, "entry_sha256": m.digest(body)}


def evidence(node, continuity, c, b, ids):
    """The same bundle evidence, registered by whichever registrant is named."""
    rows, prev = [], None
    genesis = {"schema": GENESIS_SCHEMA, "node_id": node,
               "device_continuity_id": continuity, "authority_effect": "NONE"}
    e = entry(genesis, 1, prev); rows.append(e); prev = e["entry_sha256"]
    package_entries = []
    for component in C:
        r = {"schema": "stegos.web_source_package_materialization_receipt.v1", "node_id": node,
             "device_continuity_id": continuity, "component_id": component,
             "source_identity": ids[component], "source_bundle_sha256": ids[component][7:],
             "file_count": 1, "local_custody": "INDEXEDDB_STEGOS_SOURCE_PACKAGES_V1",
             "materialization_state": "MATERIALIZED", "admission_state": "UNADMITTED",
             "execution_authority": "NONE", "credential_material_observed": False,
             "github_platform_required": False, "specific_external_platform_required": False,
             "new_node_identity_minted": False,
             "authority_effect": "NONE_SOURCE_MATERIALIZATION_ONLY"}
        e = entry(r, len(rows) + 1, prev); rows.append(e); package_entries.append(e)
        prev = e["entry_sha256"]
    expected = [{"component_id": x, "source_identity": ids[x]} for x in C]
    r = {"schema": "stegos.web_bootstrap_bundle_materialization_receipt.v1", "node_id": node,
         "device_continuity_id": continuity, "bundle_identity": b["bundle_identity"],
         "candidate_identity": c["candidate_identity"],
         "source_identity_set_sha256": b["source_catalog"]["source_identity_set_sha256"],
         "component_order": C, "component_identities": expected, "component_count": 4,
         "all_components_materialized": True, "bundle_state": "MATERIALIZED_UNADMITTED",
         "admission_state": "UNADMITTED", "execution_authority": "NONE",
         "release_activated": False, "publication_performed": False,
         "github_platform_required": False, "specific_external_platform_required": False,
         "new_node_identity_minted": False,
         "authority_effect": "NONE_BUNDLE_MATERIALIZATION_ONLY"}
    agg = entry(r, len(rows) + 1, prev); rows.append(agg)
    rep = m.replay(rows)
    return {
        "schema": "stegverse.device-node-bootstrap-bundle-evidence/v1",
        "state": "MATERIALIZED_UNADMITTED", "node_id": node, "device_continuity_id": continuity,
        "continuity_source": "LIVE_EXISTING_WEB_BOOTSTRAP",
        "bundle_identity": b["bundle_identity"], "candidate_identity": c["candidate_identity"],
        "source_identity_set_sha256": b["source_catalog"]["source_identity_set_sha256"],
        "component_count": 4, "component_order": C, "component_identities": expected,
        "package_materialization_entries": package_entries, "bundle_materialization_entry": agg,
        "journal_replay": {"schema": "stegos.web_journal_replay_report.v1", **rep,
                           "authority_effect": "NONE"},
        "continued_receipts": rows, "all_components_materialized": True,
        "admission_state": "UNADMITTED", "credential_material_observed": False,
        "github_platform_required": False, "specific_external_platform_required": False,
        "new_node_identity_minted": False, "release_activated": False,
        "publication_performed": False, "execution_authority": "NONE", "authority_effect": "NONE",
    }


class RegistrantNeutralityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate, self.bundle, self.ids = make_bundle()

    def test_every_kind_of_registrant_registers_identically(self) -> None:
        """A framework is no less a node than the browser device the name mentions."""
        for label, node, continuity in REGISTRANTS:
            with self.subTest(registrant=label):
                observed = m.validate_evidence(
                    evidence(node, continuity, self.candidate, self.bundle, self.ids),
                    self.candidate, self.bundle, self.ids,
                )
                self.assertEqual(observed["node_id"], node)
                self.assertEqual(observed["device_continuity_id"], continuity)
                self.assertEqual(observed["journal_entries"], 6)

    def test_the_identities_are_opaque_keys_checked_only_for_consistency(self) -> None:
        """Nothing parses them; what is enforced is that they agree across the chain.

        The divergence is caught at the first link that disagrees - here the
        package receipts, which still carry the original identity - rather than
        waiting for the genesis lookup. Either way the chain, not the shape of
        the identity, is what is being checked.
        """
        node, continuity = "stegnode-framework-elyria-7f3a", "framework-continuity-elyria-7f3a"
        row = evidence(node, continuity, self.candidate, self.bundle, self.ids)
        row["node_id"] = "stegnode-framework-someone-else"
        with self.assertRaisesRegex(RuntimeError, "package materialization identity mismatch"):
            m.validate_evidence(row, self.candidate, self.bundle, self.ids)

    def test_a_registrant_may_not_borrow_another_registrants_genesis(self) -> None:
        """Consistency is the whole constraint, so a foreign genesis receipt fails."""
        row = evidence("stegnode-custodian-acme", "custodian-continuity-acme",
                       self.candidate, self.bundle, self.ids)
        rows = row["continued_receipts"]
        foreign = dict(rows[0]["receipt"], node_id="stegnode-framework-elyria-7f3a")
        rows[0] = entry(foreign, 1, None)
        prev = rows[0]["entry_sha256"]
        for index in range(1, len(rows)):
            rows[index] = entry(rows[index]["receipt"], index + 1, prev)
            prev = rows[index]["entry_sha256"]
        row["package_materialization_entries"] = rows[1:5]
        row["bundle_materialization_entry"] = rows[-1]
        row["journal_replay"] = {"schema": "stegos.web_journal_replay_report.v1",
                                 **m.replay(rows), "authority_effect": "NONE"}
        with self.assertRaisesRegex(RuntimeError, "established node/device binding receipt missing"):
            m.validate_evidence(row, self.candidate, self.bundle, self.ids)

    def test_registration_lands_unadmitted_and_confers_no_authority(self) -> None:
        """Registration is orthogonal to admission: it grants standing to transport, nothing more."""
        row = evidence("stegnode-custodian-acme", "custodian-continuity-acme",
                       self.candidate, self.bundle, self.ids)
        self.assertEqual(row["state"], "MATERIALIZED_UNADMITTED")
        self.assertEqual(row["admission_state"], "UNADMITTED")
        self.assertEqual(row["execution_authority"], "NONE")
        genesis = row["continued_receipts"][0]["receipt"]
        self.assertEqual(genesis["schema"], GENESIS_SCHEMA)
        self.assertEqual(genesis["authority_effect"], "NONE")

    def test_the_web_node_prefix_belongs_to_the_browser_observation_class(self) -> None:
        """The one format constraint is local to a browser validator, not a general gate."""
        source = (ROOT / "workers/sv_dn1_browser_evidence_intr_ingress.py").read_text(encoding="utf-8")
        self.assertIn('startswith("stegnode-web-")', source)
        self.assertIn("AUTHENTIC_ESTABLISHED_STEGVERSE_WEB_NODE", source)
        # No other worker constrains the shape of a node identity.
        others = [p for p in (ROOT / "workers").glob("*.py")
                  if p.name != "sv_dn1_browser_evidence_intr_ingress.py"
                  and 'startswith("stegnode' in p.read_text(encoding="utf-8")]
        self.assertEqual(others, [], f"a node identity prefix is constrained outside the browser class: {others}")


if __name__ == "__main__":
    unittest.main()
