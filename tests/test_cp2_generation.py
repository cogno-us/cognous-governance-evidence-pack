"""Strict-tenant generation (CP-2): Control Plane 484fdbd2, runtime f7a55e2a, Manifest fa170815, Replay pin ``imp.CP2_REPLAY_PIN``.

Added beside the current generation (CUR) and every earlier generation, which are unchanged. PROVISIONAL DEVELOPMENT PIN, UNQUALIFIED, non-authorizing:
assigned under the Constitution at pin 1c2e920f, adoption not recorded. The Replay revision is PROVISIONAL (Replay PR cogno-us/cognous-replay-bundle#87 head
d6c05bc5, to be re-pinned to the merge commit); it is written once (``CP2_REPLAY_PIN``).

Two kinds of case, as in tests/test_current_generation.py:

* stub cases replace only the Replay constant module, so they run without Replay installed;
* end-to-end cases feed REAL records captured from a pristine Control Plane 484fdbd2 and runtime f7a55e2a (tests/fixtures/cp2_generation, provenance
  alongside) through a real Replay at exactly the pinned revision (a scratch clone of the repository named by ``AGEP_CP2_REPLAY_SOURCE``), then through
  the pack. ``AGEP_REQUIRE_CP2_E2E=1`` turns every skip into a failure (set in CI).

What this proves: the generation is accepted only as one exact tuple, paired exactly (the shared runtime is paired with BOTH CUR and CP-2 and the
Control Plane label disambiguates), the exact pinned Replay is required, real CP-2 records keep their content and their strict tenant-aware effect
identity, evidence tampering and unsupported scope are refused, and a bundle is stamped with the generation it DECLARES.

What it does NOT prove: that provenance labels are anything but caller-asserted (a CUR-captured record is accepted under the CP-2 label, and a strict
tenant record under the CUR label, by Replay: see the explicit characterization tests), that the pack re-derives any producer decision or effect identity
(only Replay recomputes it), or that a strict-tenant run EXECUTES through the runtime path: runtime f7a55e2a refuses the tenant-aware operation
("runtime proposal mismatch: tenant_id"), so only DENIED strict-tenant runtime exports exist (tests/fixtures/cp2_generation/PROVENANCE.json).
"""
import copy
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from agent_governance_evidence_pack import importer as imp
from agent_governance_evidence_pack.importer import ImportContractError
from tests.test_current_generation import (CUR, CUR_CP_PROFILE, CUR_EXECUTOR_PROFILE, CUR_TRANSFORMATION, EXE_NOT_PAIRED, GENUINE_VERIFICATION,  # noqa: F401
                                           MANIFEST_NOT_PAIRED, OTHER_GENERATIONS, P2_REPLAY, cur_bundle, cur_replay_stub, _other_bundle)
from tests.test_f5b_generation import F5B, MANIFEST, OLD, RUNTIME_AUTHORITY_EXECUTOR, _bundle, replay  # noqa: F401
from tests.test_p2_generation import P2, PREVIOUS_P2_CONTROL_PLANES, PREVIOUS_P2_RUNTIMES, p2_replay  # noqa: F401
from tests.test_p4_generation import P4, p4_replay  # noqa: F401

# Every case here sees the real installed-Replay-revision check (tests/conftest.py stubs it for the other modules).
pytestmark = pytest.mark.real_distribution_check

ROOT = Path(__file__).resolve().parent.parent
FIX = Path(__file__).parent / "fixtures" / "cp2_generation"
# Written out here on purpose (not read back from the importer), so a typo in the importer fails these tests.
CP2 = {"manifest": "fa170815ef96a54c233d0dd9da821b60debabf8b",
       "replay": "d6c05bc552e404263a149548fc3f19ecbd8203b4",  # PROVISIONAL: Replay PR #87 head d6c05bc5, to be re-pinned to the merge SHA
       "control_plane": "484fdbd297235dd24148ddb0703f2055a31eabff",
       "moltbot_safe": "f7a55e2a8494801e49193f9f46935f0a971c248d"}
CP2_CP_PROFILE = "control-plane-strict-tenant-stack@484fdbd2"
CP2_TRANSFORMATION = "agep-manifest-reconstruction-import/0.3.10-strict-tenant-candidate"
CUR_REPLAY = "6f45e288ae37ec7e7712f9296760927d2d843bba"
REPLAY_2_BASE = "d9b7418051d2f5078a7a223a04c8d9d01bafd0c3"  # Replay main before #87 (Replay-2): knows no CP-2 label
GENERATED = "2026-10-05T19:05:00+00:00"
PAIRED = ("adapter-default", "adapter-operation-identity", "atomic-default", "atomic-operation-key")
RECOVERY = {"lost_ack": "reconciled", "race": "failed", "revoked": "denied", "tampered_evidence": "denied"}
ENV = "AGEP_CP2_REPLAY_SOURCE"
REQUIRE_ENV = "AGEP_REQUIRE_CP2_E2E"  # =1: a missing or shadowed Replay source FAILS the end-to-end tests instead of skipping them (set in CI)
CP2_CONSTANTS = dict(CONTROL_PLANE_STRICT_TENANT_REVISION=CP2["control_plane"], BOUNDED_STRICT_TENANT_PROFILE=CP2_CP_PROFILE)
# CP-2 reuses the CUR runtime and Manifest, which Replay names through its CUR constants (MOLTBOT_CUR_REVISION, MANIFEST_CUR_REVISION).
ALL_GENERATIONS = {**OTHER_GENERATIONS, "cur": CUR}


# --------------------------------------------------------------------------------------------------------- stub fixtures
@pytest.fixture
def cp2_replay_stub(cur_replay_stub):
    """Replay stub exporting the P2 and CUR constants (via cur_replay_stub) plus the strict-tenant constants."""
    cur_replay_stub(**CP2_CONSTANTS)
    return cur_replay_stub


def cp2_bundle(cp=CP2["control_plane"], executor=CP2["moltbot_safe"], manifest_revision=None):
    bundle = _bundle(cp, executor, manifest_revision if manifest_revision is not None or cp != CP2["control_plane"] else CP2["manifest"])
    if cp == CP2["control_plane"]:
        bundle["metadata"]["moltbot_safe_revision"] = executor
        bundle["metadata"]["executor_failure_reference_verification"] = GENUINE_VERIFICATION
        bundle["producer_profiles"][0]["profile_id"] = CP2_CP_PROFILE
        bundle["records"][0]["producer_profile_id"] = CP2_CP_PROFILE
    return bundle


# ------------------------------------------------------------------------------------------------------- pins and sets
def test_cp2_generation_is_added_and_every_earlier_generation_is_unchanged():
    assert imp.CP2_REVISIONS == CP2
    assert imp.CP2_REPLAY_PIN == CP2["replay"] == imp.CP2_REVISIONS["replay"]
    assert imp.CP2_TRANSFORMATION_VERSION == CP2_TRANSFORMATION
    # CUR and every earlier tuple, byte for byte (the CUR Replay pin is NOT re-tied, and CP-2 does not move it)
    assert imp.CUR_REVISIONS == CUR and imp.CUR_REPLAY_PIN == CUR_REPLAY
    assert imp.CUR_TRANSFORMATION_VERSION == CUR_TRANSFORMATION
    assert imp.P2_REVISIONS == P2 and imp.P4_REVISIONS == P4 and imp.F5B_REVISIONS == F5B and imp.SECURITY_REVISIONS == OLD
    assert imp.P2_TRANSFORMATION_VERSION == "agep-manifest-reconstruction-import/0.3.8-programme2-profiles-candidate"
    assert imp.P4_TRANSFORMATION_VERSION == "agep-manifest-reconstruction-import/0.3.7-security-runtime-p4-candidate"
    assert imp.F5B_TRANSFORMATION_VERSION == "agep-manifest-reconstruction-import/0.3.6-security-runtime-f5b-candidate"
    assert imp.SECURITY_TRANSFORMATION_VERSION == "agep-manifest-reconstruction-import/0.3.5-security-runtime-candidate"
    others = {imp.TRANSFORMATION_VERSION, imp.LEGACY_TRANSFORMATION_VERSION, imp.PERSISTENCE_TRANSFORMATION_VERSION, imp.MERGED_TRANSFORMATION_VERSION,
              imp.REFUSAL_TRANSFORMATION_VERSION, imp.RUNTIME_AUTHORITY_TRANSFORMATION_VERSION, imp.SECURITY_TRANSFORMATION_VERSION,
              imp.F5B_TRANSFORMATION_VERSION, imp.P4_TRANSFORMATION_VERSION, imp.P2_TRANSFORMATION_VERSION, imp.CUR_TRANSFORMATION_VERSION}
    assert imp.CP2_TRANSFORMATION_VERSION not in others and len(others) == 11


