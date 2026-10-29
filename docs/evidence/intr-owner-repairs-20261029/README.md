# InTr owner repair candidates — 2026-10-29

These are inert review candidates for existing owners, not applied production changes,
protected integration, Registry admission or private runtime evidence. No dependencies installed.

| Lane | Exact tested source | Candidate and validation | Owner coordination |
| --- | --- | --- | --- |
| Labs #3207 | main 6b13c3a749b2940d6142644196a8302823c1f45a | labs-3207-current-main.patch: five refusal sites gain two missing fields; 76 tests + 7 subtests pass | https://github.com/StegVerse-Labs/.github/pull/3207#issuecomment-6505490127 |
| Labs #3213 | main 6b13c3a7 + head 37d74a04c10867a5a3c9bc513caa3d621035c4fc; combined tree 83b7a4bba41670d93c22580764acc87ccc4f7aca | labs-3213-current-main-fixture.patch: temporary consumer explicitly declares POSIX; 188 tests pass, zero skips | https://github.com/StegVerse-Labs/.github/pull/3213#issuecomment-6505615876 |
| TVC #562 | head 31bfba214188798358e56d985adc580a3599a5d6 | tvc562-root-confinement.patch: reject absolute and symlink-escaping folded records; 8 tests + 10 subtests pass, 143 deselected | https://github.com/StegVerse-Labs/TVC/pull/562#issuecomment-6505602211 |

#3207's older branch would resurrect retired workflow_dispatch/self-close machinery;
use only the current-main metadata candidate. #3213's unmodified combined tree had
187 passes and one fixture error; production preflight correctly refused an undeclared
Git-ledger location. The fixture correction preserves that guard. SDK source pin:
c138cad4c37db0bb675bc2c66515b5558cc5fa7b, STEGVERSE_SDK_REQUIRED=1.

TVC validation is deliberately bounded: the broader suite stopped at collection because
the partial tree lacks scripts/activate_app_store_connect_skap_resident.py. The existing
owner must run the four-file suite documented in #562 from a complete exact-head checkout.
The same two helpers occur in #561. Do not infer a full-suite pass or runtime exploit.

Patch SHA256 values:
- #3207: 0804779d15fd706786d5a9e5167de96da642463a3d7d6553a294e3576922fa4b
- #3213: 0cac0291aa9b63de693e51319738762fe79ba0aa080d25043193be6af9daef2f
- #562: 2edaa3295046b8a56e7247e902bbbec9bf1197e51cdb64b409a6e898f0871da1

Retained logs report local validation, not hosted CI. Existing owners apply/rebase candidates,
refresh exact-head CI and perform protected integration under their own authority.
