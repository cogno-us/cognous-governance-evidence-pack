import copy
import pytest
from agent_governance_evidence_pack.loader import load_evidence_pack_json
from agent_governance_evidence_pack.models import ReviewRecord, ReviewStatus
from agent_governance_evidence_pack.validator import validate_evidence_pack
from agent_governance_evidence_pack.renderer import render_markdown, _escape
from agent_governance_evidence_pack.summary import summarize_evidence_pack
from agent_governance_evidence_pack.importer import _records, _redaction_status, ImportContractError
from tests.test_loader import _minimal_payload


def test_unrelated_review_cannot_approve_pack():
    raw=_minimal_payload();raw['review_status']='approved'
    raw['review_records']=[{'reviewer':'synthetic','reviewed_at':'2026-01-01T00:00:00Z','decision':'rejected'}]
    pack=load_evidence_pack_json(raw)
    assert not validate_evidence_pack(pack).valid
    assert summarize_evidence_pack(pack)['review_status']=='invalid'
    with pytest.raises(ValueError):render_markdown(pack)


@pytest.mark.parametrize('trace',[{'transformation_version':'unknown'}, {'executor_producer_contract':True}, True])
def test_unbound_or_malformed_trace_fails_without_attribute_error(trace):
    raw=_minimal_payload();raw['metadata']={'traceable_import':trace}
    assert not validate_evidence_pack(load_evidence_pack_json(raw)).valid


def test_source_redaction_claim_cannot_assert_sanitization():
    findings=[]
    redacted,source=_redaction_status({'status':'redacted'},findings)
    assert redacted is False
    assert source=='unverified_source_claim'
    assert findings


def test_duplicate_record_ids_fail_before_attribution():
    record={'record_id':'same','record_type':'runtime_decision','producer_profile_id':'synthetic','data':{}}
    with pytest.raises(ImportContractError,match='duplicate'):_records({'records':[record,copy.deepcopy(record)]})


def test_large_metadata_rejected_before_loading():
    raw=_minimal_payload();raw['metadata']={'oversized':'x'*1048577}
    with pytest.raises(ValueError,match='budget'):load_evidence_pack_json(raw)


def test_control_characters_do_not_reach_rendered_output():
    assert '\x1b' not in _escape('name\x1b[31m')


def test_import_files_reject_duplicate_json_keys(tmp_path):
    from agent_governance_evidence_pack.importer import build_evidence_pack_from_files
    manifest = tmp_path / 'manifest.json'
    bundle = tmp_path / 'bundle.json'
    manifest.write_text('{"manifest_version": "1.1", "manifest_id": "m", "manifest_id": "substituted"}', encoding='utf-8')
    bundle.write_text('{"bundle_version": "0.2.0"}', encoding='utf-8')
    with pytest.raises(ValueError, match='duplicate JSON key'):
        build_evidence_pack_from_files(manifest, bundle)
    manifest.write_text('{"manifest_version": "1.1"}', encoding='utf-8')
    bundle.write_text('{"bundle_version": "0.2.0", "status": "a", "status": "b"}', encoding='utf-8')
    with pytest.raises(ValueError, match='duplicate JSON key'):
        build_evidence_pack_from_files(manifest, bundle)