def test_cp2_shares_only_the_manifest_and_the_runtime_with_earlier_generations():
    """The runtime f7a55e2a is shared with CUR (and only CUR); the Replay pin and the Control Plane are unique to CP-2."""
    for name, generation in ALL_GENERATIONS.items():
        assert CP2["replay"] != generation["replay"] and CP2["control_plane"] != generation["control_plane"], name
    assert CP2["moltbot_safe"] == CUR["moltbot_safe"]
    assert all(CP2["moltbot_safe"] != g["moltbot_safe"] for g in OTHER_GENERATIONS.values())
    assert CP2["manifest"] == CUR["manifest"] == P2["manifest"] != P4["manifest"]
    # precondition of the pairing-map fix: two generations now name one runtime revision
    sharing = [cp for cp, (revisions, _) in imp.SECURITY_RUNTIME_GENERATIONS.items() if revisions["moltbot_safe"] == CP2["moltbot_safe"]]
    assert sorted(sharing) == sorted([CUR["control_plane"], CP2["control_plane"]])


def test_cp2_pins_are_in_exactly_the_sets_that_hold_the_other_generations():
    historical = {imp.V2_REVISIONS["control_plane"], imp.CONTROL_PLANE_V2_PERSISTENCE_REVISION, imp.MERGED_REVISIONS["control_plane"],
                  imp.REFUSAL_REVISIONS["control_plane"], imp.RUNTIME_AUTHORITY_REVISIONS["control_plane"], *(g["control_plane"] for g in ALL_GENERATIONS.values())}
    assert set(imp.ALL_CONTROL_PLANE_V2_REVISIONS) == historical | {CP2["control_plane"]}
    assert imp.ALL_CONTROL_PLANE_V2_REVISIONS.count(CP2["control_plane"]) == 1 and imp.ALL_CONTROL_PLANE_V2_REVISIONS[-3:] == (
        P2["control_plane"], CUR["control_plane"], CP2["control_plane"])
    assert set(imp.SECURITY_RUNTIME_GENERATIONS) == {g["control_plane"] for g in ALL_GENERATIONS.values()} | {CP2["control_plane"]}
    assert imp.SECURITY_RUNTIME_GENERATIONS[CP2["control_plane"]] == (imp.CP2_REVISIONS, imp.CP2_TRANSFORMATION_VERSION)
    assert imp.SECURITY_RUNTIME_GENERATIONS[CUR["control_plane"]] == (imp.CUR_REVISIONS, imp.CUR_TRANSFORMATION_VERSION)
    assert imp.REQUIRED_REPOS["cogno-us/cognous-agent-control-plane"] == {imp.CONTROL_PLANE_REVISION, *imp.ALL_CONTROL_PLANE_V2_REVISIONS}
    for repo, key in [("cogno-us/cognous-agent-action-manifest", "manifest"), ("cogno-us/cognous-agent-replay-bundle", "replay"),
                      ("cogno-us/cognous-agent-control-plane", "control_plane"), ("cogno-us/moltbot-safe", "moltbot_safe")]:
        assert {*(g[key] for g in ALL_GENERATIONS.values()), CP2[key]} <= imp.REQUIRED_REPOS[repo]
    assert CP2["replay"] in imp.REQUIRED_REPOS["cogno-us/cognous-agent-replay-bundle"]
    for revisions in imp.SUPPORTED_REVISION_SETS.values():
        assert not {CP2["control_plane"], CP2["moltbot_safe"], CP2["replay"]} & set(revisions)
    assert CP2["moltbot_safe"] not in imp.PRODUCER_REVISIONS.values()


def test_cp2_pins_appear_in_the_importer_only_through_the_one_tuple():
    source = Path(imp.__file__).read_text()
    assert source.count(CP2["replay"]) == 1, "the CP-2 Replay pin is written in ONE place"
    assert source.count(CP2["control_plane"]) == 1
    # literals on purpose (manifest and runtime are NOT references to CUR_REVISIONS): CUR, CP-2 and, for the manifest, P2
    assert source.count(CP2["moltbot_safe"]) == 2 and source.count(CUR["replay"]) == 1 and source.count(CUR["control_plane"]) == 1
    assert re.search(rf'^CP2_REPLAY_PIN = "{CP2["replay"]}"$', source, re.M), "the CI sed reads this exact line shape"
    assert '"moltbot_safe": "f7a55e2a8494801e49193f9f46935f0a971c248d"}\nCP2_TRANSFORMATION_VERSION' in source


def test_the_provisional_cp2_replay_pin_is_written_on_exactly_one_source_line_and_marked_provisional():
    """The re-pin to the Replay #87 merge SHA touches this one source line (plus the PR-marked comment, the CHANGELOG/README rows and this file's literal)."""
    source = Path(imp.__file__).read_text().splitlines()
    assert [n for n, line in enumerate(source, 1) if CP2["replay"] in line] == [n for n, line in enumerate(source, 1) if line.startswith("CP2_REPLAY_PIN = ")]
    comment = "\n".join(line for line in source if line.startswith("# Strict-tenant generation (CP-2)") or line.startswith("# ") and "PR #87" in line)
    assert "PR cogno-us/cognous-replay-bundle#87 head d6c05bc5, to be re-pinned" in "\n".join(source) and comment


def test_expected_replay_revision_is_the_cp2_pin_for_cp2_and_unchanged_for_the_others(cp2_replay_stub):
    assert imp._expected_replay_revision(cp2_bundle()) == CP2["replay"]
    assert imp._expected_replay_revision(cur_bundle()) == CUR_REPLAY != CP2["replay"]
    assert imp._expected_replay_revision(_bundle(P2["control_plane"], P2["moltbot_safe"], P2["manifest"])) == P2_REPLAY
    assert imp._expected_replay_revision(_bundle(P4["control_plane"], P4["moltbot_safe"], P4["manifest"])) == P4["replay"]
    # an unknown label does not silently expect the CP-2 Replay
    assert imp._expected_replay_revision(cp2_bundle(cp=CP2["control_plane"][:-1] + "0")) == imp.REPLAY_REVISION != CP2["replay"]


# --------------------------------------------------------------------------- headers, pairing (including the shared-runtime fix)
def test_cp2_selects_only_its_own_revisions_and_cur_still_validates_in_the_same_process(cp2_replay_stub):
    bundle = cp2_bundle()
    imp._validate_headers(MANIFEST, bundle)
    assert imp._is_security(bundle) and imp._is_v2(bundle) and imp._security_revisions(bundle) == CP2
    assert imp.SECURITY_RUNTIME_GENERATIONS[CP2["control_plane"]][1] == imp.CP2_TRANSFORMATION_VERSION
    cur = cur_bundle()
    imp._validate_headers(MANIFEST, cur)  # the shared-runtime pairing fix: CUR must not be overwritten by CP-2
    assert imp._security_revisions(cur) == CUR and imp.SECURITY_RUNTIME_GENERATIONS[CUR["control_plane"]][1] == imp.CUR_TRANSFORMATION_VERSION
    p2 = _other_bundle(P2, P2["moltbot_safe"])
    imp._validate_headers(MANIFEST, p2)
    assert imp._security_revisions(p2) == P2


