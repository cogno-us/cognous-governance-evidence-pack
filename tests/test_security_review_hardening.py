"""Hardening from the 2026-10 security review (neutral): full retained-source comparison, installed-Replay check,
selector rule, builtin normalisation, escaping, rendered examples and lineage validation.

The revalidation cases use REAL Replay output for the programme-2 generation (skipped unless the installed Replay lists it),
the rest run without Replay.
"""
import copy
import json
from collections import OrderedDict, UserDict
from pathlib import Path

import pytest

from agent_governance_evidence_pack import importer as imp
from agent_governance_evidence_pack.admission import admit_value
from agent_governance_evidence_pack.models import EvidencePack
from agent_governance_evidence_pack.renderer import render_markdown
from agent_governance_evidence_pack.validator import REVIEW_OVERLAY_FIELDS, validate_evidence_pack
from agent_governance_evidence_pack.w3_atomic_evidence import W3EvidenceContractError, transform_atomic_failure_reconstruction
from agent_governance_evidence_pack.w3_c8_lineage import C8EvidenceError, project_c8_lineage

from .test_p2_generation import _pack, _paired, _real_replay
from .test_w3_atomic_evidence import sample as w3_sample
from .test_w3_c8_lineage import source as c8_source

EXAMPLES = Path(__file__).parent.parent / "examples"


# ---------------------------------------------------------------- full comparison against the retained sources
@pytest.fixture(scope="module")
def traced():
    return _pack(_paired(_real_replay(), "adapter-default")).model_dump(mode="json")


def _errors(dump):
    report = validate_evidence_pack(EvidencePack.model_validate(dump))
    return {i.code for i in report.issues if i.severity.value == "error"}


def test_unedited_imported_pack_is_valid(traced):
    assert _errors(copy.deepcopy(traced)) == set()


@pytest.mark.parametrize("name,edit", [
    ("agent_name", lambda d: d["agent_overview"].__setitem__("agent_name", "Another agent")),
    ("business_purpose", lambda d: d["agent_overview"].__setitem__("business_purpose", "Another purpose")),
    ("pack_version", lambda d: d.__setitem__("pack_version", "9.9")),
    ("deployment_name", lambda d: d["deployment_context"].__setitem__("deployment_name", "elsewhere")),
    ("tool_inventory", lambda d: d["tool_inventory"][0].__setitem__("tool_name", "renamed_tool")),
    ("tool_inventory_added", lambda d: d["tool_inventory"].append(copy.deepcopy(d["tool_inventory"][0]) | {"tool_name": "extra"})),
    ("generated_at", lambda d: d.__setitem__("generated_at", "2030-01-01T00:00:00+00:00")),
    ("title", lambda d: d.__setitem__("title", "A different title")),
    ("environment", lambda d: d["deployment_context"].__setitem__("environment", "production")),
    ("systems_touched", lambda d: d["deployment_context"]["systems_touched"].append("another-system")),
])
def test_editing_an_imported_member_is_refused(traced, name, edit):
    dump = copy.deepcopy(traced)
    edit(dump)
    assert "E_TRACE_SEMANTICS" in _errors(dump)


def test_review_overlay_fields_stay_editable(traced):
    dump = copy.deepcopy(traced)
    dump["review_status"] = "in_review"
    dump["metadata"]["reviewer_note"] = "free extension space"
    assert "E_TRACE_SEMANTICS" not in _errors(dump)
    assert REVIEW_OVERLAY_FIELDS == {"review_status", "review_records", "risk_register", "blocked_actions", "reliance_summary", "redaction_exports"}



# ---------------------------------------------------------------- installed Replay distribution
@pytest.mark.real_distribution_check
def test_refuses_when_installed_replay_is_not_the_pinned_revision(monkeypatch):
    monkeypatch.setattr(imp, "_installed_replay_revision", lambda: "0" * 40)
    with pytest.raises(imp.ImportContractError, match="not the pinned revision"):
        imp._require_pinned_replay_distribution("1" * 40)


@pytest.mark.real_distribution_check
def test_refuses_when_installed_replay_has_no_revision_record(monkeypatch):
    monkeypatch.setattr(imp, "_installed_replay_revision", lambda: None)
    with pytest.raises(imp.ImportContractError, match="not the pinned revision"):
        imp._require_pinned_replay_distribution("1" * 40)


@pytest.mark.real_distribution_check
def test_accepts_when_installed_replay_is_the_pinned_revision(monkeypatch):
    monkeypatch.setattr(imp, "_installed_replay_revision", lambda: "1" * 40)
    imp._require_pinned_replay_distribution("1" * 40)


@pytest.mark.real_distribution_check
def test_import_refuses_without_the_pinned_distribution(monkeypatch):
    replay = _real_replay()
    bundle = _paired(replay, "adapter-default")
    monkeypatch.setattr(imp, "_installed_replay_revision", lambda: "f" * 40)
    with pytest.raises(imp.ImportContractError, match="not the pinned revision"):
        _pack(bundle)


