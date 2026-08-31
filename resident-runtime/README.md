# StegVerse-Labs Organization Resident Runtime

This directory declares `StegVerse-Labs/.github` as the canonical home for organization resident-runtime activation.

The mature implementation remains the existing heartbeat and Universal InTr machinery in this repository. This directory does not fork those components; it binds them as the organization runtime and boundary implementation.

All organization-crossing ingress and egress must use Interlock/InTr semantics. HB/HB-derived carrier correctness is non-authorizing.
