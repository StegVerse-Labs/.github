import json
import tempfile
from pathlib import Path

from workers import sv_dn1_browser_evidence_intr_ingress as ingress


def _make_source(root: Path):
    (root / "heartbeat_runtime").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)
    (root / "control").mkdir(parents=True)
    for rel in ["heartbeat_runtime/worker_runtime.py", "scripts/run_worker_runtime.py", "control/worker-registry.json"]:
        path = root / rel
        path.write_text("{}\n" if path.suffix == ".json" else "# source\n", encoding="utf-8")


def test_dispatch_requires_distinct_canonical_source_from_refresh_receipt():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        runtime = root / "runtime"
        source = root / "source"
        runtime.mkdir()
        source.mkdir()
        _make_source(source)
        receipt_path = runtime / ingress.REFRESH_RECEIPT_REL
        receipt_path.parent.mkdir(parents=True)
        receipt_path.write_text(json.dumps({
            "source_root": str(source),
            "network_fetch_performed": False,
            "credential_read_or_acquired": False,
        }), encoding="utf-8")
        assert ingress._canonical_source_from_refresh(runtime) == source.resolve()


def test_dispatch_rejects_runtime_as_its_own_source():
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td).resolve()
        _make_source(runtime)
        receipt_path = runtime / ingress.REFRESH_RECEIPT_REL
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps({
            "source_root": str(runtime),
            "network_fetch_performed": False,
            "credential_read_or_acquired": False,
        }), encoding="utf-8")
        assert ingress._canonical_source_from_refresh(runtime) is None