@pytest.mark.real_distribution_check
def test_import_succeeds_with_the_pinned_distribution(monkeypatch):
    replay = _real_replay()
    bundle = _paired(replay, "adapter-default")
    monkeypatch.setattr(imp, "_installed_replay_revision", lambda: imp.P2_REVISIONS["replay"])
    assert _pack(bundle).metadata["traceable_import"]["replay_semantic_validation"]["required_revision"] == imp.P2_REVISIONS["replay"]


def test_expected_replay_revision_follows_the_selected_generation():
    for generation in (imp.P2_REVISIONS, imp.P4_REVISIONS, imp.F5B_REVISIONS):
        bundle = {"metadata": {"control_plane_revision": generation["control_plane"]}}
        assert imp._expected_replay_revision(bundle) == generation["replay"]
    assert imp._expected_replay_revision({}) == imp.REPLAY_REVISION


def test_replay_extra_is_pinned_to_the_full_revision():
    text = (Path(__file__).parent.parent / "pyproject.toml").read_text()
    assert f"cognous-replay-bundle@{imp.P2_REVISIONS['replay']}" in text


# ---------------------------------------------------------------- selector rule
@pytest.mark.parametrize("revision", imp.ALL_CONTROL_PLANE_V2_REVISIONS)
def test_v2_producer_profile_without_selector_is_refused(revision):
    bundle = {"metadata": {}, "producer_profiles": [{"revision": revision}]}
    with pytest.raises(imp.ImportContractError, match="control_plane_revision is missing"):
        imp._selected_control_plane_revision(bundle)


def test_bundle_without_selector_and_without_v2_profile_keeps_the_legacy_default():
    assert imp._selected_control_plane_revision({"metadata": {}, "producer_profiles": [{"revision": "other"}]}) == imp.CONTROL_PLANE_REVISION
    assert imp._selected_control_plane_revision({}) == imp.CONTROL_PLANE_REVISION


# ---------------------------------------------------------------- builtin normalisation
class LyingDict(dict):
    def items(self):
        return iter(())

    def __len__(self):
        return 0


class LyingList(list):
    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0


class LyingStr(str):
    def encode(self, *a, **k):
        return b""

    def __len__(self):
        return 0


def test_subclass_containers_are_budgeted_and_returned_as_builtins():
    value = {"a": LyingDict(x=[LyingList([1, 2])], y=LyingStr("text"))}
    out = admit_value(value)
    assert type(out) is dict and type(out["a"]) is dict and type(out["a"]["x"]) is list and type(out["a"]["y"]) is str
    assert out == {"a": {"x": [[1, 2]], "y": "text"}}


def test_list_subclass_cannot_dodge_the_cardinality_budget():
    with pytest.raises(ValueError, match="budget"):
        admit_value({"x": LyingList([0] * 10001)})


def test_dict_subclass_cannot_dodge_the_field_budget():
    with pytest.raises(ValueError, match="budget"):
        admit_value({"x": OrderedDict((str(i), 0) for i in range(5000))})


def test_subclass_string_cannot_dodge_the_surrogate_check():
    class Quiet(str):
        def encode(self, *a, **k):
            return b""
    with pytest.raises(ValueError, match="surrogate"):
        admit_value({"x": Quiet("\ud800")})


def test_subclass_nan_is_refused():
    class Num(float):
        def __ne__(self, other):
            return False
    with pytest.raises(ValueError, match="nonfinite"):
        admit_value({"x": Num("nan")})


# ---------------------------------------------------------------- renderer escaping
def test_backslash_is_escaped_before_pipe():
    from agent_governance_evidence_pack.loader import load_evidence_pack
    pack = load_evidence_pack(EXAMPLES / "customer_service_agent_evidence_pack.json")
    pack.agent_overview.owner = "a\\|b\\"
    text = render_markdown(pack)
    assert "a&#92;\\|b&#92;" in text
    assert "a\\|b\\ " not in text


# ---------------------------------------------------------------- rendered examples are current
@pytest.mark.parametrize("path", sorted(EXAMPLES.glob("*_evidence_pack.json")), ids=lambda p: p.stem)
def test_rendered_examples_are_regenerated_from_the_renderer(path):
    from agent_governance_evidence_pack.loader import load_evidence_pack
    rendered = (EXAMPLES / "rendered" / f"{path.stem}.md").read_text(encoding="utf-8")
    assert rendered == render_markdown(load_evidence_pack(path)), "run: agep render <example> --out examples/rendered/<name>.md"
    assert "asserted, unverified" in rendered


# ---------------------------------------------------------------- W3 / C8 lineage
def _w3_with_link(**override):
    s = w3_sample()
    profile = s["records"][0]["producer_profile_id"]
    s["records"][0]["identifiers"] = {"failure_id": "f-1", "effect_id": "e-1", "decision_id": "d-1", "attempt_id": "a-1"}
    s["records"].append({"record_id": "attempt-1", "record_type": "atomic_attempt", "producer_profile_id": profile,
                         "identifiers": {"effect_id": "e-1", "decision_id": "d-1", "attempt_id": "a-1"}, "data": {}})
    s["links"] = [{"from_record_id": "failure-1", "to_record_id": "attempt-1"}]
    s.update(override)
    return s


