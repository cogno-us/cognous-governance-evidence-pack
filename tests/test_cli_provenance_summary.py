"""`agep summarize` source attribution (S2 Pack presentation remediation; DEVELOPMENT ONLY, SYNTHETIC, UNQUALIFIED).

Presentation only: the existing summary lines stay byte-identical and the pack JSON is untouched; additive lines say which retained record family (Control Plane or executor) each
statement rests on. Unit tests need no Replay. End-to-end tests build real packs under the opt-in candidate (Replay 7eb7d76e in AGEP_CP2B_REPLAY_SOURCE, as tests/test_cp2b_replay_candidate.py),
run the real `agep summarize` / `validate` code path in a subprocess and assert the semantic content of the rendered output (not a whole-output snapshot).
"""
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from agent_governance_evidence_pack import cli
from tests.test_cp2_generation import _import, _load
from tests.test_cp2b_replay_candidate import ID, _executed_inputs, _pack, new_clone, new_replay, old_clone, _source  # noqa: F401

pytestmark = pytest.mark.real_distribution_check
FIX = Path(__file__).parent / "fixtures" / "pack_presentation"
SRC = Path(__file__).resolve().parent.parent / "src"
# "independently verified" is allowed ONLY in the negated header phrase "none independently verified"; the frozen oracle forbids it as an affirmative claim.
FORBIDDEN = re.compile(r"verified execution|independently observed|(?<!none )independently verified|zero executions|no execution occurred|0 executions", re.I)


def test_fixture_hashes_are_pinned():
    pinned = json.loads((FIX / "PROVENANCE.json").read_text())["sha256"]
    for name, digest in pinned.items():
        assert hashlib.sha256((FIX / name).read_bytes()).hexdigest() == digest, name


# ----------------------------------------------------------------------------------------------------------------- unit (no Replay)
def _trace(*, executor, cp=1, ack="received", ack_counts=None, results=(), observed="applied", attempted="yes"):
    kinds = {"control_plane_attempt_transition": [{}], "effect_observation": [{}], "reconciliation": [{}]}
    if executor:
        kinds.update({"destination_attempt": [{}], "destination_effect": [{}], "execution_result": list(results)})
    return {"derived_counts": {"control_plane_attempt_count": cp, "executor_attempt_count": 1 if executor else 0, "destination_effect_count": 1 if executor else 0,
                               "execution_result_state_counts": {"applied": 1} if executor else {}, "effect_observation_count": 2, "reconciliation_count": 2,
                               "acknowledgement_counts": ack_counts or {"control_plane_received": 1}},
            "lifecycle_summary": {"execution_attempted": attempted, "destination_observed": observed, "acknowledgement": ack, "independent_verification": "unavailable",
                                  "destination_observation_scope": "latest supplied Control Plane reconciliation per exact effect; not a fresh query"},
            "lifecycle_records": kinds}


def _text(trace):
    return "\n".join(cli.provenance_lines(trace))


def test_unit_missing_executor_export_is_stated_as_absence_not_zero_executions():
    text = _text(_trace(executor=False))
    assert "executor_evidence      : NOT supplied" in text and "no executor records were supplied" in text and "not a measured zero-execution outcome" in text
    assert "execution_attempted_source : yes (source: Control Plane attempts (1); no executor attempt records)" in text
    assert "destination_observed_source : applied (Control Plane reconciliation;" in text and "not a fresh query" in text and "executor destination_effect_count 0" in text
    assert "independent_verification : unavailable" in text and not FORBIDDEN.search(text)


def test_unit_supplied_executor_evidence_is_named_and_lost_acknowledgment_is_distinguishable():
    positive = _text(_trace(executor=True, results=[{"status": "executed", "acknowledged": True, "newly_executed": True}], ack_counts={"execution_result_received": 1}))
    lost = _text(_trace(executor=True, ack="unknown", ack_counts={"execution_result_unknown": 1}, results=[{"status": "reconciled", "acknowledged": False, "newly_executed": False}]))
    assert "executor_evidence      : supplied" in positive and "executor_result        : status=executed acknowledged=True newly_executed=True" in positive
    assert "executor_result        : status=reconciled acknowledged=False newly_executed=False" in lost and "acknowledgement        : unknown" in lost
    assert positive != lost and "acknowledgement        : received" in positive
    assert "executor attempts (1)" in positive and not FORBIDDEN.search(positive + lost)


def test_unit_missing_or_foreign_fields_degrade_to_na_and_never_raise():
    for trace in ({}, {"derived_counts": {}}, {"lifecycle_summary": {}}, {"lifecycle_records": {"execution_result": ["not-a-dict"]}}):
        lines = cli.provenance_lines(copy.deepcopy(trace))
        assert lines[0].startswith("provenance (retained records; source-asserted, none independently verified)") and any("n/a" in line or "NOT supplied" in line for line in lines)


def test_unit_summarize_path_does_not_change_the_pack(tmp_path):
    t = _trace(executor=False)
    before = json.dumps(t, sort_keys=True)
    cli.provenance_lines(t)
    assert json.dumps(t, sort_keys=True) == before


