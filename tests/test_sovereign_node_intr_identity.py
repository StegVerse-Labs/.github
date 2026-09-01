from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bootstrap = load_module("bootstrap_sovereign_runtime_identity_test", "scripts/bootstrap_sovereign_runtime.py")
resolver = load_module("sovereign_node_repository_resolution_identity_test", "workers/sovereign_node_repository_resolution_worker.py")
evaluator_route = load_module("materialize_evaluator_intr_route_config_identity_test", "scripts/materialize_evaluator_intr_route_config.py")
sv002_route = load_module("materialize_sv002_observation_route_config_identity_test", "scripts/materialize_sv002_observation_route_config.py")


class SovereignNodeInTrIdentityTests(unittest.TestCase):
    def test_bootstrap_and_resolver_derive_same_stable_node_id(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            state = root / "state"
            source.mkdir()
            state.mkdir()
            left = bootstrap.derived_node_id(source, state)
            right = resolver.derived_node_id(source, state)
            self.assertEqual(left, right)
            self.assertRegex(left, r"^SV-NODE-[0-9a-f]{24}$")
            self.assertEqual(left, bootstrap.derived_node_id(source, state))

    def test_identity_changes_when_durable_state_root_changes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            state_a = root / "state-a"
            state_b = root / "state-b"
            source.mkdir()
            state_a.mkdir()
            state_b.mkdir()
            self.assertNotEqual(
                bootstrap.derived_node_id(source, state_a),
                bootstrap.derived_node_id(source, state_b),
            )


    def test_sv002_route_autodiscovers_canonical_local_repository_roots(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            home = root / "home"
            stegos = home / ".stegverse/repos/StegVerse-Labs/StegOS"
            micro = home / ".stegverse/repos/StegVerse-002/micro-node-runtime"
            (stegos / "stegos").mkdir(parents=True)
            (stegos / ".git").mkdir()
            (stegos / "stegos/universal_intr_transport.py").write_text(
                "# local canonical transport\n", encoding="utf-8"
            )
            provenance = micro / "experiments/self-characterization-001/CONSTRUCTION_PROVENANCE.v0.1.json"
            provenance.parent.mkdir(parents=True)
            (micro / ".git").mkdir()
            provenance.write_text("{}\n", encoding="utf-8")

            roots = sv002_route._roots({"HOME": str(home)})
            self.assertEqual(roots["StegVerse-Labs/StegOS"], stegos.resolve())
            self.assertEqual(
                roots["StegVerse-002/micro-node-runtime"], micro.resolve()
            )

    def test_sv002_route_runtime_root_falls_back_only_to_non_git_materialization(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / "runtime"
            (runtime / "workers").mkdir(parents=True)
            (runtime / "control").mkdir(parents=True)
            self.assertEqual(
                sv002_route._runtime_root({}, script_root=runtime),
                runtime.resolve(),
            )
            (runtime / ".git").mkdir()
            with self.assertRaisesRegex(
                sv002_route.PredicatePending, "resident runtime root unavailable"
            ):
                sv002_route._runtime_root({}, script_root=runtime)

    def test_sv002_route_autodiscovery_rejects_incomplete_repo(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            home = root / "home"
            stegos = home / ".stegverse/repos/StegVerse-Labs/StegOS"
            stegos.mkdir(parents=True)
            (stegos / ".git").mkdir()
            roots = sv002_route._roots({"HOME": str(home)})
            self.assertNotIn("StegVerse-Labs/StegOS", roots)

    def test_derived_v04_marker_unblocks_both_route_materializers(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            runtime = root / "runtime"
            site = root / "site"
            stegos = root / "stegos"
            micro = root / "micro"
            for path in (source, runtime, site, stegos, micro):
                path.mkdir()

            (stegos / "stegos").mkdir()
            (stegos / "stegos/universal_intr_transport.py").write_text(
                "# canonical transport fixture\n", encoding="utf-8"
            )

            provenance = micro / "experiments/self-characterization-001/CONSTRUCTION_PROVENANCE.v0.1.json"
            provenance.parent.mkdir(parents=True)
            provenance.write_text(
                json.dumps(
                    {
                        "schema": "stegverse.sv002-construction-provenance/v0.1",
                        "source_organization": {
                            "organization": "Admissible-Existence",
                            "availability_known": True,
                        },
                    }
                ),
                encoding="utf-8",
            )

            node_id = bootstrap.derived_node_id(source, runtime)
            marker = root / "node.json"
            marker.write_text(
                json.dumps(
                    {
                        "schema": "stegverse.sovereign-node-declaration/v0.4",
                        "declared": True,
                        "node_id": node_id,
                        "source_root": str(source.resolve()),
                        "state_root": str(runtime.resolve()),
                        "canonical_runtime_complete": True,
                        "durable_state_writable": True,
                        "continuity_model": "INDEPENDENT_OSCILLATOR_CONTINUITY",
                        "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
                        "credential_authority": "TV/TVC",
                        "github_token_required": False,
                        "authority_effect": "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
                    }
                ),
                encoding="utf-8",
            )

            evaluator_prior = evaluator_route.NODE_MARKERS
            sv002_prior = sv002_route.NODE_MARKERS
            evaluator_route.NODE_MARKERS = (marker,)
            sv002_route.NODE_MARKERS = (marker,)
            try:
                common = {
                    "STEGVERSE_HEARTBEAT_ROOT": str(runtime),
                    "STEGVERSE_STEGOS_ROOT": str(stegos),
                }
                evaluator = evaluator_route.materialize(
                    {
                        **common,
                        "STEGVERSE_SITE_ROOT": str(site),
                        "STEGVERSE_EVALUATOR_INTR_PORT": "8765",
                    },
                    output=root / "evaluator.json",
                )
                master_receipt=root/"master-records-reconstruction.json"
                sv002 = sv002_route.materialize(
                    {
                        **common,
                        "STEGVERSE_MICRO_NODE_RUNTIME_ROOT": str(micro),
                        "STEGVERSE_SV002_OBSERVE_PORT": "8766",
                        "STEGVERSE_SV002_MASTER_RECORDS_RECONSTRUCTION_RECEIPT": str(master_receipt),
                    },
                    output=root / "sv002.json",
                )
            finally:
                evaluator_route.NODE_MARKERS = evaluator_prior
                sv002_route.NODE_MARKERS = sv002_prior

            self.assertEqual(evaluator["config"]["boundary_identity_ref"], node_id)
            self.assertEqual(sv002["config"]["boundary_identity_ref"], node_id)
            self.assertEqual(evaluator["config"]["host"], "127.0.0.1")
            self.assertEqual(sv002["config"]["host"], "127.0.0.1")
            self.assertEqual(evaluator["config"]["credential_authority"], "TV/TVC")
            self.assertEqual(sv002["config"]["credential_authority"], "TV/TVC")
            self.assertEqual(evaluator["config"]["github_token_runtime_authority"], "NONE")
            self.assertEqual(sv002["config"]["github_token_runtime_authority"], "NONE")
            self.assertEqual(
                sv002["config"]["master_records_reconstruction_receipt"],
                str(master_receipt.resolve()),
            )


if __name__ == "__main__":
    unittest.main()
