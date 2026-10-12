# Optional recovery inspection evidence 0.1

Candidate implementation for Evidence Pack issue #22. This is a distinct native inspection transformation, not the historical Manifest/Reconstruction importer or an instance of its EvidencePack model. It requires the actual Replay inspection module and has no substitute parser.

## Exact dependencies and format

| Item | Selected for this candidate |
| --- | --- |
| Runtime source | `8e7d634cf0a22b6f3c1fc6d93afe92c7414fa243` |
| Replay source | `696e7bc2432fc7b5cf2d6e6c5f0b944b2d9a265f` |
| Replay input | `cognous-replay-recovery-inspection/0.1` |
| Native output | `cognous-recovery-inspection-evidence/0.1` |
| Transformation | `agep-recovery-inspection/0.1` |

These pins are optional qualification dependencies, not selected-release lock changes. Existing package versions, transformation versions, CLI, renderer, and default import behavior remain unchanged. Do not send this new artifact to a historical renderer/validator and infer compatibility from successful generic parsing.

```python
from agent_governance_evidence_pack.recovery_inspection import (
    REPLAY_REVISION, build_recovery_inspection_evidence,
    validate_recovery_inspection_evidence,
)

evidence = build_recovery_inspection_evidence(
    replay_inspection,
    replay_revision=REPLAY_REVISION,
    expected_identity=selected_original_identity,
)
validate_recovery_inspection_evidence(evidence)
```

The caller selects the exact dependency revision and the five-field original identity required by Replay. Both must agree with the supplied inspection. They are caller-selected provenance, not authenticated repository origin or independently verified identity. No tenant, actor, manifest, policy decision, grant, generation timestamp, or missing source payload is fabricated.

## Validation and retention

The builder deep-copies the supplied JSON-compatible inspection, checks the exact profiles and caller selection, invokes Replay's native semantic validator, and then constructs a deterministic evidence artifact. Unsupported input or an unavailable/failing Replay validator raises `RecoveryEvidenceError`; there is no fallback to a permissive model or local substitute.

The result retains the complete native input under `replay_inspection`, including original uncertainty, all retained events/receipts, current projection, legacy entries, and source limitations. The derived summary separately labels producer work state, observation, finality, event count, commitment-only event count, and legacy presence. The copied `loss_report` remains unchanged. A copied source evaluation time is labeled `recorded_source_evaluation_time`, not evidence-generation time or a fresh observation.

`provenance.input_sha256` is computed over the retained Replay input with sorted ASCII JSON, compact separators, no NaN, and UTF-8 without a trailing newline. This checks supplied content consistency, not source authenticity. No hash is recomputed over an unavailable submitted payload and described as its original digest.

The native validator calls the same actual Replay validator, rebuilds the transformation, and requires exact equality of every derived field. Altering the summary, count, loss report, identity, provenance commitment, review status, or assurance without corresponding valid source fails. Coordinated fabrication of unauthenticated source and derived data is outside this consistency guarantee.

## Assurance boundary

- Producer `resolved` remains only a synthetic work-state assertion, with `synthetic_profile_only` finality where applicable.
- Unknown/absent, partial follow-up, conflicts, and no-first-observation remain distinguishable.
- Conflict bodies that were not retained remain unavailable; legacy gaps are not repaired by formatting.
- `review_status` is `unreviewed`; review acceptance is not established.
- Source authentication and independent verification are not established.
- Settlement verification and retry eligibility are false; execution authority is none.
- Freshness at transformation is not evaluated. Recorded admission freshness is historical evidence.

No Runtime database is opened by the transformer, no effect is attempted, and no authority decision is made. Tests separately use temporary Runtime stores to generate synthetic inputs.

## Qualification and inspected example

Install this package's dev dependencies and the exact Replay dependency, then run:

```bash
COGNOUS_REPLAY_SOURCE=/absolute/path/to/pinned-replay COGNOUS_RUNTIME_SOURCE=/absolute/path/to/pinned-runtime python -m pytest -q tests/recovery_inspection_checks.py
```

The optional qualification file is explicitly selected so default suites do not acquire another producer fixture dependency. Missing fixture configuration fails this command rather than silently skipping tests. The dedicated workflow verifies both dependency commits and runs the suite.

The suite uses the merged Replay fixture helpers and actual Runtime APIs, checking the imported Replay module and both Runtime module blob hashes. Cases cover empty/unknown/absent/partial/applied/conflict/legacy evidence, exact input retention and deterministic copying, unsupported profiles/revisions, wrong identity, dropped events, altered source loss findings, and changed derived assurance. Disposable mutation controls require the same negative test to pass on intact code and fail when Replay validation or loss copying is removed.

A locally generated and validated collision example had:

| Observed output field | Value |
| --- | --- |
| producer work state | `conflict_review` |
| original disposition | `in_doubt` |
| retained event count | `2` |
| commitment-only event count | `1` |
| unavailable evidence path | `events[1].body` |
| full payload reconstruction | `unavailable` |
| settlement verified / retry eligible | `false` / `false` |

The gap listed the checks not performed: submitted-body digest, submitted predecessor, and observation facts. This is an executed synthetic mapping check, not a real recovery, independent verification, or settlement observation.

Local validation used fetched source material; CI verifies full checkout revisions. The complete historical test suite was not run locally. Orchestrator qualification, independent review, release adoption, authenticated deployment, migration, durable refusal audit, and external provider finality remain separate. C0 check-to-commit limits, optional same-host C1, no C2/C3, no real settlement, and operational trust HOLD remain.
