from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
WORKER_PATH = ROOT / "workers" / "governance_sovereign_task_observer_worker.py"
spec = importlib.util.spec_from_file_location("governance_sovereign_task_observer_worker", WORKER_PATH)
worker = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(worker)


class GovernanceSovereignTaskObserverTests(unittest.TestCase):
    def build_source(self, root: Path, include_decision: bool = False) -> None:
        (root / "automation").mkdir(parents=True)
        (root / "scripts").mkdir(parents=True)
        (root / "docs" / "governance").mkdir(parents=True)
        (root / "evidence" / "cge-decision-issuer-architecture").mkdir(parents=True)
        (root / "GOVERNANCE_MIRROR_HANDOFF.md").write_text("Governance\n", encoding="utf-8")
        (root / "docs" / "governance" / "CGE_DECISION_ISSUER_ARCHITECTURE_MIRROR_HANDOFF.md").write_text("CGE\n", encoding="utf-8")
        registry = {
            "registry_version": "1.0.0",
            "owner": "StegVerse-Labs/Governance",
            "tasks": [{
                "id": "CGE-DECISION-ISSUER-ARCHITECTURE-OWNERSHIP-001",
                "title": "watch",
                "organization": "StegVerse-Labs",
                "repository": "Governance",
                "path": "docs/governance/CGE_DECISION_ISSUER_ARCHITECTURE_MIRROR_HANDOFF.md",
                "mode": "evidence_watch",
                "prerequisites": [],
                "completion_condition": {
                    "type": "file_exists",
                    "path": "evidence/cge-decision-issuer-architecture/latest.json"
                },
                "evidence_path": "evidence/cge-decision-issuer-architecture/latest.json",
                "status": "blocked"
            }]
        }
        (root / "automation" / "governance_task_registry.json").write_text(json.dumps(registry), encoding="utf-8")
        script = root / "scripts" / "run_governance_tasks.py"
        script.write_text(
            "import argparse,json,pathlib\n"
            "p=argparse.ArgumentParser(); p.add_argument('--receipt',required=True); a=p.parse_args()\n"
            "root=pathlib.Path(__file__).resolve().parents[1]\n"
            "decision=root/'evidence/cge-decision-issuer-architecture/latest.json'\n"
            "state='completed' if decision.is_file() else 'blocked'\n"
            "out={'registry_version':'1.0.0','repository':'StegVerse-Labs/Governance','validation_status':'pass','validation_errors':[],'tasks':[{'id':'CGE-DECISION-ISSUER-ARCHITECTURE-OWNERSHIP-001','state':state}]}\n"
            "path=pathlib.Path(a.receipt); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(out))\n",
            encoding="utf-8",
        )
        if include_decision:
            (root / "evidence" / "cge-decision-issuer-architecture" / "latest.json").write_text("{}\n", encoding="utf-8")

    def invocation(self) -> dict:
        return {
            "task": {
                "task_id": worker.TASK_ID,
                "worker_id": worker.WORKER_ID,
                "claim_id": "claim-test-001",
            },
            "handoff": {
                "authority": {
                    "credential_authority": "TV/TVC",
                    "github_token_required": False,
                    "non_tv_tvc_secret_or_token_allowed": False,
                    "repository_writeback_authority": False,
                    "heartbeat_authority": False,
                }
            },
        }

    def test_blocked_watch_is_valid_sovereign_observation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            home = base / "home"
            source = base / "Governance"
            home.mkdir(); source.mkdir()
            self.build_source(source, include_decision=False)
            marker = base / "node.json"
            marker.write_text(json.dumps({
                "declared": True,
                "credential_authority": "TV/TVC",
                "github_token_required": False,
                "declaration_source": "unit-test",
            }), encoding="utf-8")
            clean_env = {
                "HOME": str(home),
                worker.ROOT_ENV: str(source),
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            }
            with patch.dict(os.environ, clean_env, clear=True), patch.object(worker, "NODE_MARKERS", (marker,)):
                receipt = worker.execute(self.invocation())
            self.assertEqual(receipt["state"], "COMPLETE")
            self.assertEqual(receipt["cge_architecture_watch_state"], "blocked")
            self.assertFalse(receipt["architecture_decision_receipt_observed"])
            self.assertFalse(receipt["github_token_used"])
            self.assertFalse(receipt["repository_writeback_performed"])
            self.assertFalse(receipt["heartbeat_effect"])

    def test_hosted_environment_is_rejected(self) -> None:
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "hosted environments"):
                worker.execute(self.invocation())

    def test_github_token_environment_is_rejected(self) -> None:
        with patch.dict(os.environ, {"GITHUB_TOKEN": "forbidden"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "credential-bearing environment"):
                worker.execute(self.invocation())

    def test_invocation_cannot_grant_writeback_or_heartbeat_authority(self) -> None:
        bad = self.invocation()
        bad["handoff"]["authority"]["repository_writeback_authority"] = True
        with self.assertRaisesRegex(RuntimeError, "write back"):
            worker.validate_invocation(bad)
        bad = self.invocation()
        bad["handoff"]["authority"]["heartbeat_authority"] = True
        with self.assertRaisesRegex(RuntimeError, "heartbeat authority"):
            worker.validate_invocation(bad)


if __name__ == "__main__":
    unittest.main()
