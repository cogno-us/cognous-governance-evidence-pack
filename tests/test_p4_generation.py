"""P4 producer generation: added beside F5b, exactly paired, never mixed with an earlier generation.

P4 (Control Plane 26a7e659, runtime 3024ef6e, Manifest 2c36bcd0) is the producer set after the execution-attempt
lifecycle contract work. These cases stub only the Replay constant module, so they run without Replay installed;
the real route-B round trip is exercised in cognous-stack-qualification (SCN-C06 route-B export, import, re-validation).
Alpha scaffolding: the pins go with the other hard pins at end-of-alpha (P5).
"""
import pytest

from agent_governance_evidence_pack import importer as imp
from agent_governance_evidence_pack.importer import ImportContractError
from tests.test_f5b_generation import F5B, MANIFEST, OLD, RUNTIME_AUTHORITY_EXECUTOR, _bundle, _replay_constants, replay  # noqa: F401

P4 = {"manifest": "2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e",
      "replay": "9aab3f6c34d2721ef1be3f6468b71dc3bad99a2a",
      "control_plane": "26a7e6594eb535827ccc248cbca36a7d119d613b",
      "moltbot_safe": "3024ef6e6ecf7da22e5f4fdf90d873f93b2a55c9"}


@pytest.fixture
def p4_replay(monkeypatch, replay):
    """Replay stub exporting the F5b constants (as test_f5b_generation) plus the P4 constants."""
    import sys
    module = sys.modules["agent_replay_bundle.importers"]
    module.CONTROL_PLANE_P4_REVISION = P4["control_plane"]
    module.MOLTBOT_P4_REVISION = P4["moltbot_safe"]
    module.MANIFEST_P4_REVISION = P4["manifest"]
    module.BOUNDED_P4_PROFILE = "control-plane-security-runtime@26a7e659"

    def override(**values):
        for key, value in values.items():
            if value is None:
                monkeypatch.delattr(module, key, raising=False)
            else:
                setattr(module, key, value)
    return override


def test_p4_generation_is_added_and_earlier_generations_are_unchanged():
    assert imp.P4_REVISIONS == P4
    assert imp.F5B_REVISIONS == F5B
    assert imp.SECURITY_REVISIONS == OLD
    assert imp.P4_TRANSFORMATION_VERSION not in {imp.F5B_TRANSFORMATION_VERSION, imp.SECURITY_TRANSFORMATION_VERSION}
    for key in ("replay", "control_plane", "moltbot_safe"):
        assert P4[key] != F5B[key]
    assert {OLD["control_plane"], F5B["control_plane"], P4["control_plane"]} <= set(imp.ALL_CONTROL_PLANE_V2_REVISIONS)
    for repo, key in [("cogno-us/cognous-agent-action-manifest", "manifest"), ("cogno-us/cognous-agent-replay-bundle", "replay"),
                      ("cogno-us/cognous-agent-control-plane", "control_plane"), ("cogno-us/moltbot-safe", "moltbot_safe")]:
        assert {F5B[key], P4[key]} <= imp.REQUIRED_REPOS[repo]


def test_p4_selects_only_its_own_revisions(p4_replay):
    bundle = _bundle(P4["control_plane"], P4["moltbot_safe"], P4["manifest"])
    imp._validate_headers(MANIFEST, bundle)
    assert imp._is_security(bundle) and imp._security_revisions(bundle) == P4
    assert imp.SECURITY_RUNTIME_GENERATIONS[P4["control_plane"]][1] == imp.P4_TRANSFORMATION_VERSION


@pytest.mark.parametrize("cp,executor,manifest_revision", [
    (P4["control_plane"], F5B["moltbot_safe"], None),
    (F5B["control_plane"], P4["moltbot_safe"], None),
    (P4["control_plane"], OLD["moltbot_safe"], None),
    (OLD["control_plane"], P4["moltbot_safe"], None),
    (P4["control_plane"], RUNTIME_AUTHORITY_EXECUTOR, None),
    (P4["control_plane"], P4["moltbot_safe"], OLD["manifest"]),
], ids=["p4cp+f5bex", "f5bcp+p4ex", "p4cp+secex", "seccp+p4ex", "p4cp+raex", "p4+manifest-e385f8c1"])
def test_p4_cross_generation_pairs_rejected(p4_replay, cp, executor, manifest_revision):
    with pytest.raises(ImportContractError, match="not paired"):
        imp._validate_headers(MANIFEST, _bundle(cp, executor, manifest_revision))


@pytest.mark.parametrize("override,message", [
    ({"MOLTBOT_P4_REVISION": F5B["moltbot_safe"]}, "P4 security-runtime source mapping contradicts"),
    ({"MANIFEST_P4_REVISION": OLD["manifest"]}, "P4 security-runtime source mapping contradicts"),
    ({"CONTROL_PLANE_P4_REVISION": None, "MOLTBOT_P4_REVISION": None, "MANIFEST_P4_REVISION": None,
      "BOUNDED_P4_PROFILE": None}, "P4 security-runtime Replay mapping unavailable"),
])
def test_p4_requires_exact_replay_mapping(p4_replay, override, message):
    p4_replay(**override)
    with pytest.raises(ImportContractError, match=message):
        imp._validate_headers(MANIFEST, _bundle(P4["control_plane"], P4["moltbot_safe"], P4["manifest"]))


def test_f5b_generation_does_not_require_p4_mapping(p4_replay):
    # Retained F5b evidence must still import under a Replay without the P4 constants.
    p4_replay(CONTROL_PLANE_P4_REVISION=None, MOLTBOT_P4_REVISION=None, MANIFEST_P4_REVISION=None, BOUNDED_P4_PROFILE=None)
    imp._validate_headers(MANIFEST, _bundle(F5B["control_plane"], F5B["moltbot_safe"], F5B["manifest"]))
