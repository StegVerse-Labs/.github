from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from workers import sv002_public_profile_lease_resumer as resumer


class FakeLeaseState:
    LEASE_OPEN = "LEASE_OPEN"


class FakeMachine:
    SNAPSHOT_SCHEMA = "stegverse.esrl.lease-machine-snapshot/v1"

    def __init__(self, snapshot):
        self.value = json.loads(json.dumps(snapshot))

    @classmethod
    def from_snapshot(cls, value):
        if value.get("state") != "PUBLIC_VERIFYING":
            raise ValueError("expected PUBLIC_VERIFYING")
        return cls(value)

    def snapshot(self):
        return json.loads(json.dumps(self.value))

    def transition(self, target):
        if target != "LEASE_OPEN":
            raise ValueError("bad target")
        self.value["state"] = "LEASE_OPEN"
        self.value["history"] = list(self.value["history"]) + ["LEASE_OPEN"]


LEASE_MOD = SimpleNamespace(LeaseMachine=FakeMachine, LeaseState=FakeLeaseState)
PROFILE_MOD = SimpleNamespace()


def snapshot():
    return {
        "schema":"stegverse.esrl.lease-machine-snapshot/v1",
        "request":{"lease_id":"SV002-TEST","implementation_ref":"git:sv002@test"},
        "state":"PUBLIC_VERIFYING",
        "history":list(resumer.PUBLIC_VERIFYING_HISTORY),
        "credential_authority":"TV/TVC",
        "authority_effect":"NONE",
    }


def verified(**overrides):
    value = {
        "schema":"stegverse.universal-intr-public-profile-observation/v1",
        "verified":True,
        "observation_origin":"INDEPENDENT_PUBLIC_HTTPS",
        "observed_profile_url":resumer.PROFILE_URL,
        "profile_schema":"stegverse.universal-intr-profiled-ingress/v1",
        "profile_sha256":"a"*64,
        "required_profile":resumer.REQUIRED_PROFILE,
        "profile":{"schema":"stegverse.universal-intr-profiled-ingress/v1"},
        "credential_used":False,
        "credential_authority":"TV/TVC",
        "github_token_runtime_authority":"NONE",
        "execution_authority":"NONE",
        "authority_effect":"NONE_OBSERVATION_ONLY",
    }
    value.update(overrides)
    return value


class SV002PublicProfileLeaseResumerTests(unittest.TestCase):
    def run_resume(self, before, verifier_result):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        runtime = Path(td.name)
        path = runtime / "receipts/sovereign-network/sv002-public-observation/canonical-runtime-lease.snapshot.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(before), encoding="utf-8")
        verifier = mock.Mock(return_value=verifier_result)
        with mock.patch.object(resumer, "find_stegos_root", return_value=runtime),              mock.patch.object(resumer, "_load_stegos_modules", return_value=(LEASE_MOD, PROFILE_MOD)):
            result = resumer.resume_public_lease(
                control_root=runtime,
                execution_runtime=runtime,
                snapshot_path=path,
                expected_snapshot_digest=resumer.digest_uri(before),
                env={},
                verifier=verifier,
            )
        return runtime, path, verifier, result

    def test_exact_public_verifying_snapshot_advances_same_lease_to_open(self):
        runtime, path, verifier, result = self.run_resume(snapshot(), verified())
        self.assertEqual(result["state"], "LEASE_OPEN")
        self.assertEqual(result["lease_snapshot"]["history"], resumer.LEASE_OPEN_HISTORY)
        self.assertFalse(result["runtime_execution_authority_granted_by_observation"])
        verifier.assert_called_once_with(
            resumer.PROFILE_URL,
            required_profile=resumer.REQUIRED_PROFILE,
            timeout_seconds=10.0,
        )
        persisted = json.loads(path.read_text())
        self.assertEqual(persisted["request"], snapshot()["request"])
        observation = json.loads((path.parent / "canonical-runtime-public-profile.observation.json").read_text())
        self.assertFalse(observation["receiver_ready_claimed"])
        self.assertFalse(observation["round_trip_claimed"])
        self.assertFalse(observation["master_records_custody_claimed"])
        self.assertFalse(observation["sv002_principal_execution_claimed"])

    def test_wrong_observed_url_fails_closed(self):
        with self.assertRaisesRegex(resumer.SV002PublicLeaseOpenError, "observed_profile_url"):
            self.run_resume(snapshot(), verified(observed_profile_url="https://example.invalid/intr/profile"))

    def test_wrong_observation_origin_fails_closed(self):
        with self.assertRaisesRegex(resumer.SV002PublicLeaseOpenError, "observation_origin"):
            self.run_resume(snapshot(), verified(observation_origin="LOCAL_FIXTURE"))

    def test_missing_required_profile_identity_fails_closed(self):
        with self.assertRaisesRegex(resumer.SV002PublicLeaseOpenError, "required_profile"):
            self.run_resume(snapshot(), verified(required_profile="HIL:Ingress"))

    def test_snapshot_digest_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td)
            path=runtime/"canonical-runtime-lease.snapshot.json"
            before=snapshot()
            path.write_text(json.dumps(before))
            with self.assertRaisesRegex(resumer.SV002PublicLeaseOpenError, "digest_drift"):
                resumer.resume_public_lease(
                    control_root=runtime,
                    execution_runtime=runtime,
                    snapshot_path=path,
                    expected_snapshot_digest="sha256:"+"0"*64,
                    env={},
                    verifier=mock.Mock(),
                )

    def test_history_drift_fails_closed(self):
        before=snapshot()
        before["history"]=["ABSENT","PUBLIC_VERIFYING"]
        with self.assertRaisesRegex(resumer.SV002PublicLeaseOpenError, "precondition"):
            self.run_resume(before, verified())

    def test_existing_lease_open_requires_bound_public_observation(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td)
            path=runtime/"canonical-runtime-lease.snapshot.json"
            before=snapshot()
            before["state"]="LEASE_OPEN"
            before["history"]=list(resumer.LEASE_OPEN_HISTORY)
            path.write_text(json.dumps(before))
            with mock.patch.object(resumer, "find_stegos_root", return_value=runtime),                  mock.patch.object(resumer, "_load_stegos_modules", return_value=(LEASE_MOD, PROFILE_MOD)):
                with self.assertRaisesRegex(resumer.SV002PublicLeaseOpenError, "observation_missing"):
                    resumer.resume_public_lease(
                        control_root=runtime,
                        execution_runtime=runtime,
                        snapshot_path=path,
                        expected_snapshot_digest=resumer.digest_uri(before),
                        env={},
                        verifier=mock.Mock(),
                    )


if __name__ == "__main__":
    unittest.main()
