"""Programme-2 producer generation: Control Plane 7a4bcd40, runtime ec728da6, Replay ab421ad0, Manifest fa170815.

Added beside P4, exactly paired, never mixed with an earlier generation. The stub cases replace only the Replay constant module
(as test_p4_generation), so they run without Replay installed. The end-to-end cases run real Replay output (inputs under
tests/fixtures/p2_generation, real Control Plane and runtime captures) through the pack and are skipped unless the installed Replay
lists exactly this generation. Alpha scaffolding: the pins go with the other hard pins at end-of-alpha (P5).

What this proves: the generation is accepted only as one exact tuple, the executor pairing is exact both ways, and a real Replay
bundle of this generation (adapter route, atomic route, with and without operation identity, and the N4 record types) is
admitted and keeps its records. What it does not prove: that any producer's decision re-derives (the verifier's work).
"""
import copy
import json
from pathlib import Path

import pytest

from agent_governance_evidence_pack import importer as imp
from agent_governance_evidence_pack.importer import ImportContractError
from tests.test_f5b_generation import F5B, MANIFEST, OLD, RUNTIME_AUTHORITY_EXECUTOR, _bundle, _replay_constants, replay  # noqa: F401
from tests.test_p4_generation import P4, p4_replay  # noqa: F401

FIX = Path(__file__).parent / "fixtures" / "p2_generation"
P2 = {"manifest": "fa170815ef96a54c233d0dd9da821b60debabf8b",
      "replay": "ab421ad0fdc6a24999273adf82455968953598ae",
      "control_plane": "7a4bcd40b3b49e61ff3c294dcca53b52f460b22c",
      "moltbot_safe": "ec728da6dc301a664b331ac8986afd6e850a1273"}
P2_CP_PROFILE = "control-plane-programme2-profiles@7a4bcd40"
# P5/P6/r9: the executor pairing moved from fc034d14 to 7170da59 to 11de097c to 62a5cc15 to c4a05883 to 6b16962d to 79f39166 to cab4d9ab to ec728da6; the earlier pairings are replaced, not kept.
PREVIOUS_P2_RUNTIMES = ("fc034d140ce55d9887ac3a0aab598f3a2c05ea47", "7170da59e04854a3dbe13f151400d0ac368b8dcb", "11de097c450d3ad4d89f9add41b00e38e7cc2c7c", "62a5cc156ecb439b4103b757fd265f276bb30374", "c4a05883266b815f39d97cbf2240406647985147", "6b16962db140590b808f02b5c2cb11a217aec46f", "79f391662afd8b7f1034d201932231b49dd02ab9", "cab4d9abc651c7efbafb429798d2c908f048bf5c")
PREVIOUS_P2_CONTROL_PLANES = ("128eaa5e36fdff772fdc709581712dbeac046db3", "3755c71a20eab1a41135967b682342c809929572", "3cd17ead6b24301290ad1e50ae4b22bbd93c12fb", "6093aca7b945698e89c0d8ac7c75306375e1a298", "2bac7875391cad0a431fa0d75208b7ade39743e3", "5c474ba83a1477df93dec92d076f8e62b0a98ae1", "e77fe0ee8714617899592528e660a80fbb2e864a", "0a41faa972699f7ec3063967a14cd9bdd3e67d27")
PREVIOUS_P2_REPLAYS = ("541180fde891a3048b8a61e77518f3311917e00b", "46e8bd7c263f5075cac3a7a9defcb265384f40e9", "c8e665bd1936e4da90f6a324b486a320934c4bff", "2a7963b18d96eb2e9e4fdb1a09c7588cf5c0ef00", "6a6a477495ac24e813f12bb0fe314acfe8bac9cf", "d268b1ea864cfb9400fab334f1f72987cb1409bb", "53c0cd60d565ea1797ed0be87a2310c5b68b24f6", "028f63d1c001f99580583888fa4b4e46d77a267b")


@pytest.fixture
def p2_replay(monkeypatch, p4_replay):
    """Replay stub exporting the earlier constants plus the programme-2 constants."""
    import sys
    module = sys.modules["agent_replay_bundle.importers"]
    module.CONTROL_PLANE_P2_REVISION = P2["control_plane"]
    module.MOLTBOT_P2_REVISION = P2["moltbot_safe"]
    module.MANIFEST_P2_REVISION = P2["manifest"]
    module.BOUNDED_P2_PROFILE = P2_CP_PROFILE

    def override(**values):
        for key, value in values.items():
            if value is None:
                monkeypatch.delattr(module, key, raising=False)
            else:
                setattr(module, key, value)
    return override


