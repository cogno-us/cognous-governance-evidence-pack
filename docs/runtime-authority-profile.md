# Runtime authority candidate import

The nonselected mapping uses Control Plane
`2a17b2ba147462a592d9b1882aad09d8a3eb7904`, runtime
`a9a4f75a9a880ba0ae2c3b5a01fcee0ae904e127`, and Replay
`05345feeff343cc6195bc8f7f37a3eed25278969` with the existing Manifest
`46c950bed37fe3812000895430bc0312d29e37ce`.
Its transformation is `agep-manifest-reconstruction-import/0.3.4-runtime-authority-candidate`.
Historical transformations and source pairings remain unchanged.

The importer restores journal events and vocabulary changes before invoking the
full Replay semantic comparison. It retains the exact reconstruction source,
including purpose reads, unknown/interrupted checks, typed refusal version and
approval/input/catalogue bindings. The usual Evidence Pack validation reconstructs
and compares this trace when `metadata.traceable_import` is present, so relabeled source counts in an import cannot pass that comparison; a pack that identifies as an import without the marker is refused (`E_TRACE_SEMANTICS`), and a pack not marked as an import is treated as hand-authored (all fields are caller assertions).

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
