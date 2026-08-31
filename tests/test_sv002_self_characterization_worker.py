from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sv002_self_characterization_worker",
    ROOT / "workers/sv002_self_characterization_worker.py",
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


class _Response:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.value).encode("utf-8")


class SV002SelfCharacterizationWorkerTests(unittest.TestCase):
    def fake_urlopen(self, value):
        def _open(url, timeout=3):
            self.assertTrue(url.startswith("http://127.0.0.1:11434/"))
            self.assertEqual(timeout, 3)
            return _Response(value)
        return _open

    def test_discovers_exact_requested_ollama_model_and_digest(self):
        digest = "a" * 64
        model, row = mod.discover_ollama_model(
            "http://127.0.0.1:11434",
            "reasoner:7b",
            urlopen=self.fake_urlopen(
                {"models": [{"name": "reasoner:7b", "digest": "sha256:" + digest}]}
            ),
        )
        self.assertEqual(model, "reasoner:7b")
        self.assertEqual(row["digest"], "sha256:" + digest)

    def test_unrequested_model_discovery_requires_single_non_reference_candidate(self):
        one, _ = mod.discover_ollama_model(
            "http://127.0.0.1:11434",
            None,
            urlopen=self.fake_urlopen(
                {"models": [{"name": "reasoner:latest", "digest": "b" * 64}]}
            ),
        )
        self.assertEqual(one, "reasoner:latest")

        ambiguous, row = mod.discover_ollama_model(
            "http://127.0.0.1:11434",
            None,
            urlopen=self.fake_urlopen(
                {
                    "models": [
                        {"name": "reasoner-a:latest", "digest": "b" * 64},
                        {"name": "reasoner-b:latest", "digest": "c" * 64},
                    ]
                }
            ),
        )
        self.assertIsNone(ambiguous)
        self.assertIsNone(row)

    def test_remote_endpoint_never_enters_local_discovery(self):
        called = False

        def _open(*args, **kwargs):
            nonlocal called
            called = True
            raise AssertionError("should not perform remote request")

        model, row = mod.discover_ollama_model(
            "https://models.example",
            "reasoner",
            urlopen=_open,
        )
        self.assertIsNone(model)
        self.assertIsNone(row)
        self.assertFalse(called)

    def test_builds_identity_from_local_tags_and_unique_process_executable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            executable = root / "ollama"
            executable.write_bytes(b"local ollama executable")
            proc = root / "proc"
            pid_dir = proc / "321"
            pid_dir.mkdir(parents=True)
            (pid_dir / "exe").symlink_to(executable)
            (pid_dir / "cmdline").write_bytes(b"/usr/local/bin/ollama\x00serve\x00")

            model_digest = "d" * 64
            identity = mod.build_ollama_subject_identity(
                "http://127.0.0.1:11434",
                "reasoner:latest",
                proc_root=proc,
                urlopen=self.fake_urlopen(
                    {
                        "models": [
                            {
                                "name": "reasoner:latest",
                                "digest": "sha256:" + model_digest,
                            }
                        ]
                    }
                ),
            )

            self.assertEqual(
                identity["schema"],
                "stegverse.self-characterization-runtime-identity/v0.1",
            )
            self.assertEqual(identity["model_id"], "reasoner:latest")
            self.assertEqual(identity["endpoint"], "http://127.0.0.1:11434")
            self.assertEqual(identity["model_digest"], model_digest)
            self.assertEqual(identity["process_id"], 321)
            self.assertEqual(identity["runtime_engine"], "ollama")
            self.assertEqual(identity["runtime_executable"], str(executable.resolve()))
            self.assertEqual(
                identity["runtime_digest"],
                hashlib.sha256(executable.read_bytes()).hexdigest(),
            )
            self.assertFalse(identity["network_fetch_performed"])
            self.assertFalse(identity["credential_required"])
            self.assertEqual(identity["authority_effect"], "NONE")

    def test_identity_fails_closed_when_process_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            executable = root / "ollama"
            executable.write_bytes(b"local ollama executable")
            proc = root / "proc"
            for pid in ("321", "322"):
                pid_dir = proc / pid
                pid_dir.mkdir(parents=True)
                (pid_dir / "exe").symlink_to(executable)
                (pid_dir / "cmdline").write_bytes(b"ollama\x00serve\x00")
            with self.assertRaisesRegex(RuntimeError, "unique local Ollama runtime process"):
                mod.build_ollama_subject_identity(
                    "http://127.0.0.1:11434",
                    "reasoner:latest",
                    proc_root=proc,
                    urlopen=self.fake_urlopen(
                        {
                            "models": [
                                {
                                    "name": "reasoner:latest",
                                    "digest": "e" * 64,
                                }
                            ]
                        }
                    ),
                )


    def test_builds_identity_from_local_llamacpp_process_and_exact_gguf(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            executable = root / "llama-server"
            executable.write_bytes(b"local llama.cpp server executable")
            model_path = root / "reasoner.gguf"
            model_path.write_bytes(b"exact local gguf bytes")
            proc = root / "proc"
            pid_dir = proc / "777"
            pid_dir.mkdir(parents=True)
            (pid_dir / "exe").symlink_to(executable)
            (pid_dir / "cwd").symlink_to(root)
            (pid_dir / "cmdline").write_bytes(
                (
                    str(executable)
                    + "\x00--model\x00"
                    + str(model_path)
                    + "\x00--port\x008080\x00--alias\x00reasoner\x00"
                ).encode("utf-8")
            )

            def _open(url, timeout=3):
                self.assertEqual(url, "http://127.0.0.1:8080/v1/models")
                self.assertEqual(timeout, 3)
                return _Response({"object": "list", "data": [{"id": "reasoner"}]})

            identity = mod.build_llamacpp_subject_identity(
                "http://127.0.0.1:8080",
                "reasoner",
                proc_root=proc,
                urlopen=_open,
            )
            self.assertEqual(identity["runtime_engine"], "llama.cpp")
            self.assertEqual(identity["model_id"], "reasoner")
            self.assertEqual(identity["process_id"], 777)
            self.assertEqual(identity["runtime_executable"], str(executable.resolve()))
            self.assertEqual(identity["model_artifact_path"], str(model_path.resolve()))
            self.assertEqual(
                identity["runtime_digest"],
                hashlib.sha256(executable.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                identity["model_digest"],
                hashlib.sha256(model_path.read_bytes()).hexdigest(),
            )
            self.assertFalse(identity["network_fetch_performed"])
            self.assertFalse(identity["credential_required"])
            self.assertEqual(identity["authority_effect"], "NONE")

    def test_llamacpp_identity_rejects_endpoint_port_process_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            executable = root / "llama-server"
            executable.write_bytes(b"server")
            model_path = root / "reasoner.gguf"
            model_path.write_bytes(b"model")
            proc = root / "proc"
            pid_dir = proc / "778"
            pid_dir.mkdir(parents=True)
            (pid_dir / "exe").symlink_to(executable)
            (pid_dir / "cwd").symlink_to(root)
            (pid_dir / "cmdline").write_bytes(
                (
                    str(executable)
                    + "\x00--model\x00"
                    + str(model_path)
                    + "\x00--port\x008081\x00"
                ).encode("utf-8")
            )
            with self.assertRaisesRegex(RuntimeError, "llama.cpp model/process identity"):
                mod.build_llamacpp_subject_identity(
                    "http://127.0.0.1:8080",
                    "reasoner",
                    proc_root=proc,
                    urlopen=lambda *args, **kwargs: _Response({"data": []}),
                )

    def test_llamacpp_identity_rejects_ambiguous_local_servers(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            executable = root / "llama-server"
            executable.write_bytes(b"server")
            model_path = root / "reasoner.gguf"
            model_path.write_bytes(b"model")
            proc = root / "proc"
            for pid in ("779", "780"):
                pid_dir = proc / pid
                pid_dir.mkdir(parents=True)
                (pid_dir / "exe").symlink_to(executable)
                (pid_dir / "cwd").symlink_to(root)
                (pid_dir / "cmdline").write_bytes(
                    (
                        str(executable)
                        + "\x00--model\x00"
                        + str(model_path)
                        + "\x00--port\x008080\x00--alias\x00reasoner\x00"
                    ).encode("utf-8")
                )
            with self.assertRaisesRegex(RuntimeError, "llama.cpp model/process identity"):
                mod.build_llamacpp_subject_identity(
                    "http://127.0.0.1:8080",
                    "reasoner",
                    proc_root=proc,
                    urlopen=lambda *args, **kwargs: _Response({"data": [{"id": "reasoner"}]}),
                )


    def test_autodiscovers_unique_ollama_principal_without_environment_endpoint(self):
        def _open(url, timeout=3):
            self.assertEqual(url, "http://127.0.0.1:11434/api/tags")
            return _Response(
                {"models": [{"name": "reasoner:latest", "digest": "f" * 64}]}
            )

        endpoint, model, source = mod.discover_local_principal(
            None,
            None,
            urlopen=_open,
            proc_root=Path("/definitely-not-present"),
        )
        self.assertEqual(endpoint, "http://127.0.0.1:11434")
        self.assertEqual(model, "reasoner:latest")
        self.assertEqual(source, "CANONICAL_OLLAMA_LOOPBACK_DISCOVERY")

    def test_autodiscovers_unique_llamacpp_principal_from_local_process(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            executable = root / "llama-server"
            executable.write_bytes(b"server")
            model_path = root / "reasoner.gguf"
            model_path.write_bytes(b"gguf")
            proc = root / "proc"
            pid_dir = proc / "881"
            pid_dir.mkdir(parents=True)
            (pid_dir / "exe").symlink_to(executable)
            (pid_dir / "cwd").symlink_to(root)
            (pid_dir / "cmdline").write_bytes(
                (
                    str(executable)
                    + "\x00--model\x00"
                    + str(model_path)
                    + "\x00--port\x008321\x00--alias\x00reasoner\x00"
                ).encode("utf-8")
            )

            def _open(url, timeout=3):
                if url == "http://127.0.0.1:11434/api/tags":
                    raise OSError("no ollama")
                self.assertEqual(url, "http://127.0.0.1:8321/v1/models")
                return _Response({"data": [{"id": "reasoner"}]})

            endpoint, model, source = mod.discover_local_principal(
                None,
                None,
                proc_root=proc,
                urlopen=_open,
            )
            self.assertEqual(endpoint, "http://127.0.0.1:8321")
            self.assertEqual(model, "reasoner")
            self.assertEqual(source, "UNIQUE_LOCAL_LLAMACPP_PROCESS_DISCOVERY")

    def test_autodiscovery_fails_closed_on_multiple_llamacpp_principals(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            executable = root / "llama-server"
            executable.write_bytes(b"server")
            model_path = root / "reasoner.gguf"
            model_path.write_bytes(b"gguf")
            proc = root / "proc"
            for pid, port in (("882", 8322), ("883", 8323)):
                pid_dir = proc / pid
                pid_dir.mkdir(parents=True)
                (pid_dir / "exe").symlink_to(executable)
                (pid_dir / "cwd").symlink_to(root)
                (pid_dir / "cmdline").write_bytes(
                    (
                        str(executable)
                        + "\x00--model\x00"
                        + str(model_path)
                        + f"\x00--port\x00{port}\x00"
                    ).encode("utf-8")
                )

            endpoint, model, source = mod.discover_local_principal(
                None,
                None,
                proc_root=proc,
                urlopen=lambda *args, **kwargs: (_ for _ in ()).throw(OSError("no ollama")),
            )
            self.assertIsNone(endpoint)
            self.assertIsNone(model)
            self.assertEqual(source, "AMBIGUOUS_LOCAL_LLAMACPP_PRINCIPALS")

    def test_explicit_endpoint_and_model_take_priority_over_discovery(self):
        endpoint, model, source = mod.discover_local_principal(
            "http://127.0.0.1:9999",
            "explicit-reasoner",
            proc_root=Path("/definitely-not-present"),
            urlopen=lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("explicit binding should not probe")
            ),
        )
        self.assertEqual(endpoint, "http://127.0.0.1:9999")
        self.assertEqual(model, "explicit-reasoner")
        self.assertEqual(source, "EXPLICIT_ENDPOINT_AND_MODEL")

    def test_reference_model_cannot_be_principal(self):
        with self.assertRaisesRegex(RuntimeError, "reference model"):
            mod.build_ollama_subject_identity(
                "http://127.0.0.1:11434",
                "stegverse-reference-lm-v1",
                urlopen=self.fake_urlopen({"models": []}),
            )

    def test_explicit_subject_identity_must_match_endpoint_and_model(self):
        prior = dict(os.environ)
        try:
            os.environ["STEGVERSE_SELF_CHAR_SUBJECT_IDENTITY_JSON"] = json.dumps(
                {
                    "schema": "stegverse.self-characterization-runtime-identity/v0.1",
                    "model_id": "reasoner:latest",
                    "endpoint": "http://127.0.0.1:11434",
                }
            )
            identity, error = mod.resolve_subject_identity(
                "http://127.0.0.1:11434",
                "reasoner:latest",
            )
            self.assertIsNotNone(identity)
            self.assertIsNone(error)

            identity, error = mod.resolve_subject_identity(
                "http://127.0.0.1:11434",
                "different-model",
            )
            self.assertIsNone(identity)
            self.assertEqual(error, "EXPLICIT_SUBJECT_IDENTITY_BINDING_MISMATCH")
        finally:
            os.environ.clear()
            os.environ.update(prior)

    def test_master_records_reconstruction_pending_when_verifier_not_materialized(self):
        with tempfile.TemporaryDirectory() as td:
            state_root = Path(td) / "state"
            state_root.mkdir()
            with patch.object(mod, "find_repo", return_value=(None, [{"present": False}])):
                result = mod.attempt_master_records_reconstruction(state_root)
            self.assertEqual(result["state"], "PENDING")
            self.assertEqual(
                result["blocker"],
                "MASTER_RECORDS_RECONSTRUCTION_VERIFIER_NOT_MATERIALIZED",
            )
            self.assertFalse(result["network_fetch_performed"])
            self.assertFalse(result["credential_required"])
            self.assertEqual(result["authority_effect"], "NONE")

    def test_master_records_reconstruction_pass_is_retained_separately(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state_root = root / "state"
            master = root / "master-records"
            (master / "scripts").mkdir(parents=True)
            state_root.mkdir()
            verifier = master / "scripts/verify_sv002_self_characterization_reconstruction.py"
            verifier.write_text("# synthetic verifier placeholder\n", encoding="utf-8")

            class Completed:
                returncode = 0
                stdout = ""
                stderr = ""

            def fake_run(args, **kwargs):
                output = Path(args[args.index("--output") + 1])
                output.write_text(
                    json.dumps(
                        {
                            "schema": "master-records.sv002-self-characterization-reconstruction/v0.1",
                            "experiment_id": "STEGVERSE-002-SELF-CHARACTERIZATION-001",
                            "status": "PASS",
                            "reconstruction": "PASS",
                            "authority_boundary": {
                                "receipt_alone_establishes_custody": False,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return Completed()

            with patch.object(mod, "find_repo", return_value=(master, [])):
                with patch.object(mod.subprocess, "run", side_effect=fake_run):
                    result = mod.attempt_master_records_reconstruction(state_root)

            self.assertEqual(result["state"], "PASS")
            self.assertTrue(Path(result["receipt_path"]).is_file())
            self.assertEqual(result["receipt"]["reconstruction"], "PASS")
            self.assertFalse(
                result["receipt"]["authority_boundary"]["receipt_alone_establishes_custody"]
            )
            self.assertEqual(result["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
