# Payment Provider Authentic Ingress Mirror Handoff

Goal Task ID: `PAYMENT-PROVIDER-AUTHENTIC-INGRESS-001`
COSV: `40000010100000`
Status: `ACTIVE / CHECKED_OUT / SOURCE_MERGED_AUTHENTIC_COMPLETED_EVIDENCE_PENDING`
Parent Goal Task ID: `STRIPE-GODADDY-PROVIDER-EQUIVALENCE-001`
Canonical issue: `StegVerse-Labs/.github#1974`
Implementation issue: `StegVerse-Labs/TVC#437`
Implementation PR: `StegVerse-Labs/TVC#438`
Implementation merge: `StegVerse-Labs/TVC@c0a46b6b6c470b5a39499600678fc222822afc79`
Exact-head implementation validation: `StegVerse-Labs/TVC/actions/runs/35047474638` — SUCCESS

## Goal

Observe authentic completed Stripe and GoDaddy payment records through TV/TVC-governed read-only provider paths, convert them into the already-merged `stegverse.tvc.completed-payment-evidence/v1` boundary, and prove that provider ingress does not expand payment, entitlement, governance, credential, transport, or execution authority.

## Parent boundary reused

The retired provider-equivalence task already proved deterministic Stripe/GoDaddy equivalence and fail-closed authority behavior. This task reuses `StegVerse-Labs/TVC:scripts/tvc_payment_evidence_adapter.py`; it does not recreate provider-specific payment semantics downstream.

## Merged implementation

`StegVerse-Labs/TVC#438` merged:

- `scripts/tvc_payment_provider_observation.py`;
- deterministic observation tests;
- a dedicated credential-free validation workflow;
- `payment_ingress/README.md`;
- repository-local mirror handoff.

Exact-head workflow run `35047474638` succeeded before merge.

The observer terminates raw provider records at TV/TVC and emits only minimal completed-payment evidence. Observation receipts retain provider ID, GET-only endpoint, read scope, observation time, and a hash of a safe source projection while explicitly recording that raw provider records and credential material were not persisted.

## Current authentic observations

### Stripe

The connected live Stripe account `StegVerse.org` was queried through authenticated GET-only Stripe API reads. `GET /v1/payment_intents?limit=20` and `GET /v1/charges?limit=20` both returned valid empty lists. This proves an authentic read-only Stripe observation surface is available, but there is no completed payment record in the currently observed account data and therefore no authentic completed-payment normalization receipt yet.

The merged Stripe observer admits only a GET-observed PaymentIntent with `status=succeeded`, retaining `amount_received`, currency, and PaymentIntent ID as payment evidence.

### GoDaddy

Official GoDaddy Commerce documentation exposes the read-only Transaction API at `GET /v2/commerce/stores/{storeId}/transactions` and `GET /v2/commerce/stores/{storeId}/transactions/{transactionId}` under `commerce.transaction:read`.

The connected GoDaddy app surface available to this session exposes domain operations only. It does not expose owner Commerce/Payments transaction reads, so no authenticated GoDaddy transaction has been observed. Public documentation is architecture evidence only and is not owner transaction evidence.

The merged GoDaddy observer intentionally fails closed unless a TV/TVC provider profile supplies an evidence-backed completed-status vocabulary. No status string is invented from examples.

## Validated source predicates

1. Stripe successful PaymentIntent records map into the merged provider-neutral completed-payment evidence schema.
2. GoDaddy transaction records map into the same schema only when their status is explicitly admitted by an evidence-backed TV/TVC profile.
3. Non-completed Stripe state fails closed.
4. Empty/unverified GoDaddy completed-status semantics fail closed.
5. The existing provider-neutral adapter is reused for StegPay `payment_verified` normalization.
6. Provider credentials and full raw provider/customer/card records are excluded from durable observation receipts.
7. No payment, entitlement, governance, execution, webhook-activation, or failover-activation authority is created.

These are deterministic source-contract predicates, not authentic completed-provider traffic claims.

## Remaining completion predicates

1. Observe at least one authentic completed Stripe record if/when one exists in the connected live account and retain its normalization receipt; absence remains explicit rather than synthesized.
2. Establish TV/TVC-governed GoDaddy `commerce.transaction:read` owner access, observe an authentic transaction, admit completed-status semantics from authoritative evidence, and retain a normalization receipt.
3. Keep webhook evaluation inadmissible until authentic completed-payment normalization evidence exists for both providers.
4. Keep provider-failover evaluation inadmissible until both provider proofs exist or an explicit evidence-backed single-provider limitation is admitted.

## Authority boundaries

- TV/TVC remains credential authority.
- Provider credentials authorize provider reads only.
- Payment/provider data is evidence only.
- Transport is not authority.
- StegPay normalization/signing does not create entitlement.
- No charge, capture, refund, order mutation, provider write, governance decision, or execution grant is authorized.

## Webhook and failover gate

The merged `evaluate_webhook_failover_gate()` is evaluation-only and currently returns both webhook and failover evaluation inadmissible because authentic completed-payment normalization evidence is not green for both providers. It never grants activation authority.

## Next execution

Materialize the least-privilege GoDaddy `commerce.transaction:read` owner credential/session through the existing TV/TVC custody path without exposing plaintext outside TV/TVC, perform a GET-only transaction observation, establish the provider's actual completed-status semantics from authoritative evidence, and normalize the first authentic completed GoDaddy transaction if one exists. In parallel, repeat the live Stripe GET observation and normalize only if an authentic successful PaymentIntent exists. Only after both proofs are green may webhook-driven ingestion and provider-failover evaluation begin.
