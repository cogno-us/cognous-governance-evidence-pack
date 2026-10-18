"""Opt-in freshness block (control plane freshness/0.1, #47): counts from the retained journal, absent unless members are retained.

Replay (cognous-replay-bundle d0e7b36) refuses these members today (see the last section), so the end-to-end cases here stub the
Replay semantic step (``_semantic``) and feed the importer retained records directly; they prove the pack's own part only.
"""
import copy
import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import agent_governance_evidence_pack.importer as imp
from agent_governance_evidence_pack import freshness as fr

FIX = Path(__file__).parent / "fixtures" / "freshness_inputs"
MANIFEST = {"manifest_version": "1.1", "manifest_id": "m",
            "actions": [{"action_id": "a", "review_requirement": "none", "reliance_requirement": "none"}], "tools": []}
GENERATED = "2026-10-18T00:00:00+00:00"
AS_OF = datetime(2026, 10, 18, 12, 0, 0, tzinfo=timezone.utc)
T0 = datetime(2026, 10, 18, 11, 0, 0, tzinfo=timezone.utc)


def stamp(seconds):
    return (T0 + timedelta(seconds=seconds)).isoformat()


def ev(check, phase, at, **extra):
    return {"check_id": check, "phase": phase, "stage": "effect", "recorded_at": stamp(at), "reasons": [], **extra}


def journal():
    """Eight checks covering every state the block counts, deadlines in seconds after T0 (as_of is T0 + 3600 s)."""
    return [
        ev("done", "opened", 0, deadline=stamp(60)), ev("done", "completed", 5),                        # closed
        ev("live", "opened", 100, deadline=stamp(7200)),                                                # open, within deadline
        ev("late1", "opened", 200, deadline=stamp(300)),                                                # open, overdue
        ev("late2", "opened", 50, deadline=stamp(400)), ev("late2", "overdue", 500),                    # open, overdue (reaper wrote it)
        ev("dead", "opened", 10, deadline=stamp(100)), ev("dead", "interrupted", 900),                  # abandoned
        ev("stale", "opened", 20, deadline=stamp(120)), ev("stale", "completed", 30), ev("stale", "expired", 3000),  # expired
        ev("legacy", "opened", 1),                                                                      # no deadline: open, never overdue
    ]


RUNS = [{"run_id": "run1", "trigger": "startup", "recorded_at": stamp(1000), "interrupted": ["dead"], "overdue": ["late2"],
         "open_count": 4, "oldest_open_age_seconds": 3599.0}]
REFUSALS = [{"refusal_id": "r1", "decision_id": "d", "effect_id": "e", "recorded_at": stamp(3000),
             "reasons": [fr.EXPIRED_CODE], "deadline": stamp(120)}]


def independent_counts(rows, as_of):
    """Recompute from raw rows by a different route than the module: last-state per check, no phase-set intersection."""
    checks = {}
    for r in rows:
        checks.setdefault(r["check_id"], []).append(r)
    out = dict(open=0, abandoned=0, overdue=0, expired=0, ages=[])
    for rs in checks.values():
        phases = [r["phase"] for r in rs]
        out["abandoned"] += phases.count("interrupted") > 0
        out["expired"] += phases.count("expired") > 0
        opened = [r for r in rs if r["phase"] == "opened"]
        closed = any(p in ("completed", "interrupted", "expired") for p in phases)
        if not opened or closed:
            continue
        out["open"] += 1
        out["ages"].append((as_of - datetime.fromisoformat(opened[0]["recorded_at"])).total_seconds())
        d = opened[0].get("deadline")
        if d is not None and as_of > datetime.fromisoformat(d):
            out["overdue"] += 1
    return out


# ---------------------------------------------------------------------------------------------------------- the counts
def test_counts_match_hand_derivation():
    c = fr.freshness_counts(journal(), as_of=AS_OF)
    # open: live, late1, late2, legacy; abandoned: dead; expired: stale; overdue: late1, late2 (legacy has no deadline)
    assert (c["open_count"], c["abandoned_open_count"], c["overdue_count"], c["expired_before_dispatch_count"]) == (4, 1, 2, 1)
    assert c["oldest_open_age_seconds"] == 3599.0          # legacy, opened at T0 + 1 s
    assert c["as_of"] == AS_OF.isoformat()


