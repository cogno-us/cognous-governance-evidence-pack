"""Current generation (CUR): Control Plane b19c47dd, runtime f7a55e2a, Manifest fa170815, Replay pin ``imp.CUR_REPLAY_PIN``.

Added beside Programme 2 (P2 and every earlier generation are unchanged), exactly paired, never mixed. PROVISIONAL DEVELOPMENT PIN,
UNQUALIFIED (inherited from P2). The Replay pin is the merge commit d395e37c of Replay PR cogno-us/cognous-replay-bundle#81 (E1); it is
written once (``CUR_REPLAY_PIN``) and a later Replay re-tie is a one-line change.

Two kinds of case:

* stub cases replace only the Replay constant module (as test_p2_generation), so they run without Replay installed;
* end-to-end cases feed REAL current-generation Control Plane run records and runtime exports (tests/fixtures/current_generation,
  provenance alongside) through a real Replay at exactly the pinned revision, then through the pack, and check content. Pack requires
  the installed Replay HEAD to equal the pin (``_require_pinned_replay_distribution``), so the fixture ``cur_replay`` makes a clean
  scratch clone of the Replay repository named by the environment variable ``AGEP_CUR_REPLAY_SOURCE`` (a local path or URL; never
  edited), checks out the pin and puts it first on ``sys.path`` for the test. Without the variable (or when an installed Replay
  distribution's metadata would shadow the scratch clone) those cases are skipped, like the P2 end-to-end cases.

What this proves: the generation is accepted only as one exact tuple, the pairing is exact both ways, the pinned Replay is required,
real current records of the four scenarios are admitted and keep their content, and the explicitly unsupported scope
(effective_configuration, policy-binding members, reason vocabulary 0.3, selection_refusal, authorization_pin) is still refused
through Replay. What it does not prove: that provenance labels are anything but caller-asserted, or that any producer decision
re-derives.
"""
import copy
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from agent_governance_evidence_pack import importer as imp
from agent_governance_evidence_pack.importer import ImportContractError
from tests.test_f5b_generation import F5B, MANIFEST, OLD, RUNTIME_AUTHORITY_EXECUTOR, _bundle, replay  # noqa: F401
from tests.test_p2_generation import P2, PREVIOUS_P2_CONTROL_PLANES, PREVIOUS_P2_RUNTIMES, p2_replay  # noqa: F401
from tests.test_p4_generation import P4, p4_replay  # noqa: F401

# Every case here sees the real installed-Replay-revision check (tests/conftest.py stubs it for the other modules).
pytestmark = pytest.mark.real_distribution_check

FIX = Path(__file__).parent / "fixtures" / "current_generation"
# Written out here on purpose (not read back from the importer), so a typo in the importer fails these tests.
CUR = {"manifest": "fa170815ef96a54c233d0dd9da821b60debabf8b",
       "replay": "d395e37c443fedf1bf6b9a4651338b7b7de4a553",
       "control_plane": "b19c47ddd020409d24e52e70b11359c46265edbb",
       "moltbot_safe": "f7a55e2a8494801e49193f9f46935f0a971c248d"}
CUR_CP_PROFILE = "control-plane-current-stack@b19c47dd"
CUR_EXECUTOR_PROFILE = "moltbot-safe-executor-producer-2.0.0@f7a55e2a"
CUR_TRANSFORMATION = "agep-manifest-reconstruction-import/0.3.9-current-stack-candidate"
P2_REPLAY = "40012b8c174c6f25685bd5d9bc93ff46cc9a5842"
GENERATED = "2026-10-05T19:05:00+00:00"
SCENARIOS = ("adapter-default", "adapter-operation-identity", "atomic-default", "atomic-operation-key")
OTHER_GENERATIONS = {"security": OLD, "f5b": F5B, "p4": P4, "p2": P2}
ENV = "AGEP_CUR_REPLAY_SOURCE"
REQUIRE_ENV = "AGEP_REQUIRE_CUR_E2E"  # =1: a missing or shadowed Replay source FAILS the end-to-end tests instead of skipping them (set in CI)
CUR_CONSTANTS = dict(CONTROL_PLANE_CUR_REVISION=CUR["control_plane"], MOLTBOT_CUR_REVISION=CUR["moltbot_safe"],
                     MANIFEST_CUR_REVISION=CUR["manifest"], BOUNDED_CUR_PROFILE=CUR_CP_PROFILE)


# --------------------------------------------------------------------------------------------------------- stub fixtures
@pytest.fixture
def cur_replay_stub(monkeypatch, p2_replay):
    """Replay stub exporting the P2 constants (via p2_replay) plus the current-generation constants."""
    module = sys.modules["agent_replay_bundle.importers"]
    for key, value in CUR_CONSTANTS.items():
        setattr(module, key, value)

    def override(**values):
        for key, value in values.items():
            if value is None:
                monkeypatch.delattr(module, key, raising=False)
            else:
                setattr(module, key, value)
    return override


def _other_bundle(other, executor):
    """A bundle of another generation's Control Plane with its own accepted profile identity."""
    bundle = _bundle(other["control_plane"], executor, other["manifest"])
    if other is P2:
        bundle["producer_profiles"][0]["profile_id"] = bundle["records"][0]["producer_profile_id"] = "control-plane-programme2-profiles@7a4bcd40"
    return bundle


def cur_bundle(cp=CUR["control_plane"], executor=CUR["moltbot_safe"], manifest_revision=None):
    bundle = _bundle(cp, executor, manifest_revision if manifest_revision is not None or cp != CUR["control_plane"] else CUR["manifest"])
    if cp == CUR["control_plane"]:
        bundle["producer_profiles"][0]["profile_id"] = CUR_CP_PROFILE
        bundle["records"][0]["producer_profile_id"] = CUR_CP_PROFILE
    return bundle


