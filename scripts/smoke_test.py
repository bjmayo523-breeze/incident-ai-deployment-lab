import json
import urllib.request

with urllib.request.urlopen("http://localhost:8000/context/INC-1001", timeout=5) as resp:
    payload = json.load(resp)
assert payload["incident_id"] == "INC-1001"
assert payload["service"] == "checkout-api"
for key in ["symptoms", "dependencies", "recent_changes", "similar_incidents", "runbook_refs", "evidence_quality"]:
    assert key in payload, key
print(json.dumps(payload, indent=2))
