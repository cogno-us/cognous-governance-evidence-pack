"""C8 trace projection of explicitly retained source records; no authority."""
from __future__ import annotations
from typing import Any

class C8EvidenceError(ValueError):
    pass

ALLOWED_RECORD_TYPES=frozenset({"execution_claims_v1","authority_grants_v1","authority_approvals_v1","authority_policies_v1","local_stop_event"})

def project_c8_lineage(bundle:dict[str,Any])->dict[str,Any]:
    if bundle.get("bundle_version")!="0.2.0":
        raise C8EvidenceError("unsupported Replay version")
    reports=bundle.get("import_reports")
    if not isinstance(reports,list) or len(reports)!=1:
        raise C8EvidenceError("exactly one import report required")
    profile=reports[0].get("adapter_profile","")
    if profile!="c8-retained-sqlite-and-explicit-stop/0.1":
        raise C8EvidenceError("unsupported C8 profile")
    sem=bundle.get("semantics",{})
    if sem.get("external_effect_execution") is not False or sem.get("independent_effect_verification") is not False:
        raise C8EvidenceError("Replay cannot authorize or independently attest")
    rows=bundle.get("records")
    if not isinstance(rows,list):raise C8EvidenceError("missing retained records")
    status=bundle.get("status")
    findings=reports[0].get("findings",[])
    if not isinstance(findings,list):
        raise C8EvidenceError("import report findings must be an array")
    report_complete=reports[0].get("complete") is True and not findings
    if status not in ("reconstruction_complete","reconstruction_partial","incomplete","redacted"):
        raise C8EvidenceError("unknown reconstruction completeness")
    if status=="reconstruction_complete" and not report_complete:
        raise C8EvidenceError("bundle status claims completeness its import report does not show")
    ids=set()
    for r in rows:
        if not isinstance(r,dict):
            raise C8EvidenceError("duplicate or invalid source identity")
        rid=r.get("record_id")
        if not isinstance(rid,str) or not rid or rid in ids:
            raise C8EvidenceError("duplicate or invalid source identity")
        if r.get("record_type") not in ALLOWED_RECORD_TYPES:
            raise C8EvidenceError("unsupported C8 source record type")
        data,identifiers=r.get("data"),r.get("identifiers",{})
        if not isinstance(data,dict) or not isinstance(identifiers,dict):
            raise C8EvidenceError("source record data and identifiers must be objects")
        for key,value in identifiers.items():
            if not isinstance(key,str) or not isinstance(value,str) or str(data.get(key))!=value:
                raise C8EvidenceError("source record identifier contradicts its data")
        ids.add(rid)
    return {"transformation_version":"agep-c8-lineage/0.1",
       "source_bundle_id":bundle.get("bundle_id"),
       "source_records":rows,
       "source_findings":reports[0].get("findings",[]),
       "reconstruction_status":status,
       "report_supports_complete":report_complete,
       "source_asserted_metadata":bundle.get("metadata",{}),
       "independent_provenance_verification":False,
       "current_execution_authority":"not_provided",
       "stop_authority":"not_provided",
       "non_authorizing":True}