# ------------------------------------------------------------------------------------------------------- pins and sets
def test_current_generation_is_added_and_every_earlier_generation_is_unchanged():
    assert imp.CUR_REVISIONS == CUR
    assert imp.CUR_REPLAY_PIN == CUR["replay"] == imp.CUR_REVISIONS["replay"]
    assert imp.CUR_TRANSFORMATION_VERSION == CUR_TRANSFORMATION
    assert imp.P2_REVISIONS == P2 and imp.P4_REVISIONS == P4 and imp.F5B_REVISIONS == F5B and imp.SECURITY_REVISIONS == OLD
    assert imp.P2_TRANSFORMATION_VERSION == "agep-manifest-reconstruction-import/0.3.8-programme2-profiles-candidate"
    others = {imp.TRANSFORMATION_VERSION, imp.LEGACY_TRANSFORMATION_VERSION, imp.PERSISTENCE_TRANSFORMATION_VERSION, imp.MERGED_TRANSFORMATION_VERSION,
              imp.REFUSAL_TRANSFORMATION_VERSION, imp.RUNTIME_AUTHORITY_TRANSFORMATION_VERSION, imp.SECURITY_TRANSFORMATION_VERSION,
              imp.F5B_TRANSFORMATION_VERSION, imp.P4_TRANSFORMATION_VERSION, imp.P2_TRANSFORMATION_VERSION}
    assert imp.CUR_TRANSFORMATION_VERSION not in others and len(others) == 10
    for key in ("replay", "control_plane", "moltbot_safe"):
        assert all(CUR[key] != generation[key] for generation in OTHER_GENERATIONS.values())
    assert CUR["manifest"] == P2["manifest"] != P4["manifest"]  # the action manifest did not move between P2 and the current generation


def test_current_pins_are_in_exactly_the_sets_that_hold_the_other_generations():
    historical_cps = {imp.V2_REVISIONS["control_plane"], imp.CONTROL_PLANE_V2_PERSISTENCE_REVISION, imp.MERGED_REVISIONS["control_plane"],
                      imp.REFUSAL_REVISIONS["control_plane"], imp.RUNTIME_AUTHORITY_REVISIONS["control_plane"],
                      *(g["control_plane"] for g in OTHER_GENERATIONS.values())}
    assert set(imp.ALL_CONTROL_PLANE_V2_REVISIONS) == historical_cps | {CUR["control_plane"]}
    assert len(imp.ALL_CONTROL_PLANE_V2_REVISIONS) == len(historical_cps) + 1
    assert set(imp.SECURITY_RUNTIME_GENERATIONS) == {g["control_plane"] for g in OTHER_GENERATIONS.values()} | {CUR["control_plane"]}
    assert imp.SECURITY_RUNTIME_GENERATIONS[CUR["control_plane"]] == (imp.CUR_REVISIONS, imp.CUR_TRANSFORMATION_VERSION)
    assert imp.REQUIRED_REPOS["cogno-us/cognous-agent-control-plane"] == {imp.CONTROL_PLANE_REVISION, *imp.ALL_CONTROL_PLANE_V2_REVISIONS}
    for repo, key in [("cogno-us/cognous-agent-action-manifest", "manifest"), ("cogno-us/cognous-agent-replay-bundle", "replay"),
                      ("cogno-us/cognous-agent-control-plane", "control_plane"), ("cogno-us/moltbot-safe", "moltbot_safe")]:
        assert {*(g[key] for g in OTHER_GENERATIONS.values()), CUR[key]} <= imp.REQUIRED_REPOS[repo]
    assert imp.REQUIRED_REPOS["cogno-us/cognous-agent-replay-bundle"] >= {CUR["replay"], P2["replay"]}
    assert imp.REQUIRED_REPOS["cogno-us/moltbot-safe"] >= {CUR["moltbot_safe"], P2["moltbot_safe"]}
    # not in the legacy / v2-era supported sets nor the producer version map
    for revisions in imp.SUPPORTED_REVISION_SETS.values():
        assert not {CUR["control_plane"], CUR["moltbot_safe"], CUR["replay"]} & set(revisions)
    assert CUR["moltbot_safe"] not in imp.PRODUCER_REVISIONS.values()


def test_current_pins_appear_in_the_importer_only_through_the_one_tuple():
    source = Path(imp.__file__).read_text()
    assert source.count(CUR["replay"]) == 1, "the Replay pin is written in ONE place"
    assert source.count(CUR["control_plane"]) == 1 and source.count(CUR["moltbot_safe"]) == 1
    assert source.count("7a4bcd40b3b49e61ff3c294dcca53b52f460b22c") == 1 and source.count("c5e97e87dd239c821b1b4a406a55dcd03c5bc61f") == 1


def test_expected_replay_revision_is_the_pin_for_current_and_unchanged_for_p2(cur_replay_stub):
    assert imp._expected_replay_revision(cur_bundle()) == CUR["replay"] != P2_REPLAY
    assert imp._expected_replay_revision(_bundle(P2["control_plane"], P2["moltbot_safe"], P2["manifest"])) == P2_REPLAY == P2["replay"]
    assert imp._expected_replay_revision(_bundle(P4["control_plane"], P4["moltbot_safe"], P4["manifest"])) == P4["replay"]


