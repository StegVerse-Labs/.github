# StegVerse-Labs Organization Resident Runtime

This directory declares `StegVerse-Labs/.github` as the canonical home for organization resident-runtime activation.

The mature implementation remains the existing heartbeat and Universal InTr machinery in this repository. This directory does not fork those components; it binds them as the organization runtime and boundary implementation.

All organization-crossing ingress and egress must use Interlock/InTr semantics. HB/HB-derived carrier correctness is non-authorizing.

The Organization ledger's durable locus is declared by `.stegverse/transition-ledger/org-contract.json` (`organization_ledger_locus`: repository `StegVerse-Labs/.github`, ref `refs/heads/stegverse/organization-ledger`, path `organization-ledger`). `aggregate_repo_transition.py` appends one commit per transition on that ref by expected-head compare-and-swap (`git push --force-with-lease=<ref>:<expected>`, always a fast-forward) and reads the receipt back by digest; a lost race re-reads and re-links, a refused write fails closed. A local directory (`STEGVERSE_ORG_LEDGER_ROOT`, or a fresh temporary one) is only a non-authoritative cache bound to that locus; one bound elsewhere, or holding an unbound ledger, fails closed.
