"""Opt-in freshness block: open, abandoned, overdue and expired-before-dispatch checks, derived from the retained journal.

Selected only by the retained run record: the block exists when (and only when) it carries freshness members, which are

* a ``resolution_check_event`` with phase ``overdue`` or ``expired``, or a ``deadline`` member,
* a ``recovery_run`` record,
* an ``effect_time_refusal`` row with the reason ``check_expired_before_dispatch`` or a ``deadline`` member.

Without them nothing here runs and the pack is byte-identical to the output without this module.

The counts are computed exactly as the Control Plane's ``freshness.freshness_counts`` (freshness/0.1, control plane #47) computes
them; this is a reimplementation, not an import. A check without a deadline is open and never overdue.

What the block does not prove: the counts are derived from the controller's own journal. They are not an independent monitor.
A holder of the record-store key could have rewritten the rows, and a check that was never journalled is not counted. See ODES
``docs/engineering/INDEPENDENT-VERIFIER-DESIGN.md``.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

EVENT_RECORD = "resolution_check_event"
RUN_RECORD = "recovery_run"
REFUSAL_RECORD = "effect_time_refusal"
FRESHNESS_PHASES = frozenset({"overdue", "expired"})
EXPIRED_CODE = "check_expired_before_dispatch"
TERMINAL = frozenset({"completed", "interrupted", "expired"})

NOT_PROVEN = (
    "The counts come from the controller's own journal, not from an independent monitor (see ODES "
    "docs/engineering/INDEPENDENT-VERIFIER-DESIGN.md); a holder of the record-store key can rewrite the rows, and a check that "
    "was never journalled is not counted.",
    "An open check is not evidence of a stall: it may be in flight. overdue_count only says a deadline recorded by the "
    "controller has passed as of as_of.",
    "A check without a deadline is open and never overdue; the block cannot say how long it should have taken.",
    "as_of is the pack's source generation time, not the time the pack is read; ages and overdue state are as of that instant.",
    "A deadline narrows the window between check and commit; it does not close it.",
)


def parse_time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def freshness_counts(check_events: list[dict], *, as_of: datetime) -> dict[str, Any]:
    """Same derivation as the Control Plane's ``freshness_counts``, over plain dict rows."""
    terminal = TERMINAL
    by_check: dict[str, list[dict]] = {}
    for e in check_events:
        by_check.setdefault(e["check_id"], []).append(e)
    open_checks, abandoned, expired, overdue = [], 0, 0, 0
    for events in by_check.values():
        opening = next((e for e in events if e["phase"] == "opened"), None)
        phases = {e["phase"] for e in events}
        if "interrupted" in phases:
            abandoned += 1
        if "expired" in phases:
            expired += 1
        if opening is None or phases & terminal:
            continue
        open_checks.append(opening)
        deadline = opening.get("deadline")
        if deadline and as_of > parse_time(deadline):
            overdue += 1
    ages = [(as_of - parse_time(o["recorded_at"])).total_seconds() for o in open_checks]
    return {"as_of": iso(as_of), "open_count": len(open_checks), "abandoned_open_count": abandoned,
            "overdue_count": overdue, "expired_before_dispatch_count": expired,
            "oldest_open_age_seconds": max(ages) if ages else None}


def has_freshness_members(check_events: list[dict], recovery_runs: list[dict], refusals: list[dict]) -> bool:
    return (bool(recovery_runs)
            or any(e.get("phase") in FRESHNESS_PHASES or "deadline" in e for e in check_events)
            or any("deadline" in r or EXPIRED_CODE in (r.get("reasons") or []) for r in refusals))


def freshness_block(check_events: list[dict], recovery_runs: list[dict], refusals: list[dict],
                    *, as_of: str | None) -> dict[str, Any] | None:
    """The block, or None when the retained rows carry no freshness members (opt-in)."""
    if not has_freshness_members(check_events, recovery_runs, refusals):
        return None
    when = parse_time(as_of) if as_of else None
    if when is None:
        # No source generation time: do not read the wall clock (the pack stays reproducible). Count what needs no clock.
        counts = freshness_counts(check_events, as_of=datetime.max.replace(tzinfo=timezone.utc))
        counts.update(as_of=None, overdue_count=None, oldest_open_age_seconds=None)
        note = "as_of unavailable: no source generation time; overdue_count and oldest_open_age_seconds not computed"
    else:
        counts, note = freshness_counts(check_events, as_of=when), None
    block = {"profile": "freshness-block/0.1", "source": "controller_journal", **counts,
             "refusal_rows_expired_before_dispatch": sum(EXPIRED_CODE in (r.get("reasons") or []) for r in refusals),
             "recovery_run_count": len(recovery_runs),
             "not_proven": list(NOT_PROVEN)}
    if note:
        block["note"] = note
    return block


def block_for_records(records: list[dict], *, as_of: str | None) -> dict[str, Any] | None:
    """Pull the three retained record types out of a reconstruction bundle's records (in source order) and build the block."""
    ordered = sorted(records, key=lambda r: r.get("source_sequence", 0))
    pick = lambda kind: [dict(r["data"]) for r in ordered if r.get("record_type") == kind]
    return freshness_block(pick(EVENT_RECORD), pick(RUN_RECORD), pick(REFUSAL_RECORD), as_of=as_of)
