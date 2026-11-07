"""S2 Pack compatibility: explicit opt-in CP2 Replay candidate ``cp2-replay-7eb7d76e-tenant-binding-dev-0.1`` (DEVELOPMENT ONLY, SYNTHETIC, UNQUALIFIED, NOT ADOPTED).

The existing CP2 generation keeps its exact Replay pin (93a76e28); the candidate accepts the repaired Replay merge commit 7eb7d76e ONLY when the caller declares it with
``replay_generation=...``. Needs a Replay git repository holding both revisions in ``AGEP_CP2B_REPLAY_SOURCE`` (scratch clones are made at each pin; the original is never
touched). ``AGEP_REQUIRE_CP2B_E2E=1`` turns a missing source into a failure (skips are not passes). Expected values are written out here, not read back from the importer.
"""
import copy
import hashlib
import json
import os
from pathlib import Path

import pytest

from agent_governance_evidence_pack import importer as imp
from agent_governance_evidence_pack.importer import ImportContractError
from agent_governance_evidence_pack.validator import validate_evidence_pack
from tests.test_cp2_generation import (CP2, CP2_TRANSFORMATION, EFFECTIVE_CONFIGURATION, GENERATED, POLICY_BINDING, _activate, _authority, _clone_at, _e2e_required,  # noqa: F401
                                       _git, _import, _kinds, _load, _paired_inputs, _record, _strict_inputs, _trace)

pytestmark = pytest.mark.real_distribution_check

FIX = Path(__file__).parent / "fixtures" / "cp2b_replay_candidate"
ENV, REQUIRE_ENV = "AGEP_CP2B_REPLAY_SOURCE", "AGEP_REQUIRE_CP2B_E2E"
NEW_REPLAY = "7eb7d76eda10ca1ff997bb86853e903e57da625c"
OLD_REPLAY = "93a76e281fcae6a65d2cd1d35376f87442dafb95"
ID = "cp2-replay-7eb7d76e-tenant-binding-dev-0.1"
TRANSFORMATION = "agep-manifest-reconstruction-import/0.3.11-strict-tenant-replay-7eb7d76e-dev-candidate"
RECORD = {"id": ID, "replay_revision": NEW_REPLAY, "control_plane": CP2["control_plane"], "moltbot_safe": CP2["moltbot_safe"], "manifest": CP2["manifest"], "opt_in": "caller_declared"}


def _required():
    return os.environ.get(REQUIRE_ENV) == "1"


@pytest.fixture(scope="session")
def _source():
    source = os.environ.get(ENV)
    if not source:
        if _required():
            pytest.fail(f"{REQUIRE_ENV}=1 but {ENV} is not set")
        pytest.skip(f"{ENV} is not set")
    return source


def _scratch(tmp_path_factory, source, revision, name):
    clone = tmp_path_factory.mktemp(name) / "replay"
    _git("clone", "--quiet", source, str(clone))
    _git("checkout", "--quiet", revision, cwd=clone)
    assert _git("rev-parse", "HEAD", cwd=clone) == revision and _git("status", "--porcelain", "--untracked-files=no", cwd=clone) == ""
    return clone


@pytest.fixture(scope="session")
def new_clone(_source, tmp_path_factory):
    return _scratch(tmp_path_factory, _source, NEW_REPLAY, "replay-new")


@pytest.fixture(scope="session")
def old_clone(_source, tmp_path_factory):
    return _scratch(tmp_path_factory, _source, OLD_REPLAY, "replay-old")


@pytest.fixture
def new_replay(monkeypatch, new_clone):
    module = _activate(monkeypatch, new_clone)
    assert Path(module.__file__).resolve().is_relative_to(new_clone.resolve()) and hasattr(module, "_validate_operation_tenant")
    return module


def _executed_inputs():
    return tuple(json.loads((FIX / n).read_text()) for n in ("control_plane_run.json", "proposal.json", "runtime_export.json"))


def _pack(bundle, **kw):
    return imp.import_manifest_reconstruction(_load("manifest.json"), bundle, generated_at=GENERATED, **kw)


def _opt(bundle):
    return _pack(bundle, replay_generation=ID)


def test_fixture_hashes_are_pinned():
    pinned = json.loads((FIX / "PROVENANCE.json").read_text())["sha256"]
    for name, digest in pinned.items():
        assert hashlib.sha256((FIX / name).read_bytes()).hexdigest() == digest, name


def test_defaults_are_unchanged_in_source():
    assert imp.CP2_REPLAY_PIN == OLD_REPLAY and imp.CP2_REVISIONS["replay"] == OLD_REPLAY and imp.CP2_TRANSFORMATION_VERSION == CP2_TRANSFORMATION
    assert list(imp.CP2_REPLAY_CANDIDATES) == [ID] and imp.CP2_REPLAY_CANDIDATES[ID]["replay"] == NEW_REPLAY
    candidate = imp.CP2_REPLAY_CANDIDATES[ID]
    assert {k: candidate[k] for k in ("control_plane", "moltbot_safe", "manifest")} == {k: CP2[k] for k in ("control_plane", "moltbot_safe", "manifest")}
    assert imp.SECURITY_RUNTIME_GENERATIONS[CP2["control_plane"]] == (imp.CP2_REVISIONS, CP2_TRANSFORMATION)
    assert NEW_REPLAY not in {r for generation in imp.SECURITY_RUNTIME_GENERATIONS.values() for r in generation[0].values()}


