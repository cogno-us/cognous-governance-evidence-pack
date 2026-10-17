"""F5b security-runtime generation: additive, exactly paired, never mixed with the earlier generation.

Native producer output at the F5b pins is exercised centrally in
cognous-stack-qualification/suites/security-runtime. These component-local
cases stub only the Replay constant module, so they run without Replay installed.
"""
import sys
import types

import pytest

from agent_governance_evidence_pack import importer as imp
from agent_governance_evidence_pack.importer import ImportContractError

OLD = {"manifest": "e385f8c19b4444817a8b84b72ed6edbc37deb807",
       "replay": "3601fb218d5c02f5d86e55d2cf33983e5e130ac3",
       "control_plane": "996baeb476c8745b1a58ddc968b9eecc6a39b76b",
       "moltbot_safe": "fd6b76fa0e85feb5b67324114bf790d3a12fdaf1"}
F5B = {"manifest": "2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e",
       "replay": "def0ee0f3af713283ea3cd13f0caf79e1607b651",
       "control_plane": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
       "moltbot_safe": "4a83b175d2ef0e65a7ee22a0513bb94a5fdf3a6f"}
RUNTIME_AUTHORITY_EXECUTOR = "a9a4f75a9a880ba0ae2c3b5a01fcee0ae904e127"


def _replay_constants(**overrides):
    """Constants Replay def0ee0f exports, as the Evidence Pack mapping check reads them."""
    values = dict(
        BOUNDED_V2_PROFILE="control-plane-bounded-v2", CONTROL_PLANE_V2_REVISION=imp.V2_REVISIONS["control_plane"],
        BOUNDED_V2_PERSISTENCE_PROFILE="control-plane-bounded-v2-persistence",
        CONTROL_PLANE_V2_PERSISTENCE_REVISION=imp.CONTROL_PLANE_V2_PERSISTENCE_REVISION,
        CONTROL_PLANE_V2_REVISIONS=imp.CONTROL_PLANE_V2_REVISIONS,
        CONTROL_PLANE_SECURITY_REVISION=OLD["control_plane"], MOLTBOT_SECURITY_REVISION=OLD["moltbot_safe"],
        MANIFEST_SECURITY_REVISION=OLD["manifest"], BOUNDED_SECURITY_PROFILE="control-plane-security-runtime@996baeb4",
        CONTROL_PLANE_F5B_REVISION=F5B["control_plane"], MOLTBOT_F5B_REVISION=F5B["moltbot_safe"],
        MANIFEST_F5B_REVISION=F5B["manifest"], BOUNDED_F5B_PROFILE="control-plane-security-runtime@a34c3dc2",
        CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION=imp.RUNTIME_AUTHORITY_REVISIONS["control_plane"],
        MOLTBOT_RUNTIME_AUTHORITY_REVISION=RUNTIME_AUTHORITY_EXECUTOR,
        # Stub label chosen so the synthetic bundle below reaches the pairing check.
        BOUNDED_RUNTIME_AUTHORITY_PROFILE="control-plane-security-runtime@2a17b2ba",
    )
    values.update(overrides)
    return {k: v for k, v in values.items() if v is not None}


@pytest.fixture
def replay(monkeypatch):
    def install(**overrides):
        package = types.ModuleType("agent_replay_bundle")
        module = types.ModuleType("agent_replay_bundle.importers")
        module.__dict__.update(_replay_constants(**overrides))
        package.importers = module
        monkeypatch.setitem(sys.modules, "agent_replay_bundle", package)
        monkeypatch.setitem(sys.modules, "agent_replay_bundle.importers", module)
    install()
    return install


def _bundle(cp, executor, manifest_revision=None):
    cp_profile = f"control-plane-security-runtime@{cp[:8]}"
    executor_profile = f"moltbot-safe-executor-producer-2.0.0@{executor[:8]}"
    return {
        "bundle_version": "0.2.0",
        "metadata": {"control_plane_revision": cp, "manifest_revision": manifest_revision},
        "producer_profiles": [
            {"profile_id": cp_profile, "repository": "cogno-us/cognous-agent-control-plane", "revision": cp,
             "format_name": "BoundedRunRecord"},
            {"profile_id": executor_profile, "repository": "cogno-us/moltbot-safe", "revision": executor,
             "format_version": "2.0.0"},
        ],
        "records": [{"record_id": "r1", "record_type": "runtime_decision", "producer_profile_id": cp_profile, "data": {}}],
    }


