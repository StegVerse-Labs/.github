# SKAP-HOSTNAME-BINDING-001 — Task Registry Registration Mirror Handoff

Canonical registration request: `control/canonical-task-registration-requests/skap-hostname-binding-001.json`
(this repository, filed in the same commit as this handoff).

- **Task:** add public hostname `skap.stegverse.org` -> `http://localhost:8812` to the
  Cloudflare tunnel serving 8374.stegverse.org, with its DNS record, existing
  ingress entries unchanged — the SKAP Vault placement door.
- **Addressed lane:** ChatGPT/CODEX (holder of Cloudflare API access to the
  stegverse.org zone; read access confirmed 2026-11-21).
- **Method:** Cloudflare API composite expressly authorized; dashboard route
  expressly not authorized. Token write scope is the open predicate; a 403 is a
  clean six-field NON-ALLOW.
- **Queue item of record:** `QUEUE__WORK__SKAP_HOSTNAME_BINDING__01.md`,
  Ecosystem KV coordination folder, Drive id `1Yy60BoYNLBlZfsWGNWPx2ZRKi76a5fw_`, MD5 `1587c0b42ab289e07268cc6529e7ad10`.
- **Scope digest:** `sha256:70c990bba7dfef7979d877528f2e802860f12006e49c3f2360e39bb46cfd7ab2`
- **Authority:** NONE_REGISTRATION_ONLY — this request proposes only; the
  registry transition derives the row, generation, and seal.
- **Observed registry generation at filing:** G326.
