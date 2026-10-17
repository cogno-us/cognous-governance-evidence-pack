"""Pinned-Replay re-validation of route-B bundles (finding F-25 / ODES P0 note N-2).

Replay retains a destination recovery report as record type ``executor_recovery_report`` and export-level
extensions as ``executor_export_extensions``. The pack rebuilds the executor export from the retained records and
re-runs Replay's importer, so those records must map back to the export layout their ``source_path`` names.

These tests use the real ``agent_replay_bundle`` (Replay main 8702b8a7 or later, which retains these record types)
and the three route-B fixtures copied from Replay's ``tests/fixtures/route_b_post_commit``. They are skipped when the
importable Replay does not retain recovery reports (for example the older pinned revision), so the default CI job
without a Replay install is unaffected.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import agent_governance_evidence_pack.importer as imp

replay = pytest.importorskip("agent_replay_bundle.importers")

BASE = Path(__file__).parent / "fixtures" / "route_b_post_commit"
VARIANTS = ("observe_bound_fail", "lost_ack_recon_down", "reconcile_only")

if not hasattr(replay, "CONTROL_PLANE_F5B_REVISION"):
    pytest.skip("installed Replay predates the F5b generation", allow_module_level=True)


def load(variant):
    d = BASE / variant
    return tuple(json.loads((d / name).read_text()) for name in ("control_plane_run.json", "proposal.json", "executor.json"))


def bundle_of(cp, proposal, executor):
    reconstructed = replay.import_bounded_workflow(
        cp, proposal=proposal, moltbot_export=executor,
        control_plane_revision=replay.CONTROL_PLANE_F5B_REVISION)
    return reconstructed.model_dump(mode="json")


@pytest.fixture(scope="module")
def retains_recovery_reports():
    bundle = bundle_of(*load("observe_bound_fail"))
    if "executor_recovery_report" not in {r["record_type"] for r in bundle["records"]}:
        pytest.skip("installed Replay does not retain executor_recovery_report records")


@pytest.mark.parametrize("variant", VARIANTS)
def test_route_b_bundle_revalidates(variant, retains_recovery_reports):
    bundle = bundle_of(*load(variant))
    assert imp._run_pinned_replay_validator(bundle) == "validated_complete"


@pytest.mark.parametrize("variant", VARIANTS)
def test_rebuilt_export_equals_original_executor_export(variant, retains_recovery_reports):
    cp, proposal, executor = load(variant)
    bundle = bundle_of(cp, proposal, executor)
    _, _, rebuilt = imp._retained_replay_inputs(bundle)
    for member in ("execution_result", "observations", "attempts", "attempt_events", "effects",
                   "rejected_observations", "control_plane_evidence"):
        assert rebuilt[member] == executor[member], member
    assert "recovery_observations" not in rebuilt  # legacy layout: mirrored in observations
    assert "extensions" not in rebuilt


def _new_layout(executor, *, mirror):
    executor = copy.deepcopy(executor)
    report = executor["execution_result"]["observation"]
    executor["observations"] = []
    if mirror:
        executor["recovery_observations"] = [copy.deepcopy(report)]
    return executor


@pytest.mark.parametrize("variant", VARIANTS)
def test_new_layout_recovery_observations_round_trip(variant, retains_recovery_reports):
    cp, proposal, executor = load(variant)
    executor = _new_layout(executor, mirror=True)
    bundle = bundle_of(cp, proposal, executor)
    assert [r["source_path"] for r in bundle["records"] if r["record_type"] == "executor_recovery_report"] == [
        "moltbot.recovery_observations[0]"]
    _, _, rebuilt = imp._retained_replay_inputs(bundle)
    assert rebuilt["recovery_observations"] == executor["recovery_observations"]
    assert rebuilt["observations"] == []
    assert imp._run_pinned_replay_validator(bundle) == "validated_complete"


@pytest.mark.parametrize("variant", VARIANTS)
def test_new_layout_result_only_report_round_trips(variant, retains_recovery_reports):
    cp, proposal, executor = load(variant)
    executor = _new_layout(executor, mirror=False)
    bundle = bundle_of(cp, proposal, executor)
    assert [r["source_path"] for r in bundle["records"] if r["record_type"] == "executor_recovery_report"] == [
        "moltbot.execution_result.observation"]
    _, _, rebuilt = imp._retained_replay_inputs(bundle)
    assert "recovery_observations" not in rebuilt
    assert rebuilt["observations"] == []
    assert imp._run_pinned_replay_validator(bundle) == "validated_complete"


@pytest.mark.parametrize("variant", VARIANTS)
def test_export_extensions_round_trip(variant, retains_recovery_reports):
    cp, proposal, executor = load(variant)
    executor = copy.deepcopy(executor)
    executor["extensions"] = {"x-trace": {"id": 1}}
    bundle = bundle_of(cp, proposal, executor)
    assert "executor_export_extensions" in {r["record_type"] for r in bundle["records"]}
    _, _, rebuilt = imp._retained_replay_inputs(bundle)
    assert rebuilt["extensions"] == executor["extensions"]
    assert imp._run_pinned_replay_validator(bundle) == "validated_complete"


def test_tampered_recovery_report_is_rejected(retains_recovery_reports):
    bundle = bundle_of(*load("observe_bound_fail"))
    for record in bundle["records"]:
        if record["record_type"] == "executor_recovery_report":
            record["data"]["status"] = "absent"
    with pytest.raises(imp.ImportContractError):
        imp._run_pinned_replay_validator(bundle)


def test_dropped_recovery_report_record_is_rejected(retains_recovery_reports):
    bundle = bundle_of(*load("observe_bound_fail"))
    bundle["records"] = [r for r in bundle["records"] if r["record_type"] != "executor_recovery_report"]
    with pytest.raises(imp.ImportContractError):
        imp._run_pinned_replay_validator(bundle)


def test_unsupported_recovery_report_source_path_is_rejected(retains_recovery_reports):
    bundle = bundle_of(*load("observe_bound_fail"))
    for record in bundle["records"]:
        if record["record_type"] == "executor_recovery_report":
            record["source_path"] = "moltbot.elsewhere[0]"
    with pytest.raises(imp.ImportContractError, match="unsupported source_path"):
        imp._retained_replay_inputs(bundle)
