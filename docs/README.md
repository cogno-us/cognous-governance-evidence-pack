# Documentation index: Cognous Governance Evidence Pack

Every documentation page in this repository, by purpose. Historical, candidate and planning pages are labelled rather than hidden: they stay valid for the revision or plan they describe and do not describe the current selection. Back to the [repository README](../README.md).

Labels follow the hub [stack map](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/stack-map.md#status-labels): **merged**, **selected**, **known limit**, **proposed**. Names are explained in the hub [naming table](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/naming.md).

## Start by role

| Your role | First page | Then |
|---|---|---|
| New reader | [Concepts](concepts.md) | [Evidence pack format](evidence_pack_format.md), [examples](examples.md) |
| Using the `agep` command | [README quick start](../README.md#quick-start-about-two-minutes) | [Validation](validation.md), [rendering](rendering.md) |
| Importing a Manifest and a Reconstruction Bundle | [Traceable imports](traceable_imports.md) | [Merged producer compatibility](merged-producer-compatibility.md), [producer 2.0.0 import](producer-v2-migration.md), [migration notes](migration_v0_2_0.md) |
| Reviewer judging what a pack shows | [Rendering: caller assertions](rendering.md#caller-assertions) | [README known limits](../README.md#known-limits), [security policy](../SECURITY.md) |
| Checking generations and compatibility | [Persistence checkpoint](workstreams/evidence-pack-control-plane-store-checkpoint.md) | [Producer 2.0.0 checkpoint](workstreams/evidence-pack-producer-v2-checkpoint.md), [W0 C8 contract](w0-c8-compatibility-contract.md) |
| Contributor | [CONTRIBUTING](../CONTRIBUTING.md) | [Cross-component tests](../CROSS_COMPONENT_TESTS.md), [changelog](../CHANGELOG.md) |

## Current pages

| Page | What it covers | Label |
|---|---|---|
| [Concepts](concepts.md) | The core concepts of an evidence pack: agent overview, inventories, authority model, controls, replay bundle inventory, risk register, review records. | merged |
| [Evidence pack format](evidence_pack_format.md) | Every top-level field, the review status values and the schema files. | merged |
| [Validation](validation.md) | The error and warning rules, including `E_BUDGET` and `E_TRACE_SEMANTICS`. | merged |
| [Rendering](rendering.md) | The Markdown output structure, the CLI, and the caller-assertion labels. | merged |
| [Traceable imports](traceable_imports.md) | The import contract: supported producer baselines, the CLI, provenance, the retained Replay bundle comparison, loss register. | selected |
| [Merged producer compatibility](merged-producer-compatibility.md) | Transformation 0.3.2 for the exact merged producer combination. | selected |
| [Examples](examples.md) | What each example pack demonstrates. | merged |
| [Integration with the Control Plane](integration_with_agent_control_plane.md) | The conceptual relationship between the Evidence Pack and the rest of the stack. | merged |
| [Optional recovery inspection evidence 0.1](recovery-inspection.md) | A candidate native inspection transformation of a pinned synthetic recovery export; not the manifest importer. | merged |

## Candidate mappings and producer generations

Each page below describes an additive, exact-revision mapping that is not selected by the hub lock. They are kept so the revisions they name stay attributable.

| Page | What it covers | Label |
|---|---|---|
| [Typed refusal consumer candidate migration](typed-refusal-profile.md) | A separate non-selected profile for typed effect-time refusal evidence. | merged |
| [Runtime authority candidate import](runtime-authority-profile.md) | A non-selected mapping for runtime-authority journals, with how a pack compares the reconstructed trace. | merged |
| [Repaired runtime Evidence Pack generation (16 October 2026)](security-runtime-profile-20261016.md) | Transformation 0.3.5 for one exact generation. | merged |
| [F5b repaired runtime Evidence Pack generation (16 October 2026)](security-runtime-f5b-profile-20261016.md) | Transformation 0.3.6 for a further exact generation. | merged |
| [W0 C8 Evidence Pack compatibility contract](w0-c8-compatibility-contract.md) | A W0 candidate mapping contract. | merged |

## Historical, checkpoint and planning pages

| Page | What it is | Label |
|---|---|---|
| [Migration notes for Evidence Pack 0.2.0](migration_v0_2_0.md) | The change that added the traceable import path, with later generation notes. Older sections describe their original generation. | historical |
| [Importing executor producer profile 2.0.0](producer-v2-migration.md) | The producer 2.0.0 import, written when transformation 0.3.0 was current. | historical |
| [Persistence checkpoint](workstreams/evidence-pack-control-plane-store-checkpoint.md) | Compatibility checkpoint for the Control Plane persistence repair. | historical |
| [Producer 2.0.0 checkpoint](workstreams/evidence-pack-producer-v2-checkpoint.md) and [scenario results](workstreams/evidence-pack-producer-v2-results.json) | Checkpoint for producer 2.0.0 compatibility, with machine-readable scenario results. | historical |
| [Remediation proposal (October 2026)](security-cloud-remediation-20261016.md) | The original proposal for a set of findings, kept as written; read it with the changelog for what was merged. | historical |
| [Roadmap](roadmap.md) | Planned and aspirational improvements. Items are plans, not features. | proposed |
| [Changelog](../CHANGELOG.md) | Unreleased changes and earlier notes, newest first. | merged |

## Other files

- [README](../README.md): what it is, quick start, what ships, known limits.
- [SECURITY](../SECURITY.md): scope, input admission and caller assertions.
- [CONTRIBUTING](../CONTRIBUTING.md), [CODE_OF_CONDUCT](../CODE_OF_CONDUCT.md), [LICENSE](../LICENSE), [NOTICE](../NOTICE).
- [Cross-component tests](../CROSS_COMPONENT_TESTS.md): where the integration suites live and how the workflows call them.
- [Business overview](../collateral/business-collateral.md) and [one-page overview](../collateral/one-page-overview.md): nontechnical introductions. They describe this component's role and evidence limits, not additional features.
- [`templates/`](../templates): fill-in Markdown templates for reviewers; nothing in the package reads them.
- [`examples/rendered/`](../examples/rendered): the Markdown rendering of the four example packs, regenerated by CI.
