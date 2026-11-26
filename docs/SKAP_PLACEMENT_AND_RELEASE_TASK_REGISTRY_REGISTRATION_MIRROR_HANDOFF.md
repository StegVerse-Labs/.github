# SKAP-PLACEMENT-AND-RELEASE-001 — Registration Mirror Handoff

**Task:** SKAP-PLACEMENT-AND-RELEASE-001 — the credential
placement surface and governed release route for the ecosystem
SKAP Vault. **Registration request:**
`control/canonical-task-registration-requests/skap-placement-and-release-001.json`
(schema `stegverse.canonical-task-registration-request/v1`,
observed registry generation G326, NEW_IDENTITY, authority
NONE_REGISTRATION_ONLY). **Operative task text:** Ecosystem KV
coordination folder, `QUEUE__WORK__SKAP_PLACEMENT_AND_RELEASE__01.md`
(Drive `1F2dalbHSu5GkXJ5tdgX0zjkLu9leBB38`, MD5
`a21d37be02fcfe848572be1e78932bb7`). **Pairing surface:**
StegVerse-Labs/.github#3467.

The ecosystem holds zero credentials (standing since
2026-10-29): all ecosystem security material lives in the
ecosystem SKAP Vault inside the KV, under TV/TVC authority,
and a credential anywhere else is out-of-custody by
definition. The placement surface (the principal deposits
from his own device, destination bound by his statement) and
the governed release route (a component obtains a named
credential's value at the moment of use, receipted on both
sides, memory-only, FAIL_CLOSED after revocation) have stood
open since 2026-11-15. They became load-bearing on 2026-11-25
when the owner landed the requirement that email transport is
SKAP-custody transport: the Receipt Mailer (port 8811) is the
first client and stands PENDING until the release route
exists. Ordering: KV-native receipt notification is the
primary path; email is the guest/legacy path for submitters
without a KV.

**Discharge:** the SKAP lifecycle test reproduced by a
non-author lane from the receipts alone (deposit+seal →
governed release byte-identical → revoke → post-revoke
release FAIL_CLOSED, zero bytes out), plus one live receipt
email delivered by the Receipt Mailer using a released
credential; or a six-field non-ALLOW per part. Any lane is
eligible; first claim owns it. Registration proposes only —
the owner-side transition derives the registry row, the next
generation, and the COSV.