# ------------------------------------------------------------------------------------------------------------------ positives
def test_p2_executed_strict_tenant_reconstruction_is_accepted_only_under_the_opt_in(new_replay):
    bundle = _import(new_replay, _executed_inputs())
    assert bundle["status"] == "reconstruction_complete"
    pack = _opt(bundle)
    t = _trace(pack)
    assert t["replay_generation"] == RECORD and pack.metadata["traceable_import"]["transformation_version"] == TRANSFORMATION
    assert t["replay_semantic_validation"]["required_revision"] == NEW_REPLAY and t["replay_semantic_validation"]["status"] == "validated_complete"
    assert t["input_artifacts"][1]["trusted_revision"] == NEW_REPLAY and t["selected_revisions"]["replay"] == NEW_REPLAY
    assert t["selected_revisions"]["control_plane"] == CP2["control_plane"] and t["selected_revisions"]["manifest"] == CP2["manifest"]
    c = t["derived_counts"]
    assert c["executor_attempt_count"] >= 1 and c["destination_effect_count"] == 1 and c["execution_result_state_counts"], c
    report = validate_evidence_pack(pack)
    assert report.valid, [i for i in report.issues if i.severity.value == "error"]


def test_p2b_the_candidate_changes_no_counter_or_evidence_semantics(monkeypatch, old_clone, new_clone):
    """Same executed inputs: the CP2 pack under 93a76e28 and the candidate pack under 7eb7d76e agree on every derived count and lifecycle summary."""
    old = _import(_activate(monkeypatch, old_clone), _executed_inputs())
    old_trace = _trace(_pack(old))
    assert "replay_generation" not in old_trace and old_trace["transformation_version"] == CP2_TRANSFORMATION
    new = _import(_activate(monkeypatch, new_clone), _executed_inputs())
    new_trace = _trace(_opt(new))
    for key in ("derived_counts", "lifecycle_summary"):
        assert new_trace[key] == old_trace[key], key


def test_p3_tenantless_paired_run_is_unchanged_and_accepted_under_the_opt_in_too(new_replay):
    bundle = _import(new_replay, _paired_inputs("adapter-default"))
    assert _trace(_opt(bundle))["replay_semantic_validation"]["status"] == "validated_complete"


def test_p4_no_opt_in_never_selects_the_candidate_merely_because_the_installed_replay_is_newer(new_replay):
    bundle = _import(new_replay, _executed_inputs())
    for kw in ({}, {"replay_generation": None}):
        with pytest.raises(ImportContractError, match=f"is not the pinned revision {OLD_REPLAY}"):
            _pack(bundle, **kw)


# ------------------------------------------------------------------------------------------------------------------ negatives
def test_n1_old_generation_with_the_new_replay_is_refused(new_replay):
    bundle = _import(new_replay, _executed_inputs())
    cur = copy.deepcopy(bundle)
    cur["metadata"]["control_plane_revision"] = imp.CUR_REVISIONS["control_plane"]       # an older generation's label, with the opt-in
    with pytest.raises(ImportContractError, match="not paired with the selected Control Plane revision"):
        _opt(cur)
    with pytest.raises(ImportContractError, match=f"is not the pinned revision {OLD_REPLAY}"):    # and without the opt-in
        _pack(bundle)


def test_n2_new_generation_with_the_old_replay_is_refused(monkeypatch, old_clone, new_clone):
    bundle = _import(_activate(monkeypatch, new_clone), _executed_inputs())
    _activate(monkeypatch, old_clone)
    with pytest.raises(ImportContractError, match=f"is not the pinned revision {NEW_REPLAY}"):
        _opt(bundle)


def test_n3_unsupported_replay_revision_or_candidate_id_is_refused(monkeypatch, new_clone, tmp_path):
    bundle = _import(_activate(monkeypatch, new_clone), _executed_inputs())
    dirty = tmp_path / "dirty"
    import shutil
    shutil.copytree(new_clone, dirty)
    target = dirty / "src" / "agent_replay_bundle" / "importers.py"
    target.write_text(target.read_text() + "\n# local modification\n")
    _activate(monkeypatch, dirty)
    with pytest.raises(ImportContractError, match="is not the pinned revision"):
        _opt(bundle)
    past = tmp_path / "past"
    shutil.copytree(new_clone, past)
    _git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "--quiet", "--allow-empty", "-m", "past the pin", cwd=past)
    _activate(monkeypatch, past)
    with pytest.raises(ImportContractError, match=f"is not the pinned revision {NEW_REPLAY}"):
        _opt(bundle)
    _activate(monkeypatch, new_clone)
    for bad in ("", "x", ID.upper(), ID + "-2", "cp2-replay-7eb7d76e", 7, ["a"], True):
        with pytest.raises(ImportContractError, match="unsupported Replay generation candidate"):
            _pack(bundle, replay_generation=bad)


