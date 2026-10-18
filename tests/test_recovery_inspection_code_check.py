"""Recovery inspection evidence uses the same imported-code binding as the pinned Replay import.

The check (``importer._imported_replay_code_problem``) must also run before ``recovery_inspection`` hands data to the
Replay package. Each refusal case has a paired valid control.
"""
import json
import subprocess
import sys
import textwrap
from pathlib import Path

from .test_evidence_check_hardening import _site

REPLAY_FILES = {
    "__init__.py": "X = 1\n",
    "recovery_inspection.py": (
        "INSPECTION_FORMAT = 'cognous-replay-recovery-inspection/0.1'\n"
        "def validate_recovery_inspection(retained):\n"
        "    return None\n"
    ),
}

CHILD = textwrap.dedent('''
    import json, sys
    pack_src, *paths = sys.argv[1:]
    sys.path[:0] = paths
    sys.path.insert(len(paths), pack_src)
    sys.dont_write_bytecode = True
    import agent_governance_evidence_pack.recovery_inspection as ri
    identity = {"run": "r1"}
    inspection = {
        "inspection_format": ri.REPLAY_FORMAT,
        "runtime_revision": ri.RUNTIME_REVISION,
        "expected_identity": identity,
        "assurance": {"settlement_verified": False, "independent_verification": "not_established",
                      "execution_authority": "none", "retry_eligible": False},
        "source": {"evaluated_at": "2026-10-18T00:00:00Z", "events": [], "legacy": None,
                   "disposition": {"status": "open"},
                   "current": {"work_state": "unknown", "observation": "unknown", "finality": "not_final"}},
        "event_checks": [],
        "loss_report": {"full_payload_reconstruction": False},
    }
    try:
        ri.build_recovery_inspection_evidence(inspection, replay_revision=ri.REPLAY_REVISION, expected_identity=identity)
        print(json.dumps({"refused": False}))
    except ri.RecoveryEvidenceError as exc:
        print(json.dumps({"refused": True, "why": str(exc)}))
''')


def _run(tmp_path, *sites):
    script = tmp_path / "child.py"
    script.write_text(CHILD)
    src = str(Path(__file__).parent.parent / "src")
    out = subprocess.run([sys.executable, "-I", str(script), src, *map(str, sites)],
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-400:]
    return json.loads(out.stdout.splitlines()[-1])


def test_code_and_distribution_together_build_the_evidence(tmp_path):
    real = _site(tmp_path, "real", REPLAY_FILES, record_hashes=True)
    assert _run(tmp_path, real)["refused"] is False


def test_code_ahead_of_the_distribution_is_refused(tmp_path):
    real = _site(tmp_path, "real", REPLAY_FILES, record_hashes=True)
    other = tmp_path / "other"
    (other / "agent_replay_bundle").mkdir(parents=True)
    for rel, text in REPLAY_FILES.items():
        (other / "agent_replay_bundle" / rel).write_text(text)
    result = _run(tmp_path, other, real)
    assert result["refused"] is True
    assert "installed distribution" in result["why"]


def test_recorded_digest_mismatch_is_refused(tmp_path):
    real = _site(tmp_path, "real", REPLAY_FILES, record_hashes=True)
    (real / "agent_replay_bundle" / "recovery_inspection.py").write_text(
        REPLAY_FILES["recovery_inspection.py"] + "# changed\n")
    assert _run(tmp_path, real)["refused"] is True


def test_unrecorded_module_in_the_package_is_refused(tmp_path):
    real = _site(tmp_path, "real", REPLAY_FILES, record_hashes=True)
    (real / "agent_replay_bundle" / "extra.py").write_text("Y = 1\n")
    assert _run(tmp_path, real)["refused"] is True


def test_editable_install_with_code_inside_its_directory_is_unchanged(tmp_path):
    # Control: an editable install imported from the directory its metadata names is not refused by the code check.
    root = tmp_path / "checkout"
    (root / "agent_replay_bundle").mkdir(parents=True)
    for rel, text in REPLAY_FILES.items():
        (root / "agent_replay_bundle" / rel).write_text(text)
    meta = _site(tmp_path, "meta", {"__init__.py": "X = 1\n"}, dir_url=root.as_uri())
    # the metadata names `root`; the code is imported from `root`, which comes first on the path
    assert _run(tmp_path, root, meta)["refused"] is False