def test_the_shared_runtime_is_paired_with_both_generations_and_the_label_disambiguates(cp2_replay_stub):
    """Executor f7a55e2a is paired with CUR and with CP-2; it is not paired with any other generation (both directions)."""
    for cp in (CUR["control_plane"], CP2["control_plane"]):
        for runtime in (CUR["moltbot_safe"], CP2["moltbot_safe"]):
            bundle = cur_bundle() if cp == CUR["control_plane"] else cp2_bundle()
            bundle["producer_profiles"][1]["revision"] = runtime
            imp._check_security_generation_pairing(bundle, bundle["producer_profiles"])
    for other in OTHER_GENERATIONS.values():
        with pytest.raises(ImportContractError, match=EXE_NOT_PAIRED):
            imp._validate_headers(MANIFEST, cp2_bundle(executor=other["moltbot_safe"]))
        with pytest.raises(ImportContractError, match=EXE_NOT_PAIRED):
            imp._validate_headers(MANIFEST, _other_bundle(other, CP2["moltbot_safe"]))
    with pytest.raises(ImportContractError, match=EXE_NOT_PAIRED):
        imp._validate_headers(MANIFEST, cp2_bundle(executor=RUNTIME_AUTHORITY_EXECUTOR))
    with pytest.raises(ImportContractError, match=EXE_NOT_PAIRED):
        imp._validate_headers(MANIFEST, cp2_bundle(cp=imp.RUNTIME_AUTHORITY_REVISIONS["control_plane"]))


def test_a_runtime_that_is_in_no_generation_is_refused_for_every_security_generation(cp2_replay_stub):
    for bundle in (cp2_bundle(executor="1" * 40), cur_bundle(executor="1" * 40)):
        with pytest.raises(ImportContractError):
            imp._validate_headers(MANIFEST, bundle)


@pytest.mark.parametrize("manifest_revision", [OLD["manifest"], F5B["manifest"], "0" * 40])
def test_cp2_with_a_manifest_of_another_generation_is_rejected(cp2_replay_stub, manifest_revision):
    with pytest.raises(ImportContractError, match=MANIFEST_NOT_PAIRED):
        imp._validate_headers(MANIFEST, cp2_bundle(manifest_revision=manifest_revision))


def test_the_unchanged_manifest_serves_cp2_cur_and_p2_alike(cp2_replay_stub):
    imp._validate_headers(MANIFEST, cp2_bundle(manifest_revision=CP2["manifest"]))
    imp._validate_headers(MANIFEST, cur_bundle(manifest_revision=CUR["manifest"]))


def test_cp2_revisions_are_not_accepted_by_older_generations(cp2_replay_stub):
    for generation in (imp.REFUSAL_REVISIONS, imp.MERGED_REVISIONS, imp.PERSISTENCE_REVISIONS, imp.V2_REVISIONS):
        assert not {CP2["control_plane"], CP2["replay"]} & set(generation.values())
    for other in ALL_GENERATIONS.values():
        assert imp._security_revisions(_bundle(other["control_plane"], other["moltbot_safe"], other["manifest"])) == other


def _near_misses(value):
    return sorted({value[:8], value.upper(), value[:-1] + "0", value[:-1] + "1", value[:8] + "0" * 32, "0" * 40, value + " ", " " + value, value[:-1], value + "0",
                   "latest", "*", ""} - {value})


@pytest.mark.parametrize("cp", _near_misses(CP2["control_plane"]))
def test_a_near_miss_cp2_control_plane_revision_is_not_the_cp2_generation(cp2_replay_stub, cp):
    bundle = cp2_bundle(cp=cp, manifest_revision=CP2["manifest"])
    assert not imp._is_security(bundle) and imp._selected_control_plane_revision(bundle) != CP2["control_plane"]
    with pytest.raises(ImportContractError):
        imp._validate_headers(MANIFEST, bundle)


@pytest.mark.parametrize("executor", _near_misses(CP2["moltbot_safe"]))
def test_a_near_miss_cp2_executor_revision_is_rejected(cp2_replay_stub, executor):
    with pytest.raises(ImportContractError):
        imp._validate_headers(MANIFEST, cp2_bundle(executor=executor))


@pytest.mark.parametrize("previous", PREVIOUS_P2_RUNTIMES)
def test_previous_p2_runtimes_do_not_pair_with_cp2(cp2_replay_stub, previous):
    with pytest.raises(ImportContractError):
        imp._validate_headers(MANIFEST, cp2_bundle(executor=previous))


@pytest.mark.parametrize("previous", PREVIOUS_P2_CONTROL_PLANES)
def test_previous_p2_control_planes_are_not_accepted_for_cp2(cp2_replay_stub, previous):
    assert previous not in imp.ALL_CONTROL_PLANE_V2_REVISIONS
    with pytest.raises(ImportContractError):
        imp._validate_headers(MANIFEST, cp2_bundle(cp=previous))


# -------------------------------------------------------------------------------------------- cross-generation profile identity
@pytest.mark.parametrize("wrong", [CUR_CP_PROFILE, "control-plane-programme2-profiles@7a4bcd40", "control-plane-security-runtime@484fdbd2",
                                   "control-plane-strict-tenant-stack@b19c47dd", "control-plane-strict-tenant-stack@00000000"])
def test_cp2_with_another_generations_profile_id_is_refused_and_the_reverse(cp2_replay_stub, wrong):
    bundle = cp2_bundle()
    bundle["producer_profiles"][0]["profile_id"] = bundle["records"][0]["producer_profile_id"] = wrong
    with pytest.raises(ImportContractError, match="Control Plane producer profile identity contradicts accepted Replay revision/profile mapping"):
        imp._validate_headers(MANIFEST, bundle)
    reverse = cur_bundle()
    reverse["producer_profiles"][0]["profile_id"] = reverse["records"][0]["producer_profile_id"] = CP2_CP_PROFILE
    with pytest.raises(ImportContractError, match="Control Plane producer profile identity contradicts accepted Replay revision/profile mapping"):
        imp._validate_headers(MANIFEST, reverse)


def test_cp2_executor_profile_identity_is_the_replay_profile_of_the_shared_runtime(cp2_replay_stub):
    bundle = cp2_bundle()
    assert bundle["producer_profiles"][1]["profile_id"] == CUR_EXECUTOR_PROFILE
    for wrong in ("moltbot-safe-executor-producer-2.0.0@c5e97e87", "moltbot-safe-executor-producer-1.0.0@f7a55e2a"):
        bundle["producer_profiles"][1]["profile_id"] = wrong
        with pytest.raises(ImportContractError, match="requires accepted Replay producer profile identity"):
            imp._validate_headers(MANIFEST, bundle)
    bundle = cp2_bundle()
    bundle["producer_profiles"][1]["format_version"] = "1.0.0"
    with pytest.raises(ImportContractError, match="requires executor producer profile 2.0.0"):
        imp._validate_headers(MANIFEST, bundle)


# --------------------------------------------------------------------------------------------- Replay constants mirrored
@pytest.mark.parametrize("override", [
    {"CONTROL_PLANE_STRICT_TENANT_REVISION": CUR["control_plane"]}, {"CONTROL_PLANE_STRICT_TENANT_REVISION": P2["control_plane"]},
    {"CONTROL_PLANE_STRICT_TENANT_REVISION": CP2["control_plane"][:-1] + "0"}, {"MOLTBOT_CUR_REVISION": P2["moltbot_safe"]},
    {"MOLTBOT_CUR_REVISION": CP2["moltbot_safe"][:-1] + "0"}, {"MANIFEST_CUR_REVISION": OLD["manifest"]}, {"MANIFEST_CUR_REVISION": P4["manifest"]},
])
def test_cp2_requires_exact_replay_mapping(cp2_replay_stub, override):
    cp2_replay_stub(**override)
    with pytest.raises(ImportContractError, match="CP-2 generation source mapping contradicts"):
        imp._validate_headers(MANIFEST, cp2_bundle())


