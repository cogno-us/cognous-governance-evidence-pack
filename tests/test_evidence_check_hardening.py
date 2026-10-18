"""Evidence check hardening: imported-code binding, legacy status label, marker presence, strict timestamps.

Each tightening has a paired control for the valid producer path.
"""
import copy
import json
import subprocess
import sys
import textwrap
from collections import Counter
from pathlib import Path

import pytest

from agent_governance_evidence_pack import importer as imp
from agent_governance_evidence_pack.freshness import parse_time
from agent_governance_evidence_pack.models import EvidencePack
from agent_governance_evidence_pack.validator import validate_evidence_pack

from .test_freshness_block import MANIFEST

FIX = Path(__file__).parent / "fixtures"
EXAMPLES = Path(__file__).parent.parent / "examples"
PINNED = "1" * 40


# ------------------------------------------------------------------------------------ imported code binding
CHILD = textwrap.dedent('''
    import json, sys
    pack_src, expected, *paths = sys.argv[1:]
    sys.path[:0] = paths
    sys.path.insert(len(paths), pack_src)
    sys.dont_write_bytecode = True
    import agent_governance_evidence_pack.importer as imp
    if "--load" in sys.argv:
        import agent_replay_bundle
    try:
        imp._require_pinned_replay_distribution(expected)
        print(json.dumps({"refused": False}))
    except imp.ImportContractError as exc:
        print(json.dumps({"refused": True, "why": str(exc)}))
''')


def _site(root, name, files, *, record_hashes=False, dir_url=None):
    """A throw-away site directory: a package named like the Replay package plus distribution metadata naming PINNED."""
    import base64
    import hashlib
    site = root / name
    package = site / "agent_replay_bundle"
    package.mkdir(parents=True)
    rows = []
    for rel, text in files.items():
        (package / rel).write_text(text)
        digest = ""
        if record_hashes:
            raw = hashlib.sha256(text.encode()).digest()
            digest = "sha256=" + base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
        rows.append(f"agent_replay_bundle/{rel},{digest},")
    info = site / "agent_replay_bundle-0.1.0.dist-info"
    info.mkdir()
    (info / "METADATA").write_text("Metadata-Version: 2.1\nName: agent-replay-bundle\nVersion: 0.1.0\n")
    direct = {"url": "https://example.invalid/replay", "vcs_info": {"vcs": "git", "commit_id": PINNED}}
    if dir_url:
        direct = {"url": dir_url, "dir_info": {"editable": True}}
    (info / "direct_url.json").write_text(json.dumps(direct))
    (info / "RECORD").write_text("\n".join(rows) + "\n")
    return site


def _check(tmp_path, *sites, expected=PINNED, load=False):
    script = tmp_path / "child.py"
    script.write_text(CHILD)
    src = str(Path(__file__).parent.parent / "src")
    args = [sys.executable, "-I", str(script), src, expected, *map(str, sites)] + (["--load"] if load else [])
    out = subprocess.run(args, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-400:]
    return json.loads(out.stdout.splitlines()[-1])


def test_code_and_distribution_together_are_accepted(tmp_path):
    real = _site(tmp_path, "real", {"__init__.py": "X = 1\n"}, record_hashes=True)
    assert _check(tmp_path, real)["refused"] is False
    assert _check(tmp_path, real, load=True)["refused"] is False


def test_code_ahead_of_the_distribution_is_refused(tmp_path):
    real = _site(tmp_path, "real", {"__init__.py": "X = 1\n"}, record_hashes=True)
    other = tmp_path / "other"
    (other / "agent_replay_bundle").mkdir(parents=True)
    (other / "agent_replay_bundle" / "__init__.py").write_text("X = 2\n")
    assert _check(tmp_path, other, real)["refused"] is True
    assert _check(tmp_path, other, real, load=True)["refused"] is True