@pytest.mark.parametrize("what", ["control_plane", "runtime", "manifest"])
def test_n4_n5_n6_wrong_control_plane_runtime_or_manifest_revision_is_refused(new_replay, what):
    bundle = _import(new_replay, _executed_inputs())
    near = lambda r: r[:-1] + ("0" if r[-1] != "0" else "1")          # noqa: E731  (a one-character near miss)
    if what == "control_plane":
        bundle["metadata"]["control_plane_revision"] = near(CP2["control_plane"])
        message = "not paired with the selected Control Plane revision"
    elif what == "runtime":
        for p in bundle["producer_profiles"]:
            if p.get("repository") == "cogno-us/moltbot-safe":
                p["revision"] = near(CP2["moltbot_safe"])
        message = "producer_profiles\\[\\d+\\].revision for cogno-us/moltbot-safe conflicts with pinned supported revision"
    else:
        bundle["metadata"]["manifest_revision"] = near(CP2["manifest"])
        message = "Manifest revision is not paired"
    with pytest.raises(ImportContractError, match=message):
        _opt(bundle)


def _candidate_pack(new_replay):
    return _opt(_import(new_replay, _executed_inputs()))


@pytest.mark.parametrize("tamper", ["unknown_id", "id_removed", "transformation_to_cp2", "pins_to_cp2", "added_to_default_shape"])
def test_n7_missing_or_conflicting_candidate_identity_is_reported_by_the_validator(new_replay, tamper):
    pack = _candidate_pack(new_replay).model_copy(deep=True)
    t = pack.metadata["traceable_import"]
    if tamper == "unknown_id":
        t["replay_generation"]["id"] = "cp2-replay-unknown"
    elif tamper == "id_removed":
        del t["replay_generation"]
    elif tamper == "transformation_to_cp2":
        t["transformation_version"] = CP2_TRANSFORMATION
    elif tamper == "pins_to_cp2":
        t["replay_semantic_validation"]["required_revision"] = OLD_REPLAY
        t["input_artifacts"][1]["trusted_revision"] = OLD_REPLAY
    else:
        t["replay_generation"]["opt_in"] = "automatic"
    report = validate_evidence_pack(pack)
    assert not report.valid and any(i.code == "E_TRACE_SEMANTICS" for i in report.issues), [(i.code, i.message) for i in report.issues]


def test_n7b_a_cp2_pack_that_declares_a_candidate_is_reported_by_the_validator(monkeypatch, old_clone):
    old = _import(_activate(monkeypatch, old_clone), _executed_inputs())
    pack = _pack(old).model_copy(deep=True)
    assert validate_evidence_pack(pack).valid
    pack.metadata["traceable_import"]["replay_generation"] = copy.deepcopy(RECORD)
    report = validate_evidence_pack(pack)
    assert not report.valid and any(i.code == "E_TRACE_SEMANTICS" for i in report.issues)


def test_n8_completeness_is_never_manufactured(new_replay):
    cp, proposal, _ = _strict_inputs("cp_only", "strict")
    partial = _import(new_replay, (cp, proposal, None))
    assert partial["status"] == "reconstruction_partial"
    t = _trace(_opt(partial))
    assert t["replay_semantic_validation"]["status"] == "validated_partial" and "execution_result" not in _kinds(_opt(partial))
    complete = _import(new_replay, _executed_inputs())
    stripped = copy.deepcopy(complete)
    stripped["records"] = [r for r in stripped["records"] if r["record_type"] not in imp.EXECUTION_TYPES]
    with pytest.raises(ImportContractError):
        _opt(stripped)


@pytest.mark.parametrize("members", [{"effective_configuration": EFFECTIVE_CONFIGURATION}, POLICY_BINDING, {"policy_generation": 1}],
                         ids=["effective_configuration", "policy_binding_all", "policy_generation"])
def test_n9_unsupported_authority_members_are_refused_as_under_cp2(new_replay, members):
    bundle = _import(new_replay, _paired_inputs("adapter-default"))
    _authority(bundle).update(copy.deepcopy(members))
    with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed: .*runtime authority fields unsupported"):
        _opt(bundle)


def test_n9b_reason_vocabulary_0_3_and_selection_refusal_are_refused_as_under_cp2(new_replay):
    bundle = _import(new_replay, _paired_inputs("adapter-default"))
    _record(bundle, "runtime_decision")["data"]["reason_vocabulary_version"] = "runtime-authority-reasons/0.3"
    with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed: .*decision vocabulary missing"):
        _opt(bundle)
    bundle = _import(new_replay, _paired_inputs("adapter-default"))
    _record(bundle, "executor_control_plane_evidence")["data"]["selection_refusal"] = {"version": "0.1"}
    _record(bundle, "execution_result")["data"].setdefault("control_plane_evidence", {})["selection_refusal"] = {"version": "0.1"}
    with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed: .*unsupported typed refusal executor evidence field"):
        _opt(bundle)
