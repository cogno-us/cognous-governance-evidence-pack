# Security Cloud remediation proposal — cognous-governance-evidence-pack

Scan: https://chatgpt.com/codex/cloud/security/runs/wfr_53e59d7788d79c0ec957b5f217503f2ab1a16086560f4df0f4e24fa15b1e0229
Scanned/base revision: `814ee4ac49a8824ddb47f96cbad4b0077b77dab4`.

Require matching review decisions and replay semantic validation before affirmative rendering. All traceable versions retain exact inputs; malformed provenance fails validation. Imported signature and redaction declarations remain unverified; counts preserve actual Replay errors. Summaries expose semantic validity and CLI refuses invalid summaries. Apply input budgets and terminal-safe rendering; align nonblank/approval schema constraints.

## Finding coverage

- `csf_922e6773e415f55d7372eab4` (medium): Source-declared redaction is promoted to an export-safe redacted claim. Proposed code correction; final disposition pending review and source-bound checks.
- `csf_760db9e4ed66d146e3dd5a98` (medium): Replay import errors are hard-coded out of the validation summary. Proposed code correction; final disposition pending review and source-bound checks.
- `csf_8091d91a62e4e752ca6eb769` (medium): Traceable rendering accepts unbound provenance and lifecycle claims. Proposed code correction; final disposition pending review and source-bound checks.
- `csf_52e726cd65e37ad80d7ec756` (medium): Render and summarize entry points bypass semantic validation. Proposed code correction; final disposition pending review and source-bound checks.
- `csf_cd84510b5c4a589079040170` (medium): Approved status is not bound to a matching review decision. Proposed code correction; final disposition pending review and source-bound checks.
- `csf_ff309fbf165aa21285b32663` (medium): Unverified integrity metadata is promoted to cryptographically signed status. Proposed code correction; final disposition pending review and source-bound checks.
- `csf_9db4a5d26c1150608539384c` (medium): Legacy imports copy an unvalidated reconstruction status into evidence. Proposed code correction; final disposition pending review and source-bound checks.
- `csf_ed96e618de21ddb8f3832453` (low): Duplicate legacy identifiers create ambiguous provenance attribution. Proposed code correction; final disposition pending review and source-bound checks.
- `csf_d4a3be6592ed5e3de352fe92` (low): Model-valid trace metadata can crash validate, summarize, and trace rendering. Proposed code correction; final disposition pending review and source-bound checks.
- `csf_762cd45219ce66079f6de68a` (low): Unbounded evidence processing permits local resource exhaustion. Proposed code correction; final disposition pending review and source-bound checks.
- `csf_e29f7e71f8d15224ae61d594` (low): Evidence fields can inject terminal control sequences into CLI output. Proposed code correction; final disposition pending review and source-bound checks.
- `csf_12614a5ed3adacb6a77bd48f` (low): Published JSON Schema accepts packs rejected by runtime validation. Proposed code correction; final disposition pending review and source-bound checks.

## Validation and limits

135 tests passed.

Component changes require integrated qualification before any selected hub pin advances. These are proposed repairs; passing local checks is not independent security certification. The package frozen at hub `7f335099ca52a68533b6e78c2e35166a9109e35c` has not been regenerated or relabeled as containing these edits. No publication or production authorization is granted. No paid model trials, production probes or external communications ran.

Historical retained packages may fail stricter claim validation. They must not be silently rewritten; compatibility and any newly generated package require explicit evidence reconciliation.