def test_counts_equal_independent_recomputation_from_raw_rows():
    rows = journal()
    c = fr.freshness_counts(rows, as_of=AS_OF)
    i = independent_counts(rows, AS_OF)
    assert (c["open_count"], c["abandoned_open_count"], c["overdue_count"], c["expired_before_dispatch_count"]) == \
        (i["open"], i["abandoned"], i["overdue"], i["expired"])
    assert c["oldest_open_age_seconds"] == max(i["ages"])


@pytest.mark.parametrize("offset", [0, 150, 301, 450, 7000, 9000, 100000])
def test_counts_equal_independent_recomputation_at_every_as_of(offset):
    when = T0 + timedelta(seconds=offset)
    c = fr.freshness_counts(journal(), as_of=when)
    i = independent_counts(journal(), when)
    assert (c["open_count"], c["overdue_count"]) == (i["open"], i["overdue"])


def test_counts_equal_control_plane_freshness_counts():
    cp = pytest.importorskip("agent_control_plane.freshness")
    if not hasattr(cp, "freshness_counts"):
        pytest.skip("installed control plane predates freshness/0.1")
    for offset in (0, 301, 450, 3600, 9000):
        when = T0 + timedelta(seconds=offset)
        assert fr.freshness_counts(journal(), as_of=when) == cp.freshness_counts(journal(), as_of=when)


def test_check_without_a_deadline_is_open_never_overdue():
    rows = [ev("old", "opened", -10_000_000)]                    # opened long ago, no deadline member
    c = fr.freshness_counts(rows, as_of=AS_OF)
    assert (c["open_count"], c["overdue_count"]) == (1, 0)
    assert c["oldest_open_age_seconds"] > 10_000_000
    for forever in (None, ""):                                    # an empty deadline is not a deadline either
        assert fr.freshness_counts([ev("old", "opened", 0, deadline=forever)], as_of=AS_OF)["overdue_count"] == 0


def test_deadline_boundary_is_strict():
    rows = [ev("c", "opened", 0, deadline=stamp(60))]
    assert fr.freshness_counts(rows, as_of=T0 + timedelta(seconds=60))["overdue_count"] == 0
    assert fr.freshness_counts(rows, as_of=T0 + timedelta(seconds=61))["overdue_count"] == 1


def test_empty_journal_has_no_oldest_age():
    c = fr.freshness_counts([], as_of=AS_OF)
    assert (c["open_count"], c["oldest_open_age_seconds"]) == (0, None)


# ---------------------------------------------------------------------------------------------------------- mutation check
def _counts(rows):
    c = fr.freshness_counts(rows, as_of=AS_OF)
    return (c["open_count"], c["abandoned_open_count"], c["overdue_count"], c["expired_before_dispatch_count"])


BASE = _counts(journal())


def _drop(check, phase):
    return lambda rows: [r for r in rows if not (r["check_id"] == check and r["phase"] == phase)]


def _set(check, phase, **fields):
    def apply(rows):
        out = copy.deepcopy(rows)
        for r in out:
            if r["check_id"] == check and r["phase"] == phase:
                r.update(fields)
        return out
    return apply


@pytest.mark.parametrize("mutate,expected", [
    (_set("late1", "opened", deadline=stamp(7200)), (4, 1, 1, 1)),              # deadline moved past as_of: no longer overdue
    (_set("live", "opened", deadline=stamp(10)), (4, 1, 3, 1)),                 # deadline moved before as_of: overdue
    (_drop("stale", "expired"), (4, 1, 2, 0)),                                  # expired event removed: not counted
    (_drop("dead", "interrupted"), (5, 0, 3, 1)),                               # interruption removed: back to open (and overdue)
    (_drop("late1", "opened"), (3, 1, 1, 1)),                                   # opening removed: not an open check
    (lambda rows: rows + [ev("late1", "completed", 600)], (3, 1, 1, 1)),        # completion added: closed
    (lambda rows: [r for r in rows if r["check_id"] != "legacy"], (3, 1, 2, 1)),
    (_set("legacy", "opened", deadline=stamp(5)), (4, 1, 3, 1)),                # a deadline appears: now overdue
], ids=["deadline-later", "deadline-earlier", "no-expired", "no-interrupted", "no-opening", "late-completed", "no-legacy", "legacy-deadline"])
def test_each_row_mutation_moves_exactly_the_expected_counts(mutate, expected):
    assert BASE == (4, 1, 2, 1)
    assert _counts(mutate(journal())) == expected