def test_current_selects_only_its_own_revisions(cur_replay_stub):
    bundle = cur_bundle()
    imp._validate_headers(MANIFEST, bundle)
    assert imp._is_security(bundle) and imp._is_v2(bundle) and imp._security_revisions(bundle) == CUR
    assert imp.SECURITY_RUNTIME_GENERATIONS[CUR["control_plane"]][1] == imp.CUR_TRANSFORMATION_VERSION
    p2 = _bundle(P2["control_plane"], P2["moltbot_safe"], P2["manifest"])
    p2["producer_profiles"][0]["profile_id"] = p2["records"][0]["producer_profile_id"] = "control-plane-programme2-profiles@7a4bcd40"
    imp._validate_headers(MANIFEST, p2)  # P2 is untouched
    assert imp._security_revisions(p2) == P2 and imp.SECURITY_RUNTIME_GENERATIONS[P2["control_plane"]][1] == imp.P2_TRANSFORMATION_VERSION


# ------------------------------------------------------------------------------------------------------- negative pairing
@pytest.mark.parametrize("name", sorted(OTHER_GENERATIONS))
def test_current_cross_generation_pairs_rejected_both_ways(cur_replay_stub, name):
    other = OTHER_GENERATIONS[name]
    with pytest.raises(ImportContractError, match="not paired"):
        imp._validate_headers(MANIFEST, cur_bundle(CUR["control_plane"], other["moltbot_safe"]))
    with pytest.raises(ImportContractError, match="not paired"):
        imp._validate_headers(MANIFEST, _other_bundle(other, CUR["moltbot_safe"]))


def test_current_executor_with_the_runtime_authority_control_plane_and_the_reverse_is_rejected(cur_replay_stub):
    with pytest.raises(ImportContractError, match="not paired"):
        imp._validate_headers(MANIFEST, cur_bundle(CUR["control_plane"], RUNTIME_AUTHORITY_EXECUTOR))
    with pytest.raises(ImportContractError, match="not paired"):
        imp._validate_headers(MANIFEST, cur_bundle(imp.RUNTIME_AUTHORITY_REVISIONS["control_plane"], CUR["moltbot_safe"]))


@pytest.mark.parametrize("manifest_revision", [OLD["manifest"], F5B["manifest"], "0" * 40])
def test_current_with_a_manifest_of_another_generation_is_rejected(cur_replay_stub, manifest_revision):
    with pytest.raises(ImportContractError, match="not paired"):
        imp._validate_headers(MANIFEST, cur_bundle(manifest_revision=manifest_revision))


def test_the_unchanged_manifest_serves_p2_and_current_alike(cur_replay_stub):
    assert CUR["manifest"] == P2["manifest"]
    imp._validate_headers(MANIFEST, cur_bundle(manifest_revision=CUR["manifest"]))


def test_current_revisions_are_not_accepted_by_older_generations(cur_replay_stub):
    for name, other in OTHER_GENERATIONS.items():
        executors = {g["moltbot_safe"] for g in OTHER_GENERATIONS.values()}
        assert CUR["moltbot_safe"] not in {g["moltbot_safe"] for g in OTHER_GENERATIONS.values()}
        assert imp._security_revisions(_bundle(other["control_plane"], other["moltbot_safe"], other["manifest"])) == other
        assert CUR["control_plane"] != other["control_plane"] and executors
    for revision in (CUR["moltbot_safe"], CUR["control_plane"]):
        for generation in (imp.REFUSAL_REVISIONS, imp.MERGED_REVISIONS, imp.PERSISTENCE_REVISIONS, imp.V2_REVISIONS):
            assert revision not in generation.values()


@pytest.mark.parametrize("executor", sorted({CUR["moltbot_safe"][:8], CUR["moltbot_safe"].upper(), CUR["moltbot_safe"][:-1] + "0", CUR["moltbot_safe"][:-1] + "1",
                                             "f7a55e2a" + "0" * 32, "0" * 40, CUR["moltbot_safe"] + " "}))
def test_a_near_miss_executor_revision_is_rejected(cur_replay_stub, executor):
    with pytest.raises(ImportContractError):
        imp._validate_headers(MANIFEST, cur_bundle(executor=executor))


@pytest.mark.parametrize("cp", sorted({CUR["control_plane"][:8], CUR["control_plane"].upper(), CUR["control_plane"][:-1] + "0", CUR["control_plane"][:-1] + "1",
                                       "b19c47dd" + "0" * 32, "0" * 40}))
def test_a_near_miss_control_plane_revision_is_not_the_current_generation(cur_replay_stub, cp):
    # An unknown Control Plane revision is not v2/security at all: it is never admitted as the current generation.
    bundle = cur_bundle(cp=cp, manifest_revision=CUR["manifest"])
    assert not imp._is_security(bundle) and imp._selected_control_plane_revision(bundle) != CUR["control_plane"]
    with pytest.raises(ImportContractError):
        imp._validate_headers(MANIFEST, bundle)


@pytest.mark.parametrize("previous", PREVIOUS_P2_RUNTIMES)
def test_previous_p2_runtimes_do_not_pair_with_current(cur_replay_stub, previous):
    with pytest.raises(ImportContractError):
        imp._validate_headers(MANIFEST, cur_bundle(executor=previous))


@pytest.mark.parametrize("previous", PREVIOUS_P2_CONTROL_PLANES)
def test_previous_p2_control_planes_are_not_accepted_for_current(cur_replay_stub, previous):
    assert previous not in imp.ALL_CONTROL_PLANE_V2_REVISIONS
    with pytest.raises(ImportContractError):
        imp._validate_headers(MANIFEST, cur_bundle(cp=previous))


