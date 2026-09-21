from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = "585cf38aad95fda69dbcbd0150c1256571f90feb"

FILES = [
    ROOT / "workers" / "healer_sovereign_scheduler_worker.py",
    ROOT / "scripts" / "consume_one_shot_resident_stack_activation_request.py",
    ROOT / "scripts" / "package_sovereign_control_plane_bundle.py",
]


def test_healer_freshness_requires_kv_schedule_merge():
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        assert REQUIRED in text, f"{path} does not require the KV schedule merge"


def test_old_steghealth_only_floor_is_retired_from_runtime_freshness_gates():
    retired = "8683611f035d684ea295020e2f55971d5797655b"
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        assert retired not in text, f"{path} still accepts the pre-KV schedule source floor"