def test_w3_matching_identity_link_is_accepted():
    assert transform_atomic_failure_reconstruction(_w3_with_link())["retained_links"]


@pytest.mark.parametrize("key,value", [("effect_id", "e-2"), ("decision_id", "d-2"), ("attempt_id", "a-2"), ("attempt_id", None)])
def test_w3_link_between_different_identities_is_refused(key, value):
    s = _w3_with_link()
    s["records"][1]["identifiers"][key] = value
    with pytest.raises(W3EvidenceContractError):
        transform_atomic_failure_reconstruction(s)


@pytest.mark.parametrize("bad", [["failure-1"], {"x": 1}, 7, None])
def test_w3_link_ids_must_be_strings(bad):
    s = _w3_with_link()
    s["links"][0]["from_record_id"] = bad
    with pytest.raises(W3EvidenceContractError):
        transform_atomic_failure_reconstruction(s)


def test_w3_complete_status_needs_a_complete_report():
    s = _w3_with_link(status="reconstruction_complete")
    with pytest.raises(W3EvidenceContractError, match="completeness"):
        transform_atomic_failure_reconstruction(s)
    s["import_reports"] = [{"complete": True, "findings": []}]
    assert transform_atomic_failure_reconstruction(s)["report_supports_complete"] is True


@pytest.mark.parametrize("bad", [["one"], {"k": 1}, 5, None])
def test_c8_record_ids_must_be_strings(bad):
    s = c8_source()
    s["records"][0]["record_id"] = bad
    with pytest.raises(C8EvidenceError):
        project_c8_lineage(s)


def test_c8_record_type_must_be_allowed():
    s = c8_source()
    s["records"][0]["record_type"] = "anything_else"
    with pytest.raises(C8EvidenceError, match="record type"):
        project_c8_lineage(s)


def test_c8_identifiers_must_match_their_data():
    s = c8_source()
    s["records"][0].update(data={"claim_id": "c-1"}, identifiers={"claim_id": "c-2"})
    with pytest.raises(C8EvidenceError, match="identifier"):
        project_c8_lineage(s)
    s["records"][0]["identifiers"] = {"claim_id": "c-1"}
    assert project_c8_lineage(s)["source_records"]


def test_c8_complete_status_needs_a_complete_report():
    s = c8_source()
    s["status"] = "reconstruction_complete"
    with pytest.raises(C8EvidenceError, match="completeness"):
        project_c8_lineage(s)


# ---------------------------------------------------------------- local-checkout installs
def _fake_distribution(monkeypatch, direct_url):
    import importlib.metadata as metadata

    class Dist:
        def read_text(self, name):
            return json.dumps(direct_url) if name == "direct_url.json" else None

    monkeypatch.setattr(metadata, "distribution", lambda name: Dist())


def _checkout(tmp_path):
    import subprocess
    root = tmp_path / "replay"
    root.mkdir()
    run = lambda *a: subprocess.run(["git", "-C", str(root), *a], check=True, capture_output=True, text=True).stdout.strip()  # noqa: E731
    run("init", "-q")
    run("config", "user.email", "t@example.invalid")
    run("config", "user.name", "t")
    (root / "m.py").write_text("x = 1\n")
    run("add", "m.py")
    run("commit", "-q", "-m", "c")
    return root, run("rev-parse", "HEAD")


@pytest.mark.real_distribution_check
def test_clean_local_checkout_install_reports_its_head(monkeypatch, tmp_path):
    root, head = _checkout(tmp_path)
    _fake_distribution(monkeypatch, {"url": root.as_uri(), "dir_info": {"editable": True}})
    assert imp._installed_replay_revision() == head


@pytest.mark.real_distribution_check
def test_modified_local_checkout_install_is_not_trusted(monkeypatch, tmp_path):
    root, _ = _checkout(tmp_path)
    (root / "m.py").write_text("x = 2\n")
    _fake_distribution(monkeypatch, {"url": root.as_uri(), "dir_info": {"editable": True}})
    assert imp._installed_replay_revision() is None


@pytest.mark.real_distribution_check
def test_vcs_install_reports_its_recorded_commit(monkeypatch):
    _fake_distribution(monkeypatch, {"url": "https://example.invalid/r", "vcs_info": {"vcs": "git", "commit_id": "a" * 40}})
    assert imp._installed_replay_revision() == "a" * 40


@pytest.mark.real_distribution_check
def test_install_without_provenance_is_not_trusted(monkeypatch):
    _fake_distribution(monkeypatch, {"url": "https://example.invalid/wheel.whl", "archive_info": {}})
    assert imp._installed_replay_revision() is None
