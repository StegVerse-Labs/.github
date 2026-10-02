import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_current_engineering_state_validator():
 p=subprocess.run([sys.executable,str(ROOT/"scripts/validate_current_engineering_state.py")],cwd=ROOT,text=True,capture_output=True)
 assert p.returncode==0,p.stderr+p.stdout
 assert "CURRENT_ENGINEERING_STATE_VALIDATION_PASS" in p.stdout
def test_historical_assessment_not_promoted():
 d=json.loads((ROOT/"data/current-engineering-state.json").read_text())
 assert d["historical_assessment"]["status"]=="IMMUTABLE_EXTERNAL_HISTORICAL_EVIDENCE"
 assert d["coverage"]["assessment_invariants_complete"] is False
 assert all(x["independent_observation_status"]=="NOT_OBSERVED" for x in d["invariants"])
