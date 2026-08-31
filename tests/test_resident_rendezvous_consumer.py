from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.consume_resident_rendezvous import (
    ResidentRendezvousConsumerError,
    consume,
    sha256_uri,
    validate_fetch,
)


def resident_request():
    return {
        "schema": "stegverse.resident-execution-request/v1",
        "request_id": "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-001",
        "state": "REQUESTED",
        "task_id": "SHWP-STEGOS-KV-INTR-CHAIN-001",
        "mode": "STEGOS_KV_INTR_CHAIN",
        "entrypoint": "scripts/refresh_and_execute_resident_task.py",
        "steps": [
            "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001",
            "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001",
            "SHWP-DEVICE-KV-INTR-OBSERVATION-001",
            "SHWP-ENDPOINT-FANOUT-SOVEREIGN-RUNTIME-001",
        ],
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "network_source_fetch_allowed": False,
        "second_machine_required": False,
        "authority_effect": "NONE_REQUEST_ONLY",
        "note": "Advance existing admitted chain only.",
    }


def fetch_result():
    inner = resident_request()
    request = {
        "schema": "stegverse.resident-rendezvous.request/v1",
        "request_id": "rendezvous-kv-001",
        "target_node_ref": "node:primary",
        "consumer": "stegos_kv_intr_chain",
        "resident_request": inner,
        "resident_request_sha256": sha256_uri(inner),
        "submitted_at": "2099-01-01T00:00:00Z",
        "expires_at": "2099-01-01T01:00:00Z",
        "submitter_authorization_ref": "owner:opaque",
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    return {
        "schema": "stegverse.resident-rendezvous.fetch-result/v1",
        "state": "REQUEST_AVAILABLE",
        "request": request,
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_REQUEST_ONLY",
    }


class ResidentRendezvousConsumerTests(unittest.TestCase):
    def test_validate_fetch_rejects_task_drift(self):
        value = fetch_result()
        value["request"]["resident_request"]["task_id"] = "OTHER"
        value["request"]["resident_request_sha256"] = sha256_uri(
            value["request"]["resident_request"]
        )
        with self.assertRaisesRegex(
            ResidentRendezvousConsumerError, "task_id mismatch"
        ):
            validate_fetch(value, node_ref="node:primary")

    def test_consume_materializes_and_dispatches_existing_consumer(self):
        runtime = Path(tempfile.mkdtemp())
        (runtime / "scripts").mkdir()
        (runtime / "scripts" / "dispatch_resident_execution_requests.py").write_text(
            "# placeholder\n", encoding="utf-8"
        )
        posted = []

        def getter(url, *, node_ref):
            self.assertEqual(node_ref, "node:primary")
            return fetch_result()

        def poster(url, payload, *, node_ref):
            self.assertEqual(node_ref, "node:primary")
            posted.append(payload)
            return {"state": "ACKNOWLEDGED"}

        def runner(command, **kwargs):
            dispatch = {
                "schema": "stegverse.resident-request-dispatch/v1",
                "state": "DISPATCH_COMPLETE",
                "selection_scope": "EXACT_SELECTOR",
                "selected_consumers": ["stegos_kv_intr_chain"],
                "consumer_count": 1,
            }
            chain = {
                "schema": "stegverse.stegos-kv-intr-chain.resident-consumption/v1",
                "state": "ATTEMPT_RECORDED",
                "terminal_chain_observed": False,
            }
            path = runtime / "receipts/sovereign-host"
            path.mkdir(parents=True, exist_ok=True)
            (path / "resident-request-dispatch.latest.json").write_text(
                json.dumps(dispatch), encoding="utf-8"
            )
            (path / "stegos-kv-intr-chain-consumption.latest.json").write_text(
                json.dumps(chain), encoding="utf-8"
            )
            return subprocess.CompletedProcess(command, 0, "", "")

        result = consume(
            runtime,
            base_url="https://stegverse.org",
            node_ref="node:primary",
            source_root=runtime,
            runner=runner,
            getter=getter,
            poster=poster,
            env={"PATH": "/usr/bin"},
        )
        self.assertEqual(result["state"], "ATTEMPT_RECORDED")
        self.assertIs(result["runtime_execution_attempted"], True)
        self.assertIs(result["network_source_fetch_performed"], False)
        self.assertEqual(result["gateway_execution_authority"], "NONE")
        self.assertTrue(
            (
                runtime
                / "control/resident-execution-request.d/stegos-kv-intr-chain-001.json"
            ).is_file()
        )
        self.assertTrue(posted)
        self.assertEqual(posted[-1]["gateway_execution_authority"], "NONE")

    def test_no_request_is_non_authorizing(self):
        runtime = Path(tempfile.mkdtemp())
        result = consume(
            runtime,
            base_url="https://stegverse.org",
            node_ref="node:primary",
            source_root=runtime,
            getter=lambda *_args, **_kwargs: {
                "schema": "stegverse.resident-rendezvous.fetch-result/v1",
                "state": "NO_REQUEST",
                "gateway_execution_authority": "NONE",
                "authority_effect": "NONE",
            },
            poster=lambda *_args, **_kwargs: {},
            env={"PATH": "/usr/bin"},
        )
        self.assertEqual(result["state"], "NO_REQUEST")
        self.assertIs(result["runtime_execution_attempted"], False)

    def test_hosted_environment_rejected(self):
        runtime = Path(tempfile.mkdtemp())
        with self.assertRaisesRegex(
            ResidentRendezvousConsumerError, "hosted environment"
        ):
            consume(
                runtime,
                base_url="https://stegverse.org",
                node_ref="node:primary",
                getter=lambda *_args, **_kwargs: {},
                poster=lambda *_args, **_kwargs: {},
                env={"PATH": "/usr/bin", "GITHUB_ACTIONS": "true"},
            )


if __name__ == "__main__":
    unittest.main()
