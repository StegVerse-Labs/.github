# Stripe / GoDaddy Provider Equivalence Mirror Handoff

Goal Task ID: `STRIPE-GODADDY-PROVIDER-EQUIVALENCE-001`
COSV: `20011000100000`
Status: `ACTIVE / CHECKED_OUT`
Canonical issue: `StegVerse-Labs/.github#1954`
Implementation issue: `StegVerse-Labs/TVC#431`

## Goal

Prove that completed Stripe and GoDaddy payment evidence can enter one TV/TVC-owned provider-neutral normalization boundary and produce the existing StegPay `payment_verified` event shape while retaining provider provenance and granting no provider, payment, transport, entitlement, governance, credential, or execution authority.

## Current truth

Existing Site source already exposes Stripe payment/support links. Existing StegPay source already defines the canonical `payment_verified` fields and rejects entitlement creation. Historical direct provider-secret handling inside StegPay is retired; credential-bearing provider execution belongs at TV/TVC.

The new implementation owner is `StegVerse-Labs/TVC`. Deterministic fixtures are test-only and must not be described as authentic Stripe or GoDaddy runtime evidence.

## Required implementation

The smallest acceptable implementation contains:

- one provider-neutral adapter contract owned by TV/TVC;
- deterministic completed-payment fixtures for Stripe and GoDaddy;
- exact mapping into the StegPay event keys: `amount`, `currency`, `event_id`, `event_type`, `issue`, `provider`, `provider_id`, `service`, `verified_utc`;
- provider provenance retained only in `provider` / `provider_id` and adapter provenance evidence;
- explicit `authority_effect = NONE` and `creates_entitlement = false` boundaries;
- deterministic equivalence validation that ignores only provider identity when comparing semantic payment facts;
- no provider credentials and no charge/refund/payment mutation in fixture validation.

## Completion predicates

Source-complete when the TVC branch contains the adapter, contract, fixtures, tests, workflow, repository README, and repository-local mirror handoff.

Validated when exact-head deterministic tests prove:

1. Stripe completed evidence normalizes to the canonical StegPay schema;
2. GoDaddy completed evidence normalizes to the same schema;
3. semantic fields are equal across equivalent fixtures except provider identity;
4. non-completed provider states fail closed;
5. authority and entitlement flags cannot be elevated by provider evidence.

This task does not claim live Stripe or GoDaddy API/webhook activation, owner credentials, production settlement observation, runtime ingestion, or downstream StegOps consumption.

## Authority boundaries

- TV/TVC remains credential authority.
- Provider credentials authorize provider access only.
- Provider evidence is evidence only.
- Payment is evidence only.
- StegPay normalization/signing does not create entitlement.
- Governance and execution remain outside provider/payment authority.
- Transport is not authority.

## Next execution

Finish and validate `StegVerse-Labs/TVC#431`; reconcile this task record and COSV only from observed repository/CI evidence; merge only after exact-head green validation.
