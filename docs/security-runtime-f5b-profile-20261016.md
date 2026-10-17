# F5b repaired runtime Evidence Pack generation — 16 October 2026

Adds transformation `agep-manifest-reconstruction-import/0.3.6-security-runtime-f5b-candidate` for the exact CP a34c3dc2 / runtime 4a83b175 / Replay 0cfe7a63 / Manifest 2c36bcd0 generation. These are the merged revisions after the F5b security repairs. Replay 0cfe7a63 exports them as `CONTROL_PLANE_F5B_REVISION`, `MOLTBOT_F5B_REVISION`, `MANIFEST_F5B_REVISION` and `BOUNDED_F5B_PROFILE`.

The change follows the same additive pattern as the [repaired runtime generation](security-runtime-profile-20261016.md). It does not change the CP 996baeb4 / runtime fd6b76fa / Replay 3601fb21 / Manifest e385f8c1 generation, its `0.3.5-security-runtime-candidate` transformation, or any other historical mapping, so retained evidence from those generations still imports. Importing that earlier generation does not require the F5b Replay constants.

Each generation is an exact set. The importer rejects a bundle whose executor or Manifest revision belongs to a different security-runtime generation than its Control Plane revision. It also rejects a security-runtime Control Plane revision paired with an executor from outside the security-runtime generations. An F5b import requires the Replay F5b constants to match this contract exactly.

The F5b generation uses the same import semantics as the earlier one: runtime-authority journals and reason vocabulary, typed refusals, closeouts, time floors and refusal-vocabulary summaries. Retained failure-record identifiers stay labelled `source_asserted_not_independently_verified`; they do not prove independently verified durability.

Component-local tests are in `tests/test_f5b_generation.py`. Cross-component cases and results belong to `cognous-stack-qualification/suites/security-runtime`. This mapping is a candidate component revision. It needs F3 requalification, refreeze and re-review before anyone accepts it. It does not select a profile and does not authorize a release or production use. C0 and deployment limits remain.
