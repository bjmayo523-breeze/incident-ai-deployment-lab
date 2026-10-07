import json
import logging
import os
import socket
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SERVICE = "integration-client"
PORT = int(os.getenv("PORT", "8000"))
SERVICENOW_URL = os.getenv("SERVICENOW_URL", "http://mock-servicenow:8001").rstrip("/")
DATADOG_URL = os.getenv("DATADOG_URL", "http://mock-datadog:8002").rstrip("/")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "2"))
LAB_BEARER_TOKEN = os.getenv("LAB_BEARER_TOKEN", "phase2-demo-token")

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(SERVICE)

def emit(event, **fields):
    payload = {"service": SERVICE, "event": event, **fields}
    log.info(json.dumps(payload, sort_keys=True))

def fetch_json(target_name, url):
    emit("outbound_request", dependency=target_name, url=url, timeout_seconds=REQUEST_TIMEOUT_SECONDS)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {LAB_BEARER_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            emit("dependency_success", dependency=target_name, status=resp.status)
            return body
    except urllib.error.HTTPError as exc:
        emit("dependency_failure", dependency=target_name, failure_type="http_error", status=exc.code)
        raise
    except (TimeoutError, socket.timeout) as exc:
        emit("dependency_failure", dependency=target_name, failure_type="timeout", timeout_seconds=REQUEST_TIMEOUT_SECONDS)
        raise exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        kind = "timeout" if isinstance(reason, (TimeoutError, socket.timeout)) else "connection_error"
        emit("dependency_failure", dependency=target_name, failure_type=kind, detail=str(reason or exc))
        raise

def build_context(incident_id):
    incident = fetch_json("mock-servicenow", f"{SERVICENOW_URL}/api/incidents/{incident_id}")
    service = incident["service"]
    health = fetch_json("mock-datadog", f"{DATADOG_URL}/api/service-health/{service}")
    context = {
        "incident_id": incident["incident_id"],
        "service": service,
        "symptoms": list(dict.fromkeys(incident.get("symptoms", []) + health.get("symptoms", []))),
        "dependencies": health.get("dependencies", []),
        "recent_changes": incident.get("recent_changes", []),
        "similar_incidents": incident.get("similar_incidents", []),
        "runbook_refs": incident.get("runbook_refs", []),
        "evidence_quality": "unknown",
    }
    emit("context_built", incident_id=incident_id, service=service)
    return context

class Handler(BaseHTTPRequestHandler):
    def _json(self, code, body):
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self._json(200, {"service": SERVICE, "status": "ok"})
        if self.path.startswith("/context/"):
            incident_id = self.path.rsplit("/", 1)[-1]
            emit("context_request", incident_id=incident_id)
            try:
                return self._json(200, build_context(incident_id))
            except Exception as exc:
                emit("context_failed", incident_id=incident_id, error_type=type(exc).__name__)
                return self._json(502, {"error": "dependency_failure", "incident_id": incident_id})
        return self._json(404, {"error": "not_found"})

    def log_message(self, *_):
        return

if __name__ == "__main__":
    emit(
        "startup",
        port=PORT,
        servicenow_url=SERVICENOW_URL,
        datadog_url=DATADOG_URL,
        request_timeout_seconds=REQUEST_TIMEOUT_SECONDS,
        auth_configured=bool(LAB_BEARER_TOKEN),
    )
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
