# Phase-2 Architect Validation

## Acceptance coverage

- Three independent runtime services exist: `mock-servicenow`, `mock-datadog`, and `integration-client`.
- The integration client preserves the Phase-1 normalized incident-context contract.
- Client-owned runtime configuration is injected through `config/lab.env` and loaded at process startup.
- Structured logs expose startup, effective non-secret configuration, outbound dependency calls, dependency success/failure, and timeout/error behavior.
- Healthy application behavior is testable through `/context/INC-1001`; container/process state alone is not treated as health proof.
- Three opaque deterministic fault activations exist (`F1`, `F2`, `F3`) and are intended to be diagnosed from state, behavior, logs, and configuration evidence before corrective guidance.
- `config/lab.env` supplies a bounded Git-tracked D3 change path with a service-scoped deployment impact and rollback path.

## Validation performed by the Deployment Lab Architect

The service code was executed as three independent local processes in the build sandbox. The following checks passed:

1. Healthy baseline returned HTTP 200 and the expected Phase-1 normalized context keys.
2. Fault activation F1 produced deterministic observable failure evidence.
3. Fault activation F2 produced deterministic startup-failure evidence.
4. Fault activation F3 produced deterministic timeout/runtime evidence.
5. Structured logs were present across the request path.
6. `compose.yaml` and all three override YAML files parsed successfully.
7. A bounded timeout configuration edit was inspected with `git diff`, then rolled back with `git restore`; the working tree returned clean.

## Container-runtime validation constraint

Docker is not installed in the build sandbox, so Docker Compose itself could not be executed here. The Compose/container path is therefore configuration-validated rather than container-runtime-validated by the architect. Formal GATE-02 D1 is the learner-owned proof that the packaged Compose stack runs on the learner host.

This constraint does not award or imply any readiness change.