# --------------------------------------------------------------------------------------------- Replay constants mirrored
@pytest.mark.parametrize("override", [
    {"MOLTBOT_CUR_REVISION": P2["moltbot_safe"]}, {"MOLTBOT_CUR_REVISION": P4["moltbot_safe"]},
    {"CONTROL_PLANE_CUR_REVISION": P2["control_plane"]}, {"CONTROL_PLANE_CUR_REVISION": P4["control_plane"]},
    {"MANIFEST_CUR_REVISION": OLD["manifest"]}, {"MANIFEST_CUR_REVISION": P4["manifest"]},
    {"MOLTBOT_CUR_REVISION": CUR["moltbot_safe"][:-1] + "0"}, {"CONTROL_PLANE_CUR_REVISION": CUR["control_plane"][:-1] + "0"},
])
def test_current_requires_exact_replay_mapping(cur_replay_stub, override):
    cur_replay_stub(**override)
    with pytest.raises(ImportContractError, match="current-generation source mapping contradicts"):
        imp._validate_headers(MANIFEST, cur_bundle())


@pytest.mark.parametrize("override", [
    {"CONTROL_PLANE_CUR_REVISION": None, "MOLTBOT_CUR_REVISION": None, "MANIFEST_CUR_REVISION": None, "BOUNDED_CUR_PROFILE": None},
    {"MOLTBOT_CUR_REVISION": None}, {"CONTROL_PLANE_CUR_REVISION": None}, {"MANIFEST_CUR_REVISION": None}, {"BOUNDED_CUR_PROFILE": None},
], ids=["all", "moltbot", "control_plane", "manifest", "profile"])
def test_current_with_a_replay_that_lacks_the_constants_is_refused(cur_replay_stub, override):
    """A Replay that does not list the generation (for instance the P2 Replay) cannot vouch for a current bundle."""
    cur_replay_stub(**override)
    with pytest.raises(ImportContractError, match="current-generation Replay mapping unavailable"):
        imp._validate_headers(MANIFEST, cur_bundle())


def test_current_profile_identity_must_match_the_replay_profile(cur_replay_stub):
    for wrong in ("control-plane-programme2-profiles@7a4bcd40", "control-plane-security-runtime@b19c47dd", "control-plane-current-stack@7a4bcd40"):
        bundle = cur_bundle()
        bundle["producer_profiles"][0]["profile_id"] = bundle["records"][0]["producer_profile_id"] = wrong
        with pytest.raises(ImportContractError, match="contradicts accepted Replay revision/profile mapping"):
            imp._validate_headers(MANIFEST, bundle)
    cur_replay_stub(BOUNDED_CUR_PROFILE="control-plane-current-stack@00000000")
    with pytest.raises(ImportContractError, match="contradicts accepted Replay revision/profile mapping"):
        imp._validate_headers(MANIFEST, cur_bundle())


def test_current_executor_profile_identity_is_the_replay_profile_of_the_pinned_runtime(cur_replay_stub):
    bundle = cur_bundle()
    assert bundle["producer_profiles"][1]["profile_id"] == CUR_EXECUTOR_PROFILE
    for wrong in ("moltbot-safe-executor-producer-2.0.0@c5e97e87", "moltbot-safe-executor-producer-1.0.0@f7a55e2a"):
        bundle["producer_profiles"][1]["profile_id"] = wrong
        with pytest.raises(ImportContractError, match="requires accepted Replay producer profile identity"):
            imp._validate_headers(MANIFEST, bundle)
    bundle = cur_bundle()
    bundle["producer_profiles"][1]["format_version"] = "1.0.0"
    with pytest.raises(ImportContractError, match="requires executor producer profile 2.0.0"):
        imp._validate_headers(MANIFEST, bundle)


def test_earlier_generations_do_not_require_the_current_mapping(cur_replay_stub):
    cur_replay_stub(**{key: None for key in CUR_CONSTANTS})
    imp._validate_headers(MANIFEST, _bundle(P4["control_plane"], P4["moltbot_safe"], P4["manifest"]))
    imp._validate_headers(MANIFEST, _bundle(F5B["control_plane"], F5B["moltbot_safe"], F5B["manifest"]))
    p2 = _bundle(P2["control_plane"], P2["moltbot_safe"], P2["manifest"])
    p2["producer_profiles"][0]["profile_id"] = p2["records"][0]["producer_profile_id"] = "control-plane-programme2-profiles@7a4bcd40"
    imp._validate_headers(MANIFEST, p2)


def test_accepted_profile_mapping_has_current_only_when_required(cur_replay_stub):
    assert imp._accepted_replay_v2_profiles(require_p2=True, require_cur=True)[CUR["control_plane"]] == CUR_CP_PROFILE
    assert CUR["control_plane"] not in imp._accepted_replay_v2_profiles(require_p2=True)
    assert P2["control_plane"] not in imp._accepted_replay_v2_profiles(require_cur=True)


# ------------------------------------------------------------------------------------------------ real Replay, pinned scratch
def _git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=300).stdout.strip()


def _e2e_required():
    return os.environ.get(REQUIRE_ENV) == "1"


def _distribution_metadata_present():
    import importlib.metadata as metadata
    try:
        metadata.distribution("agent-replay-bundle")
        return True
    except metadata.PackageNotFoundError:
        return False


@pytest.fixture(scope="session")
def replay_source_clone(tmp_path_factory):
    """Clean scratch clone of the Replay repository (never the original checkout), HEAD at the pin."""
    source = os.environ.get(ENV)
    if not source:
        if _e2e_required():
            pytest.fail(f"{REQUIRE_ENV}=1 but {ENV} is not set: the current-generation end-to-end tests cannot run")
        pytest.skip(f"{ENV} is not set: no Replay checkout to make the pinned scratch clone from")
    root = tmp_path_factory.mktemp("replay-scratch")
    clone = root / "replay"
    _git("clone", "--quiet", source, str(clone))
    _git("checkout", "--quiet", imp.CUR_REPLAY_PIN, cwd=clone)
    assert _git("rev-parse", "HEAD", cwd=clone) == imp.CUR_REPLAY_PIN
    assert _git("status", "--porcelain", "--untracked-files=no", cwd=clone) == ""
    return clone


