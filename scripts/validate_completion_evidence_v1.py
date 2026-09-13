#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'data/task-registry-global-invariants.json'
RECORDS=ROOT/'data/canonical-task-records'
CLASSES=['SOURCE_IMPLEMENTED','MERGED','CI_VALIDATED','SANDBOX_RUNTIME_OBSERVED','EXTERNAL_PROVIDER_OBSERVED','MASTER_RECORDS_RECONSTRUCTED','END_TO_END']
RANK={v:i for i,v in enumerate(CLASSES)}
def fail(m): print('ERROR:',m,file=sys.stderr); raise SystemExit(1)
def classify(r):
 c=r.get('completion') or {}; active=c.get('claimed') is True or c.get('validated') is True
 if not active: return 'NOT_CLAIMED'
 v=c.get('evidence_contract_version') or r.get('completion_evidence_contract_version')
 e=c.get('evidence_class')
 if v!='v1' or e not in RANK: return 'LEGACY_UNQUALIFIED_NON_AUTHORITATIVE'
 t=c.get('terminal_evidence_class')
 return 'QUALIFIED_TERMINAL_SATISFIED' if (RANK[e]>=RANK[t] if t in RANK else e=='END_TO_END') else 'QUALIFIED_PARTIAL_EVIDENCE'
def validate(path,r):
 c=r.get('completion') or {}; active=c.get('claimed') is True or c.get('validated') is True
 if not active: return
 v=c.get('evidence_contract_version') or r.get('completion_evidence_contract_version')
 engaged=v=='v1' or any(k in c for k in ('evidence_class','terminal_evidence_class','evidence_refs','end_to_end_complete'))
 if not engaged: return
 if v!='v1': fail(f'{path.name}: completion contract must be v1')
 if c.get('validated') is True and c.get('claimed') is not True: fail(f'{path.name}: validated requires claimed')
 e=c.get('evidence_class'); refs=c.get('evidence_refs'); t=c.get('terminal_evidence_class')
 if e not in RANK: fail(f'{path.name}: missing evidence class')
 if not isinstance(refs,list) or not refs: fail(f'{path.name}: missing evidence refs')
 if t is not None and t not in RANK: fail(f'{path.name}: invalid terminal evidence class')
 if t in RANK and RANK[e]<RANK[t]: fail(f'{path.name}: evidence class weaker than terminal class')
 if c.get('end_to_end_complete') is True and e!='END_TO_END': fail(f'{path.name}: END_TO_END evidence required')
def main():
 p=json.loads(POLICY.read_text()); i=p.get('invariants') or {}
 if i.get('completion_evidence_contract_version')!='v1': fail('completion evidence contract missing')
 if i.get('completion_evidence_classes')!=CLASSES: fail('completion evidence classes mismatch')
 if i.get('unqualified_complete_or_completed_prohibited') is not True: fail('unqualified completion prohibition missing')
 legacy=0
 for path in sorted(RECORDS.glob('*.json')):
  r=json.loads(path.read_text()); validate(path,r); legacy+=classify(r)=='LEGACY_UNQUALIFIED_NON_AUTHORITATIVE'
 print('TASK_COMPLETION_EVIDENCE_V1_PASS'); print(f'LEGACY_NON_AUTHORITATIVE={legacy}')
if __name__=='__main__': main()
