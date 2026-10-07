import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SERVICE = "mock-servicenow"
PORT = int(os.getenv("PORT", "8001"))
EXPECTED_TOKEN = os.getenv("LAB_BEARER_TOKEN", "phase2-demo-token")
FAIL_STARTUP = os.getenv("FAIL_STARTUP", "false").lower() in {"1", "true", "yes"}

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(SERVICE)

def emit(event, **fields):
    payload = {"service": SERVICE, "event": event, **fields}
    log.info(json.dumps(payload, sort_keys=True))

if FAIL_STARTUP:
    emit("startup_failed", reason="startup_guard_triggered")
    sys.exit(12)

INCIDENTS = {
    "INC-1001": {
        "incident_id": "INC-1001",
        "service": "checkout-api",
        "symptoms": ["elevated checkout errors", "intermittent latency"],
        "recent_changes": ["checkout-api deployment v42"],
        "similar_incidents": ["INC-0988"],
        "runbook_refs": ["RB-CHECKOUT-01"],
    }
}

class Handler(BaseHTTPRequestHandler):
    def _json(self, code, body):
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self):
        return self.headers.get("Authorization") == f"Bearer {EXPECTED_TOKEN}"

    def do_GET(self):
        if self.path == "/health":
            return self._json(200, {"service": SERVICE, "status": "ok"})

        if self.path.startswith("/api/incidents/"):
            incident_id = self.path.rsplit("/", 1)[-1]
            emit("request_received", path=self.path, incident_id=incident_id)
            if not self._authorized():
                emit("request_rejected", path=self.path, status=401)
                return self._json(401, {"error": "unauthorized"})
            incident = INCIDENTS.get(incident_id)
            if not incident:
                emit("request_completed", path=self.path, status=404)
                return self._json(404, {"error": "incident_not_found"})
            emit("request_completed", path=self.path, status=200)
            return self._json(200, incident)

        return self._json(404, {"error": "not_found"})

    def log_message(self, *_):
        return

if __name__ == "__main__":
    emit("startup", port=PORT, auth_required=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
