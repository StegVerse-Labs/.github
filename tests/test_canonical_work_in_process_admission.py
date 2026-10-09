#!/usr/bin/env python3
"""The CanonicalWork bootstrap admits in-process: no listener, socket or timeout (#3012 ECO-08)."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
SHARDS = ROOT / "data" / "canonical-task-records"
TASK_ID = "STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


bootstrap = load_module("canonical_work_bootstrap_in_process", ROOT / "scripts" / "run_canonical_work_event_bootstrap.py")
ingress = load_module("canonical_work_intr_ingress_in_process", ROOT / "workers" / "canonical_work_intr_ingress.py")


class _NoProcess:
    pid = 0


def _no_network(*_args, **_kwargs):
    raise AssertionError("in-process admission must not open a socket or listener")


class CanonicalWorkInProcessAdmissionTests(unittest.TestCase):
    def setUp(self):
        # Exercise the in-process path with an origin the shared validator admits;
        # the bootstrap's declared origin is covered by its own refusal test below.
        patcher = patch.object(bootstrap, "TRANSPORT_ORIGIN", ingress.transport_boundary.ORIGIN_NODE)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _request(self, runtime: Path) -> Path:
        # The builder subprocess resolves repository packages the way its workflow does.
        with patch.dict(os.environ, {"PYTHONPATH": str(ROOT)}):
            return bootstrap.run_builder(task_id=TASK_ID, runtime=runtime, registry=REGISTRY, registry_shards=SHARDS, without_carrier_binding=True)

    def test_absent_listener_does_not_block_admission(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request_path = self._request(runtime)
            request = json.loads(request_path.read_text(encoding="utf-8"))
            with patch("urllib.request.urlopen", _no_network), patch("socket.socket", _no_network), \
                    patch("socket.create_connection", _no_network), \
                    patch.object(ingress.subprocess, "Popen", return_value=_NoProcess()):
                receipt = bootstrap.post_one(runtime=runtime, request_path=request_path, admit=ingress.admit)
            self.assertEqual(receipt["state"], "INGRESS_ADMITTED")
            self.assertEqual(receipt["request_hash"], request["request_hash"])
            self.assertTrue(receipt["write_once_persisted"])
            self.assertEqual(json.loads(Path(receipt["queue_ref"]).read_text(encoding="utf-8"))["request_hash"], request["request_hash"])

    def test_same_request_admitted_twice_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request_path = self._request(runtime)
            with patch.object(ingress.subprocess, "Popen", return_value=_NoProcess()) as popen:
                first = bootstrap.post_one(runtime=runtime, request_path=request_path, admit=ingress.admit)
                queued = Path(first["queue_ref"]).read_bytes()
                second = bootstrap.post_one(runtime=runtime, request_path=request_path, admit=ingress.admit)
            self.assertEqual(second["request_hash"], first["request_hash"])
            self.assertEqual(second["admitted_at"], first["admitted_at"])
            self.assertEqual(Path(first["queue_ref"]).read_bytes(), queued)
            # The replay returns the write-once receipt; the consumer is not dispatched again.
            self.assertEqual(popen.call_count, 1)

    def test_malformed_request_is_refused_typed_without_effect(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request_path = self._request(runtime)
            request = json.loads(request_path.read_text(encoding="utf-8"))
            request["request_hash"] = "sha256:" + "0" * 64
            request_path.write_text(json.dumps(request), encoding="utf-8")
            with patch.object(ingress.subprocess, "Popen", return_value=_NoProcess()) as popen:
                with self.assertRaises(SystemExit) as ctx:
                    bootstrap.post_one(runtime=runtime, request_path=request_path, admit=ingress.admit)
            self.assertTrue(str(ctx.exception).startswith("FAIL_CLOSED: canonical_work_intr_admission_refused:"))
            self.assertFalse((runtime / ingress.REQUEST_DIR_REL).exists())
            self.assertFalse((runtime / ingress.RECEIPT_DIR_REL).exists())
            popen.assert_not_called()

    def test_ingress_admitted_never_claims_downstream_completion(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request_path = self._request(runtime)
            with patch.object(ingress.subprocess, "Popen", return_value=_NoProcess()):
                receipt = bootstrap.post_one(runtime=runtime, request_path=request_path, admit=ingress.admit)
            self.assertFalse(receipt["runtime_execution_attempted"])
            self.assertFalse(receipt["claim_or_fence_minted"])
            self.assertEqual(receipt["authority_effect"], "INGRESS_TRANSITION_ONLY")

    def test_declared_sovereign_node_origin_is_refused_typed_without_effect(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td).resolve()
            request_path = self._request(runtime)
            with patch.object(bootstrap, "TRANSPORT_ORIGIN", "SOVEREIGN_NODE"), \
                    patch.object(ingress.subprocess, "Popen", return_value=_NoProcess()) as popen:
                with self.assertRaises(SystemExit) as ctx:
                    bootstrap.post_one(runtime=runtime, request_path=request_path, admit=ingress.admit)
            self.assertEqual(str(ctx.exception), "FAIL_CLOSED: canonical_work_intr_admission_refused:transport_origin_header_invalid")
            self.assertFalse((runtime / ingress.RECEIPT_DIR_REL).exists())
            popen.assert_not_called()

    def test_bootstrap_opens_no_loopback_connection(self):
        source = (ROOT / "scripts" / "run_canonical_work_event_bootstrap.py").read_text(encoding="utf-8")
        for forbidden in ("urlopen", "urllib.request", "http.client", "import socket", "shared_ingress.Server", "handle_request"):
            self.assertNotIn(forbidden, source)
        self.assertIn('getattr(shared_ingress, "admit_canonical_work", None)', source)


if __name__ == "__main__":
    unittest.main()
