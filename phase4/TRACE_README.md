# ACT-013 / ADR-004 — offline synthetic policy/trace proof

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
