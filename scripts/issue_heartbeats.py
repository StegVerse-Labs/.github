#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,secrets
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())
def canon(v): return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def main():
 s=load('control/org-state.json'); c=load('control/claims-active.json'); hs=load('control/heartbeat-state.json')
 out=ROOT/'heartbeats/outbound'; out.mkdir(parents=True,exist_ok=True)
 epoch=int(hs.get('epoch',0))+1; now=datetime.now(timezone.utc).isoformat()
 issued=[]
 for claim in c.get('claims',[]):
  assertion={'schema':'stegverse.org-heartbeat/v1','epoch':epoch,'nonce':secrets.token_hex(16),'issued_at':now,'claimant_id':claim['task_id'],'repository':claim['repository']['full_name'],'claims':[claim],'fencing_token':claim['fencing_token'],'scope':claim.get('scope',{}),'policy_version':s['schema'],'evidence_pointer':claim.get('last_evidence_pointer'),'authority_effect':'none'}
  assertion['payload_sha256']=hashlib.sha256(canon(assertion)).hexdigest()
  p=out/f"{claim['task_id']}-{epoch}.json"; p.write_text(json.dumps(assertion,indent=2,sort_keys=True)+'\n'); issued.append(str(p.relative_to(ROOT)))
 hs['epoch']=epoch; hs['last_issued_at']=now; hs['expected_returns']=len(issued); hs['issued']=issued
 (ROOT/'control/heartbeat-state.json').write_text(json.dumps(hs,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'epoch':epoch,'issued':issued},sort_keys=True))
if __name__=='__main__': main()
