# Payment Provider Authentic Ingress Mirror Handoff

Goal Task ID: `PAYMENT-PROVIDER-AUTHENTIC-INGRESS-001`
COSV: `20011000100000`
Status: `ACTIVE / CHECKED_OUT`
Parent Goal Task ID: `STRIPE-GODADDY-PROVIDER-EQUIVALENCE-001`
Canonical issue: `StegVerse-Labs/.github#1974`
Implementation issue: `StegVerse-Labs/TVC#437`

## Goal

Observe authentic completed Stripe and GoDaddy payment records through TV/TVC-governed read-only provider paths, convert them into the already-merged `stegverse.tvc.completed-payment-evidence/v1` boundary, and prove that provider ingress does not expand payment, entitlement, governance, credential, transport, or execution authority.

## Parent boundary reused

The retired provider-equivalence task already proved deterministic Stripe/GoDaddy equivalence and fail-closed authority behavior. This task must reuse `StegVerse-Labs/TVC:scripts/tvc_payment_evidence_adapter.py`; it must not recreate provider-specific payment semantics downstream.

## Current authentic observations

### Stripe

The connected live Stripe account `StegVerse.org` was queried through authenticated GET-only Stripe API reads during task registration. `GET /v1/payment_intents?limit=20` and `GET /v1/charges?limit=20` both returned valid empty lists. This proves an authentic read-only Stripe observation surface is available, but it does not provide a completed payment record and therefore does not satisfy authentic completed-payment normalization.

### GoDaddy

Official GoDaddy Commerce documentation currently exposes the read-only Transaction API at `GET /v2/commerce/stores/{storeId}/transactions` and `GET /v2/commerce/stores/{storeId}/transactions/{transactionId}` under `commerce.transaction:read`. The connected GoDaddy app surface available to this session exposes domain functions only, so no authenticated owner GoDaddy Payments transaction read has yet been observed.

Public documentation is architecture evidence only and is not owner transaction evidence.

## Implementation contract

TVC must own provider observation. The observer may accept a raw provider response only after it has been obtained through a read-only provider operation. It must emit sanitized `stegverse.tvc.completed-payment-evidence/v1` evidence with:

- provider and provider transaction ID retained;
- amount in minor units and ISO currency;
- completed/succeeded state only;
- provider observation timestamp;
- `authority_effect = NONE`;
- all entitlement/payment/governance/execution grant fields false;
- source endpoint and read-only scope retained separately in the observation receipt;
- no provider credential persisted in output evidence.

The sanitized evidence must then pass unchanged through the merged provider-neutral adapter to the StegPay `payment_verified` shape.

## Completion predicates

1. TVC observation adapter source, tests, README, workflow, and repository-local handoff merged.
2. Stripe authenticated read path retained as evidence.
3. At least one authentic completed Stripe record, if one exists, normalizes successfully; absence of transactions remains explicit rather than synthesized.
4. At least one authentic completed GoDaddy transaction normalizes successfully after TV/TVC-governed `commerce.transaction:read` access becomes available; no synthetic fixture may satisfy this predicate.
5. No raw credential value is persisted.
6. Provider-specific fields do not create downstream provider-specific payment semantics.
7. Webhook evaluation remains inadmissible until authentic completed-payment normalization evidence exists for the relevant provider.
8. Provider-failover evaluation remains inadmissible until both providers have authentic completed-payment normalization evidence or an explicit evidence-backed single-provider limitation is admitted.

## Authority boundaries

- TV/TVC remains credential authority.
- Provider credentials authorize provider reads only.
- Payment/provider data is evidence only.
- Transport is not authority.
- StegPay normalization/signing does not create entitlement.
- No charge, capture, refund, order mutation, provider write, governance decision, or execution grant is authorized.

## Webhook and failover gate

Webhook-driven ingestion and provider failover are evaluation-only future phases. They cannot be treated as implemented, activated, or admissible from source code or public API documentation. The gate opens only from authentic completed-payment observation evidence and retained normalization receipts.

## Next execution

Implement the TVC provider-observation adapter and deterministic structural tests; retain the current authentic Stripe empty-read observation; prepare the GoDaddy `commerce.transaction:read` TV/TVC provider profile without materializing credentials outside TV/TVC; then obtain authentic completed-payment observations when provider data exists.