MANIFEST = {"manifest_version": "1.1", "manifest_id": "m", "actions": [{"action_id": "a", "review_requirement": "none", "reliance_requirement": "none"}]}


def test_f5b_generation_is_added_and_security_generation_is_unchanged():
    assert imp.SECURITY_REVISIONS == OLD
    assert imp.F5B_REVISIONS == F5B
    assert imp.SECURITY_TRANSFORMATION_VERSION == "agep-manifest-reconstruction-import/0.3.5-security-runtime-candidate"
    assert imp.F5B_TRANSFORMATION_VERSION != imp.SECURITY_TRANSFORMATION_VERSION
    assert {OLD["control_plane"], F5B["control_plane"]} <= set(imp.ALL_CONTROL_PLANE_V2_REVISIONS)
    for repo, key in [("cogno-us/cognous-agent-action-manifest", "manifest"), ("cogno-us/cognous-agent-replay-bundle", "replay"),
                      ("cogno-us/cognous-agent-control-plane", "control_plane"), ("cogno-us/moltbot-safe", "moltbot_safe")]:
        assert {OLD[key], F5B[key]} <= imp.REQUIRED_REPOS[repo]


@pytest.mark.parametrize("generation", [OLD, F5B], ids=["security-996baeb4", "f5b-a34c3dc2"])
def test_each_generation_selects_only_its_own_revisions(replay, generation):
    bundle = _bundle(generation["control_plane"], generation["moltbot_safe"], generation["manifest"])
    imp._validate_headers(MANIFEST, bundle)
    assert imp._is_security(bundle) and imp._is_runtime_authority(bundle) and imp._is_refusal_v2(bundle)
    assert imp._security_revisions(bundle) == generation
    expected = imp.F5B_TRANSFORMATION_VERSION if generation is F5B else imp.SECURITY_TRANSFORMATION_VERSION
    assert imp.SECURITY_RUNTIME_GENERATIONS[generation["control_plane"]][1] == expected


@pytest.mark.parametrize("cp,executor,manifest_revision", [
    (OLD["control_plane"], F5B["moltbot_safe"], None),
    (F5B["control_plane"], OLD["moltbot_safe"], None),
    (F5B["control_plane"], RUNTIME_AUTHORITY_EXECUTOR, None),
    (imp.RUNTIME_AUTHORITY_REVISIONS["control_plane"], F5B["moltbot_safe"], None),
    (F5B["control_plane"], F5B["moltbot_safe"], OLD["manifest"]),
    (OLD["control_plane"], OLD["moltbot_safe"], F5B["manifest"]),
], ids=["cp996baeb4+ex4a83b175", "cpa34c3dc2+exfd6b76fa", "cpa34c3dc2+exa9a4f75a", "cp2a17b2ba+ex4a83b175",
        "f5b+manifest-e385f8c1", "security+manifest-2c36bcd0"])
def test_cross_generation_pairs_rejected(replay, cp, executor, manifest_revision):
    with pytest.raises(ImportContractError, match="not paired"):
        imp._validate_headers(MANIFEST, _bundle(cp, executor, manifest_revision))


@pytest.mark.parametrize("override,message", [
    ({"MOLTBOT_F5B_REVISION": OLD["moltbot_safe"]}, "F5b security-runtime source mapping contradicts"),
    ({"MANIFEST_F5B_REVISION": OLD["manifest"]}, "F5b security-runtime source mapping contradicts"),
    ({"CONTROL_PLANE_F5B_REVISION": None, "MOLTBOT_F5B_REVISION": None, "MANIFEST_F5B_REVISION": None,
      "BOUNDED_F5B_PROFILE": None}, "F5b security-runtime Replay mapping unavailable"),
])
def test_f5b_requires_exact_replay_mapping(replay, override, message):
    replay(**override)
    with pytest.raises(ImportContractError, match=message):
        imp._validate_headers(MANIFEST, _bundle(F5B["control_plane"], F5B["moltbot_safe"], F5B["manifest"]))


def test_security_generation_does_not_require_f5b_mapping(replay):
    # Retained 996baeb4 evidence must still import under a Replay without the F5b constants.
    replay(CONTROL_PLANE_F5B_REVISION=None, MOLTBOT_F5B_REVISION=None, MANIFEST_F5B_REVISION=None, BOUNDED_F5B_PROFILE=None)
    imp._validate_headers(MANIFEST, _bundle(OLD["control_plane"], OLD["moltbot_safe"], OLD["manifest"]))
