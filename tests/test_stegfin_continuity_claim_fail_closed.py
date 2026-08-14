from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import unittest

from scripts.acquire_stegfin_continuity_claim import TASK_ID, acquire_claim


def write_heartbeat(path: Path, *, leases: list[dict] | None = None, epoch: int = 31) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "epoch": epoch,
        "subsignals": {
            "worker_coordination": {
                "active_leases": leases or [],
            }
        },
    }) + "\n", encoding="utf-8")


class StegFinContinuityClaimFailClosedTests(unittest.TestCase):
    def test_missing_coordination_state_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state_root = tmp_path / "state"
            with self.assertRaisesRegex(RuntimeError, "coordination state unavailable"):
                acquire_claim(
                    carrier_id="worker-a",
                    heartbeat_state=tmp_path / "missing-heartbeat.json",
                    state_root=state_root,
                    ttl_seconds=900,
                )
            self.assertFalse((state_root / "claims" / f"{TASK_ID}.json").exists())

    def test_malformed_coordination_state_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            heartbeat = tmp_path / "heartbeat.json"
            heartbeat.write_text("{not-json", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "coordination state malformed"):
                acquire_claim(
                    carrier_id="worker-a",
                    heartbeat_state=heartbeat,
                    state_root=tmp_path / "state",
                    ttl_seconds=900,
                )

    def test_missing_active_leases_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            heartbeat = tmp_path / "heartbeat.json"
            heartbeat.write_text(
                json.dumps({"epoch": 31, "subsignals": {"worker_coordination": {}}}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "missing active_leases"):
                acquire_claim(
                    carrier_id="worker-a",
                    heartbeat_state=heartbeat,
                    state_root=tmp_path / "state",
                    ttl_seconds=900,
                )

    def test_conflicting_resident_stegfin_lease_denies_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            heartbeat = tmp_path / "heartbeat.json"
            write_heartbeat(heartbeat, leases=[{
                "task_id": "STEGFIN-LIVE-ENTRY-003",
                "task_state": "ACTIVE",
                "fencing_token": 27,
            }])
            with self.assertRaisesRegex(RuntimeError, "resident StegFin worker"):
                acquire_claim(
                    carrier_id="worker-a",
                    heartbeat_state=heartbeat,
                    state_root=tmp_path / "state",
                    ttl_seconds=900,
                )

    def test_valid_coordination_records_verified_epoch_and_authority_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            heartbeat = tmp_path / "heartbeat.json"
            write_heartbeat(heartbeat, leases=[{
                "task_id": "OTHER-TASK",
                "task_state": "ACTIVE",
                "fencing_token": 27,
            }], epoch=31)
            claim = acquire_claim(
                carrier_id="worker-a",
                heartbeat_state=heartbeat,
                state_root=tmp_path / "state",
                ttl_seconds=900,
            )
            self.assertIs(claim["resident_conflict_checked"], True)
            self.assertEqual(claim["heartbeat_state_epoch_observed"], 31)
            self.assertEqual(claim["fencing_token"], 28)
            self.assertEqual(claim["credential_authority"], "TV/TVC")
            self.assertIs(claim["non_tv_tvc_secret_or_token_allowed"], False)
            self.assertIs(claim["github_token_required"], False)
            self.assertEqual(claim["wallet_signing_authority"], "USER_ONLY")
            self.assertEqual(claim["broadcast_authority"], "USER_ONLY")

    def test_concurrent_same_scope_acquisition_mints_only_one_active_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            heartbeat = tmp_path / "heartbeat.json"
            state_root = tmp_path / "state"
            write_heartbeat(heartbeat)
            barrier = threading.Barrier(3)
            claims: list[dict] = []
            errors: list[str] = []

            def contender(carrier_id: str) -> None:
                barrier.wait()
                try:
                    claims.append(acquire_claim(
                        carrier_id=carrier_id,
                        heartbeat_state=heartbeat,
                        state_root=state_root,
                        ttl_seconds=900,
                    ))
                except RuntimeError as exc:
                    errors.append(str(exc))

            first = threading.Thread(target=contender, args=("worker-a",))
            second = threading.Thread(target=contender, args=("worker-b",))
            first.start()
            second.start()
            barrier.wait()
            first.join(timeout=5)
            second.join(timeout=5)

            self.assertEqual(len(claims), 1)
            self.assertEqual(len(errors), 1)
            self.assertTrue(
                "claim acquisition already in progress" in errors[0]
                or "active continuity claim already exists" in errors[0]
            )
            persisted = json.loads(
                (state_root / "claims" / f"{TASK_ID}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(persisted["state"], "ACTIVE")
            self.assertEqual(persisted["claim_id"], claims[0]["claim_id"])
            self.assertEqual(persisted["fencing_token"], claims[0]["fencing_token"])


if __name__ == "__main__":
    unittest.main()
