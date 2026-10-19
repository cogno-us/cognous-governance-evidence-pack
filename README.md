<!-- cognous-banner:start -->
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

| | |
|---|---|
| Lock status | **selected**: lock key `governance_evidence_pack`, imported Evidence Pack schema 0.2.0, manifest/reconstruction transformation 0.3.2 (see [Selection and compatibility](#selection-and-compatibility)) |
| Stack group | 05 Replay & Evidence (siblings: [Replay Bundle](https://github.com/cogno-us/cognous-replay-bundle), [ODES](https://github.com/cogno-us/open-decision-evidence-standard)); see [where it fits](#cognous-stack-components) |
| Package and command | package `agent-governance-evidence-pack` 0.1.0, import `agent_governance_evidence_pack`, command `agep` ([naming](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/naming.md)) |
| Requirements | Python 3.11 or newer; Linux is the supported platform; traceable imports also need a pinned [Replay Bundle](https://github.com/cogno-us/cognous-replay-bundle) install |
| Documentation | [Documentation index](docs/README.md) |

## What it is, who it is for, what it does not do

**What it is.** A reference format, validator, traceable importer and Markdown renderer for business-facing review of agent governance records. It can represent a hand-authored evidence pack (the 0.1 shape), or build an imported pack deterministically from an Action Manifest and a Reconstruction Bundle, preserving the relationship between the declared action surface and the reconstructed runtime evidence instead of treating a summary as independent assurance.

**Who it is for.** Reviewers and engineers who need to follow a summarized decision or outcome back to its source and see the difference between historical authorization, current recovery denial and observed destination state. Engineers can inspect the reference contracts and examples; architecture, security and governance reviewers can examine the boundary and evidence.

**What it does not do.** It is not certification, legal advice, independent audit, or a runtime enforcement layer. A summary is derivative evidence: import success does not establish that a test ran, that an institution authorized current reliance, or that a control is effective in production. It makes no network calls and executes nothing. The [known limits](#known-limits) are listed below.

**Synthetic example.** A synthetic evidence pack links the refund proposal, authorization decision, runtime attempt and observed unknown outcome. Its summary is derivative evidence, not independent confirmation that a processor settled the refund.

## Quick start (about two minutes)

Prerequisites: Python 3.11 or newer, `git`, and network access for package installation (the `pydantic` dependency). Install in editable mode and run the commands from the repository root: `agep check-examples` looks for `examples/` next to the installed source, so a non-editable install prints `No example files found.`

```bash
git clone https://github.com/cogno-us/cognous-governance-evidence-pack
cd cognous-governance-evidence-pack
python3 -m venv .venv && . .venv/bin/activate
python -m pip install -e ".[dev]"
agep validate examples/customer_service_agent_evidence_pack.json
agep summarize examples/customer_service_agent_evidence_pack.json
agep render examples/customer_service_agent_evidence_pack.json --out customer_service.md
agep check-examples
```

Expected output, with exit code 0 for each command:

```text
$ agep validate examples/customer_service_agent_evidence_pack.json
Pack ID : ep-cs-agent-2026-001
Valid   : True
Issues  : 1
  [WARNING] W014 [review_records]: review_records is empty.

$ agep summarize examples/customer_service_agent_evidence_pack.json
semantic_validation_passed: True
pack_id                  : ep-cs-agent-2026-001
title                    : Customer Service Agent — Governance Evidence Pack
review_status            : in_review
...

$ agep render examples/customer_service_agent_evidence_pack.json --out customer_service.md
Rendered to customer_service.md

$ agep check-examples
VALID   customer_service_agent_evidence_pack.json (1 issue(s))
...
VALID   procurement_agent_evidence_pack.json (0 issue(s))
```

The warning is expected: the example has no review records, and the validator says so. Warnings do not make a pack invalid. `agep check-examples` also rewrites `examples/rendered/*.md` in place; with unchanged code `git status` stays clean. Exit codes: `0` valid; `1` invalid pack or an import error; `2` usage error or an input file that is missing or rejected by input admission. The command has no help flag: running `agep` with no arguments prints the usage line and exits `2`. Use `--out` with `render`: without it the Markdown goes to standard output with line breaks shown as the literal text `\u000a`. The rendered file starts with `# Customer Service Agent — Governance Evidence Pack` and a metadata table.

**What this does not prove.** `Valid: True` means the pack is internally consistent. Review status, `signed`, `redacted` and validation fields in a hand-authored pack are caller assertions that nothing here verifies (the renderer labels them "asserted, unverified"). A valid pack is not independent assurance or compliance certification.

### Optional: a traceable import

`agep import` builds an imported pack from an Action Manifest and a Reconstruction Bundle. It needs the pinned [Replay Bundle](https://github.com/cogno-us/cognous-replay-bundle) semantic validator installed in the same environment, and one environment validates only one Replay generation (the `replay` extra installs the Programme-2 generation; this example uses the older generation described in [traceable imports](docs/traceable_imports.md)). Use a separate environment:

```bash
python3 -m venv .venv-import && . .venv-import/bin/activate
git clone https://github.com/cogno-us/cognous-replay-bundle upstream/replay
git -C upstream/replay checkout f63ce914504dd06813c4ccd199b0570dbd8dd427
git clone https://github.com/cogno-us/cognous-action-manifest upstream/manifest
git -C upstream/manifest checkout 46c950bed37fe3812000895430bc0312d29e37ce
python -m pip install -e upstream/replay -e .
agep import \
  --manifest upstream/manifest/examples/refund_integration_v1_1.manifest.json \
  --reconstruction upstream/replay/examples/bounded_success_reconstruction_v0_2.json \
  --out traceable.json --render traceable.md
agep validate traceable.json
agep summarize traceable.json
```

<!-- pin-round: the two revisions above are the ones traceable_imports.md documents; the lock pins this repository at b4baccd823d2. Refresh with the docs gate. -->

These commands create `upstream/`, `traceable.json` and `traceable.md` inside the checkout; delete them when you are done. Expected output, with exit code 0 for each command:

```text
Imported traceable evidence pack to traceable.json
Rendered traceable evidence pack to traceable.md
Pack ID : agep-dcacf65f1d59156a
Valid   : True
Issues  : 7
  [WARNING] W002 [agent_overview.business_unit]: agent_overview.business_unit is missing.
  ...
semantic_validation_passed: True
...
distinct_effect_count  : 1
cp_attempt_count       : 1
executor_attempt_count : 1
destination_observed   : applied
```

The seven warnings are empty optional sections (business unit, data domains, blocked actions, reliance, redaction exports, risk register, review records). The pack identifier is derived from the inputs (the value shown is an example and can change if the importer changes). `destination_observed: applied` is what the retained records report; it is not independent confirmation of a destination effect. The files in `examples/import_inputs/` are older illustrative inputs: `agep import` refuses them with `reconstruction bundle must include producer_profiles`, so use the inputs above.

To see the manifest, replay and evidence-pack commands run together offline, use `cognous-ocs demo` from the [ergonomics repository](https://github.com/cogno-us/cognous-open-control-stack-ergonomics) (needs network once for installation; its README and `docs/demo.md` state what the demo does and does not prove). For the full selected integration, use the [hub quickstart](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/quickstart.md), whose runner supplies exact producer checkouts and test wiring.

### Run the tests

```bash
python -m pip install -e ".[dev,replay]"
python -m pytest -q tests
```

This is the component-local suite that the `native` job of the Tests workflow runs (the job also re-renders `examples/rendered/` and fails on a difference). Without the `replay` extra the tests that need the Replay validator or other pinned producers are skipped. Cross-component test commands run in a disposable checkout assembled by the [qualification workflows](CROSS_COMPONENT_TESTS.md). Historical reports and dependency pins keep their original scope.

## What ships

Status labels: **merged** = merged in this repository; **selected** = pinned in the hub lock; **known limit**; **proposed**. See the [stack map](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/stack-map.md#status-labels). A newer commit here is not selected until the hub lock changes. Items marked "after the lock" are not in the revision the lock pins.

### Command-line tool `agep`

| Command | Purpose | Label |
|---|---|---|
| `agep validate <evidence_pack.json>` | Validate an Evidence Pack. | selected |
| `agep summarize <evidence_pack.json>` | Print pack counts and, for traceable imports, derived counts. | selected |
| `agep render <evidence_pack.json> [--out F.md] [--traceable]` | Render Markdown for review; `--traceable` adds the traceability addendum. | selected |
| `agep import --manifest F --reconstruction F --out F [--render F.md]` | Build a traceable Evidence Pack from a Manifest and a Reconstruction Bundle. | selected |
| `agep check-examples` | Validate every example pack. It also rewrites `examples/rendered/*.md` in place; with unchanged code the files do not change. | selected |

### Formats, transformations and profiles

| Item | What it is | Label | Details |
|---|---|---|---|
| Evidence Pack 0.1 | The hand-authored pack shape. Its review, signature, redaction and validation fields are caller assertions. | merged | [format](docs/evidence_pack_format.md), [validation](docs/validation.md) |
| Imported Evidence Pack 0.2.0 | The traceable imported pack, with trace metadata, retained sources, loss register and lifecycle summary. | selected | [traceable imports](docs/traceable_imports.md), [migration](docs/migration_v0_2_0.md) |
| Transformation 0.3.2 | The selected manifest/reconstruction transformation, for the merged producer pair. | selected | [merged producer compatibility](docs/merged-producer-compatibility.md) |
| Transformations 0.2.6 to 0.3.8 | Distinct compatibility mappings for exact producer generations, including the Programme-2 generation. Earlier ones are retained historical mappings; later ones are not selected. | merged; later generations after the lock | [producer 2.0.0](docs/producer-v2-migration.md), [persistence checkpoint](docs/workstreams/evidence-pack-control-plane-store-checkpoint.md), [producer 2.0.0 checkpoint](docs/workstreams/evidence-pack-producer-v2-checkpoint.md) |
| Typed refusal, runtime authority and repaired-runtime profiles | Separate, non-selected, additive mappings for exact revisions. | merged, after the lock | [typed refusal](docs/typed-refusal-profile.md), [runtime authority](docs/runtime-authority-profile.md), [repaired runtime](docs/security-runtime-profile-20261016.md), [F5b](docs/security-runtime-f5b-profile-20261016.md) |
| Optional freshness block | Opt-in counts derived from the retained journal; exists only when the run record carries freshness members. Not an independent monitor. | merged, after the lock | [CHANGELOG](CHANGELOG.md) |
| Recovery inspection evidence 0.1 | Optional native inspection transformation of a pinned synthetic recovery export; not the manifest importer. | merged, after the lock | [recovery inspection](docs/recovery-inspection.md) |
| W0 C8 compatibility contract | A W0 candidate mapping contract. | merged, after the lock | [contract](docs/w0-c8-compatibility-contract.md) |

### Python modules (`src/agent_governance_evidence_pack/`)

| Module | Purpose |
|---|---|
| `models`, `loader`, `validator`, `summary` | The pack models, file loader, semantic validator (`validate_evidence_pack`) and summary statistics. |
| `renderer`, `trace_renderer` | Markdown rendering and the traceability addendum for imported packs. |
| `importer` | Traceable import with pinned Replay semantic validation. |
| `cli` | The `agep` entry point. |
| `admission` | Byte and syntax budgets for reading input files. Merged after the lock. |
| `freshness` | The optional freshness block. Merged after the lock. |
| `recovery_inspection` | Optional recovery inspection evidence. Merged after the lock. |
| `w3_atomic_evidence`, `w3_c8_lineage` | W3 atomic failure-history and C8 lineage projections (separate from the 0.2.0 schema; no authority inferred). Merged after the lock. |

### JSON schemas (`schemas/`)

| Schema | Describes |
|---|---|
| `evidence_pack.schema.json` | The pack document. |
| `agent_overview`, `deployment_context`, `tool_inventory_item`, `action_inventory_item` | The agent, deployment and its tool and action inventories. |
| `authority_model_summary`, `policy_control_summary`, `blocked_action_summary`, `reliance_summary` | The authority, policy-control, blocked-action and reliance summaries. |
| `replay_bundle_inventory_item`, `redaction_export_summary`, `validation_summary` | The replay bundle inventory, redaction and export summary, and the validation summary. |
| `risk_register_item`, `review_record` | Risks and review records. |
| `validation_report`, `validation_issue` | The validation report and its issues. |

(Each name above, except `evidence_pack.schema.json`, is a file `schemas/<name>.schema.json`.) The Python models are more permissive than these schemas; validate against the schemas separately where conformance matters.

### Templates (`templates/`)

| File | Purpose |
|---|---|
| `evidence_pack_template.md`, `executive_summary_template.md`, `audit_review_template.md` | Fill-in Markdown templates for reviewers. Nothing in the package reads them; `agep render` builds its output in code. |

### Examples (`examples/`)

| Path | Shows |
|---|---|
| `customer_service_agent_evidence_pack.json`, `finance_workflow_agent_evidence_pack.json`, `internal_research_agent_evidence_pack.json`, `procurement_agent_evidence_pack.json` | Four hand-authored packs. `agep check-examples` validates each and CI re-renders them. |
| `rendered/` | The Markdown rendering of those four packs. Regenerated by CI and must match the current renderer output. |
| `producer-v2/` | Five imported packs for producer 2.0.0 lifecycle scenarios (lost acknowledgement, partial, prior absence, rejected wrong effect, restart) with their Markdown. |
| `import_inputs/` | Older illustrative import inputs. Not importable under the current contract (see above); kept unchanged as historical examples. |

See [examples](docs/examples.md) for what each pack demonstrates.

## Documentation

The [documentation index](docs/README.md) lists every page in this repository by role, with historical pages labelled. Start with:

- [Concepts](docs/concepts.md) and the [evidence pack format](docs/evidence_pack_format.md).
- [Validation](docs/validation.md) and [rendering](docs/rendering.md).
- [Traceable imports](docs/traceable_imports.md) for the import contract.

For a nontechnical introduction, read the [business overview](collateral/business-collateral.md) and [one-page overview](collateral/one-page-overview.md). Both describe this component's role and evidence limits, not additional runtime features.

## Selection and compatibility

Use the [current component lock](https://github.com/cogno-us/cognous-open-control-stack/blob/main/component-lock.json) for integration selection and the [central test hub](https://github.com/cogno-us/cognous-stack-qualification/blob/main/results/readme-commentary/index.md) for revision-specific qualification commentary. Source acceptance, selection and deployment approval remain separate decisions.

Transformations from **0.2.6** to **0.3.8** coexist as distinct compatibility mappings; the selected one is set by the hub's component lock, and an imported pack revalidates only in an environment with the Replay revision its generation pins (otherwise `agep validate` reports `E_TRACE_SEMANTICS`). Imported pack schema remains **0.2.0**. See the [persistence checkpoint](docs/workstreams/evidence-pack-control-plane-store-checkpoint.md); older migration notes describe their original generation.

<!-- pin-round: the lock pin for governance_evidence_pack is b4baccd823d2; the "after the lock" labels in "What ships" and docs/README.md describe what main adds. Re-read them when the pin moves. -->

Operational deployment trust is still [HOLD under orchestrator #30](https://github.com/cogno-us/cognous-stack-orchestrator/issues/30). No signature, evidence package, successful test or source merge creates a production grant, proves external settlement, or changes selected release authority. Test results and historical qualification records are read against their recorded source revisions.

## Where it fits: Cognous stack components

<a id="cognous-stack-components"></a>

<!-- stack-map:start -->
<!-- Canonical block: identical text in every component README. Source: docs/stack-map.md in the hub. Refresh at the pin round. -->
The Open Control Stack groups its repositories by responsibility. The groups are a navigation map, not an execution sequence and not a requirement to install every component. The hub [component lock](https://github.com/cogno-us/cognous-open-control-stack/blob/main/component-lock.json) is the only source of selected revisions; [release status](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/release-status.md) states their evidence and limits. Last checked against `component-lock.json` at hub commit `dcc9bd7533ef`.

| Group | Members |
| --- | --- |
| **01 Knowledge & Provenance** | [Evidence Registry (The Index)](https://github.com/cogno-us/cognous-evidence-registry) · [Evidence Attestation (BitRep)](https://github.com/cogno-us/cognous-evidence-attestation) |
| **02 Institutional Governance** | [Institutional Governance (Alvorada)](https://github.com/cogno-us/cognous-institutional-governance) |
| **03 Declaration & Policy Control** | [Action Manifest](https://github.com/cogno-us/cognous-action-manifest) · [Control Plane](https://github.com/cogno-us/cognous-control-plane) |
| **04 Constrained Execution** | [Execution Runtime](https://github.com/cogno-us/cognous-execution-runtime) |
| **05 Replay & Evidence** | [Replay Bundle](https://github.com/cogno-us/cognous-replay-bundle) · [Governance Evidence Pack](https://github.com/cogno-us/cognous-governance-evidence-pack) · [ODES](https://github.com/cogno-us/open-decision-evidence-standard) |
| **Cross-cutting exchange** | [Governed Exchange (GAX/IMX)](https://github.com/cogno-us/cognous-governed-exchange) |
| **Tooling and qualification** (side group) | [Ergonomics (`cognous-ocs`)](https://github.com/cogno-us/cognous-open-control-stack-ergonomics) · [Verifier](https://github.com/cogno-us/cognous-open-control-stack-verifier) · [Orchestrator](https://github.com/cogno-us/cognous-stack-orchestrator) · [Qualification](https://github.com/cogno-us/cognous-stack-qualification) |

Status labels used in this README: **merged** (reviewed and merged in the owning repository; not by itself selected), **selected** (pinned in the hub lock), **known limit** (a limitation that is stated and kept visible) and **proposed** (draft or planned work, not a supported interface). Full map, names and commands: [stack map](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/stack-map.md), [naming](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/naming.md), [profiles and tools](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/profiles-and-tools.md). A signature, registry entry, message receipt or evidence summary does not grant execution authority.
<!-- stack-map:end -->

## Known limits

Each item below is a **known limit** documented in this repository.

- Import success does not establish that a test ran, that an institution authorized current reliance or that a control is effective in production. This is not certification, legal advice, independent audit or a runtime enforcement layer. Historical transformation outputs remain attributed to their original sources.
- Review status, review decisions, `signed`, `redacted`, validation status and counts and redaction/export records in a hand-authored pack are recorded as supplied. Validation checks only their internal consistency; nothing authenticates reviewers, verifies signatures or checks redaction ([SECURITY](SECURITY.md), [rendering](docs/rendering.md#caller-assertions)).
- The Python models are more permissive than the published schemas (they ignore unknown fields and coerce compatible scalars); a pack that loads and validates may still not conform to the schemas ([SECURITY](SECURITY.md)).
- The pinned-Replay check establishes that the installed Replay distribution's recorded commit equals the pin and that the imported package files are files of that distribution. It does not authenticate the source of those files ([traceable imports](docs/traceable_imports.md), [CHANGELOG](CHANGELOG.md)).
- A producer-v2 import compares the retained bundle with a fresh reconstruction. A legacy (non producer-v2) import re-imports the retained inputs and checks only the import status: it is labelled `inputs_reimported_only`, its findings, semantics, links and commitments are copied as supplied and may be incomplete, and `trusted_revision` records the accepted pin, not an established trust fact ([traceable imports](docs/traceable_imports.md#retained-replay-bundle-comparison)).
- An imported pack revalidates only in an environment that has the Replay revision its generation pins; otherwise `agep validate` reports `E_TRACE_SEMANTICS`. A pack that identifies as an import without `metadata.traceable_import` is refused with the same code ([validation](docs/validation.md)).
- Coordinated fabrication of unauthenticated source and derived data is outside the consistency guarantee of native recovery inspection; digests establish internal consistency of supplied bytes, not authenticity ([recovery inspection](docs/recovery-inspection.md)).
- The replay importer supports one supplied proposal and envelope operation; the pack import path keeps that boundary and does not imply fleet-wide or multi-operation coverage ([traceable imports](docs/traceable_imports.md)).
- Review original artifacts and exact source revisions before extending a claim to a new environment. New dependencies, authority sources, destinations or enforcement mechanisms need their own compatibility and qualification. A passing reference case is not a certification of an enterprise deployment.

More shared scope and limits are stated once in the hub [guarantees and limits](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/guarantees-and-limits.md).

## Contributing and attribution

[Contribution guidance](CONTRIBUTING.md) describes review and validation expectations; see also the [security policy](SECURITY.md), the [code of conduct](CODE_OF_CONDUCT.md) and the [changelog](CHANGELOG.md). Keep evidence-linked claims, preserve historical records and separate proposed features from accepted implementation.

See [LICENSE](LICENSE) and [attribution](NOTICE) for the existing terms and third-party scope. Developed by [Cognous](https://cogno.us).

## Repository locations

See the [repository rename map and compatibility notes](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/repository-renames.md) for current component URLs. Existing package names, schema identifiers and retained producer identities are unchanged.

---

## Bibliography

Selected external sources from the October 2026 research review. These inform evaluation questions; they do not establish Cognous implementation, adoption, conformance or production qualification.

- [Alexander Barrett. *Boundary Blindness Under Artificial Intelligence: Early Cross-Industry Findings on the Missing Decision-Evidence Layer* (2026)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7210798). Working paper on carrying the basis for reliance across organizational boundaries; proposed architecture, not a validated interoperability guarantee.
- [OECD. *Agentic AI in organisations: Early insights from practitioner interviews*. OECD Artificial Intelligence Papers, No. 65 (2026)](https://doi.org/10.1787/1257a26f-en). Qualitative practitioner research on bounded autonomy, oversight and organizational deployment.
- [John W. Creswell and J. David Creswell. *Research Design: Qualitative, Quantitative, and Mixed Methods Approaches*, fifth edition. SAGE (2018)](https://edge.sagepub.com/creswellrd5e). Research-methods reference for explicit questions, comparison designs and interpretation limits.

See the [research bibliography](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/research-bibliography.md) for review scope and source-verification limits.

<!-- Retained anchors for existing documentation links. -->
<a id="current-selection-historical-evidence-and-a-bounded-example"></a>
<a id="evidence-and-supported-scope"></a>
