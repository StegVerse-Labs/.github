#!/usr/bin/env python3
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())
def main():
 h=load('control/heartbeat-state.json'); expected=int(h.get('expected_returns',0)); epoch=int(h.get('epoch',0)); ret=ROOT/'heartbeats/returns'; got=0
 if ret.exists():
  for p in ret.glob('*.json'):
   try:
    if json.loads(p.read_text()).get('epoch')==epoch: got+=1
   except Exception: pass
 result={'schema':'stegverse.org-heartbeat-watchdog/v1','epoch':epoch,'expected_returns':expected,'observed_returns':got,'missing_returns':max(0,expected-got),'checked_at':datetime.now(timezone.utc).isoformat(),'fault':got<expected,'authority_effect':'none'}
 out=ROOT/'heartbeats/watchdog'; out.mkdir(parents=True,exist_ok=True); (out/f'epoch-{epoch}.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 if result['fault']:
  w=ROOT/'warrants'; w.mkdir(exist_ok=True); p=w/f'SCAN-HB-{epoch}.json'; p.write_text(json.dumps({'schema':'stegverse.scan-warrant/v1','warrant_id':f'SCAN-HB-{epoch}','status':'open','opened_by':'delta_observation','triggering_observation':{'field':'expected_return_count','delta':expected-got,'claimants':[]},'scope':{'subsystems':['organization-heartbeat'],'streams':['heartbeats/returns'],'time_range':{}},'correlation_class':'shared_path' if expected>1 else 'isolated','occurrence_count':1,'finding':None,'closed_at':None,'closure_evidence':[]},indent=2,sort_keys=True)+'\n')
 print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
