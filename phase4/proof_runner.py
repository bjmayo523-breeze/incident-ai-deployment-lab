#!/usr/bin/env python3
"""ACT-013: offline deterministic policy/trace proof. NO external I/O or incident writes.

Learner command is `observe`; `verify` reveals policy classifications and should
be run with the Technical Fluency Mentor after first attempts.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = tuple(f'P{i}' for i in range(7))
FIXTURE_POLICY = 'ADR-004/offline-v1'
POLICY = 'ADR-004/offline-v1.1-p1-isolation'
TOOLS = {'get_incident_context','get_service_health','search_runbooks','get_related_incidents'}
NEXT = {'escalate_to_service_owner','request_manual_verification','continue_read_only_investigation','close_incident'}
UNCERTAINTY = {'tentative','moderate','unknown'}
TOOL_KEYS = {
  'get_incident_context': {'incident_id'},
  'get_service_health': {'service','within_minutes'},
  'search_runbooks': {'incident_id','service','limit'},
  'get_related_incidents': {'incident_id','limit'}
}
LIMITS = {'calls':5,'rounds':2,'elapsed_ms':30000,'token_units':1600,'cost_units':50,'dependency_depth':1,'records':5}
REQUIRED_PROPOSAL = {'incident_id','hypothesis','evidence_refs','uncertainty','suggested_next_step','claim_type'}


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def age_minutes(observed, as_of):
    try:
        a=datetime.fromisoformat(as_of.replace('Z','+00:00'))
        b=datetime.fromisoformat(observed.replace('Z','+00:00'))
        if a.tzinfo is None or b.tzinfo is None: return None
        return (a-b).total_seconds()/60
    except (TypeError, ValueError, AttributeError):
        return None


def load_case(case):
    if case not in CASES: raise ValueError('Case must be one of P0..P6')
    f = ROOT/'fixtures'/f'{case}.json'
    value=json.loads(f.read_text(encoding='utf-8'))
    if value.get('case_id') != case or value.get('policy_version') != FIXTURE_POLICY:
        raise ValueError('Fixture or policy identifier mismatch')
    return value


def observable(c):
    """Synthetic evidence, with outcomes, eligibility and policy reasons withheld."""
    # Source IDs intentionally visible for trace localization; policy judgments are not.
    return {
      'case_id':c['case_id'], 'kind':'offline_synthetic_observation',
      'as_of':c['as_of'], 'incident':c['incident'],
      'requester':{'tenant':c['principal']['tenant'],'services_in_scope':c['principal']['allowed_services']},
      'retrieval_candidate_refs':c['candidate_order'],
      'source_observations':[{k:s.get(k) for k in ('id','type','service','tenant','status','source','version','observed_at','retrieved_at','rank','text')} for s in c['sources']],
      'telemetry_observation':c['telemetry'],
      'agent_requests':[{'name':r['name'],'args':r['args'],'round':r['round'],'elapsed_ms':r['elapsed_ms'],'depth':r['depth']} for r in c['tool_requests']],
      'proposed_recommendation':c['model_proposal'],
      'approval_observation':c['approval'],
      'notice':'Synthetic observations only. Diagnose before requesting validator decision. No live service data.'
    }


def read_only_tool_decisions(c, audit):
    calls=0; spent_tokens=0; spent_cost=0; reasons=[]; results=[]
    for r in c['tool_requests']:
        n=r.get('name'); a=r.get('args',{}); calls+=1
        spent_tokens+=r.get('token_units',0); spent_cost+=r.get('cost_units',0)
        why=[]
        if calls>LIMITS['calls'] or r.get('round',0)>LIMITS['rounds'] or r.get('elapsed_ms',0)>LIMITS['elapsed_ms'] or spent_tokens>LIMITS['token_units'] or spent_cost>LIMITS['cost_units'] or r.get('depth',0)>LIMITS['dependency_depth']:
            why.append('agent_budget_exceeded')
        if n not in TOOLS: why.append('tool_not_allowlisted')
        elif set(a) != TOOL_KEYS[n]: why.append('tool_argument_schema_invalid')
        else:
            if ('incident_id' in a and (not isinstance(a['incident_id'],str) or a['incident_id'] != c['incident']['id'])): why.append('incident_scope_denied')
            if ('service' in a and (not isinstance(a['service'],str) or a['service'] not in c['principal']['allowed_services'] or a['service'] not in [c['incident']['service'], *c['incident'].get('dependencies',[])])): why.append('service_scope_denied')
            if ('limit' in a and (not isinstance(a['limit'],int) or isinstance(a['limit'],bool) or not 1<=a['limit']<=LIMITS['records'])): why.append('record_limit_invalid')
            if ('within_minutes' in a and (not isinstance(a['within_minutes'],int) or isinstance(a['within_minutes'],bool) or not 1<=a['within_minutes']<=15)): why.append('within_minutes_invalid')
        allowed=not why
        audit.append({'event':'read_tool_gate','tool':n,'allowed':allowed,'reasons':sorted(set(why)), 'call_index':calls})
        results.append({'tool':n,'allowed':allowed,'reasons':sorted(set(why))})
        reasons.extend(why)
    return results, sorted(set(reasons)), {'calls_attempted':calls, 'token_units':spent_tokens,'cost_units':spent_cost, 'max_elapsed_ms':max((r.get('elapsed_ms',0) for r in c['tool_requests']),default=0), 'max_round':max((r.get('round',0) for r in c['tool_requests']),default=0)}


def evaluate(c):
    audit=[]; reasons=[]; incident=c['incident']; principal=c['principal']; asof=c['as_of']
    # Audit-only intake: candidate IDs are NOT a model payload. Keep rejected
    # IDs visible to the reviewer, never in the model-context assembly.
    retrieved_candidate_ids=list(c['candidate_order'])
    access_allowed=[]; access_rejected=[]
    for s in c['sources']:
        access_ok=(s.get('tenant')==incident['tenant']==principal['tenant'] and
          s.get('service') in principal['allowed_services'] and s.get('source') in principal['allowed_sources'])
        (access_allowed if access_ok else access_rejected).append(s)
    access_rejected_ids=sorted(s['id'] for s in access_rejected)
    audit.append({'event':'pre_retrieval_scope_gate','authorized_count':len(access_allowed),
      'excluded_count':len(access_rejected),'access_rejected_source_ids':access_rejected_ids})
    accessible_ids={s['id'] for s in access_allowed}
    ordered=[i for i in retrieved_candidate_ids if i in accessible_ids]
    ranked=[{'ref':i,'rank':next(s['rank'] for s in access_allowed if s['id']==i)} for i in ordered]
    audit.append({'event':'rerank_access_allowed_candidates_only','candidate_ids':ordered})

    # CRITICAL P1 boundary: deterministic integrity, status, freshness and
    # untrusted-instruction eligibility run BEFORE assembling model context.
    # Retain every rejected source in audit-only metadata, not model payload.
    eligibility=[]; accepted=set(); eligibility_rejected_ids=[]
    for s in access_allowed:
        why=[]
        if not s.get('provenance_valid') or not s.get('id') or not s.get('source') or not s.get('version') or not s.get('retrieved_at'):
            why.append('invalid_provenance')
        snapshot_id=s.get('id','')
        if not isinstance(snapshot_id,str) or '@' not in snapshot_id or snapshot_id.rsplit('@',1)[-1] != s.get('version'):
            why.append('snapshot_version_mismatch')
        if s.get('status') != 'active' and s['type']=='runbook': why.append('runbook_not_active')
        if s.get('unsafe_instruction') and s['type']=='runbook': why.append('untrusted_instruction_annotation')
        age=age_minutes(s.get('observed_at'),asof)
        threshold=5 if s['type']=='telemetry' else 1440
        if age is None or age<0 or age>threshold: why.append('source_stale_or_unverifiable')
        if s.get('service') not in [incident['service'], *incident.get('dependencies',[])]: why.append('service_mismatch')
        accepted_flag=not why
        if accepted_flag: accepted.add(s['id'])
        else: eligibility_rejected_ids.append(s['id'])
        eligibility.append({'snapshot_id':s['id'], 'source':s['source'],'version':s['version'],
          'observed_at':s.get('observed_at'),'retrieved_at':s.get('retrieved_at'),
          'eligible':accepted_flag,'reasons':sorted(set(why)),'rank':s.get('rank')})
    eligibility_rejected_ids=sorted(eligibility_rejected_ids)
    audit.append({'event':'pre_model_eligibility_gate','evaluated_count':len(eligibility),
      'accepted_count':len(accepted),'eligibility_rejected_source_ids':eligibility_rejected_ids})

    # The ONLY simulated model input payload is built from allowed AND eligible
    # snapshots. Telemetry is appended separately because candidate_order holds
    # ranked runbooks, whereas the context may also include telemetry evidence.
    # There is no live model call in this offline fixture runner.
    eligible_ranked_ids=[i for i in ordered if i in accepted]
    eligible_telemetry_ids=sorted(s['id'] for s in access_allowed if s['id'] in accepted
      and s['type']=='telemetry' and s['id'] not in eligible_ranked_ids)
    context_ids=eligible_ranked_ids+eligible_telemetry_ids
    by_id={s['id']:s for s in access_allowed if s['id'] in accepted}
    model_context_sources=[{'snapshot_id':i,'version':by_id[i]['version'],
      'source':by_id[i]['source'],'observed_at':by_id[i]['observed_at'],
      'retrieved_at':by_id[i]['retrieved_at'],'text':by_id[i]['text']}
      for i in context_ids]
    audit.append({'event':'model_context_constructed_after_eligibility',
      'source_ids':context_ids,'source_count':len(context_ids)})
    t=c['telemetry']; t_ref=t.get('snapshot_ref')
    if not t.get('available') or t_ref not in accepted:
        reasons.append('current_telemetry_not_verified')
    proposal=c['model_proposal']; unexpected=set(proposal)-REQUIRED_PROPOSAL
    if unexpected: reasons.append('model_authority_or_extra_fields_rejected')
    if set(proposal)&REQUIRED_PROPOSAL != REQUIRED_PROPOSAL: reasons.append('proposal_missing_required_fields')
    if (proposal.get('incident_id')!=incident['id'] or
        not isinstance(proposal.get('hypothesis'),str) or not proposal.get('hypothesis') or len(proposal.get('hypothesis',''))>500 or
        proposal.get('uncertainty') not in UNCERTAINTY or proposal.get('claim_type') not in {'dependency_suspected','recovery_verified','investigation_needed'} or proposal.get('suggested_next_step') not in NEXT or
        not isinstance(proposal.get('evidence_refs'),list) or not 1<=len(proposal['evidence_refs'])<=5):
        reasons.append('proposal_schema_or_scope_invalid')
    refs=proposal.get('evidence_refs',[])
    if not isinstance(refs,list): refs=[]
    if len(refs)!=len(set(map(str,refs))) or any(i not in context_ids for i in refs):
        reasons.append('proposal_references_ineligible_or_missing')
    if not any(proposal.get('claim_type') in s.get('claim_support',[]) for s in access_allowed if s['id'] in context_ids and s['id'] in refs):
        reasons.append('claim_not_supported_by_eligible_sources')
    if proposal.get('suggested_next_step') == 'close_incident':
        reasons.append('closure_not_supported_in_phase4')
    # Second independent defense: even if a pre-model rejected ID appears in a
    # model-originated proposal, citations must resolve to the assembled context.
    cited_source_ids=list(refs)
    cited_rejected_ids=sorted(i for i in refs if i not in context_ids)
    audit.append({'event':'post_model_citation_validation','post_model_cited_source_ids':cited_source_ids,
      'rejected_citation_source_ids':cited_rejected_ids,
      'accepted_refs':sorted(i for i in refs if i in context_ids),
      'schema_valid':not any('proposal_' in r or 'model_authority' in r for r in reasons)})
    tools, toolreasons,budget=read_only_tool_decisions(c,audit)
    reasons.extend(toolreasons)
    approval=c.get('approval'); approval_status='pending'; preexecution='not_requested'
    if approval:
        approval_status='recorded_for_dry_run' if approval.get('authorized') else 'rejected'
        if not approval.get('authorized') or not approval.get('approver'): reasons.append('unauthorized_human_approval')
        if approval.get('incident_version_at_review') != approval.get('incident_version_now') or approval.get('incident_version_now')!=incident.get('version'):
            reasons.append('preexecution_incident_version_changed')
        if (age_minutes(approval.get('evidence_observed_at'),asof) is None or age_minutes(approval.get('evidence_observed_at'),asof)>5):
            reasons.append('preexecution_evidence_stale')
        preexecution='blocked' if any(r.startswith('preexecution_') or r=='unauthorized_human_approval' for r in reasons) else 'precondition_passed_dry_run_only'
        audit.append({'event':'preexecution_revalidation_dry_run','outcome':preexecution,'actual_write_count':0})
    reasons=sorted(set(reasons))
    if any('tool_' in r or 'agent_budget_' in r or 'scope_denied' in r or r.startswith('preexecution_') or r.startswith('model_authority') or r.startswith('proposal_') or r=='claim_not_supported_by_eligible_sources' or r=='closure_not_supported_in_phase4' for r in reasons):
        status='blocked'
    elif 'current_telemetry_not_verified' in reasons: status='degraded'
    elif not any(i for i in refs if i in context_ids): status='abstain'
    else: status='validated_for_review'
    # Absolute rule: never endorse closure/current-recovery on missing current telemetry.
    safe_next_step='manual_verification' if 'current_telemetry_not_verified' in reasons else ('manual_review' if status=='blocked' else proposal.get('suggested_next_step','manual_review'))
    audit.append({'event':'decision_finalized','result':status,'reason_codes':reasons,'policy_version':POLICY,'writes':0})
    report={
      'case_id':c['case_id'], 'kind':'synthetic_offline_policy_trace','policy_version':POLICY,
      'as_of':asof,'input_sha256':hashlib.sha256(canonical(c).encode()).hexdigest(),
      'incident_id':incident['id'], 'incident_version':incident['version'],
      'retrieved_candidate_ids':retrieved_candidate_ids,
      'access_rejected_source_ids':access_rejected_ids,
      'eligibility_rejected_source_ids':eligibility_rejected_ids,
      'actual_model_context_source_ids':context_ids,
      'model_context_sources':model_context_sources,
      'post_model_cited_source_ids':cited_source_ids,
      'post_model_citation_rejected_source_ids':cited_rejected_ids,
      'access_excluded_count':len(access_rejected),
      'retrieval_rank_order':ranked,'source_eligibility':eligibility,
      'tool_trace':tools,'budgets':budget,
      'validation_status':status, 'validation_reasons':reasons,
      'safe_next_step':safe_next_step,'approval_status':approval_status,
      'preexecution_dry_run':preexecution,'execution_status':'no_write_path_in_phase4',
      'side_effect_count':0,'audit_events':audit,
      'decision_id':hashlib.sha256((c['case_id']+canonical(c)+POLICY).encode()).hexdigest()[:20]
    }
    return report


def self_verify(reports, cases):
    failures=[]
    if len(reports)!=7 or sorted(x['case_id'] for x in reports)!=list(CASES): failures.append('missing_cases')
    for r,c in zip(reports,cases):
        if canonical(r)!=canonical(evaluate(c)): failures.append('non_deterministic_'+c['case_id'])
        if r['side_effect_count']!=0 or r['execution_status']!='no_write_path_in_phase4': failures.append('side_effect_'+c['case_id'])
        visible=set(r['actual_model_context_source_ids']); principal=c['principal']; src={s['id']:s for s in c['sources']}
        if any(src[id]['tenant']!=principal['tenant'] or src[id]['service'] not in principal['allowed_services'] or src[id]['source'] not in principal['allowed_sources'] for id in visible): failures.append('scope_leak_'+c['case_id'])
        eligible={s['snapshot_id'] for s in r['source_eligibility'] if s['eligible']}
        if not visible.issubset(eligible): failures.append('ineligible_model_context_'+c['case_id'])
        if visible.intersection(r['access_rejected_source_ids']) or visible.intersection(r['eligibility_rejected_source_ids']): failures.append('rejected_model_context_'+c['case_id'])
        if [s['snapshot_id'] for s in r['model_context_sources']] != r['actual_model_context_source_ids']: failures.append('context_payload_id_mismatch_'+c['case_id'])
        if any(s['text'] != src[s['snapshot_id']]['text'] for s in r['model_context_sources']): failures.append('context_payload_content_mismatch_'+c['case_id'])
        if r['post_model_citation_rejected_source_ids'] != sorted(i for i in r['post_model_cited_source_ids'] if i not in visible): failures.append('post_model_citation_gate_'+c['case_id'])
        if r['validation_status']=='validated_for_review':
            if r['validation_reasons'] or not set(c['model_proposal'].get('evidence_refs',[])).issubset(visible):
                failures.append('invalid_validation_'+c['case_id'])
        if 'current_telemetry_not_verified' in r['validation_reasons'] and r['validation_status']=='validated_for_review': failures.append('stale_telemetry_accepted_'+c['case_id'])
        if r['preexecution_dry_run']=='blocked' and any(x.get('writes',0)!=0 for x in r['audit_events']): failures.append('preexecution_write_'+c['case_id'])
    # Evaluator-required specific P1 regression, including stage ordering.
    p1=next(r for r in reports if r['case_id']=='P1')
    reject='RB-CHK-OLD@v1'
    reasons_for_rejected={s['snapshot_id']:s['reasons'] for s in p1['source_eligibility']}
    if reject not in p1['retrieved_candidate_ids']: failures.append('P1_retrieval_audit_missing')
    if reject not in p1['eligibility_rejected_source_ids']: failures.append('P1_eligibility_exclusion_missing')
    if not {'source_stale_or_unverifiable','untrusted_instruction_annotation','snapshot_version_mismatch'}.issubset(reasons_for_rejected.get(reject,[])):
        failures.append('P1_rejection_reason_missing')
    if reject in p1['actual_model_context_source_ids'] or any(s['snapshot_id']==reject or reject in s['text'] for s in p1['model_context_sources']):
        failures.append('P1_model_context_exposure')
    if reject not in p1['post_model_cited_source_ids'] or reject not in p1['post_model_citation_rejected_source_ids']:
        failures.append('P1_post_model_citation_not_blocked')
    if p1['validation_status']!='blocked' or 'proposal_references_ineligible_or_missing' not in p1['validation_reasons'] or p1['side_effect_count']!=0:
        failures.append('P1_unsafe_decision')
    event_order=[e['event'] for e in p1['audit_events']]
    if not (event_order.index('pre_retrieval_scope_gate') < event_order.index('pre_model_eligibility_gate') < event_order.index('model_context_constructed_after_eligibility') < event_order.index('post_model_citation_validation')):
        failures.append('P1_gate_order_invalid')
    seen={reason for r in reports for reason in r['validation_reasons']}
    required={'current_telemetry_not_verified','source_stale_or_unverifiable','untrusted_instruction_annotation','proposal_references_ineligible_or_missing','tool_not_allowlisted','agent_budget_exceeded','preexecution_incident_version_changed','preexecution_evidence_stale'}
    # Source-eligibility reason codes are distinct from proposal-level decision codes.
    source_reasons={reason for r in reports for s in r['source_eligibility'] for reason in s['reasons']}
    for reason in required:
        if reason not in seen and reason not in source_reasons:failures.append('missing_coverage_'+reason)
    if not any(r['access_excluded_count']>0 for r in reports): failures.append('no_prefilter_coverage')
    if not any(r['validation_status']=='validated_for_review' for r in reports):failures.append('no_normal_case')
    return failures


def main():
    ap=argparse.ArgumentParser(description='Offline synthetic ADR-004 trace simulator; no service calls.')
    sub=ap.add_subparsers(dest='command',required=True)
    obs=sub.add_parser('observe',help='Learner-facing observations WITHOUT decisions/answers');obs.add_argument('case',choices=CASES)
    verify=sub.add_parser('verify',help='Mentor/reviewer: full decisions and reproducibility AFTER initial learner attempts');verify.add_argument('--out',default='phase4-traces.jsonl',help='Where to write full traces (relative to cwd)')
    one=sub.add_parser('review',help='Mentor/reviewer: full single-case decision AFTER initial diagnosis');one.add_argument('case',choices=CASES)
    args=ap.parse_args()
    if args.command=='observe':print(json.dumps(observable(load_case(args.case)),indent=2,sort_keys=True));return
    if args.command=='review':print(json.dumps(evaluate(load_case(args.case)),indent=2,sort_keys=True));return
    cases=[load_case(c) for c in CASES]; reports=[evaluate(c) for c in cases]
    failures=self_verify(reports,cases)
    if failures:
        print(json.dumps({'verification':'FAILED','errors':failures},indent=2));raise SystemExit(1)
    out=Path(args.out)
    if out.is_dir(): raise SystemExit('--out must be a file')
    out.parent.mkdir(parents=True,exist_ok=True)
    output=''.join(canonical(r)+'\n' for r in reports)
    out.write_text(output,encoding='utf-8')
    print(json.dumps({'verification':'PASS','cases_verified':len(reports),'deterministic_replay':True,'side_effects':0,'fixture_time':'frozen','trace_path':str(out),'trace_sha256':hashlib.sha256(output.encode()).hexdigest(), 'caution':'Synthetic policy proof, not real RAG/model evaluation or live telemetry.'},indent=2))

if __name__=='__main__':main()