@pytest.mark.parametrize("override", [
    {"CONTROL_PLANE_STRICT_TENANT_REVISION": None, "BOUNDED_STRICT_TENANT_PROFILE": None},
    {"CONTROL_PLANE_STRICT_TENANT_REVISION": None}, {"BOUNDED_STRICT_TENANT_PROFILE": None}, {"MOLTBOT_CUR_REVISION": None}, {"MANIFEST_CUR_REVISION": None},
], ids=["both", "control_plane", "profile", "runtime", "manifest"])
def test_cp2_with_a_replay_that_lacks_the_constants_is_refused(cp2_replay_stub, override):
    """A Replay that does not list the generation (for instance the CUR or P2 Replay) cannot vouch for a CP-2 bundle."""
    cp2_replay_stub(**override)
    with pytest.raises(ImportContractError, match="CP-2 generation Replay mapping unavailable"):
        imp._validate_headers(MANIFEST, cp2_bundle())


def test_earlier_generations_do_not_require_the_cp2_mapping(cp2_replay_stub):
    cp2_replay_stub(**{key: None for key in CP2_CONSTANTS})
    imp._validate_headers(MANIFEST, cur_bundle())
    imp._validate_headers(MANIFEST, _bundle(P4["control_plane"], P4["moltbot_safe"], P4["manifest"]))
    imp._validate_headers(MANIFEST, _bundle(F5B["control_plane"], F5B["moltbot_safe"], F5B["manifest"]))
    imp._validate_headers(MANIFEST, _other_bundle(P2, P2["moltbot_safe"]))


def test_accepted_profile_mapping_has_cp2_only_when_required(cp2_replay_stub):
    assert imp._accepted_replay_v2_profiles(require_cur=True, require_cp2=True)[CP2["control_plane"]] == CP2_CP_PROFILE
    assert CP2["control_plane"] not in imp._accepted_replay_v2_profiles(require_cur=True)
    assert CUR["control_plane"] not in imp._accepted_replay_v2_profiles(require_cp2=True)
    assert imp._accepted_replay_v2_profiles(require_cur=True, require_cp2=True)[CUR["control_plane"]] == CUR_CP_PROFILE


# --------------------------------------------------------------------------- generalised metadata checks follow the selected generation
def test_cp2_metadata_labels_are_required_and_checked_like_cur(cp2_replay_stub):
    bundle = cp2_bundle()
    imp._validate_headers(MANIFEST, bundle)
    cases = {  # label -> mutation; each alone must be refused
        "manifest absent": lambda m: m.pop("manifest_revision"),
        "manifest wrong": lambda m: m.update(manifest_revision=OLD["manifest"]),
        "runtime label wrong": lambda m: m.update(moltbot_safe_revision=P2["moltbot_safe"]),
        "runtime label absent": lambda m: m.pop("moltbot_safe_revision"),
        "governed profile label": lambda m: m.update(control_plane_profile="registry-governed-effective-configuration/0.1"),
        "governed verification label": lambda m: m.update(effective_configuration_verification="x"),
        "effective_configuration in metadata": lambda m: m.update(effective_configuration={"version": "x"}),
        "nested effective_configuration": lambda m: m.update(extra=[{"effective_configuration": 1}]),
        "forged failure reference": lambda m: m.update(executor_failure_reference_verification="independently_verified_authoritative"),
        "failure reference absent": lambda m: m.pop("executor_failure_reference_verification"),
    }
    for mutate in cases.values():
        broken = copy.deepcopy(bundle)
        mutate(broken["metadata"])
        with pytest.raises(ImportContractError):
            imp._validate_headers(MANIFEST, broken)


def test_the_metadata_check_follows_the_selected_generation_not_a_hard_coded_one(cp2_replay_stub, monkeypatch):
    """A CP-2 bundle is checked against CP-2's own labels (equal in value to CUR's today, but read from the selected generation)."""
    moved = {**CP2, "manifest": "9" * 40}
    monkeypatch.setitem(imp.SECURITY_RUNTIME_GENERATIONS, CP2["control_plane"], (moved, imp.CP2_TRANSFORMATION_VERSION))
    with pytest.raises(ImportContractError, match="Manifest revision is not paired"):
        imp._validate_headers(MANIFEST, cp2_bundle())  # the label no longer equals the (altered) generation's manifest
    imp._validate_headers(MANIFEST, cur_bundle())  # CUR is untouched by an alteration of CP-2


def test_cp2_without_an_executor_requires_no_runtime_label(cp2_replay_stub):
    bundle = cp2_bundle()
    bundle["producer_profiles"] = bundle["producer_profiles"][:1]
    bundle["metadata"]["moltbot_safe_revision"] = None
    imp._validate_headers(MANIFEST, bundle)
    bundle["metadata"]["moltbot_safe_revision"] = CP2["moltbot_safe"]
    with pytest.raises(ImportContractError, match="metadata.moltbot_safe_revision is not paired"):
        imp._validate_headers(MANIFEST, bundle)


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
def cp2_source_clone(tmp_path_factory):
    """Clean scratch clone of the Replay repository (never the original checkout), HEAD at the CP-2 pin."""
    source = os.environ.get(ENV)
    if not source:
        if _e2e_required():
            pytest.fail(f"{REQUIRE_ENV}=1 but {ENV} is not set: the CP-2 end-to-end tests cannot run")
        pytest.skip(f"{ENV} is not set: no Replay checkout to make the pinned scratch clone from")
    clone = tmp_path_factory.mktemp("replay-scratch") / "replay"
    _git("clone", "--quiet", source, str(clone))
    _git("checkout", "--quiet", imp.CP2_REPLAY_PIN, cwd=clone)
    assert _git("rev-parse", "HEAD", cwd=clone) == imp.CP2_REPLAY_PIN
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
def cp2_replay(monkeypatch, cp2_source_clone):
    module = _activate(monkeypatch, cp2_source_clone)
    assert (module.CONTROL_PLANE_STRICT_TENANT_REVISION, module.MOLTBOT_CUR_REVISION, module.MANIFEST_CUR_REVISION, module.BOUNDED_STRICT_TENANT_PROFILE) == (
        CP2["control_plane"], CP2["moltbot_safe"], CP2["manifest"], CP2_CP_PROFILE)
    assert Path(module.__file__).resolve().is_relative_to(cp2_source_clone.resolve())
    return module


def _load(*parts):
    return json.loads(FIX.joinpath(*parts).read_text())


def _paired_inputs(name):
    return [_load("paired", name, f"{n}.json") for n in ("control_plane_run", "proposal", "executor")]


def _recovery_inputs(name):
    return [_load("scenarios", name, f"{n}.json") for n in ("control_plane_run", "proposal", "runtime_export")]


def _strict_inputs(kind, which):
    """kind: cp_only (no runtime export) or runtime_denied (a genuine denied export); which: strict or legacy."""
    if kind == "cp_only":
        return _load("strict_tenant_cp_only", f"{which}_control_plane_run.json"), _load("strict_tenant_cp_only", f"{which}_proposal.json"), None
    return [_load("strict_tenant_runtime_denied", which, f"{n}.json") for n in ("control_plane_run", "proposal", "runtime_export")]


def _import(replay_module, inputs, label=CP2["control_plane"]):
    cp, proposal, executor = inputs
    return replay_module.import_bounded_workflow(cp, proposal=proposal, moltbot_export=executor, control_plane_revision=label).model_dump(mode="json")


def _pack(bundle, manifest=None):
    return imp.import_manifest_reconstruction(manifest or _load("manifest.json"), bundle, generated_at=GENERATED)


