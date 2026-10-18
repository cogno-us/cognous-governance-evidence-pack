"""Test configuration.

Most tests replace the Replay constant module with a stub, so no pinned Replay distribution is installed and the
installed-revision check (``importer._require_pinned_replay_distribution``) would refuse every import. The autouse fixture
below reports the expected revision for them. Tests of the check itself carry the ``real_distribution_check`` marker and
see the real function.
"""
import pytest

from agent_governance_evidence_pack import importer as imp


def pytest_configure(config):
    config.addinivalue_line("markers", "real_distribution_check: exercise the installed-Replay-revision check unpatched")


@pytest.fixture(autouse=True)
def _installed_replay_matches_pin(request, monkeypatch):
    if request.node.get_closest_marker("real_distribution_check"):
        return
    monkeypatch.setattr(imp, "_require_pinned_replay_distribution", lambda expected: None)