def p2_bundle(cp=P2["control_plane"], executor=P2["moltbot_safe"], manifest_revision=None):
    bundle = _bundle(cp, executor, manifest_revision if manifest_revision is not None or cp != P2["control_plane"] else P2["manifest"])
    if cp == P2["control_plane"]:
        bundle["producer_profiles"][0]["profile_id"] = P2_CP_PROFILE
        bundle["records"][0]["producer_profile_id"] = P2_CP_PROFILE
    return bundle


def test_p2_generation_is_added_and_earlier_generations_are_unchanged():
    assert imp.P2_REVISIONS == P2
    assert imp.P4_REVISIONS == P4 and imp.F5B_REVISIONS == F5B and imp.SECURITY_REVISIONS == OLD
    assert imp.P2_TRANSFORMATION_VERSION not in {imp.P4_TRANSFORMATION_VERSION, imp.F5B_TRANSFORMATION_VERSION, imp.SECURITY_TRANSFORMATION_VERSION}
    for key in ("replay", "control_plane", "moltbot_safe"):
        assert P2[key] != P4[key]
    assert P2["manifest"] != P4["manifest"]  # the action manifest moved with the scan-4 fix stream (fa170815, was 8b016916); P4 and F5b keep 2c36bcd0
    assert "128eaa5e36fdff772fdc709581712dbeac046db3" not in imp.ALL_CONTROL_PLANE_V2_REVISIONS, "the earlier tie is not kept"
    assert {OLD["control_plane"], F5B["control_plane"], P4["control_plane"], P2["control_plane"]} <= set(imp.ALL_CONTROL_PLANE_V2_REVISIONS)
    for repo, key in [("cogno-us/cognous-agent-action-manifest", "manifest"), ("cogno-us/cognous-agent-replay-bundle", "replay"),
                      ("cogno-us/cognous-agent-control-plane", "control_plane"), ("cogno-us/moltbot-safe", "moltbot_safe")]:
        assert {F5B[key], P4[key], P2[key]} <= imp.REQUIRED_REPOS[repo]


def test_p2_selects_only_its_own_revisions(p2_replay):
    bundle = p2_bundle(manifest_revision=P2["manifest"])
    imp._validate_headers(MANIFEST, bundle)
    assert imp._is_security(bundle) and imp._security_revisions(bundle) == P2
    assert imp.SECURITY_RUNTIME_GENERATIONS[P2["control_plane"]][1] == imp.P2_TRANSFORMATION_VERSION


@pytest.mark.parametrize("cp,executor", [
    (P2["control_plane"], P4["moltbot_safe"]), (P4["control_plane"], P2["moltbot_safe"]),
    (P2["control_plane"], F5B["moltbot_safe"]), (F5B["control_plane"], P2["moltbot_safe"]),
    (P2["control_plane"], OLD["moltbot_safe"]), (OLD["control_plane"], P2["moltbot_safe"]),
    (P2["control_plane"], RUNTIME_AUTHORITY_EXECUTOR),
], ids=["p2cp+p4ex", "p4cp+p2ex", "p2cp+f5bex", "f5bcp+p2ex", "p2cp+secex", "seccp+p2ex", "p2cp+raex"])
def test_p2_cross_generation_pairs_rejected(p2_replay, cp, executor):
    with pytest.raises(ImportContractError, match="not paired"):
        imp._validate_headers(MANIFEST, p2_bundle(cp, executor))


@pytest.mark.parametrize("previous", PREVIOUS_P2_RUNTIMES)
def test_p2_previous_runtime_pairing_is_replaced_not_kept(p2_replay, previous):
    """P5/P6: neither fc034d14 nor 7170da59 is a pinned runtime revision any more."""
    assert previous not in imp.P2_REVISIONS.values()
    assert all(previous not in revisions for revisions in imp.REQUIRED_REPOS.values())
    with pytest.raises(ImportContractError):
        imp._validate_headers(MANIFEST, p2_bundle(executor=previous))