def _trace(pack):
    return pack.metadata["traceable_import"]


def _kinds(pack):
    return _trace(pack)["lifecycle_records"]


def _record(bundle, record_type):
    (found,) = [r for r in bundle["records"] if r["record_type"] == record_type]
    return found


def _collect(node, key, found=None):
    found = [] if found is None else found
    if isinstance(node, dict):
        for k, v in node.items():
            if k == key:
                found.append(v)
            _collect(v, key, found)
    elif isinstance(node, list):
        for item in node:
            _collect(item, key, found)
    return found


def test_the_fixtures_are_real_cp2_captures_with_the_cp2_revisions_and_unchanged_cur_fixtures_are_untouched():
    assert sorted(p.name for p in (FIX / "paired").iterdir()) == sorted(PAIRED)
    assert sorted(p.name for p in (FIX / "scenarios").iterdir()) == sorted(RECOVERY)
    provenance = _load("PROVENANCE.json")
    assert provenance["producer"]["control_plane"] == CP2["control_plane"] and provenance["producer"]["runtime"] == CP2["moltbot_safe"]
    import hashlib
    for relative, digest in provenance["sha256"].items():
        assert hashlib.sha256((FIX / relative).read_bytes()).hexdigest() == digest, relative
    for name in PAIRED:
        cp, proposal, executor = _paired_inputs(name)
        assert executor["repository"]["revision"] == CP2["moltbot_safe"]
        assert "7a4bcd40" not in json.dumps([cp, proposal, executor]) and "c5e97e87" not in json.dumps(executor)
        # not a relabelled CUR capture: the CUR fixtures are different files (run-specific ids, timestamps), only the tenantless proposal is identical
        cur_run = json.loads((Path(__file__).parent / "fixtures" / "current_generation" / name / "control_plane_run.json").read_text())
        assert cp != cur_run and (FIX / "paired" / name / "proposal.json").read_bytes() == (Path(__file__).parent / "fixtures" / "current_generation" / name / "proposal.json").read_bytes()
    assert (FIX / "manifest.json").read_bytes() == (Path(__file__).parent / "fixtures" / "current_generation" / "manifest.json").read_bytes()


@pytest.mark.parametrize("name", PAIRED)
def test_real_cp2_bundle_is_admitted_with_the_cp2_generation_and_keeps_its_content(cp2_replay, name):
    cp, proposal, executor = _paired_inputs(name)
    bundle = _import(cp2_replay, (cp, proposal, executor))
    assert bundle["metadata"]["control_plane_revision"] == CP2["control_plane"]  # the retained label is the declared CP-2 label
    pack = _pack(bundle)
    trace = _trace(pack)
    assert trace["transformation_version"] == CP2_TRANSFORMATION != imp.CUR_TRANSFORMATION_VERSION
    assert trace["selected_revisions"] == CP2 and {k: trace["supported_revisions"][k] for k in CP2} == CP2
    assert trace["replay_semantic_validation"] == {"validator": "agent_replay_bundle.importers.import_bounded_workflow",
                                                   "required_revision": CP2["replay"], "status": "validated_complete"}
    assert [r["adapter_profile"] for r in trace["replay_import_reports"]] == [CP2_CP_PROFILE]
    kinds = _kinds(pack)
    assert {"execution_envelope", "execution_result", "destination_effect", "runtime_decision"} <= set(kinds)
    assert kinds["runtime_decision"] == cp["decisions"] and kinds["runtime_proposal"] == [proposal]
    assert kinds["execution_result"] == [executor["execution_result"]] and executor["execution_result"]["status"] == "executed"
    assert kinds["executor_control_plane_evidence"] == [executor["control_plane_evidence"]]
    assert bundle["metadata"]["moltbot_producer_contract"]["compatible_control_plane_revisions"] == [CP2["control_plane"]]
    assert bundle["metadata"]["moltbot_producer_contract"]["profile_id"] == CUR_EXECUTOR_PROFILE
    assert trace["executor_failure_reference_verification"] == GENUINE_VERIFICATION
    for profile in bundle["producer_profiles"]:
        assert profile["revision"] in {CP2["control_plane"], CP2["moltbot_safe"]}


def test_operation_identity_records_of_the_cp2_run_reach_the_pack(cp2_replay):
    with_identity = {name: _kinds(_pack(_import(cp2_replay, _paired_inputs(name)))) for name in PAIRED}
    assert {"operation", "attempt_join"} <= set(with_identity["adapter-operation-identity"])
    for name in ("adapter-default", "atomic-default"):
        assert not {"operation", "attempt_join"} & set(with_identity[name])
    assert "operation" in with_identity["atomic-operation-key"]


# ------------------------------------------------------------------------------------- recovery, partial failure, denial
@pytest.mark.parametrize("name,status", sorted(RECOVERY.items()))
def test_real_cp2_recovery_and_denial_scenarios_are_admitted_and_retain_the_source_status(cp2_replay, name, status):
    cp, proposal, export = _recovery_inputs(name)
    result = export["execution_result"]
    bundle = _import(cp2_replay, (cp, proposal, export))
    pack = _pack(bundle)
    trace = _trace(pack)
    assert trace["replay_semantic_validation"]["status"] == "validated_complete" and trace["selected_revisions"] == CP2
    assert trace["transformation_version"] == CP2_TRANSFORMATION
    kinds = _kinds(pack)
    assert kinds["execution_result"] == [result]
    expected_status = {"lost_ack": "reconciled", "race": "failed", "revoked": "denied", "tampered_evidence": "denied"}[name]
    assert result["status"] == expected_status == status, "fixture status drift"
    assert kinds["runtime_decision"] == cp["decisions"]
    if name == "lost_ack":
        assert result["acknowledged"] is False and kinds.get("reconciliation"), "a lost acknowledgement is recovered through reconciliation, not dropped"
        assert [o for o in kinds.get("effect_observation", [])], "the observation that settled the lost acknowledgement is retained"
    if status == "denied":
        assert "destination_effect" not in kinds or not kinds["destination_effect"], "a denied run retains no destination effect"


@pytest.mark.parametrize("name", sorted(PAIRED))
def test_an_executor_less_cp2_run_is_a_validated_partial_import(cp2_replay, name):
    """Partial failure: the Control Plane run alone (the executor export is absent) reconstructs only partially, and the pack says so."""
    cp, proposal, _ = _paired_inputs(name)
    bundle = _import(cp2_replay, (cp, proposal, None))
    assert bundle["status"] == "reconstruction_partial"
    pack = _pack(bundle)
    assert _trace(pack)["replay_semantic_validation"]["status"] == "validated_partial"
    selected = _trace(pack)["selected_revisions"]
    assert {k: selected[k] for k in ("manifest", "replay", "control_plane")} == {k: CP2[k] for k in ("manifest", "replay", "control_plane")}
    assert "execution_result" not in _kinds(pack)


@pytest.mark.parametrize("name", ["lost_ack", "race", "revoked"])
def test_a_recovery_scenario_whose_executor_export_is_dropped_is_partial_not_complete(cp2_replay, name):
    cp, proposal, _ = _recovery_inputs(name)
    bundle = _import(cp2_replay, (cp, proposal, None))
    assert _trace(_pack(bundle))["replay_semantic_validation"]["status"] == "validated_partial"


def test_a_complete_cp2_bundle_with_the_executor_records_stripped_is_refused_not_silently_downgraded(cp2_replay):
    bundle = _import(cp2_replay, _paired_inputs("adapter-default"))
    bundle["records"] = [r for r in bundle["records"] if r["record_type"] not in imp.EXECUTION_TYPES]
    with pytest.raises(ImportContractError):
        _pack(bundle)


