"""Input bounds and error reporting for admission of JSON text and values."""

import json
from pathlib import Path

import pytest

from agent_governance_evidence_pack.admission import admit_value, loads

ROOT = Path(__file__).parent.parent


def _json_files():
    out = []
    for base in ("examples", "tests/fixtures"):
        out.extend(sorted((ROOT / base).rglob("*.json")))
    return out


def test_valid_files_parse_exactly_as_before():
    files = _json_files()
    assert files
    checked = 0
    for path in files:
        raw = path.read_bytes()
        try:
            expected = json.loads(raw)
        except ValueError:
            continue
        try:
            got = loads(raw)
        except ValueError as exc:
            # only the pre-existing refusals (repeated members, budgets) may apply
            assert "duplicate" in str(exc) or "budget" in str(exc), path
            continue
        assert got == expected, path
        checked += 1
    assert checked > 10


@pytest.mark.parametrize("text", ['{"a": 1e400}', '[-1e999]', '{"a": [2e308]}'])
def test_number_out_of_range_is_refused_with_code(text):
    with pytest.raises(ValueError, match=r"\[input_json_non_finite_number\]"):
        loads(text)


@pytest.mark.parametrize("text", ['"\\ud800"', '{"a": "x\\udfffy"}', '{"\\ud800": 1}', '["\\udc00"]'])
def test_lone_surrogate_is_refused_with_code(text):
    with pytest.raises(ValueError, match=r"\[input_not_utf8\]"):
        loads(text)


def test_valid_surrogate_pair_and_large_finite_numbers_accepted():
    assert loads('"\\ud83d\\ude00"') == "\U0001F600"
    assert loads('[1e308, -1e308, 0.5, 12345678901234567890]') == [1e308, -1e308, 0.5, 12345678901234567890]


def test_admit_value_refuses_non_finite_and_surrogate():
    with pytest.raises(ValueError, match="input_json_non_finite_number"):
        admit_value({"a": [float("inf")]})
    with pytest.raises(ValueError, match="input_not_utf8"):
        admit_value({"a": "\ud800"})
    assert admit_value({"a": [1.5, "ok"]}) == {"a": [1.5, "ok"]}
