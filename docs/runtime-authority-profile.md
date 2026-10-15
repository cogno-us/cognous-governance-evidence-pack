# Runtime authority candidate import

The nonselected mapping uses Control Plane
`7aa98ac452de4619161bef177cdd9c07fc606f03`, runtime
`a9a4f75a9a880ba0ae2c3b5a01fcee0ae904e127`, and Replay
`3ef89c8a2af880f6505f4db1ffbabbedffdc5e4d` with the existing Manifest
`46c950bed37fe3812000895430bc0312d29e37ce`.
Its transformation is `agep-manifest-reconstruction-import/0.3.4-runtime-authority-candidate`.
Historical transformations and source pairings remain unchanged.

The importer restores journal events and vocabulary changes before invoking the
full Replay semantic comparison. It retains the exact reconstruction source,
including purpose reads, unknown/interrupted checks, typed refusal version and
approval/input/catalogue bindings. The usual Evidence Pack validation reconstructs
and compares this trace; relabeled source counts cannot pass that comparison.

`refusal_vocabulary_summary` reports each versioned code over total refusal rows.
The prior window and traffic exposure are unavailable unless separately supplied;
this transformation does not invent disappearance findings. The control plane's
exposure-aware trend helper can be used with actual historical windows. Unknown
vocabularies remain visible. Source consistency is not independent origin or
effect verification, operational effectiveness, approval or compliance.

Cross-component acceptance tests are maintained in cognous-stack-qualification,
`suites/runtime-authority`. They are original synthetic cases derived from the
supplied Moltbook 101526_A K1–K5 dated 15 October 2026 and carry the existing
Apache-2.0 project license. This change adds no new selected profile, ODES conformance
claim, deployment configuration or release permission.