# ------------------------------------------------------------------------------------------------------ strict effect identity
def test_strict_and_legacy_tenant_effect_identities_are_retained_verbatim_and_differ(cp2_replay):
    vectors = _load("strict_tenant_cp_only", "vectors.json")
    assert vectors["strict"]["effect_id"] != vectors["legacy"]["effect_id"]
    assert vectors["strict"]["generation"] == "bounded-authorization-effect/0.3-strict-tenant" and vectors["legacy"]["generation"] == "bounded-authorization-effect/0.2"
    for which in ("strict", "legacy"):
        bundle = _import(cp2_replay, _strict_inputs("cp_only", which))
        pack = _pack(bundle)
        trace = _trace(pack)
        assert trace["replay_semantic_validation"]["status"] == "validated_partial" and trace["selected_revisions"]["control_plane"] == CP2["control_plane"]
        ids = {i for i in _collect(_kinds(pack), "effect_id") if i}
        assert ids == {vectors[which]["effect_id"]}, "effect_id is retained verbatim, never re-derived or substituted by the pack"
        decision = _kinds(pack)["runtime_decision"][0]
        assert decision["effect_id"] == vectors[which]["effect_id"] and decision["binding"]["tenant_id"] == vectors[which]["tenant_id"]
        assert decision["binding"]["generation"] == vectors[which]["generation"]


@pytest.mark.parametrize("which", ["strict", "legacy"])
def test_a_tenant_aware_run_driven_through_the_runtime_is_a_retained_denial_with_the_control_plane_effect_identity(cp2_replay, which):
    """Runtime f7a55e2a refuses a tenant-aware operation ('runtime proposal mismatch: tenant_id'): the denied export is genuine, retained, and carries the
    Control Plane's strict (or explicit legacy) effect identity. This is NOT an executed strict-tenant run."""
    vectors = _load("strict_tenant_cp_only", "vectors.json")
    cp, proposal, export = _strict_inputs("runtime_denied", which)
    assert export["execution_result"]["status"] == "denied" and export["execution_result"]["error"] == "runtime proposal mismatch: tenant_id"
    pack = _pack(_import(cp2_replay, (cp, proposal, export)))
    assert _trace(pack)["replay_semantic_validation"]["status"] == "validated_complete"
    assert _kinds(pack)["execution_result"] == [export["execution_result"]]
    assert {i for i in _collect(_kinds(pack), "effect_id") if i} == {vectors[which]["effect_id"]}


def test_a_strict_effect_identity_swapped_for_the_legacy_one_is_refused_and_the_reverse(cp2_replay):
    vectors = _load("strict_tenant_cp_only", "vectors.json")
    for which, other in (("strict", "legacy"), ("legacy", "strict")):
        bundle = _import(cp2_replay, _strict_inputs("cp_only", which))
        text = json.dumps(bundle).replace(vectors[which]["effect_id"], vectors[other]["effect_id"])
        assert text != json.dumps(bundle)
        with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed"):
            _pack(json.loads(text))


@pytest.mark.parametrize("which", ["strict", "legacy"])
def test_a_generation_edit_to_a_retained_cp2_record_is_refused(cp2_replay, which):
    """The effect-identity generation marker is part of what Replay recomputes: swapping it is refused."""
    bundle = _import(cp2_replay, _strict_inputs("cp_only", which))
    binding = _record(bundle, "runtime_decision")["data"]["binding"]
    binding["generation"] = "bounded-authorization-effect/0.2" if which == "strict" else "bounded-authorization-effect/0.3-strict-tenant"
    with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed"):
        _pack(bundle)


@pytest.mark.xfail(strict=True, reason="KNOWN GAP in Replay PR #87 head d6c05bc5 (reported in the PR, not weakened here): a decision whose binding.tenant_id is edited "
                   "(effect_id and generation unchanged) is accepted by Replay's reconstruction, so neither Replay nor the pack detects a tenant mismatch between the "
                   "decision binding and the proposal. strict=True: this test fails the day Replay closes the gap, prompting removal of the xfail.")
@pytest.mark.parametrize("which", ["strict", "legacy"])
def test_a_tenant_edit_to_a_retained_cp2_decision_binding_is_refused(cp2_replay, which):
    bundle = _import(cp2_replay, _strict_inputs("cp_only", which))
    _record(bundle, "runtime_decision")["data"]["binding"]["tenant_id"] = "tenant-beta"
    with pytest.raises(ImportContractError):
        _pack(bundle)


def test_a_strict_tenant_record_is_accepted_by_replay_under_every_security_label_so_the_label_is_the_only_generation_evidence(cp2_replay):
    """CHARACTERIZATION of the caller-asserted limit (not a guarantee): Replay recomputes effect identity from the record, not from the label."""
    for label in (CP2["control_plane"], CUR["control_plane"], P2["control_plane"]):
        assert _import(cp2_replay, _strict_inputs("cp_only", "strict"), label=label)["status"] == "reconstruction_partial"


# ----------------------------------------------------------------------------- evidence integrity: tampering is refused
@pytest.mark.parametrize("name", ["adapter-default", "atomic-operation-key"])
def test_a_real_cp2_bundle_with_a_tampered_retained_record_is_refused(cp2_replay, name):
    bundle = _import(cp2_replay, _paired_inputs(name))
    _record(bundle, "execution_result")["data"]["status"] = "failed"
    with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed"):
        _pack(bundle)


def test_a_tampered_decision_digest_and_a_dropped_record_are_refused(cp2_replay):
    bundle = _import(cp2_replay, _paired_inputs("adapter-default"))
    tampered = copy.deepcopy(bundle)
    _record(tampered, "runtime_decision")["data"]["binding"]["proposal_commitment"] = "sha256:" + "0" * 64
    with pytest.raises(ImportContractError):
        _pack(tampered)
    dropped = copy.deepcopy(bundle)
    dropped["records"] = [r for r in dropped["records"] if r["record_type"] != "runtime_proposal"]
    with pytest.raises(ImportContractError):
        _pack(dropped)


def test_the_tampered_evidence_scenario_is_retained_as_the_denial_it_was(cp2_replay):
    """The captured signature-invalid evidence is retained as a denial. (The pack does not re-derive the decision reasons: a coherent edit of the retained
    reason text is NOT detected, as for CUR; this file does not claim otherwise.)"""
    cp, proposal, export = _recovery_inputs("tampered_evidence")
    assert "evidence_signature_invalid" in json.dumps(cp) or "evidence_signature_invalid" in json.dumps(export)
    pack = _pack(_import(cp2_replay, (cp, proposal, export)))
    assert _kinds(pack)["execution_result"][0]["status"] == "denied" and not _kinds(pack).get("destination_effect")


# ------------------------------------------------------------------------- refusal of unsupported revisions (the exact Replay gate)
@pytest.fixture
def cp2_bundle_real(monkeypatch, cp2_source_clone):
    return _import(_activate(monkeypatch, cp2_source_clone), _paired_inputs("adapter-default"))


def _clone_at(clone, tmp_path, revision, name):
    target = tmp_path / name
    shutil.copytree(clone, target)
    _git("checkout", "--quiet", revision, cwd=target)  # a real Replay checkout, clean tree
    assert _git("rev-parse", "HEAD", cwd=target) == revision
    assert _git("status", "--porcelain", "--untracked-files=no", cwd=target) == ""
    return target


