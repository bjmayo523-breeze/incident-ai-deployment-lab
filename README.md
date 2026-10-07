# Incident AI Deployment Lab — Phase 2 Application Fluency Slice

Purpose: the minimum runnable Phase-2 lab slice for GATE-02 D1-D4. It is intentionally small: three Python services, Docker Compose, startup/runtime configuration, structured logs, three deterministic seeded faults, and a bounded Git change path.

## Boundaries

- `integration-client -> mock-servicenow`
- `integration-client -> mock-datadog`

The integration client preserves the Phase-1 normalized context contract:

```json
{
  "incident_id": "INC-1001",
  "service": "checkout-api",
  "symptoms": [],
  "dependencies": [],
  "recent_changes": [],
  "similar_incidents": [],
  "runbook_refs": [],
  "evidence_quality": "unknown"
}
```

## Prerequisites

- Docker Desktop or Docker Engine with Compose v2 (`docker compose`)
- Python 3.10+ for `labctl.py` (optional; raw Compose commands also work)
- Git
- ports 8000, 8001, and 8002 free

## Healthy baseline

```bash
python labctl.py up
python labctl.py baseline
```

Application behavior check:

```bash
curl http://localhost:8000/context/INC-1001
```

Evidence commands:

```bash
docker compose --env-file config/lab.env ps
docker compose --env-file config/lab.env logs --tail 100 integration-client
docker compose --env-file config/lab.env logs --tail 100 mock-servicenow mock-datadog
```

A healthy baseline requires more than three running containers: the context request must succeed and logs must show successful outbound calls to both dependencies.

## Runtime configuration lifecycle

`config/lab.env` is the tracked source for integration-client runtime values. Compose injects those values into the integration-client container when it is created. `integration-client/app.py` loads them at process startup. Therefore a startup-loaded value is not effective in an already running client until that client is recreated/restarted.

Key settings:

- `REQUEST_TIMEOUT_SECONDS`
- `SERVICENOW_URL`
- `DATADOG_URL`
- `LAB_BEARER_TOKEN`

For a client-only config change:

```bash
python labctl.py restart-client
```

Then verify the effective startup configuration and observed behavior in integration-client logs.

## Seeded GATE-02 faults

The learner-facing activation interface intentionally uses opaque IDs. Diagnose from runtime evidence before inspecting the override file.

```bash
python labctl.py fault F1
python labctl.py fault F2
python labctl.py fault F3
```

Run one fault at a time. Return to healthy baseline between attempts:

```bash
python labctl.py reset
```

Do not treat the fault override source as the first diagnostic step during D4. Use service/container state, application behavior, and logs first.

## Bounded Git change path for D3

The lowest-risk tracked path is `config/lab.env`. Example learner workflow:

```bash
git status
git diff -- config/lab.env
# edit one non-secret runtime value
git diff -- config/lab.env
python labctl.py restart-client
# verify runtime effect
git restore config/lab.env
python labctl.py restart-client
```

The deployment impact is bounded to the integration-client when changing a client-owned startup-loaded setting. Rollback is restoring the tracked file and recreating only the consuming service.

## Scope guard

This is not production application engineering. No database, queue, cache, Kubernetes, framework, CI/CD, or cloud deployment is added because none is required to prove GATE-02 D1-D4.
