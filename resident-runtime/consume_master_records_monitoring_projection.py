#!/usr/bin/env python3
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument("--projection",required=True);a=p.parse_args()
    value=json.loads(Path(a.projection).read_text())
    if value.get("schema")!="master-records.ecosystem-ledger-monitoring-projection/v1":
        raise SystemExit("projection schema mismatch")
    if value.get("read_only") is not True or value.get("custody_authority") is not False:
        raise SystemExit("observer authority drift")
    out={
      "schema":"stegverse-labs.master-records-observation/v1",
      "observer":"StegVerse-Labs/.github",
      "source":"master-records/monitoring",
      "ecosystem_transition_count":value.get("transition_count",0),
      "by_organization":value.get("by_organization",{}),
      "custody_head":value.get("head"),
      "authority_effect":"NONE_OBSERVER_ONLY"
    }
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__":main()