def test_a_cp2_bundle_is_refused_when_the_installed_replay_is_not_at_the_pin(monkeypatch, cp2_source_clone, tmp_path, cp2_bundle_real):
    bundle = cp2_bundle_real
    # (1)-(3) the CUR Replay (6f45e288), the P2 Replay (40012b8c) and Replay-2 (the Replay main before #87), each clean: none lists the CP-2 generation,
    # so none can vouch for it (and the exact gate refuses each as well, asserted directly)
    for revision, name in ((CUR_REPLAY, "cur"), (P2_REPLAY, "p2"), (REPLAY_2_BASE, "base")):
        _activate(monkeypatch, _clone_at(cp2_source_clone, tmp_path, revision, name))
        with pytest.raises(ImportContractError, match="CP-2 generation Replay mapping unavailable"):
            _pack(bundle)
        with pytest.raises(ImportContractError, match=f"is not the pinned revision {CP2['replay']}"):
            imp._require_pinned_replay_distribution(CP2["replay"])
    # (4) the pinned checkout with a modified tracked source file (dirty tree): the revision cannot be established
    dirty = tmp_path / "dirty"
    shutil.copytree(cp2_source_clone, dirty)
    target = dirty / "src" / "agent_replay_bundle" / "importers.py"
    target.write_text(target.read_text() + "\n# local modification\n")
    _activate(monkeypatch, dirty)
    with pytest.raises(ImportContractError, match="is not the pinned revision"):
        _pack(bundle)
    # (5) a Replay one commit past the pin
    other = tmp_path / "other"
    shutil.copytree(cp2_source_clone, other)
    _git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "--quiet", "--allow-empty", "-m", "past the pin", cwd=other)
    assert _git("rev-parse", "HEAD", cwd=other) != CP2["replay"]
    _activate(monkeypatch, other)
    with pytest.raises(ImportContractError, match=f"is not the pinned revision {CP2['replay']}"):
        _pack(bundle)
    # (6) control: the pinned scratch clone itself is accepted
    _activate(monkeypatch, cp2_source_clone)
    assert _trace(_pack(bundle))["replay_semantic_validation"]["required_revision"] == CP2["replay"]


SUPERSEDED_REPLAY_HEADS = {"d395e37c443fedf1bf6b9a4651338b7b7de4a553": "merge commit of Replay #81",
                           "bb5fe6f3cb3775729bc3a1434ad45dbc985636c8": "merge commit of Replay #80",
                           "a88a383ee3288b2776d50f4f9ea1dc92ec791df3": "head of the E1 PR branch",
                           REPLAY_2_BASE: "Replay main before #87 (Replay-2)"}


@pytest.mark.parametrize("head", sorted(SUPERSEDED_REPLAY_HEADS), ids=lambda h: h[:8])
def test_the_pinned_gate_refuses_the_superseded_and_historical_replay_heads(monkeypatch, cp2_source_clone, tmp_path, cp2_bundle_real, head):
    clone = _clone_at(cp2_source_clone, tmp_path, head, "superseded")
    _activate(monkeypatch, clone)
    assert imp._installed_replay_revision() == head != CP2["replay"]
    with pytest.raises(ImportContractError, match=f"installed Replay distribution revision '{head}' is not the pinned revision {CP2['replay']}"):
        imp._require_pinned_replay_distribution(CP2["replay"])
    with pytest.raises(ImportContractError, match="CP-2 generation Replay mapping unavailable"):
        _pack(cp2_bundle_real)  # also through the whole import: these Replays list no CP-2 generation
    _activate(monkeypatch, cp2_source_clone)
    imp._require_pinned_replay_distribution(CP2["replay"])


def test_earlier_generations_are_still_pinned_to_their_own_replay_and_the_cp2_replay_is_not_theirs(monkeypatch, cp2_source_clone):
    """CP-2 does not re-point any earlier generation: with the CP-2 Replay installed, a CUR or P2 bundle is refused for its own pin."""
    module = _activate(monkeypatch, cp2_source_clone)
    cur_inputs = [json.loads((Path(__file__).parent / "fixtures" / "current_generation" / "adapter-default" / f"{n}.json").read_text())
                  for n in ("control_plane_run", "proposal", "executor")]
    cur_manifest = json.loads((Path(__file__).parent / "fixtures" / "current_generation" / "manifest.json").read_text())
    cur_bundle_real = _import(module, cur_inputs, label=CUR["control_plane"])
    with pytest.raises(ImportContractError, match=f"is not the pinned revision {CUR_REPLAY}"):
        _pack(cur_bundle_real, cur_manifest)
    p2_inputs = [json.loads((Path(__file__).parent / "fixtures" / "p2_generation" / "adapter-default" / f"{n}.json").read_text())
                 for n in ("control_plane_run", "proposal", "executor")]
    p2_bundle_real = _import(module, p2_inputs, label=P2["control_plane"])
    p2_manifest = json.loads((Path(__file__).parent / "fixtures" / "p2_generation" / "manifest.json").read_text())
    with pytest.raises(ImportContractError, match=f"is not the pinned revision {P2_REPLAY}"):
        _pack(p2_bundle_real, p2_manifest)


def test_a_cur_captured_record_imported_under_the_cp2_label_is_accepted_because_labels_are_caller_asserted(cp2_replay):
    """CHARACTERIZATION of the honest limit, not a guarantee: Replay does not measure the Control Plane checkout and the tenantless CUR and CP-2
    record shapes and identities are equal, so a CUR-captured record declared as CP-2 is admitted and stamped CP-2. The CP-2 stamp therefore means
    'declared CP-2 and validated by the pinned Replay', not 'produced by Control Plane 484fdbd2'. The pack never upgrades a declared label."""
    cur_inputs = [json.loads((Path(__file__).parent / "fixtures" / "current_generation" / "adapter-default" / f"{n}.json").read_text())
                  for n in ("control_plane_run", "proposal", "executor")]
    pack = _pack(_import(cp2_replay, cur_inputs, label=CP2["control_plane"]))
    assert _trace(pack)["selected_revisions"] == CP2 and _trace(pack)["transformation_version"] == CP2_TRANSFORMATION


@pytest.mark.parametrize("control_plane_revision", [P2["control_plane"], P4["control_plane"], F5B["control_plane"], OLD["control_plane"], CUR["control_plane"]])
def test_a_real_cp2_bundle_relabelled_to_an_earlier_control_plane_is_refused(cp2_replay, control_plane_revision):
    bundle = _import(cp2_replay, _paired_inputs("adapter-default"))
    bundle["metadata"]["control_plane_revision"] = control_plane_revision
    for profile in bundle["producer_profiles"]:
        if profile.get("repository") == "cogno-us/cognous-agent-control-plane":
            profile["revision"] = control_plane_revision
    with pytest.raises(ImportContractError):
        _pack(bundle)


@pytest.mark.parametrize("executor_revision", [P2["moltbot_safe"], P4["moltbot_safe"], F5B["moltbot_safe"], "1" * 40])
def test_a_real_cp2_bundle_with_an_earlier_executor_revision_is_refused(cp2_replay, executor_revision):
    bundle = _import(cp2_replay, _paired_inputs("adapter-default"))
    for profile in bundle["producer_profiles"]:
        if profile.get("repository") == "cogno-us/moltbot-safe":
            profile["revision"] = executor_revision
            profile["profile_id"] = f"moltbot-safe-executor-producer-2.0.0@{executor_revision[:8]}"
    with pytest.raises(ImportContractError):
        _pack(bundle)


@pytest.mark.parametrize("label", _near_misses(CP2["control_plane"]) + ["1" * 40])
def test_a_real_cp2_bundle_with_a_near_miss_or_arbitrary_control_plane_hash_is_refused(cp2_replay, label):
    bundle = _import(cp2_replay, _paired_inputs("adapter-default"))
    bundle["metadata"]["control_plane_revision"] = label
    for profile in bundle["producer_profiles"]:
        if profile.get("repository") == "cogno-us/cognous-agent-control-plane":
            profile["revision"] = label
    with pytest.raises(ImportContractError):
        _pack(bundle)


def test_replay_itself_refuses_an_unknown_control_plane_label(cp2_replay):
    for label in _near_misses(CP2["control_plane"]) + ["1" * 40]:
        with pytest.raises(cp2_replay.ImportContractError):
            _import(cp2_replay, _paired_inputs("adapter-default"), label=label)