# ----------------------------------------------------------------------------------------------------------------- end to end (real CLI)
def _lost_inputs():
    return tuple(json.loads((FIX / "lost_ack" / n).read_text()) for n in ("control_plane_run.json", "proposal.json", "runtime_export.json"))


def _run(clone, pack, tmp_path, command):
    from agent_governance_evidence_pack.loader import dump_evidence_pack
    path = tmp_path / f"{command}.pack.json"
    dump_evidence_pack(pack, path)
    code = "import sys; sys.argv = ['agep', %r, %r]; from agent_governance_evidence_pack.cli import main; main()" % (command, str(path))
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(SRC), str(clone / "src")]), "PYTHONDONTWRITEBYTECODE": "1", "ODES_ALLOW_UNVERIFIED_REPLAY": "0"}
    done = subprocess.run([sys.executable, "-B", "-c", code], env=env, capture_output=True, text=True, timeout=300, cwd=str(tmp_path))
    return done.returncode, done.stdout, done.stderr


def _packs(new_replay):
    valid = _executed_inputs()
    p = _pack(_import(new_replay, valid), replay_generation=ID)
    lost = _pack(_import(new_replay, _lost_inputs()), replay_generation=ID)
    n8 = _pack(_import(new_replay, (valid[0], valid[1], None)), replay_generation=ID)
    return p, lost, n8


def _existing_lines(pack):
    t = pack.metadata["traceable_import"]
    c, ls = t["derived_counts"], t["lifecycle_summary"]
    return [f"distinct_effect_count  : {c['distinct_effect_count']}", f"cp_attempt_count       : {c['control_plane_attempt_count']}",
            f"executor_attempt_count : {c['executor_attempt_count']}", f"destination_observed   : {ls['destination_observed']}"]


def test_e2e_p_n7_n8_cli_attribution_and_unchanged_existing_lines(new_replay, new_clone, tmp_path):
    p, lost, n8 = _packs(new_replay)
    outs = {}
    for name, pack in (("P", p), ("N7", lost), ("N8", n8)):
        rc, out, err = _run(new_clone, pack, tmp_path, "summarize")
        assert rc == 0 and "semantic_validation_passed: True" in out, (name, rc, out, err)
        tail = out.splitlines()
        i = tail.index(_existing_lines(pack)[0])
        assert tail[i:i + 4] == _existing_lines(pack), (name, tail[i:i + 4])           # the four original lines, same text, same order, same place
        assert tail[i + 4].startswith("provenance (retained records; source-asserted, none independently verified)")
        assert not FORBIDDEN.search("\n".join(tail[i + 4:])), (name, out)
        outs[name] = "\n".join(tail[i + 4:])
    # P: both sources, executed and positively acknowledged
    assert "executor_evidence      : supplied" in outs["P"] and "executor_result        : status=executed acknowledged=True newly_executed=True" in outs["P"]
    assert "acknowledgement        : received" in outs["P"] and "control_plane_evidence : control_plane_attempt_count 1" in outs["P"]
    # N7: same counters as P in the original lines, but the lost acknowledgment is now visible and distinguishable
    assert "executor_result        : status=reconciled acknowledged=False newly_executed=False" in outs["N7"] and "acknowledgement        : unknown" in outs["N7"]
    assert "control_plane_unknown" in outs["N7"] and outs["N7"] != outs["P"]
    # N8: executor evidence absent, Control Plane sourced statements attributed to the Control Plane
    assert "executor_evidence      : NOT supplied" in outs["N8"] and "not a measured zero-execution outcome" in outs["N8"]
    assert "execution_attempted_source : yes (source: Control Plane attempts (1); no executor attempt records)" in outs["N8"]
    assert "destination_observed_source : applied (Control Plane reconciliation;" in outs["N8"] and "executor destination_effect_count 0" in outs["N8"]
    assert "executor_result" not in outs["N8"] and "executor attempts" not in outs["N8"]          # CP-only evidence is never presented as executor-sourced
    # counters and validation status unchanged for the same inputs (values from the S2 baseline)
    assert p.metadata["traceable_import"]["derived_counts"]["executor_attempt_count"] == 1 and lost.metadata["traceable_import"]["derived_counts"]["execution_result_state_counts"] == {"applied": 1}
    c8 = n8.metadata["traceable_import"]
    assert c8["derived_counts"]["executor_attempt_count"] == 0 and c8["derived_counts"]["destination_effect_count"] == 0 and c8["derived_counts"]["execution_result_state_counts"] == {}
    assert c8["replay_semantic_validation"]["status"] == "validated_partial" and c8["lifecycle_summary"]["destination_observed"] == "applied" and c8["lifecycle_summary"]["execution_attempted"] == "yes"


def test_e2e_validate_path_is_unchanged_and_clean(new_replay, new_clone, tmp_path):
    for pack in _packs(new_replay):
        rc, out, err = _run(new_clone, pack, tmp_path, "validate")
        assert rc == 0 and "Valid   : True" in out and "Origin  : import (metadata.traceable_import compared with its retained sources)" in out, (rc, out, err)
        assert "provenance (retained records" not in out                                      # validate output has no new lines
