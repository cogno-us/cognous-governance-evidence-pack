# Repaired runtime Evidence Pack generation — 16 October 2026

Adds transformation `agep-manifest-reconstruction-import/0.3.5-security-runtime-candidate` for the exact CP 996baeb4 / runtime fd6b76fa / Replay 3601fb21 / Manifest e385f8c1 generation. Historical mappings and transformations remain unchanged.

The importer reconstructs and validates full runtime-authority journals, reason vocabulary changes, typed refusals, closeouts and time floors using the actual new Replay mapping. Exact producer combinations and source attribution remain required. Retained failure-record identifiers are source-asserted references; they do not prove independently verified durability. Existing semantic revalidation and refusal-vocabulary summaries remain mandatory.

Tests and results are maintained centrally in `cognous-stack-qualification/suites/security-runtime`. No selected profile, production permission or publication acceptance changes.
