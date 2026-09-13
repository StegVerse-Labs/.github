import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/validate_completion_evidence_v1.py'
def mod():
 s=importlib.util.spec_from_file_location('cev1',SCRIPT); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def test_legacy_completion_is_not_reportable():
 m=mod(); r={'completion':{'claimed':True,'validated':True}}
 m.validate(Path('legacy.json'),r); assert m.classify(r)=='LEGACY_UNQUALIFIED_NON_AUTHORITATIVE'
def test_v1_requires_evidence_class():
 m=mod()
 with pytest.raises(SystemExit): m.validate(Path('x.json'),{'completion_evidence_contract_version':'v1','completion':{'claimed':True,'validated':True}})
def test_v1_rejects_weaker_terminal_class():
 m=mod(); r={'completion_evidence_contract_version':'v1','completion':{'claimed':True,'validated':True,'evidence_class':'CI_VALIDATED','terminal_evidence_class':'SANDBOX_RUNTIME_OBSERVED','evidence_refs':['run:1']}}
 with pytest.raises(SystemExit): m.validate(Path('x.json'),r)
def test_v1_accepts_terminal_evidence():
 m=mod(); r={'completion_evidence_contract_version':'v1','completion':{'claimed':True,'validated':True,'evidence_class':'MASTER_RECORDS_RECONSTRUCTED','terminal_evidence_class':'SANDBOX_RUNTIME_OBSERVED','evidence_refs':['mr:1']}}
 m.validate(Path('x.json'),r); assert m.classify(r)=='QUALIFIED_TERMINAL_SATISFIED'
def test_end_to_end_flag_requires_end_to_end():
 m=mod(); r={'completion_evidence_contract_version':'v1','completion':{'claimed':True,'validated':True,'evidence_class':'MASTER_RECORDS_RECONSTRUCTED','evidence_refs':['mr:1'],'end_to_end_complete':True}}
 with pytest.raises(SystemExit): m.validate(Path('x.json'),r)