def _activate(monkeypatch, clone):
    if _distribution_metadata_present():
        if _e2e_required():
            pytest.fail(f"{REQUIRE_ENV}=1 but an installed agent-replay-bundle distribution's metadata shadows the scratch clone (install the pack without the replay extra)")
        pytest.skip("an installed agent-replay-bundle distribution's metadata would shadow the scratch clone")
    for name in [n for n in sys.modules if n == "agent_replay_bundle" or n.startswith("agent_replay_bundle.")]:
        monkeypatch.delitem(sys.modules, name)
    monkeypatch.syspath_prepend(str(clone / "src"))
    importlib.invalidate_caches()
    return importlib.import_module("agent_replay_bundle.importers")


@pytest.fixture
def cur_replay(monkeypatch, replay_source_clone):
    module = _activate(monkeypatch, replay_source_clone)
    assert (module.CONTROL_PLANE_CUR_REVISION, module.MOLTBOT_CUR_REVISION, module.MANIFEST_CUR_REVISION, module.BOUNDED_CUR_PROFILE) == (
        CUR["control_plane"], CUR["moltbot_safe"], CUR["manifest"], CUR_CP_PROFILE)
    assert Path(module.__file__).resolve().is_relative_to(replay_source_clone.resolve())
    return module


def _inputs(name):
    return [json.loads((FIX / name / f"{n}.json").read_text()) for n in ("control_plane_run", "proposal", "executor")]


def _bundle_of(replay_module, name):
    cp, proposal, executor = _inputs(name)
    return replay_module.import_bounded_workflow(cp, proposal=proposal, moltbot_export=executor,
                                                 control_plane_revision=CUR["control_plane"]).model_dump(mode="json")


def _pack(bundle, manifest=None):
    manifest = manifest or json.loads((FIX / "manifest.json").read_text())
    return imp.import_manifest_reconstruction(manifest, bundle, generated_at=GENERATED)


def _trace(pack):
    return pack.metadata["traceable_import"]


def _kinds(pack):
    return _trace(pack)["lifecycle_records"]


def _record(bundle, record_type):
    (found,) = [r for r in bundle["records"] if r["record_type"] == record_type]
    return found


def test_the_fixtures_are_the_four_real_current_scenarios_with_current_revisions():
    assert sorted(p.name for p in FIX.iterdir() if p.is_dir()) == sorted(SCENARIOS)
    for name in SCENARIOS:
        cp, proposal, executor = _inputs(name)
        assert executor["repository"]["revision"] == CUR["moltbot_safe"]
        assert executor["provenance"]["source_asserted"]["repository_revision"] == CUR["moltbot_safe"]
        assert "7a4bcd40" not in json.dumps([cp, proposal, executor]) and "c5e97e87" not in json.dumps(executor)


@pytest.mark.parametrize("name", SCENARIOS)
def test_real_current_bundle_is_admitted_with_the_pinned_generation_and_keeps_its_content(cur_replay, name):
    cp, proposal, executor = _inputs(name)
    bundle = _bundle_of(cur_replay, name)
    pack = _pack(bundle)
    trace = _trace(pack)
    assert trace["transformation_version"] == CUR_TRANSFORMATION != imp.P2_TRANSFORMATION_VERSION
    assert trace["selected_revisions"] == {"manifest": CUR["manifest"], "replay": CUR["replay"], "control_plane": CUR["control_plane"],
                                           "moltbot_safe": CUR["moltbot_safe"]}
    assert {k: trace["supported_revisions"][k] for k in CUR} == CUR
    assert trace["replay_semantic_validation"] == {"validator": "agent_replay_bundle.importers.import_bounded_workflow",
                                                   "required_revision": CUR["replay"], "status": "validated_complete"}
    assert [r["adapter_profile"] for r in trace["replay_import_reports"]] == [CUR_CP_PROFILE]
    kinds = _kinds(pack)
    assert {"execution_envelope", "execution_result", "destination_effect", "runtime_decision"} <= set(kinds)
    assert "freshness_summary" not in trace
    # content, not just acceptance
    assert kinds["runtime_decision"] == cp["decisions"] and kinds["runtime_proposal"] == [proposal]
    assert kinds["runtime_decision"][0]["reason_vocabulary_version"] == "runtime-authority-reasons/0.1"
    assert kinds["execution_result"] == [executor["execution_result"]] and executor["execution_result"]["status"] == "executed"
    assert kinds["executor_control_plane_evidence"] == [executor["control_plane_evidence"]]
    assert len(kinds.get("control_plane_attempt_transition", [])) == len(cp.get("attempts", []))
    assert bundle["metadata"]["moltbot_producer_contract"]["profile_id"] == CUR_EXECUTOR_PROFILE
    assert bundle["metadata"]["moltbot_producer_contract"]["compatible_control_plane_revisions"] == [CUR["control_plane"]]
    for profile in bundle["producer_profiles"]:
        assert profile["revision"] in {CUR["control_plane"], CUR["moltbot_safe"]}


def test_operation_identity_records_of_the_current_run_reach_the_pack_and_the_default_has_none(cur_replay):
    with_identity = {name: _kinds(_pack(_bundle_of(cur_replay, name))) for name in SCENARIOS}
    assert {"operation", "attempt_join"} <= set(with_identity["adapter-operation-identity"])
    for name in ("adapter-default", "atomic-default"):
        assert not {"operation", "attempt_join"} & set(with_identity[name])
    assert "operation" in with_identity["atomic-operation-key"]
    cp = _inputs("adapter-operation-identity")[0]
    assert len(with_identity["adapter-operation-identity"]["operation"]) == len(cp["operations"]) >= 1


