import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_refresh():
    p = ROOT / "scripts" / "refresh_sovereign_worker_runtime_source.py"
    spec = importlib.util.spec_from_file_location("refresh_source", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_replace_dir_creates_missing_nested_destination_parent(tmp_path):
    mod = load_refresh()
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    staging = runtime / ".worker-source-refresh-staging"
    rel = Path("control/worker-registry.d")
    (source / rel).mkdir(parents=True)
    (source / rel / "worker.json").write_text("{}\n", encoding="utf-8")
    staging.mkdir(parents=True)
    assert not (runtime / "control").exists()
    copied = mod._replace_dir(source, runtime / rel, staging, rel)
    assert copied == 1
    assert (runtime / rel / "worker.json").is_file()
