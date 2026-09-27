# SDK review Publisher InTr existing forward producer

Goal MIR-SV-CAPABILITY-BOUNDARY-EXPERIMENT-003; COSV 50000000100000. Owner: scripts/consume_publisher_intr_materialization_request.py on existing Universal InTr, not another runtime.

Merged StegOS PR #411 adds canonical sdk-publisher-review same-ecosystem connector from SDK:ReviewerEvidenceExport to Publisher:Ingress and response Publisher:Export to SDK:ReviewerReturn. Existing KV profile unchanged; no second device.

This source patch validates exact SDK generic Publisher evidence-report payload, selects the canonical SDK profile, checks exact packet ID and transport intent hash, and rejects KV-origin impersonation and special MIR binding reuse. Generic Publisher source_export_schema chooses SDK as downstream owner. Tests document the source admission boundary.

Authentic reverse SDK:ReviewerReturn admission and binding to original SDK manifest/Master Records remains the first unproven transition: the existing reverse consumer is KV-origin or specialized MIR-only. Do not route generic SDK return through KV or call a local fixture runtime proof.

No authentic resident organization ledger, current Master Records closure, actual Publisher host operation or far-side evaluator receipt was observed. Original PDF and ten screenshots remain available privately in the source-only evaluator archive.
