from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.consume_resident_rendezvous import (
    GADI_CONSUMER,
    GADI_EXPECTED,
    ResidentRendezvousConsumerError,
    consume,
    sha256_uri,
    validate_fetch,
)


def gadi_fetch(node_ref: str = "SV-NODE-0123456789abcdef01234567") -> dict:
    inner = dict(GADI_EXPECTED)
    request = {
        "schema": "stegverse.resident-rendezvous.request/v1",
        "request_id": "rendezvous-gadi-001",
        "target_node_ref": node_ref,
        "consumer": GADI_CONSUMER,
        "resident_request": inner,
        "resident_request_sha256": sha256_uri(inner),
        "submitted_at": "2099-01-01T00:00:00Z",
        "expires_at": "2099-01-01T01:00:00Z",
        "submitter_authorization_ref": "kv-skap:opaque-correlation-only",
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    return {
        "schema": "stegverse.resident-rendezvous.fetch-result/v1",
        "state": "REQUEST_AVAILABLE",
        "request": request,
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_REQUEST_ONLY",
    }


class ReusableGadiResidentRendezvousTests(unittest.TestCase):
    def test_gadi_exact_contract_drift_fails_closed(self):
        value = gadi_fetch()
        value["request"]["resident_request"]["request_granted_authority"] = True
        value["request"]["resident_request_sha256"] = sha256_uri(
            value["request"]["resident_request"]
        )
        with self.assertRaisesRegex(
            ResidentRendezvousConsumerError,
            "GADI runtime-observation request contract mismatch",
        ):
            validate_fetch(
                value,
                node_ref="SV-NODE-0123456789abcdef01234567",
                consumer=GADI_CONSUMER,
            )

    def test_gadi_uses_registered_dispatcher_and_transport_only_ack(self):
        runtime = Path(tempfile.mkdtemp())
        dispatcher = runtime / "scripts/dispatch_resident_execution_requests.py"
        dispatcher.parent.mkdir(parents=True)
        dispatcher.write_text("# placeholder\n", encoding="utf-8")
        posted = []
        commands = []
        node_ref = "SV-NODE-0123456789abcdef01234567"

        def getter(_url, *, node_ref: str):
            return gadi_fetch(node_ref)

        def poster(url, payload, *, node_ref: str):
            posted.append((url, payload, node_ref))
            if url.endswith("/advertisements"):
                return {"state": "ADVERTISED", "gateway_execution_authority": "NONE"}
            return {"state": "ACKNOWLEDGED"}

        def runner(command, **_kwargs):
            commands.append(command)
            receipts = runtime / "receipts/sovereign-host"
            receipts.mkdir(parents=True, exist_ok=True)
            (receipts / "resident-request-dispatch.latest.json").write_text(
                json.dumps({
                    "schema": "stegverse.resident-request-dispatch/v1",
                    "state": "DISPATCH_COMPLETE",
                    "selection_scope": "EXACT_SELECTOR",
                    "selected_consumers": [GADI_CONSUMER],
                    "consumer_count": 1,
                }),
                encoding="utf-8",
            )
            (receipts / "gadi-runtime-observation-request-consumption.latest.json").write_text(
                json.dumps({
                    "schema": "stegverse.gadi-runtime-observation-request-consumption/v1",
                    "state": "OBSERVATION_ATTEMPT_RECORDED",
                    "request_granted_authority": False,
                    "claim_or_fence_created_by_consumer": False,
                    "authority_effect": "NONE_OBSERVATION_REQUEST_ONLY",
                }),
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(command, 0, "", "")

        result = consume(
            runtime,
            base_url="https://stegverse.org",
            node_ref=node_ref,
            source_root=runtime,
            consumer=GADI_CONSUMER,
            runner=runner,
            getter=getter,
            poster=poster,
            env={"PATH": "/usr/bin"},
        )

        self.assertEqual(result["state"], "ATTEMPT_RECORDED")
        self.assertEqual(result["consumer"], GADI_CONSUMER)
        self.assertEqual(result["gateway_execution_authority"], "NONE")
        self.assertEqual(result["user_verification_authority"], "KV/SKAP Vault")
        self.assertEqual(result["target_node_identity_role"], "ROUTING_ONLY")
        self.assertFalse(result["network_source_fetch_performed"])
        self.assertTrue(
            (runtime / "control/resident-execution-request.d/gadi-runtime-observation-001.json").is_file()
        )
        self.assertIn("--only-consumer", commands[0])
        self.assertIn(GADI_CONSUMER, commands[0])
        advertisement = posted[0][1]
        self.assertEqual(advertisement["consumer"], GADI_CONSUMER)
        self.assertEqual(advertisement["current_resident_request_id"], GADI_EXPECTED["request_id"])
        acknowledgement = posted[-1][1]
        self.assertEqual(acknowledgement["resident_consumption_state"], "ATTEMPT_RECORDED")
        self.assertEqual(acknowledgement["gateway_execution_authority"], "NONE")
        self.assertFalse(acknowledgement["terminal_chain_observed"])

    def test_unregistered_consumer_fails_before_dispatch(self):
        runtime = Path(tempfile.mkdtemp())
        with self.assertRaisesRegex(ResidentRendezvousConsumerError, "not registered"):
            consume(
                runtime,
                base_url="https://stegverse.org",
                node_ref="SV-NODE-0123456789abcdef01234567",
                consumer="not_registered",
                getter=lambda *_args, **_kwargs: {},
                poster=lambda *_args, **_kwargs: {},
                env={"PATH": "/usr/bin"},
            )


if __name__ == "__main__":
    unittest.main()
