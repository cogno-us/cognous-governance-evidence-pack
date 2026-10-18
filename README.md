<!-- cognous-banner:start -->

Cross-component test commands below now run in a disposable checkout assembled by the [qualification workflows](CROSS_COMPONENT_TESTS.md). Plain local test discovery covers the component-local tests retained here. Historical reports and dependency pins keep their original scope.
```text
──────────────────────────────────────────────────
   __________  _______   ______  __  _______
  / ____/ __ \/ ____/ | / / __ \/ / / / ___/
 / /   / / / / / __/  |/ / / / / / / /\__ \
/ /___/ /_/ / /_/ / /|  / /_/ / /_/ /___/ /
\____/\____/\____/_/ |_/\____/\____//____/
         COGNOUS GOVERNANCE EVIDENCE PACK
       g o v e r n e d   b y   d e s i g n
  github.com/cogno-us/cognous-open-control-stack
──────────────────────────────────────────────────
```
<!-- cognous-banner:end -->

# Cognous Governance Evidence Pack

**Turn traceable runtime records into reviewable governance evidence.**

**Stack group: 05 · Replay & Evidence.** See the [six-group component map](#cognous-stack-components).

## Overview

A reference format, validator, traceable importer and Markdown renderer for business-facing review of agent governance records. It preserves the relationship between a declared action surface and reconstructed runtime evidence instead of treating a summary as independent assurance.

**Implementation status:** public reference work. The [current component lock](https://github.com/cogno-us/cognous-open-control-stack/blob/main/component-lock.json) defines the selected integration; a component merge does not automatically change that selection or approve deployment.

## Selection and example

Use the [current component lock](https://github.com/cogno-us/cognous-open-control-stack/blob/main/component-lock.json) for integration selection and the [central test hub](https://github.com/cogno-us/cognous-stack-qualification/blob/main/results/readme-commentary/index.md) for revision-specific qualification commentary. Source acceptance, selection and deployment approval remain separate decisions.

**Synthetic example:** A synthetic evidence pack links the refund proposal, authorization decision, runtime attempt and observed unknown outcome. Its summary is derivative evidence, not independent confirmation that a processor settled the refund.

Operational deployment trust is still [HOLD under orchestrator #30](https://github.com/cogno-us/cognous-stack-orchestrator/issues/30). No signature, evidence package, successful test or source merge creates a production grant, proves external settlement, or changes selected release authority.

## Purpose and intended users

Enterprise reviewers need to understand authority, review posture, reliance, attempted actions and unresolved outcomes without reading every raw event. A useful summary must remain traceable and must not convert declarations or source assertions into verified operational facts.

Engineers can inspect the reference contracts and examples; enterprise architecture, security and governance reviewers can examine the boundary and evidence. Evaluate this component for its named responsibility rather than as a complete governance platform.

## Key features

| Capability | Implemented or specified responsibility |
|---|---|
| **Evidence structure** | Represent the agent, actions, governance context and source records in a review package. |
| **Traceable imports** | Transform Manifest and Reconstruction Bundle inputs with explicit source references and transformation versions. |
| **Assurance separation** | Distinguish declared controls, source-asserted runtime facts, executed tests and independent verification. |
| **Continuity checks** | Validate source identities, commitments and producer compatibility across the selected generation. |
| **Business rendering** | Validate, summarize and render Markdown for a reviewer while preserving unresolved and missing information. |

## How it works

The bounded refund produces retained reconstruction evidence. The importer combines it with the Manifest and records the derivation. A reviewer can follow each summarized decision or outcome back to its source and see the difference between historical authorization, current recovery denial and observed destination state.

A valid signature, chain inclusion, message receipt, reasoning instruction or evidence-package digest does not authorize execution. Institutional authority must be supplied and evaluated through the appropriate trusted boundary.

## Getting started

From a fresh repository checkout, use Python 3.11+ and an activated virtual environment. Install only into that environment. Package installation needs network access; the commands below exercise local reference tooling. For the full selected integration, use the [hub quickstart](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/quickstart.md), whose runner supplies exact producer checkouts and test wiring.

```bash
python -m pip install -e ".[dev]"
agep validate examples/customer_service_agent_evidence_pack.json
agep summarize examples/customer_service_agent_evidence_pack.json
agep check-examples
```

## Scope and compatibility

Use the [current component lock](https://github.com/cogno-us/cognous-open-control-stack/blob/main/component-lock.json) for the selected revision. Transformations from **0.2.6** to **0.3.8** coexist as distinct compatibility mappings; the selected one is set by the hub's component lock, and an imported pack revalidates only in an environment with the Replay revision its generation pins (otherwise `agep validate` reports `E_TRACE_SEMANTICS`). Imported pack schema remains **0.2.0**. See the [persistence checkpoint](docs/workstreams/evidence-pack-control-plane-store-checkpoint.md); older migration notes describe their original generation.

Test results, run commentary and historical qualification records are maintained in the [central test hub](https://github.com/cogno-us/cognous-stack-qualification/blob/main/results/readme-commentary/index.md). Read them against their recorded source revisions; source selection and deployment approval are separate decisions.

## Limitations and deployment decisions

Import success does not establish that a test ran, that an institution authorized current reliance or that a control is effective in production. This is not certification, legal advice, independent audit or a runtime enforcement layer. Historical transformation outputs remain attributed to their original sources.

Review original artifacts and their exact source revisions before extending a claim to a new environment. New dependencies, authority sources, destinations or enforcement mechanisms need their own compatibility and qualification. A passing reference case is not a certification of an enterprise deployment.

## Repository guide

Use these sources for details; their historical checkpoints retain the status and scope of the work they recorded:

- [docs/traceable_imports.md](docs/traceable_imports.md)
- [docs/producer-v2-migration.md](docs/producer-v2-migration.md)
- [docs/validation.md](docs/validation.md)
- [docs/rendering.md](docs/rendering.md)

For a nontechnical introduction, read the [business overview](collateral/business-collateral.md) and [one-page overview](collateral/one-page-overview.md). Both describe this component's role and evidence limits, not additional runtime features.

## Contributing and attribution

[Contribution guidance](CONTRIBUTING.md) describes review and validation expectations. Keep evidence-linked claims, preserve historical records and separate proposed features from accepted implementation.

See [LICENSE](LICENSE) and [attribution](NOTICE) for the existing terms and third-party scope. Developed by [Cognous](https://cogno.us); no licensing change is part of this documentation update.

---

## Bibliography

Selected external sources from the October 2026 research review. These inform evaluation questions; they do not establish Cognous implementation, adoption, conformance or production qualification.

- [Alexander Barrett. *Boundary Blindness Under Artificial Intelligence: Early Cross-Industry Findings on the Missing Decision-Evidence Layer* (2026)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7210798). Working paper on carrying the basis for reliance across organizational boundaries; proposed architecture, not a validated interoperability guarantee.
- [OECD. *Agentic AI in organisations: Early insights from practitioner interviews*. OECD Artificial Intelligence Papers, No. 65 (2026)](https://doi.org/10.1787/1257a26f-en). Qualitative practitioner research on bounded autonomy, oversight and organizational deployment.
- [John W. Creswell and J. David Creswell. *Research Design: Qualitative, Quantitative, and Mixed Methods Approaches*, fifth edition. SAGE (2018)](https://edge.sagepub.com/creswellrd5e). Research-methods reference for explicit questions, comparison designs and interpretation limits.

See the [research bibliography](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/research-bibliography.md) for review scope and source-verification limits.

## Cognous stack components

The six groups organize component responsibilities. They are not an execution
sequence or a requirement to install every component. The [hub lock](https://github.com/cogno-us/cognous-open-control-stack/blob/main/component-lock.json)
defines the selected integration; [release status](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/release-status.md)
defines its evidence and limits.

| Group | Components |
| --- | --- |
| **01 · Knowledge & Provenance** | [The Index (Evidence Registry)](https://github.com/cogno-us/cognous-evidence-registry) · [BitRep (Evidence Attestation)](https://github.com/cogno-us/cognous-evidence-attestation) |
| **02 · Institutional Governance** | [Alvorada (Institutional Governance)](https://github.com/cogno-us/cognous-institutional-governance) · authority contracts |
| **03 · Declaration & Policy Control** | [Action Manifest](https://github.com/cogno-us/cognous-action-manifest) · [Control Plane](https://github.com/cogno-us/cognous-control-plane) |
| **04 · Constrained Execution** | [Execution Runtime (Moltbot Safe)](https://github.com/cogno-us/cognous-execution-runtime) |
| **05 · Replay & Evidence** | [Replay Bundle](https://github.com/cogno-us/cognous-replay-bundle) · [Governance Evidence Pack](https://github.com/cogno-us/cognous-governance-evidence-pack) · [ODES](https://github.com/cogno-us/open-decision-evidence-standard) |
| **06 · Reasoning & Human Oversight** | [PRP](https://github.com/cogno-us/portable-reasoning-protocol) · [Research Intelligence](https://github.com/cogno-us/research-intelligence-protocol) · [TFA](https://github.com/cogno-us/truth-freedom-agency-protocol) |

**Cross-cutting exchange:** [Governed Exchange (GAX/IMX)](https://github.com/cogno-us/cognous-governed-exchange) connects
governed messages, recipient assessment and continuity across the groups. It is
separate from Alvorada's institutional authority framework.

Execution Runtime and Moltbot Safe name the same repository here. The supported
Cognous Python execution boundary remains distinct from the retained upstream
application. PRP, Research Intelligence and TFA are optional behavioral
instructions; they do not enforce authorization or substitute for human oversight.
A signature, registry entry, message receipt or evidence summary does not grant
execution authority.


## Repository locations

See the [repository rename map and compatibility notes](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/repository-renames.md) for current component URLs. Existing package names, schema identifiers and retained producer identities are unchanged.

## Merged producer compatibility

The exact merged Control Plane/executor pair has a versioned `agep-manifest-reconstruction-import/0.3.2` consumer mapping. See [qualification scope and pinned revisions](docs/merged-producer-compatibility.md). This covers the existing bounded export; atomic-claim and refund-intent evidence are not added.

## Cross component qualification

Executable integration suites and harnesses moved to the [qualification repository](https://github.com/cogno-us/cognous-stack-qualification/tree/39f038435afdd71ba162860faa5718d90d7bde64/suites/cognous-governance-evidence-pack). See [the path migration map](CROSS_COMPONENT_TESTS.md) for current commands and source identity rules. Component-local tests remain here; historical qualification results retain their original scope.

<!-- Retained anchors for existing documentation links. -->
<a id="current-selection-historical-evidence-and-a-bounded-example"></a>
<a id="evidence-and-supported-scope"></a>