def test_p2_previous_control_plane_and_replay_ties_are_replaced_not_kept(p2_replay):
    """P6: the ties to Control Plane 3755c71a and Replay 541180fd are gone from the pinned sets (earlier ones too)."""
    pinned = {rev for revisions in imp.REQUIRED_REPOS.values() for rev in revisions} | set(imp.ALL_CONTROL_PLANE_V2_REVISIONS) | set(imp.SECURITY_RUNTIME_GENERATIONS)
    for previous in (*PREVIOUS_P2_CONTROL_PLANES, *PREVIOUS_P2_REPLAYS):
        assert previous not in pinned and previous not in imp.P2_REVISIONS.values()
    with pytest.raises(ImportContractError):
        imp._validate_headers(MANIFEST, p2_bundle(cp=PREVIOUS_P2_CONTROL_PLANES[1]))


def test_p2_manifest_of_another_generation_is_rejected(p2_replay):
    with pytest.raises(ImportContractError, match="not paired"):
        imp._validate_headers(MANIFEST, p2_bundle(manifest_revision=OLD["manifest"]))


@pytest.mark.parametrize("override,message", [
    ({"MOLTBOT_P2_REVISION": P4["moltbot_safe"]}, "programme-2 source mapping contradicts"),
    ({"CONTROL_PLANE_P2_REVISION": P4["control_plane"]}, "programme-2 source mapping contradicts"),
    ({"MANIFEST_P2_REVISION": OLD["manifest"]}, "programme-2 source mapping contradicts"),
    ({"CONTROL_PLANE_P2_REVISION": None, "MOLTBOT_P2_REVISION": None, "MANIFEST_P2_REVISION": None, "BOUNDED_P2_PROFILE": None},
     "programme-2 Replay mapping unavailable"),
    ({"MOLTBOT_P2_REVISION": None}, "programme-2 Replay mapping unavailable"),
])
def test_p2_requires_exact_replay_mapping(p2_replay, override, message):
    p2_replay(**override)
    with pytest.raises(ImportContractError, match=message):
        imp._validate_headers(MANIFEST, p2_bundle())


def test_p2_profile_identity_must_match_the_replay_profile(p2_replay):
    bundle = p2_bundle()
    bundle["producer_profiles"][0]["profile_id"] = bundle["records"][0]["producer_profile_id"] = "control-plane-security-runtime@7a4bcd40"
    with pytest.raises(ImportContractError, match="contradicts accepted Replay revision/profile mapping"):
        imp._validate_headers(MANIFEST, bundle)


def test_earlier_generations_do_not_require_the_p2_mapping(p2_replay):
    # Retained P4 and F5b evidence must still import under a Replay without the programme-2 constants.
    p2_replay(CONTROL_PLANE_P2_REVISION=None, MOLTBOT_P2_REVISION=None, MANIFEST_P2_REVISION=None, BOUNDED_P2_PROFILE=None)
    imp._validate_headers(MANIFEST, _bundle(P4["control_plane"], P4["moltbot_safe"], P4["manifest"]))
    imp._validate_headers(MANIFEST, _bundle(F5B["control_plane"], F5B["moltbot_safe"], F5B["manifest"]))


def test_executor_profile_identity_is_the_replay_profile_of_the_pinned_runtime(p2_replay):
    bundle = p2_bundle()
    assert bundle["producer_profiles"][1]["profile_id"] == "moltbot-safe-executor-producer-2.0.0@ec728da6"
    bundle["producer_profiles"][1]["profile_id"] = "moltbot-safe-executor-producer-2.0.0@3024ef6e"
    with pytest.raises(ImportContractError, match="requires accepted Replay producer profile identity"):
        imp._validate_headers(MANIFEST, bundle)


# ------------------------------------------------------------------------------------------- end to end with real Replay
def _real_replay():
    replay_module = pytest.importorskip("agent_replay_bundle.importers")
    for name in ("CONTROL_PLANE_P2_REVISION", "MOLTBOT_P2_REVISION", "BOUNDED_P2_PROFILE", "MANIFEST_P2_REVISION"):
        if not hasattr(replay_module, name):
            pytest.skip("installed Replay does not list the programme-2 generation")
    if (replay_module.CONTROL_PLANE_P2_REVISION, replay_module.MOLTBOT_P2_REVISION) != (P2["control_plane"], P2["moltbot_safe"]):
        pytest.skip("installed Replay lists another programme-2 generation")
    return replay_module