def test_mutated_implementation_is_caught(monkeypatch):
    """A mutant that counts a deadline-less check as overdue, and one that treats the deadline as inclusive, both fail the suite's checks."""
    real = fr.parse_time
    rows = [ev("c", "opened", 0, deadline=stamp(60)), ev("legacy", "opened", 0)]
    assert fr.freshness_counts(rows, as_of=T0 + timedelta(seconds=60))["overdue_count"] == 0
    monkeypatch.setattr(fr, "parse_time", lambda v: real(v) - timedelta(seconds=1))   # inclusive-style off-by-one
    assert fr.freshness_counts(rows, as_of=T0 + timedelta(seconds=60))["overdue_count"] == 1


# ---------------------------------------------------------------------------------------------------------- the gate and the block
def test_block_is_absent_without_freshness_members():
    legacy = [ev("a", "opened", 0), ev("a", "completed", 1), ev("b", "opened", 2), ev("c", "opened", 3), ev("c", "interrupted", 4)]
    assert fr.freshness_block(legacy, [], [{"refusal_id": "r", "reasons": ["grant_expired"]}], as_of=GENERATED) is None
    assert fr.freshness_block([], [], [], as_of=GENERATED) is None


@pytest.mark.parametrize("rows,runs,refusals", [
    ([ev("a", "opened", 0, deadline=stamp(5))], [], []),
    ([ev("a", "opened", 0), ev("a", "overdue", 1)], [], []),
    ([ev("a", "opened", 0), ev("a", "completed", 1), ev("a", "expired", 2)], [], []),
    ([ev("a", "opened", 0)], RUNS, []),
    ([ev("a", "opened", 0)], [], [{"reasons": [fr.EXPIRED_CODE]}]),
    ([ev("a", "opened", 0)], [], [{"reasons": ["x"], "deadline": stamp(1)}]),
], ids=["deadline", "overdue-phase", "expired-phase", "recovery-run", "refusal-code", "refusal-deadline"])
def test_any_freshness_member_opens_the_block(rows, runs, refusals):
    block = fr.freshness_block(rows, runs, refusals, as_of=GENERATED)
    assert block is not None and block["source"] == "controller_journal"


def test_block_content_and_limits():
    block = fr.freshness_block(journal(), RUNS, REFUSALS, as_of=AS_OF.isoformat())
    assert {k: block[k] for k in ("open_count", "abandoned_open_count", "overdue_count", "oldest_open_age_seconds",
                                  "expired_before_dispatch_count", "as_of")} == {
        "open_count": 4, "abandoned_open_count": 1, "overdue_count": 2, "oldest_open_age_seconds": 3599.0,
        "expired_before_dispatch_count": 1, "as_of": AS_OF.isoformat()}
    assert block["recovery_run_count"] == 1 and block["refusal_rows_expired_before_dispatch"] == 1
    text = " ".join(block["not_proven"])
    assert "not from an independent monitor" in text and "INDEPENDENT-VERIFIER-DESIGN.md" in text


def test_block_without_as_of_does_not_read_the_wall_clock():
    block = fr.freshness_block(journal(), RUNS, REFUSALS, as_of=None)
    assert block["as_of"] is None and block["overdue_count"] is None and block["oldest_open_age_seconds"] is None
    assert (block["open_count"], block["abandoned_open_count"], block["expired_before_dispatch_count"]) == (4, 1, 1)
    assert "as_of unavailable" in block["note"]


# ---------------------------------------------------------------------------------------------------------- through the importer
def _import(bundle, generated_at=GENERATED):
    """``generated_at`` is the bundle's own source generation time (what the block's as_of follows); the keyword is the fallback."""
    if generated_at != GENERATED:
        bundle = {**bundle, "generated_at": generated_at}
    original = imp._semantic
    imp._semantic = lambda manifest, b: ([], [], Counter(), "validated_complete")
    try:
        return imp.import_manifest_reconstruction(MANIFEST, bundle, generated_at=generated_at)
    finally:
        imp._semantic = original


def _records(bundle, rows, kind):
    out = copy.deepcopy(bundle)
    profile = out["records"][0]["producer_profile_id"]
    out["records"] += [{"record_id": f"fresh-{kind}-{n}", "record_type": kind, "producer_profile_id": profile, "data": row}
                       for n, row in enumerate(rows)]
    return out


def _fixture(name):
    return json.loads((FIX / f"{name}.bundle.json").read_text())


NAMES = sorted(p.name[:-len(".bundle.json")] for p in FIX.glob("*.bundle.json"))


def test_fixture_set_is_what_the_golden_file_covers():
    golden = json.loads((FIX / "baseline_pack_sha256.json").read_text())["pack_json_sha256"]
    assert NAMES == sorted(golden) and len(NAMES) == 5


