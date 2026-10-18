"""Optional recovery inspection evidence; not a manifest-import transformation."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json

REPLAY_REVISION = "696e7bc2432fc7b5cf2d6e6c5f0b944b2d9a265f"
RUNTIME_REVISION = "8e7d634cf0a22b6f3c1fc6d93afe92c7414fa243"
REPLAY_FORMAT = "cognous-replay-recovery-inspection/0.1"
EVIDENCE_FORMAT = "cognous-recovery-inspection-evidence/0.1"
TRANSFORMATION = "agep-recovery-inspection/0.1"
CANONICALIZATION = "python-json-sort-ascii-compact/1"


class RecoveryEvidenceError(ValueError):
    """Unsupported or inconsistent recovery evidence input or derived output."""


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _require(condition, reason):
    if not condition:
        raise RecoveryEvidenceError(reason)


def build_recovery_inspection_evidence(inspection, *, replay_revision, expected_identity):
    """Retain a validated native Replay inspection and create a bounded summary.

    The caller explicitly selects the dependency and original identity. Matching
    inputs do not authenticate the caller, source bytes, or repository revision.
    """
    try:
        _require(replay_revision == REPLAY_REVISION, "unsupported Replay revision")
        retained = json.loads(_json(inspection))
        _require(retained["inspection_format"] == REPLAY_FORMAT, "unsupported Replay inspection format")
        _require(retained["runtime_revision"] == RUNTIME_REVISION, "unsupported Runtime revision")
        _require(_json(retained["expected_identity"]) == _json(expected_identity), "selected identity mismatch")
        # Invoke the actual owning consumer; do not duplicate its semantics.
        from agent_replay_bundle.recovery_inspection import (
            INSPECTION_FORMAT, validate_recovery_inspection,
        )
        # The imported code must be the code of the installed distribution (same check as the pinned Replay import).
        from .importer import _imported_replay_code_problem
        problem = _imported_replay_code_problem()
        _require(problem is None, f"imported Replay code is not the code of the installed distribution: {problem}")
        _require(INSPECTION_FORMAT == REPLAY_FORMAT, "installed Replay API is unsupported")
        validate_recovery_inspection(retained)
        _require(retained["assurance"]["settlement_verified"] is False
                 and retained["assurance"]["independent_verification"] == "not_established"
                 and retained["assurance"]["execution_authority"] == "none"
                 and retained["assurance"]["retry_eligible"] is False,
                 "unsupported source assurance")
        source = retained["source"]
        current = source["current"]
        digest = hashlib.sha256(_json(retained).encode("utf-8")).hexdigest()
        return {
            "evidence_format": EVIDENCE_FORMAT,
            "transformation": TRANSFORMATION,
            "review_status": "unreviewed",
            "provenance": {
                "replay_revision": replay_revision, "runtime_revision": RUNTIME_REVISION,
                "replay_inspection_format": REPLAY_FORMAT,
                "input_sha256": digest, "canonicalization": CANONICALIZATION,
                "revision_assurance": "caller_selected_not_authenticated",
            },
            "original_identity": deepcopy(expected_identity),
            "recorded_source_evaluation_time": source["evaluated_at"],
            "summary": {
                "producer_work_state": current["work_state"],
                "producer_observation": current["observation"],
                "producer_finality": current["finality"],
                "original_disposition": source["disposition"]["status"],
                "retained_event_count": len(source["events"]),
                "commitment_only_event_count": sum(
                    check["digest_check"] == "not_performed_missing_preimage"
                    for check in retained["event_checks"]),
                "legacy_record_present": source["legacy"] is not None,
                "full_payload_reconstruction": retained["loss_report"]["full_payload_reconstruction"],
            },
            "replay_inspection": retained,
            "loss_report": deepcopy(retained["loss_report"]),
            "assurance": {
                "source_authentication": "not_established",
                "independent_verification": "not_established",
                "settlement_verified": False, "execution_authority": "none", "retry_eligible": False,
                "freshness_at_transformation": "not_evaluated",
                "review_acceptance": "not_established",
            },
        }
    except RecoveryEvidenceError:
        raise
    except (ImportError, KeyError, TypeError, ValueError, OverflowError, RecursionError) as exc:
        # Includes Replay's semantic validation failures; never fall back to parsing.
        raise RecoveryEvidenceError("invalid recovery inspection or unavailable Replay validator") from exc


def validate_recovery_inspection_evidence(evidence):
    """Rebuild with the owning Replay validator; require every derived field."""
    try:
        rebuilt = build_recovery_inspection_evidence(evidence["replay_inspection"],
            replay_revision=evidence["provenance"]["replay_revision"],
            expected_identity=evidence["original_identity"])
        _require(_json(evidence) == _json(rebuilt), "evidence mapping, loss report, or assurance changed")
    except RecoveryEvidenceError:
        raise
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise RecoveryEvidenceError("malformed recovery evidence") from exc
