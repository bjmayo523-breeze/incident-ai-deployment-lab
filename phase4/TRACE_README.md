# ACT-013 / ADR-004 — offline synthetic policy/trace proof

## ACT-014 bounded P1 pre-model isolation correction (2026-10-20)

**Disposition: genuine pre-model context exposure in the original synthetic runner.** Previously, `model_exposed_source_ids` was populated after the access/scope gate but **before** source freshness, integrity, runbook status, and unsafe-instruction eligibility. Thus it included the rejected P1 source. This was not merely a misnamed audit field. The corrected runner retains the rejected ID only in audit/eligibility outputs and constructs the *simulated* model context after eligibility.

**Corrected stage order:** audit-only candidate intake -> pre-retrieval access gate -> access-limited candidate rerank -> pre-model provenance/integrity/status/freshness/untrusted-instruction eligibility -> simulated model-context assembly from approved sources only -> independent post-model proposal/citation validation -> read-tool budgets and optional approval dry run -> deterministic decision/audit. No actual model is called.

**Trace fields (do not conflate their audiences):**

| Field | Meaning / audience |
| --- | --- |
| `retrieved_candidate_ids` | Input retrieval order in the **audit**; may include blocked IDs and is **not** model input. |
| `access_rejected_source_ids` | Audit-only rejection before reranking/model-context exposure for tenant, service or source permission. |
| `eligibility_rejected_source_ids` | Audit-only rejection after authorization for freshness, provenance/integrity, runbook status, service fit, or annotated unsafe instructions. |
| `actual_model_context_source_ids` | IDs in the only **simulated** context payload that would go to a model. Superset of eligible ranked runbooks may include separately eligible telemetry; no rejected source can be included. |
| `model_context_sources` | Exact synthetic `snapshot_id`, `version`, timestamps, source, and `text` comprising that hypothetical model payload; excludes rejected content. |
| `post_model_cited_source_ids` | Fixture-supplied proposal citations. **Untrusted model output**, not proof the model saw a referenced source. |
| `post_model_citation_rejected_source_ids` | Citations independently rejected after the proposal because they do not resolve to the eligible assembled context. |
| `source_eligibility` and `audit_events` | Reviewer-only provenance/rejection reasoning and explicit control chronology. |

The P1 fixture is **unchanged**. `RB-CHK-OLD@v1` is still retrieved and remains auditable as rejected for source age, untrusted-instruction annotation, and ID/version mismatch (`@v1` versus declared `v3`); it is not in the model-context IDs **or text**, while its model-proposed citation is rejected. The fixture's original simulated proposal remains intentionally adversarial: a forged citation can be emitted whether or not a model was exposed to the source. Pre-model exclusion and post-model citation checking remain independent controls.

`python .\phase4\proof_runner.py verify --out .\phase4\evidence\ACT-014-policy-trace-2026-10-20.jsonl` replays seven unchanged P0–P6 inputs and now asserts P1's retrieved/rejected audit, three exclusion reasons, context ID/text absence, post-model citation rejection, pipeline stage order, blocked decision, and zero writes, as well as all prior cross-case safety invariants. The runner's output policy version is `ADR-004/offline-v1.1-p1-isolation`, while input fixtures retain their frozen `ADR-004/offline-v1` version so the learner's earlier diagnoses and input evidence remain reproducible. The original trace and commit are **not** overwritten.

**Host patch safety:** This release contains only updated `phase4/proof_runner.py`, `phase4/TRACE_README.md`, and a *new* corrected `phase4/evidence/ACT-014-policy-trace-2026-10-20.jsonl` file. Copy only after inspecting your `gate04-ai-systems` branch and verifying the runner's original SHA-256 `a7ccd60f6ccc3c6c6c7eda49db964e3621845fe5dd6c20df2aaeae4621c5d1a9`. Do not overwrite a modified runner; review differences first. Do not replace `.git`, Phase-1/2/3 files, existing P0/P1 observations, or the pre-remediation ACT-013 evidence trace. Git commit/push on Barry's existing branch is required for durable host commit evidence; the architect sandbox cannot access the private remote.

---

**Scope: IMPLEMENTED AND ARCHITECT-TESTED (synthetic only).** This additive `phase4/` folder simulates evidence access, relevance order, deterministic eligibility, an allowlisted read-only tool gateway, bounded investigation, proposal validation, degraded/abstention, and an application-controlled pre-execution **dry run**. No network requests, model calls, embeddings, SQLite writes, ServiceNow writes, Datadog calls or production credentials. No live AI/RAG benchmark or gate-readiness advancement.

## Important repository boundary

This ZIP contains **only** the approved `phase4/` overlay. It is deliberately **not** an older lab snapshot or a replacement Git repository. The canonical development copy has Phase-3 SQL/runbooks and Git history that the Architect could not inspect through the connected private GitHub scope. Install this folder onto your **existing up-to-date** local repository / `gate03-data-fluency` lineage, never replace existing `data/`, `integration-client/`, `mock-servicenow/`, `mock-datadog/`, `compose.yaml`, `.git/`, or Phase-3 files. Do not run `git init` or force-push.

All commands below use **Windows PowerShell**. From a shell opened at your existing lab repository root, check:

```powershell
git status --short --branch
git branch --show-current
git log --oneline -3
Get-ChildItem -Name
python --version
```

Your working tree should be clean or you should first consciously save any pending Phase-3 changes **without overwriting them**. Do not blindly reset, stash, checkout, or copy over existing files. If your current branch has Phase-3 work, branch from it:

```powershell
git switch -c gate04-ai-systems
```

To install from the delivered `gate04-act013-phase4-overlay.zip` (adjust the ZIP location):

```powershell
$Archive = Join-Path $HOME 'Downloads\gate04-act013-phase4-overlay.zip'
$Staging = Join-Path $env:TEMP 'gate04-act013-stage'
New-Item -ItemType Directory -Path $Staging -Force | Out-Null
Expand-Archive -LiteralPath $Archive -DestinationPath $Staging -Force
if (Test-Path '.\phase4') { throw 'Existing phase4 folder detected; inspect and merge manually. No overwrite performed.' }
Copy-Item -LiteralPath (Join-Path $Staging 'phase4') -Destination '.\phase4' -Recurse
```

If PowerShell reports no `python`, use `py -3` in place of `python` in all subsequent commands. No packages are required.

## Blinded learner workflow — FIRST, before any policy answer

The seven case IDs are **P0–P6**. Their fault/outcome mapping is intentionally **not documented here**. Do **not** inspect `phase4/fixtures/*.json` or `proof_runner.py` source, or ask for the reviewer trace, before your first diagnosis. The observable trace contains evidence, not the policy verdict. The mentor can choose the case order.

```powershell
python .\phase4\proof_runner.py observe P0
```

Repeat for whichever case the mentor selects (`P0` to `P6`). **Before** using the reviewer commands, record your initial assessment: the likely trust/data/action boundary; evidence with source IDs, versions and timestamps; what remains unverified; the safe outcome; and what you would challenge in engineering's design. The acceptance minimum is two blinded learner-owned first diagnoses, though the mentor may ask for all seven. Do not repeat the prior four-round conceptual ADR defense.

After the initial attempt **for one case**, the mentor may disclose that case's full deterministic result:

```powershell
python .\phase4\proof_runner.py review P0
```

For the complete post-attempt architectural verification run (mentor-controlled; output reveals all results):

```powershell
$Output = Join-Path $env:TEMP 'gate04-policy-traces.jsonl'
python .\phase4\proof_runner.py verify --out $Output
Get-FileHash -Algorithm SHA256 $Output
```

Do not use `verify` until the remaining cases have each received an initial learner attempt, or the mentor has a plan to keep undisclosed case answers hidden. Running `verify` prints a PASS summary, but the JSONL file is **not blinded**; `review` prints one case in full.

## Observable architecture / verification

Each full reviewer trace includes immutable fixture input SHA-256, source snapshot IDs and provenance, as-of/observed/retrieved timestamps, rank order **after** access filtering, eligibility decisions and reason codes, attempted tool contracts, bounded call/round/time/token/cost/depth counters, proposal validation, evidence refs, review/approval separation, TOCTOU dry-run status, policy version, and an ordered audit log. The clock is frozen inside each fixture so an identical run yields identical bytes and SHA-256. Real wall-clock/model-token metrics are **not measured**; test token/cost values are synthetic units only.

The runner enforces read-only allowlisted tool names and strict scope/budget rules, with no incident-state mutation entry point. The model cannot set application validation or approval state. Relevance rank **cannot** override tenant, service, status, source or freshness policy. Synthetic `unsafe_instruction` flags exercise untrusted-data rejection; they do **not** demonstrate a production prompt-injection classifier. `claim_support` tags are fixture-supplied, not semantic entailment checks. Conditional incident transition is a **dry-run precondition check**, never actual execution.

## Regression and scope check — learner host

No Phase-1/2/3 paths are modified by this overlay. Before committing:

```powershell
git status --short
git diff --stat
git diff -- .\data .\integration-client .\mock-servicenow .\mock-datadog .\compose.yaml
```

Existing app regression (only if your Docker lab is available; run from its repository root):

```powershell
python .\labctl.py up
python .\labctl.py baseline
```

The returned `/context/INC-1001` contract and dependency logs must be healthy. For Phase-3, run your **existing previously accepted** incident/runbook SQLite SQL query or transform on the same database with the same known expected output; keep the executed SQL and query output as regression evidence. The connected Architect sandbox did **not** have your current Phase-3 repository, so it cannot claim this host regression passed. If Phase-3 files are missing, **stop and locate the correct current working copy**, rather than copying the old Phase-2 snapshot over them.

If everything passes, preserve a bounded commit **on your dedicated branch**:

```powershell
git add -- .\phase4
git diff --cached --stat
git commit -m 'Add offline ACT-013 policy trace proof'
git push -u origin gate04-ai-systems
```

Do not stage the generated review JSONL from `%TEMP%`. If you need rollback before commit, remove only the newly added `phase4` folder after preserving any local proof notes; after commit, return to the previously verified branch (do not force/reset history). Record the commit SHA only after an actual push succeeds.

## Mentor evidence handoff

Carry forward EV-AI-001's already mentor-passed architecture defense, with its disclosed first-round follow-ups, **without replaying it**. For each newly attempted case, record (a) case ID; (b) learner's first hypothesis and source/timestamp citations before answer exposure; (c) whether scope/eligibility/tool/approval/degraded boundaries were correctly reasoned; (d) assistance level and correction path; (e) `review` verdict and `verify` trace SHA; (f) Phase-1/2 health regression and Phase-3 SQL regression evidence on the actual host; (g) final recommendation. Do **not** assign a new EV-AI ID or alter readiness without the Readiness Evaluator. The Career Architect owns gate priority, already selected in canonical state; market `active_campaign` continues.
