# Changelog

## Unreleased

- `build_evidence_pack_from_files` (and so `agep import`) now reads both input files through the shared admission parser instead of `json.load`. File import therefore also applies the admission byte budget (8 MiB), depth limit (32) and node limit (100,000 objects/arrays), and rejects duplicate JSON keys and the `NaN`/`Infinity`/`-Infinity` literals. Out-of-range numeric literals such as `1e999` are still accepted and parse as floating-point infinity.
- The Markdown renderer labels review status, review decisions, signature, redaction and validation fields "(asserted, unverified)". The `examples/producer-v2/*.md` goldens are regenerated for these labels.
