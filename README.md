# Incident AI Deployment Lab

I built this lab to study a practical incident-management question: when should an AI-assisted workflow offer a recommendation, and when should it stop?

The project uses mock services and synthetic incident data. It focuses on integration, application behavior, evidence quality, and human decision authority. It is not a production incident assistant.

## Project status

| Phase | Status | Where to find it |
| --- | --- | --- |
| 1. Integration fluency | Complete | [`main`](https://github.com/bjmayo523-breeze/incident-ai-deployment-lab/tree/main) |
| 2. Application fluency | Complete | [`main`](https://github.com/bjmayo523-breeze/incident-ai-deployment-lab/tree/main) |
| 3. Data fluency | Complete | [`gate03-data-fluency`](https://github.com/bjmayo523-breeze/incident-ai-deployment-lab/tree/gate03-data-fluency) |
| 4. AI systems fluency | Complete for the offline policy scope | [`gate04-ai-systems`](https://github.com/bjmayo523-breeze/incident-ai-deployment-lab/tree/gate04-ai-systems) |
| 5. AI evaluation fluency | Evaluation package prepared; learner work pending | Not yet published in this repository |

`main` remains the runnable Phase 2 application. Later phases live on separate branches. This README describes the entire project; it does not imply all phases have been merged into `main`.

## Why I built it

Incident teams need information quickly. They also need to know when evidence is too weak to support a claim. An AI assistant must respect those limits.

I use this lab to practice system diagnosis and deployment decisions. Each phase gives me a design to test and evidence to review. Some implementation work used AI assistance. The focus is understanding system behavior, challenging designs, and deciding when a workflow is safe to use.

## Phase 1–2: integration and application behavior

The runnable application has three Python services:

```text
mock-servicenow  ---->  integration-client  <----  mock-datadog
                              |
                     normalized incident context
```

The integration client calls both dependencies. The mock services do not call one another.

The lab covers Docker Compose, runtime configuration, structured logs, and three seeded faults. A healthy container is not enough. The context request must succeed, and logs must show successful dependency calls.

### Run the application

Requirements: Docker Compose v2, Python 3.10+, and Git.

```bash
git clone https://github.com/bjmayo523-breeze/incident-ai-deployment-lab.git
cd incident-ai-deployment-lab
python labctl.py up
python labctl.py baseline
```

Check `http://localhost:8000/context/INC-1001` and review the service logs.

Run one seeded fault at a time:

```bash
python labctl.py fault F1
python labctl.py reset
```

Runtime values live in `config/lab.env`. Changes to startup-loaded values require restarting or recreating the consuming client. Use `python labctl.py restart-client` and verify the effective configuration.

## Phase 3: data and retrieval

The [`gate03-data-fluency`](https://github.com/bjmayo523-breeze/incident-ai-deployment-lab/tree/gate03-data-fluency) branch contains a SQLite learning exercise. It includes synthetic incident and runbook records, relationships, joins, and candidate-runbook review queries.

This proves data reasoning within the exercise. It does not mean the database has been deployed behind the Phase 2 API.

## Phase 4: AI systems and policy boundaries

The [`gate04-ai-systems`](https://github.com/bjmayo523-breeze/incident-ai-deployment-lab/tree/gate04-ai-systems) branch contains an offline policy simulation. It is deterministic and makes no live model calls.

The runner tests:

- Access, freshness, integrity, and source eligibility before simulated model-context assembly.
- Independent validation of proposed claims and cited evidence.
- Read-only tool permissions, scope limits, and investigation budgets.
- Blocking, degraded behavior, and abstention when evidence is insufficient.
- Human review boundaries and dry-run checks without operational writes.

An earlier test exposed a source-isolation flaw in the synthetic runner. The corrected version excludes rejected evidence before assembling simulated model context. Rejected material remains visible in the audit trail.

Seven frozen synthetic cases passed the corrected verification on October 20, 2026. The run reported zero operational side effects. This does not establish production safety or model accuracy.

The accepted correction is commit [`b694954`](https://github.com/bjmayo523-breeze/incident-ai-deployment-lab/commit/b694954640e2d40898e469662b6308a5362b1540).

See the [Phase 4 trace guide](https://github.com/bjmayo523-breeze/incident-ai-deployment-lab/blob/gate04-ai-systems/phase4/TRACE_README.md) for reproducible evidence and scope details.

### Run the offline Phase 4 verification

From a fresh clone:

```bash
git fetch origin
git switch --track origin/gate04-ai-systems
python phase4/proof_runner.py verify --out local-phase4-trace.jsonl
```

This writes a local trace. It does not change the preserved evidence files.

## What the lab does not claim

- All incident and runbook records are synthetic.
- The Phase 4 runner does not invoke a live LLM or production API.
- Source checks use explicit synthetic fields, not a production prompt-injection detector.
- No autonomous remediation or production incident write is implemented.
- The phases are bounded exercises, not a unified production deployment.
- Phase 5 evaluation results are not yet demonstrated or published.

## Next: evaluation fluency

The planned Phase 5 exercise covers labeling, false positives, missed abstentions, and policy-version regressions. It will also require a defended release, hold, or rollback decision.

The Phase 5 learner package has been prepared outside GitHub. Installation and learner evidence remain pending.

*Project status verified October 25, 2026.*
