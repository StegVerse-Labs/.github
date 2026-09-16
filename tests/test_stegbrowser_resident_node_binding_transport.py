from __future__ import annotations

# Exact-head regression coverage for the existing non-authorizing resident dispatcher.
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "resident_dispatch",
    ROOT / "scripts/dispatch_resident_execution_requests.py",
)
assert SPEC is not None and SPEC.loader is not None
dispatcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dispatcher)


def test_clean_exec_env_preserves_stegbrowser_nonsecret_runtime_path_bindings() -> None:
    source = {
        "PATH": "/usr/bin",
        "STEGVERSE_NODE_GENESIS_RECEIPT": "/state/node-receipt-1.json",
        "STEGVERSE_STEGOS_SOURCE_ROOT": "/state/StegOS",
        "STEGVERSE_EPHEMERAL_RUNTIME_BASE": "/state/event-runtime",
        "GITHUB_TOKEN": "must-not-flow",
    }
    env = dispatcher.clean_exec_env(source)
    assert env["STEGVERSE_NODE_GENESIS_RECEIPT"] == "/state/node-receipt-1.json"
    assert env["STEGVERSE_STEGOS_SOURCE_ROOT"] == "/state/StegOS"
    assert env["STEGVERSE_EPHEMERAL_RUNTIME_BASE"] == "/state/event-runtime"
    assert "GITHUB_TOKEN" not in env
    assert env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] == "NONE"
    assert env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] == "TV/TVC"


def test_exact_stegbrowser_selector_receives_path_bindings_without_new_authority() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Path(tmp)
        consumer = runtime / "scripts/consume_stegbrowser_runtime_connection_ingress_request.py"
        consumer.parent.mkdir(parents=True, exist_ok=True)
        consumer.write_text("# materialized test consumer\n", encoding="utf-8")
        captured: dict[str, object] = {}

        def runner(command, **kwargs):
            captured["command"] = command
            captured["env"] = kwargs["env"]
            payload = {
                "state": "A1_OBSERVED_CANONICAL_INVOCATION_PENDING_OR_BOUNDARY",
                "authority_effect": "NONE_OBSERVATION_SELECTION_AND_EXISTING_AUTHORITY_COMPOSITION_ONLY",
            }
            return subprocess.CompletedProcess(command, 0, json.dumps(payload) + "\n", "")

        env = {
            "PATH": "/usr/bin",
            "STEGVERSE_NODE_GENESIS_RECEIPT": "/state/node-receipt-1.json",
            "STEGVERSE_STEGOS_SOURCE_ROOT": "/state/StegOS",
            "STEGVERSE_EPHEMERAL_RUNTIME_BASE": "/state/event-runtime",
        }
        receipt = dispatcher.dispatch(
            ROOT,
            runtime,
            runner=runner,
            env=env,
            only_consumers=("stegbrowser_runtime_connection_ingress",),
        )
        forwarded = captured["env"]
        command = captured["command"]
        assert isinstance(forwarded, dict)
        assert isinstance(command, list)
        assert command[-4:] == [
            "--source-root",
            str(ROOT.resolve()),
            "--runtime-root",
            str(runtime.resolve()),
        ]
        assert forwarded["STEGVERSE_NODE_GENESIS_RECEIPT"] == env["STEGVERSE_NODE_GENESIS_RECEIPT"]
        assert forwarded["STEGVERSE_STEGOS_SOURCE_ROOT"] == env["STEGVERSE_STEGOS_SOURCE_ROOT"]
        assert forwarded["STEGVERSE_EPHEMERAL_RUNTIME_BASE"] == env["STEGVERSE_EPHEMERAL_RUNTIME_BASE"]
        assert receipt["selected_consumers"] == ["stegbrowser_runtime_connection_ingress"]
        assert receipt["request_failures"] == []
        assert receipt["github_token_runtime_authority"] == "NONE"
        assert receipt["request_dispatch_grants_authority"] is False
        assert receipt["second_machine_required"] is False
