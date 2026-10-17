"""The retained Replay bundle must equal a fresh accepted reconstruction, including import reports and semantics.

Regression for qualification F-06/F-12 (SCN-D08, SCN-C23): dropping `import_reports` / findings or promoting
`semantics` (independent verification, destination observation) in a retained bundle used to be accepted because only
records, links, commitments, producer profiles and status were compared. Replay is stubbed (as in
test_f5b_generation.py), so no Replay install is needed.
"""
import copy
import sys
import types

import pytest

from agent_governance_evidence_pack import importer as imp
from agent_governance_evidence_pack.importer import ImportContractError

from tests.test_f5b_generation import F5B, _bundle, _replay_constants

REPORTS = [{"adapter_profile": "control-plane-security-runtime@a34c3dc2", "source_revision": F5B["control_plane"], "complete": True,
            "field_mappings": {}, "findings": [{"code": "M002", "category": "unsupported_semantic", "severity": "warning",
                                                 "path": "attempt_correlation", "message": "m", "value_state": "unknown"}]}]
SEMANTICS = {"record_reconstruction": True, "policy_reevaluation": False, "model_reexecution": False,
             "external_effect_execution": False, "destination_observation": "producer_reported",
             "independent_effect_verification": False, "notes": "n"}


def retained_bundle():
    bundle = _bundle(F5B["control_plane"], F5B["moltbot_safe"])
    bundle.update(links=[], commitments=[], status="reconstruction_complete",
                  import_reports=copy.deepcopy(REPORTS), semantics=copy.deepcopy(SEMANTICS))
    return bundle


@pytest.fixture
def validator(monkeypatch):
    package = types.ModuleType("agent_replay_bundle")
    module = types.ModuleType("agent_replay_bundle.importers")
    module.__dict__.update(_replay_constants())

    class ImportContractErrorStub(ValueError):
        pass

    module.ImportContractError = ImportContractErrorStub

    def import_bounded_workflow(control_plane, **kwargs):
        reference = retained_bundle()  # the fresh, accepted reconstruction of the retained records
        return types.SimpleNamespace(status=reference["status"], model_dump=lambda mode="json": copy.deepcopy(reference) | {"metadata": {}})

    module.import_bounded_workflow = import_bounded_workflow
    package.importers = module
    monkeypatch.setitem(sys.modules, "agent_replay_bundle", package)
    monkeypatch.setitem(sys.modules, "agent_replay_bundle.importers", module)
    monkeypatch.setattr(imp, "_retained_replay_inputs", lambda bundle: ({}, None, None))
    return imp._run_pinned_replay_validator


def test_matching_bundle_is_accepted(validator):
    assert validator(retained_bundle()) == "validated_complete"


@pytest.mark.parametrize("name,mutate,field", [
    ("drop_all_reports", lambda b: b["import_reports"].clear(), "import_reports"),
    ("drop_findings", lambda b: [r["findings"].clear() for r in b["import_reports"]], "import_reports"),
    ("promote_independent_verification", lambda b: b["semantics"].__setitem__("independent_effect_verification", True), "semantics"),
    ("promote_destination_observation", lambda b: b["semantics"].__setitem__("destination_observation", "not_performed"), "semantics"),
])
def test_tampered_reports_or_semantics_are_rejected(validator, name, mutate, field):
    bundle = retained_bundle()
    mutate(bundle)
    with pytest.raises(ImportContractError, match=f"retained Replay {field} differs from accepted reconstruction"):
        validator(bundle)