@pytest.mark.parametrize("mode", ["absent", "none", "near_miss"])
def test_a_real_cp2_bundle_with_a_missing_or_wrong_manifest_label_is_refused(cp2_replay, mode):
    bundle = _import(cp2_replay, _paired_inputs("atomic-default"))
    if mode == "absent":
        del bundle["metadata"]["manifest_revision"]
    else:
        bundle["metadata"]["manifest_revision"] = {"none": None, "near_miss": CP2["manifest"][:-1] + "0"}[mode]
    with pytest.raises(ImportContractError, match="manifest_revision|Manifest revision is not paired"):
        _pack(bundle)


@pytest.mark.parametrize("value", [P2["moltbot_safe"], CP2["moltbot_safe"][:8], CP2["moltbot_safe"].upper(), None, ""])
def test_a_real_cp2_bundle_with_another_executor_label_is_refused(cp2_replay, value):
    bundle = _import(cp2_replay, _paired_inputs("atomic-default"))
    bundle["metadata"]["moltbot_safe_revision"] = value
    with pytest.raises(ImportContractError, match="metadata.moltbot_safe_revision is not paired"):
        _pack(bundle)


@pytest.mark.parametrize("value", ["independently_verified_authoritative", GENUINE_VERIFICATION.upper(), GENUINE_VERIFICATION + " ", None, "", True])
def test_a_real_cp2_bundle_with_a_forged_failure_reference_label_is_refused(cp2_replay, value):
    bundle = _import(cp2_replay, _paired_inputs("atomic-default"))
    bundle["metadata"]["executor_failure_reference_verification"] = value
    with pytest.raises(ImportContractError, match="metadata.executor_failure_reference_verification must be present and equal"):
        _pack(bundle)


# ----------------------------------------------------------------------------- explicitly unsupported scope stays refused under CP-2
EFFECTIVE_CONFIGURATION = {"version": "effective-configuration-binding/0.1", "digest": "sha256:" + "1" * 64,
                           "members": {"scope": {"consumer_id": "consumer-test", "tenant_id": "tenant-alpha"}}}
POLICY_BINDING = {"approval_commitment_version": "approval-commitment/0.2", "policy_generation": 1, "policy_activation_ref": "sha256:" + "c" * 64}
GOVERNED_SELECTOR = "registry-governed-effective-configuration/0.1"


def _authority(bundle):
    return _record(bundle, "runtime_decision")["data"]["binding"]["runtime_authority"]


@pytest.mark.parametrize("members", [{"effective_configuration": EFFECTIVE_CONFIGURATION}, POLICY_BINDING, {"policy_generation": 1}],
                         ids=["effective_configuration", "policy_binding_all", "policy_generation"])
@pytest.mark.parametrize("name", ["adapter-default", "atomic-operation-key"])
def test_pack_refuses_a_cp2_run_carrying_effective_configuration_or_policy_binding_members(cp2_replay, name, members):
    bundle = _import(cp2_replay, _paired_inputs(name))
    _authority(bundle).update(copy.deepcopy(members))
    with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed: .*runtime authority fields unsupported"):
        _pack(bundle)


def test_pack_refuses_reason_vocabulary_0_3_under_cp2(cp2_replay):
    bundle = _import(cp2_replay, _paired_inputs("adapter-default"))
    _record(bundle, "runtime_decision")["data"]["reason_vocabulary_version"] = "runtime-authority-reasons/0.3"
    with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed: .*decision vocabulary missing"):
        _pack(bundle)


@pytest.mark.parametrize("member", ["selection_refusal", "authorization_pin"])
def test_pack_refuses_selection_refusal_and_authorization_pin_evidence_under_cp2(cp2_replay, member):
    bundle = _import(cp2_replay, _paired_inputs("adapter-default"))
    _record(bundle, "executor_control_plane_evidence")["data"][member] = {"version": "0.1"}
    _record(bundle, "execution_result")["data"].setdefault("control_plane_evidence", {})[member] = {"version": "0.1"}
    with pytest.raises(ImportContractError, match="pinned Replay semantic validation failed: .*unsupported typed refusal executor evidence field"):
        _pack(bundle)


def test_the_registry_governed_selector_is_refused_by_replay_for_the_cp2_label_and_the_pack_names_no_governed_profile(cp2_replay):
    cp, proposal, _ = _strict_inputs("cp_only", "strict")
    with pytest.raises(cp2_replay.ImportContractError, match="unsupported Control Plane profile selector"):
        cp2_replay.import_bounded_workflow(cp, proposal=proposal, moltbot_export=None, control_plane_revision=CP2["control_plane"], control_plane_profile=GOVERNED_SELECTOR)
    source = Path(imp.__file__).read_text()
    assert GOVERNED_SELECTOR not in source and "registry-governed" not in source.replace("Registry-governed", "")


@pytest.mark.parametrize("label", ["control_plane_profile", "effective_configuration_verification"])
def test_a_governed_metadata_label_on_a_real_cp2_bundle_is_refused(cp2_replay, label):
    bundle = _import(cp2_replay, _paired_inputs("atomic-default"))
    bundle["metadata"][label] = GOVERNED_SELECTOR
    with pytest.raises(ImportContractError, match=f"metadata.{label} is a governed-profile label and is unsupported under the current generation"):
        _pack(bundle)


# ------------------------------------------------------------------------------------------------ the CI switch cannot be silently skipped
def _inner_e2e(tmp_path, *, require, source, shadow):
    """Run one end-to-end case in a child pytest with a controlled environment; returns (returncode, output)."""
    env = {k: v for k, v in os.environ.items() if k not in (ENV, REQUIRE_ENV, "PYTHONPATH")}
    paths = [str(ROOT), str(ROOT / "src")]
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
    node = "tests/test_cp2_generation.py::test_real_cp2_bundle_is_admitted_with_the_cp2_generation_and_keeps_its_content[adapter-default]"
    done = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", node, "-rs"], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=600)
    return done.returncode, done.stdout + done.stderr


def test_a_missing_replay_source_skips_by_default_but_fails_when_the_ci_switch_is_set(tmp_path):
    code, out = _inner_e2e(tmp_path, require=False, source=None, shadow=False)
    assert code == 0 and "1 skipped" in out, out
    code, out = _inner_e2e(tmp_path, require=True, source=None, shadow=False)
    assert code != 0 and "cannot run" in out and "skipped" not in out, out


def test_an_installed_replay_distribution_skips_by_default_but_fails_when_the_ci_switch_is_set(tmp_path, cp2_source_clone):
    code, out = _inner_e2e(tmp_path, require=False, source=str(cp2_source_clone), shadow=True)
    assert code == 0 and "1 skipped" in out, out
    code, out = _inner_e2e(tmp_path, require=True, source=str(cp2_source_clone), shadow=True)
    assert code != 0 and "shadows the scratch clone" in out and "skipped" not in out, out


def test_the_ci_job_reads_the_pin_from_the_importer_runs_this_file_and_forbids_skipping():
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text()
    if "  current-generation-e2e:\n" not in workflow:
        # The cross-component harness runs this suite beside its own workflow files; only this repository's own tests.yml (which still carries the CUR job) is checked.
        pytest.skip("the workflow file beside this checkout is not this repository's own tests.yml")
    job = workflow.split("  cp2-generation-e2e:\n", 1)[1].split("\n  cross-component:", 1)[0]
    assert "CP2_REPLAY_PIN" in job and CP2["replay"] not in job, "the pin is read from the importer, never written in the workflow"
    assert "tests/test_cp2_generation.py" in job and "AGEP_REQUIRE_CP2_E2E: '1'" in job and "AGEP_CP2_REPLAY_SOURCE" in job
    assert "timeout-minutes" in job
    # the CUR job still reads the CUR pin and still runs the CUR file (unchanged)
    cur_job = workflow.split("  current-generation-e2e:\n", 1)[1].split("\n  cp2-generation-e2e:", 1)[0]
    assert "CUR_REPLAY_PIN" in cur_job and "tests/test_current_generation.py" in cur_job and "CP2_REPLAY_PIN" not in cur_job