def test_recorded_digest_mismatch_is_refused(tmp_path):
    real = _site(tmp_path, "real", {"__init__.py": "X = 1\n"}, record_hashes=True)
    (real / "agent_replay_bundle" / "__init__.py").write_text("X = 3\n")
    assert _check(tmp_path, real)["refused"] is True


def test_unrecorded_module_beside_the_package_files_is_refused(tmp_path):
    real = _site(tmp_path, "real", {"__init__.py": "X = 1\n"}, record_hashes=True)
    (real / "agent_replay_bundle" / "importers.py").write_text("Y = 1\n")
    assert _check(tmp_path, real)["refused"] is True


def test_editable_install_accepts_code_inside_its_directory_only(tmp_path):
    root = tmp_path / "checkout"
    root.mkdir()
    site = _site(tmp_path, "site", {"__init__.py": "X = 1\n"}, dir_url=root.as_uri())
    # the code is in the site directory, not in the directory the metadata names: no git checkout there either
    assert _check(tmp_path, site)["refused"] is True


def test_check_still_refuses_another_pinned_revision(tmp_path):
    real = _site(tmp_path, "real", {"__init__.py": "X = 1\n"}, record_hashes=True)
    assert _check(tmp_path, real, expected="2" * 40)["refused"] is True


# ------------------------------------------------------------------------------------ legacy status label
def _legacy_bundle():
    bundle = json.loads((FIX / "freshness_inputs" / "executed.bundle.json").read_text())
    bundle = copy.deepcopy(bundle)
    bundle["metadata"].pop("control_plane_revision", None)
    bundle["producer_profiles"] = []
    assert not imp._is_v2(bundle)
    return bundle


def _import(bundle, status):
    original = imp._semantic
    imp._semantic = lambda manifest, b: ([], [], Counter(), status)
    try:
        return imp.import_manifest_reconstruction(MANIFEST, bundle, generated_at="2026-10-18T00:00:00+00:00")
    finally:
        imp._semantic = original


def test_legacy_bundle_is_not_labelled_semantically_valid():
    pack = _import(_legacy_bundle(), "executed")
    labels = {r.validation_status for r in pack.replay_bundles}
    assert labels == {"inputs_reimported_only"}


def test_producer_v2_bundle_keeps_its_label():
    bundle = json.loads((FIX / "freshness_inputs" / "executed.bundle.json").read_text())
    assert imp._is_v2(bundle)
    pack = _import(bundle, "validated_complete")
    assert {r.validation_status for r in pack.replay_bundles} == {"semantically_valid"}


# ------------------------------------------------------------------------------------ marker presence
def _example(name):
    return json.loads((EXAMPLES / "producer-v2" / name).read_text())


def _codes(dump):
    report = validate_evidence_pack(EvidencePack.model_validate(dump))
    return {i.code for i in report.issues if i.severity.value == "error"}


def test_imported_pack_without_its_trace_marker_is_not_valid():
    dump = _example("lost_ack.pack.json")
    del dump["metadata"]["traceable_import"]
    assert "E_TRACE_SEMANTICS" in _codes(dump)


def test_hand_authored_pack_without_a_marker_is_still_valid():
    dump = json.loads((EXAMPLES / "customer_service_agent_evidence_pack.json").read_text())
    assert "traceable_import" not in dump.get("metadata", {})
    assert _codes(dump) == set()


# ------------------------------------------------------------------------------------ strict timestamps
@pytest.mark.parametrize("value", ["2026-10-18T00:00:00", "2026-10-18T00:00:00.5", "2026-10-18", "2026-10-18 00:00:00"])
def test_parse_time_refuses_a_timestamp_without_an_offset(value):
    with pytest.raises(ValueError):
        parse_time(value)


@pytest.mark.parametrize("value,iso", [("2026-10-18T00:00:00Z", "2026-10-18T00:00:00+00:00"),
                                       ("2026-10-18T02:00:00+02:00", "2026-10-18T00:00:00+00:00")])
def test_parse_time_accepts_an_offset(value, iso):
    assert parse_time(value).isoformat() == iso