def test_a_current_default_run_adds_no_opt_in_profile_records_to_the_pack(cur_replay):
    kinds = set(_kinds(_pack(_bundle_of(cur_replay, "adapter-default"))))
    assert not kinds & {"merge_record", "snapshot_use", "dedupe_escalation", "rule_revision", "recovery_run"}


def test_the_p2_replay_cannot_build_a_current_bundle(monkeypatch, replay_source_clone, tmp_path):
    """A Replay checkout at the P2 pin (40012b8c) does not know the current generation at all."""
    clone = tmp_path / "p2"
    shutil.copytree(replay_source_clone, clone)
    _git("checkout", "--quiet", P2_REPLAY, cwd=clone)
    module = _activate(monkeypatch, clone)
    assert _git("rev-parse", "HEAD", cwd=clone) == P2_REPLAY and not hasattr(module, "CONTROL_PLANE_CUR_REVISION")
    cp, proposal, executor = _inputs("adapter-default")
    with pytest.raises(module.ImportContractError):
        module.import_bounded_workflow(cp, proposal=proposal, moltbot_export=executor, control_plane_revision=CUR["control_plane"])


def test_a_current_bundle_is_refused_when_the_installed_replay_is_not_at_the_pin(monkeypatch, replay_source_clone, tmp_path):
    cur_module = _activate(monkeypatch, replay_source_clone)
    bundle = _bundle_of(cur_module, "adapter-default")
    # (1) the P2 Replay checkout, clean, HEAD 40012b8c
    p2_clone = tmp_path / "p2"
    shutil.copytree(replay_source_clone, p2_clone)
    _git("checkout", "--quiet", P2_REPLAY, cwd=p2_clone)
    _activate(monkeypatch, p2_clone)
    with pytest.raises(ImportContractError, match="current-generation Replay mapping unavailable"):
        _pack(bundle)  # the P2 Replay does not list the generation, so it cannot vouch for it
    # (2) the pinned checkout with a modified tracked source file (dirty tree): revision cannot be established
    dirty = tmp_path / "dirty"
    shutil.copytree(replay_source_clone, dirty)
    target = dirty / "src" / "agent_replay_bundle" / "importers.py"
    target.write_text(target.read_text() + "\n# local modification\n")
    _activate(monkeypatch, dirty)
    with pytest.raises(ImportContractError, match="is not the pinned revision"):
        _pack(bundle)
    # (3) a Replay that does list the generation but sits one commit past the pin
    other = tmp_path / "other"
    shutil.copytree(replay_source_clone, other)
    _git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "--quiet", "--allow-empty", "-m", "past the pin", cwd=other)
    assert _git("rev-parse", "HEAD", cwd=other) != CUR["replay"]
    _activate(monkeypatch, other)
    with pytest.raises(ImportContractError, match=f"is not the pinned revision {CUR['replay']}"):
        _pack(bundle)
    # (4) control: the pinned scratch clone itself is accepted
    _activate(monkeypatch, replay_source_clone)
    assert _trace(_pack(bundle))["replay_semantic_validation"]["required_revision"] == CUR["replay"]


# Two specific historical Replay heads that must NOT satisfy the gate: bb5fe6f3 (merge commit of #80, the pin before E1 was merged) and
# a88a383e (head of the E1 PR branch, the second parent of the E1 merge commit d395e37c). Written out here, not read from the importer.
SUPERSEDED_REPLAY_HEADS = {"bb5fe6f3cb3775729bc3a1434ad45dbc985636c8": "merge commit of Replay #80 (pin before E1)",
                           "a88a383ee3288b2776d50f4f9ea1dc92ec791df3": "head of the E1 PR branch (second parent of the pin)"}


@pytest.mark.parametrize("head", sorted(SUPERSEDED_REPLAY_HEADS), ids=lambda h: h[:8])
def test_the_pinned_gate_refuses_the_superseded_replay_heads(monkeypatch, replay_source_clone, tmp_path, head):
    bundle = _bundle_of(_activate(monkeypatch, replay_source_clone), "adapter-default")
    clone = tmp_path / "superseded"
    shutil.copytree(replay_source_clone, clone)
    _git("checkout", "--quiet", head, cwd=clone)  # a real Replay checkout, clean tree
    assert _git("rev-parse", "HEAD", cwd=clone) == head != CUR["replay"] == "d395e37c443fedf1bf6b9a4651338b7b7de4a553"
    assert _git("status", "--porcelain", "--untracked-files=no", cwd=clone) == ""
    _activate(monkeypatch, clone)
    assert imp._installed_replay_revision() == head
    with pytest.raises(ImportContractError, match=f"installed Replay distribution revision '{head}' is not the pinned revision {CUR['replay']}"):
        imp._require_pinned_replay_distribution(CUR["replay"])
    with pytest.raises(ImportContractError, match=f"is not the pinned revision {CUR['replay']}"):
        _pack(bundle)  # also through the whole import, not only the gate function
    _activate(monkeypatch, replay_source_clone)  # control: the pin itself passes the same gate
    imp._require_pinned_replay_distribution(CUR["replay"])