@pytest.mark.parametrize("name", NAMES)
def test_output_without_freshness_members_is_byte_identical_to_before(name):
    """The golden hashes were computed from the pack code at 76f5280a, before this block existed, over the same frozen bundles."""
    golden = json.loads((FIX / "baseline_pack_sha256.json").read_text())["pack_json_sha256"]
    pack = _import(_fixture(name))
    assert "freshness_summary" not in pack.metadata["traceable_import"]
    assert hashlib.sha256(pack.model_dump_json().encode()).hexdigest() == golden[name]


def test_retained_journal_with_freshness_members_adds_the_block_and_nothing_else():
    base = _fixture("legacy_journal_no_freshness_members")
    with_members = _records(base, journal(), fr.EVENT_RECORD)
    with_members = _records(with_members, RUNS, fr.RUN_RECORD)
    with_members = _records(with_members, REFUSALS, fr.REFUSAL_RECORD)
    with_members["generated_at"] = AS_OF.isoformat()
    pack = _import(with_members)
    block = pack.metadata["traceable_import"]["freshness_summary"]
    # the legacy fixture already retains two journal checks (c1 completed, c2 open, no deadline): +1 open check
    assert (block["open_count"], block["overdue_count"], block["abandoned_open_count"], block["expired_before_dispatch_count"]) == (5, 2, 1, 1)
    # the retained sources and every other summary are the supplied inputs, not altered by the block
    assert pack.metadata["traceable_import"]["retained_sources"]["reconstruction_bundle"] == with_members
    # dropping the freshness records from the same bundle gives the pack without the block (the block is the only addition)
    gate_off = copy.deepcopy(with_members)
    gate_off["records"] = [r for r in gate_off["records"] if not r["record_id"].startswith("fresh-")]
    assert "freshness_summary" not in _import(gate_off).metadata["traceable_import"]


def test_journal_without_deadlines_in_a_pack_has_no_block_and_no_overdue():
    pack = _import(_fixture("legacy_journal_no_freshness_members"))
    assert "freshness_summary" not in pack.metadata["traceable_import"]


def test_unparseable_generation_time_gives_a_block_without_as_of():
    base = _records(_fixture("observe_bound_fail"), journal(), fr.EVENT_RECORD)
    block = _import(base, generated_at="not a time").metadata["traceable_import"]["freshness_summary"]
    assert block["as_of"] is None and block["overdue_count"] is None


@pytest.mark.parametrize("row", [{"phase": "expired", "recorded_at": GENERATED},
                                 {"check_id": "c", "phase": "opened", "recorded_at": "nope", "deadline": GENERATED},
                                 {"check_id": "c", "phase": "opened", "recorded_at": GENERATED, "deadline": "nope"}])
def test_malformed_freshness_rows_are_refused_not_guessed(row):
    base = _records(_fixture("observe_bound_fail"), [row], fr.EVENT_RECORD)
    with pytest.raises(imp.ImportContractError, match="malformed"):
        _import(base)


# ---------------------------------------------------------------------------------------------------------- Replay today
def test_replay_today_refuses_or_drops_the_freshness_members():
    """Documents what Replay needs (see the PR): it validates the retained journal with closed models and has no record type for
    recovery runs. If Replay is changed to accept these members this test skips; remove it then."""
    pytest.importorskip("agent_replay_bundle.refusal_evidence")
    from pydantic import ValidationError
    from agent_replay_bundle import refusal_evidence as re_
    opened = {"check_id": "c", "phase": "opened", "stage": "effect", "recorded_at": GENERATED, "owner": {"holder": "h"},
              "proposal_commitment": "sha256:" + "0" * 64, "decision_id": None, "effect_id": None, "action_class": {},
              "input": None, "reasons": [], "reason_vocabulary_version": "runtime-authority-reasons/0.1"}
    re_.JournalEvent.model_validate(opened)                                    # the legacy shape is accepted
    refused = []
    for row in ({**opened, "deadline": GENERATED}, {**opened, "phase": "expired"}, {**opened, "phase": "overdue"}):
        try:
            re_.JournalEvent.model_validate(row)
        except ValidationError as exc:
            refused.append(re_._structure_code(exc))
    if not refused:
        pytest.skip("Replay now accepts freshness journal members")
    assert refused == ["undeclared_member", "unknown_enum_value", "unknown_enum_value"]
    assert "recovery_runs" not in {**re_.EXTENDED, **re_.AUTHORITY_EXTENDED}