GENERATED = "2026-10-05T19:05:00+00:00"
SCENARIOS = ("adapter-default", "adapter-operation-identity", "atomic-default", "atomic-operation-key")


def _paired(replay_module, name):
    d = FIX / name
    inputs = [json.loads((d / f"{n}.json").read_text()) for n in ("control_plane_run", "proposal", "executor")]
    bundle = replay_module.import_bounded_workflow(inputs[0], proposal=inputs[1], moltbot_export=inputs[2],
                                                   control_plane_revision=P2["control_plane"]).model_dump(mode="json")
    return bundle


def _pack(bundle, manifest=None):
    manifest = manifest or json.loads((FIX / "manifest.json").read_text())
    return imp.import_manifest_reconstruction(manifest, bundle, generated_at=GENERATED)


def _kinds(pack):
    return set(pack.metadata["traceable_import"]["lifecycle_records"])


@pytest.mark.parametrize("name", SCENARIOS)
def test_real_executor_paired_bundle_is_admitted_with_the_pinned_generation(name):
    replay_module = _real_replay()
    pack = _pack(_paired(replay_module, name))
    trace = pack.metadata["traceable_import"]
    assert trace["selected_revisions"] == {"manifest": P2["manifest"], "replay": P2["replay"], "control_plane": P2["control_plane"],
                                           "moltbot_safe": P2["moltbot_safe"]}
    assert trace["replay_semantic_validation"]["required_revision"] == P2["replay"]
    assert {"execution_envelope", "execution_result", "destination_effect", "runtime_decision"} <= _kinds(pack)
    assert "freshness_summary" not in trace


def test_operation_identity_records_of_the_paired_run_reach_the_pack_and_the_default_has_none():
    replay_module = _real_replay()
    assert {"operation", "attempt_join"} <= _kinds(_pack(_paired(replay_module, "adapter-operation-identity")))
    assert not {"operation", "attempt_join"} & _kinds(_pack(_paired(replay_module, "adapter-default")))


@pytest.mark.parametrize("name,kinds", [("cp-merge-after-both-applied-obligation", {"merge_record", "compensation_obligation"}),
                                        ("cp-dedupe-unknown-attempt-escalated", {"dedupe_escalation"}),
                                        ("cp-reversibility-cached-snapshot-accepted", {"snapshot_use"}),
                                        ("cp-terminal-revocation-recorded-refused", {"runtime_decision", "effect_time_refusal"})])
def test_n4_record_types_reach_the_pack(name, kinds):
    replay_module = _real_replay()
    run = json.loads((FIX / f"{name}.json").read_text())["run"]
    bundle = replay_module.import_bounded_workflow(run, control_plane_revision=P2["control_plane"]).model_dump(mode="json")
    manifest = {"manifest_version": "1.1", "manifest_id": "m", "actions": [{"action_id": "a", "review_requirement": "none", "reliance_requirement": "none"}], "tools": []}
    assert kinds <= _kinds(_pack(bundle, manifest))


def test_a_default_run_of_the_generation_adds_nothing_to_the_pack():
    replay_module = _real_replay()
    run = json.loads((FIX / "cp-default-path.json").read_text())["run"]
    bundle = replay_module.import_bounded_workflow(run, control_plane_revision=P2["control_plane"]).model_dump(mode="json")
    manifest = {"manifest_version": "1.1", "manifest_id": "m", "actions": [{"action_id": "a", "review_requirement": "none", "reliance_requirement": "none"}], "tools": []}
    kinds = _kinds(_pack(bundle, manifest))
    assert not kinds & {"operation", "merge_record", "snapshot_use", "dedupe_escalation", "rule_revision", "recovery_run"}


@pytest.mark.parametrize("revision", [P4["moltbot_safe"], F5B["moltbot_safe"], *PREVIOUS_P2_RUNTIMES])
def test_a_real_p2_bundle_with_an_earlier_executor_revision_is_refused(revision):
    replay_module = _real_replay()
    bundle = copy.deepcopy(_paired(replay_module, "adapter-default"))
    for profile in bundle["producer_profiles"]:
        if profile.get("repository") == "cogno-us/moltbot-safe":
            profile["revision"] = revision
            profile["profile_id"] = f"moltbot-safe-executor-producer-2.0.0@{revision[:8]}"
    with pytest.raises(ImportContractError):
        _pack(bundle)