def test_the_p2_pin_is_unchanged_by_the_current_generation(monkeypatch, replay_source_clone, tmp_path):
    """A P2 Replay at 40012b8c is still the pin of a P2 bundle, and the current Replay is not (P2 is not re-pointed)."""
    assert imp._expected_replay_revision(_bundle(P2["control_plane"], P2["moltbot_safe"], P2["manifest"])) == P2_REPLAY
    cur_module = _activate(monkeypatch, replay_source_clone)
    p2_run = json.loads((Path(__file__).parent / "fixtures" / "p2_generation" / "adapter-default" / "control_plane_run.json").read_text())
    p2_proposal = json.loads((Path(__file__).parent / "fixtures" / "p2_generation" / "adapter-default" / "proposal.json").read_text())
    p2_executor = json.loads((Path(__file__).parent / "fixtures" / "p2_generation" / "adapter-default" / "executor.json").read_text())
    p2_bundle = cur_module.import_bounded_workflow(p2_run, proposal=p2_proposal, moltbot_export=p2_executor,
                                                   control_plane_revision=P2["control_plane"]).model_dump(mode="json")
    manifest = json.loads((Path(__file__).parent / "fixtures" / "p2_generation" / "manifest.json").read_text())
    with pytest.raises(ImportContractError, match=f"is not the pinned revision {P2_REPLAY}"):
        _pack(p2_bundle, manifest)


# ------------------------------------------------------------------------- relabelling and mixing with a real current bundle
@pytest.mark.parametrize("executor_revision", [P2["moltbot_safe"], P4["moltbot_safe"], F5B["moltbot_safe"]])
def test_a_real_current_bundle_with_an_earlier_executor_revision_is_refused(cur_replay, executor_revision):
    bundle = copy.deepcopy(_bundle_of(cur_replay, "adapter-default"))
    for profile in bundle["producer_profiles"]:
        if profile.get("repository") == "cogno-us/moltbot-safe":
            profile["revision"] = executor_revision
            profile["profile_id"] = f"moltbot-safe-executor-producer-2.0.0@{executor_revision[:8]}"
    with pytest.raises(ImportContractError):
        _pack(bundle)


@pytest.mark.parametrize("control_plane_revision", [P2["control_plane"], P4["control_plane"], F5B["control_plane"], OLD["control_plane"]])
def test_a_real_current_bundle_relabelled_to_an_earlier_control_plane_is_refused(cur_replay, control_plane_revision):
    bundle = copy.deepcopy(_bundle_of(cur_replay, "adapter-default"))
    bundle["metadata"]["control_plane_revision"] = control_plane_revision
    for profile in bundle["producer_profiles"]:
        if profile.get("repository") == "cogno-us/cognous-agent-control-plane":
            profile["revision"] = control_plane_revision
    with pytest.raises(ImportContractError):
        _pack(bundle)


def test_a_real_current_bundle_with_an_arbitrary_control_plane_hash_is_refused(cur_replay):
    bundle = copy.deepcopy(_bundle_of(cur_replay, "adapter-default"))
    bundle["metadata"]["control_plane_revision"] = "1" * 40
    for profile in bundle["producer_profiles"]:
        if profile.get("repository") == "cogno-us/cognous-agent-control-plane":
            profile["revision"] = "1" * 40
    with pytest.raises(ImportContractError):
        _pack(bundle)


def test_a_real_current_bundle_with_a_tampered_retained_record_is_refused(cur_replay):
    bundle = copy.deepcopy(_bundle_of(cur_replay, "adapter-default"))
    _record(bundle, "execution_result")["data"]["status"] = "failed"
    with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed"):
        _pack(bundle)


# ----------------------------------------------------------------------------- explicitly unsupported scope stays refused
EFFECTIVE_CONFIGURATION = {"version": "effective-configuration-binding/0.1", "digest": "sha256:" + "1" * 64,
                           "members": {"scope": {"consumer_id": "consumer-test", "tenant_id": "tenant-alpha"}}}
POLICY_BINDING = {"approval_commitment_version": "approval-commitment/0.2", "policy_generation": 1, "policy_activation_ref": "sha256:" + "c" * 64}


def _authority(bundle):
    return _record(bundle, "runtime_decision")["data"]["binding"]["runtime_authority"]


def test_replay_itself_refuses_the_unsupported_scope_at_the_pin(cur_replay):
    """The premise of the propagation cases below: Replay at the pin refuses raw inputs that carry the unsupported members."""
    cp, proposal, executor = _inputs("adapter-default")
    for members in ({"effective_configuration": EFFECTIVE_CONFIGURATION}, POLICY_BINDING):
        forged = copy.deepcopy(cp)
        for decision in forged["decisions"]:
            decision["binding"]["runtime_authority"].update(members)
        with pytest.raises(cur_replay.ImportContractError, match="runtime authority fields unsupported"):
            cur_replay.import_bounded_workflow(forged, proposal=proposal, moltbot_export=executor, control_plane_revision=CUR["control_plane"])


@pytest.mark.parametrize("members", [
    {"effective_configuration": EFFECTIVE_CONFIGURATION}, {"approval_commitment_version": POLICY_BINDING["approval_commitment_version"]},
    {"policy_generation": 1}, {"policy_activation_ref": POLICY_BINDING["policy_activation_ref"]}, POLICY_BINDING],
    ids=["effective_configuration", "approval_commitment_version", "policy_generation", "policy_activation_ref", "policy_binding_all"])
@pytest.mark.parametrize("name", ["adapter-default", "atomic-operation-key"])
def test_pack_refuses_a_current_run_carrying_effective_configuration_or_policy_binding_members(cur_replay, name, members):
    bundle = copy.deepcopy(_bundle_of(cur_replay, name))
    _authority(bundle).update(copy.deepcopy(members))
    with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed: .*runtime authority fields unsupported"):
        _pack(bundle)


def test_pack_refuses_reason_vocabulary_0_3(cur_replay):
    bundle = copy.deepcopy(_bundle_of(cur_replay, "adapter-default"))
    _record(bundle, "runtime_decision")["data"]["reason_vocabulary_version"] = "runtime-authority-reasons/0.3"
    with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed: .*decision vocabulary missing"):
        _pack(bundle)


@pytest.mark.parametrize("member", ["selection_refusal", "authorization_pin"])
def test_pack_refuses_selection_refusal_and_authorization_pin_evidence(cur_replay, member):
    bundle = copy.deepcopy(_bundle_of(cur_replay, "adapter-default"))
    _record(bundle, "executor_control_plane_evidence")["data"][member] = {"version": "0.1"}
    _record(bundle, "execution_result")["data"].setdefault("control_plane_evidence", {})[member] = {"version": "0.1"}
    with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed: .*unsupported typed refusal executor evidence field"):
        _pack(bundle)


# ------------------------------------------------------------------------------------- E1 Registry-governed profile: unsupported scope
GOVERNED_SELECTOR = "registry-governed-effective-configuration/0.1"
GOVERNED_PROFILE = "control-plane-current-stack-registry-governed-effective-configuration-0.1@b19c47dd"
GOVERNED_SCENARIOS = ("governed_executed", "governed_binding_changed", "governed_decided_only", "governed_age_only")


def _governed_bundle(replay_module, clone, name):
    """A REAL bundle produced by Replay at the pin under the E1 Registry-governed profile (Replay's own fixtures at the pin, read from the clone)."""
    fix = clone / "tests" / "fixtures" / "registry_governed_effective_configuration" / name
    cp, proposal = (json.loads((fix / f"{n}.json").read_text()) for n in ("control_plane_run", "proposal"))
    bundle = replay_module.import_bounded_workflow(cp, proposal=proposal, moltbot_export=None, control_plane_revision=CUR["control_plane"],
                                                   control_plane_profile=GOVERNED_SELECTOR).model_dump(mode="json")
    assert [p["profile_id"] for p in bundle["producer_profiles"]] == [GOVERNED_PROFILE]
    assert _record(bundle, "runtime_decision")["data"]["binding"]["runtime_authority"]["effective_configuration"]["version"] == "effective-configuration-binding/0.1"
    return bundle


@pytest.mark.parametrize("name", GOVERNED_SCENARIOS)
def test_the_registry_governed_profile_is_explicitly_unsupported_by_the_pack(cur_replay, replay_source_clone, name):
    """E1 (Replay #81) added a separate Registry-governed profile. The Pack was not asked to support it: a bundle Replay produces under it is
    refused at the Pack's own producer-profile gate, before any semantic validation, and the plain current profile does not admit it either."""
    bundle = _governed_bundle(cur_replay, replay_source_clone, name)
    with pytest.raises(ImportContractError, match="^Control Plane producer profile identity contradicts accepted Replay revision/profile mapping$"):
        _pack(bundle)
    assert GOVERNED_PROFILE not in {v for v in vars(imp).values() if isinstance(v, str)}  # the importer names no governed profile


@pytest.mark.parametrize("name", ["governed_executed", "governed_decided_only"])
def test_a_governed_bundle_relabelled_as_the_plain_current_profile_is_still_refused(cur_replay, replay_source_clone, name):
    """Second gate: a caller who relabels a governed bundle with the plain current profile id passes the profile-identity gate but Replay at the
    pin still refuses the effective_configuration member (provenance labels are caller-asserted; the member check is not)."""
    bundle = json.loads(json.dumps(_governed_bundle(cur_replay, replay_source_clone, name)).replace(GOVERNED_PROFILE, CUR_CP_PROFILE))
    for key in ("control_plane_profile", "effective_configuration_verification"):
        bundle["metadata"].pop(key, None)
    with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed: .*runtime authority fields unsupported"):
        _pack(bundle)


# ------------------------------------------------------------------------------------------------ the CI switch cannot be silently skipped
def _inner_e2e(tmp_path, *, require, source, shadow):
    """Run one end-to-end case in a child pytest with a controlled environment; returns (returncode, output)."""
    root = Path(__file__).resolve().parent.parent
    env = {k: v for k, v in os.environ.items() if k not in (ENV, REQUIRE_ENV, "PYTHONPATH")}
    paths = [str(root), str(root / "src")]
    if shadow:
        dist = tmp_path / "shadow" / "agent_replay_bundle-0.0.dist-info"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "METADATA").write_text("Metadata-Version: 2.1\nName: agent-replay-bundle\nVersion: 0.0\n")
        paths.append(str(tmp_path / "shadow"))
    env["PYTHONPATH"] = os.pathsep.join(paths)
    if require:
        env[REQUIRE_ENV] = "1"
    if source:
        env[ENV] = source
    node = "tests/test_current_generation.py::test_real_current_bundle_is_admitted_with_the_pinned_generation_and_keeps_its_content[adapter-default]"
    done = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", node, "-rs"], cwd=root, env=env,
                          capture_output=True, text=True, timeout=600)
    return done.returncode, done.stdout + done.stderr


def test_a_missing_replay_source_skips_by_default_but_fails_when_the_ci_switch_is_set(tmp_path):
    code, out = _inner_e2e(tmp_path, require=False, source=None, shadow=False)
    assert code == 0 and "1 skipped" in out, out
    code, out = _inner_e2e(tmp_path, require=True, source=None, shadow=False)
    assert code != 0 and "cannot run" in out and "skipped" not in out, out


def test_an_installed_replay_distribution_skips_by_default_but_fails_when_the_ci_switch_is_set(tmp_path, replay_source_clone):
    code, out = _inner_e2e(tmp_path, require=False, source=str(replay_source_clone), shadow=True)
    assert code == 0 and "1 skipped" in out, out
    code, out = _inner_e2e(tmp_path, require=True, source=str(replay_source_clone), shadow=True)
    assert code != 0 and "shadows the scratch clone" in out and "skipped" not in out, out
