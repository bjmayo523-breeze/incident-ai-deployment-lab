SELECT
    incident_runbooks.relationship_type,
    runbooks.runbook_id,
    runbooks.title,
    runbooks.version,
    runbooks.last_reviewed_at,
    runbooks.status,
    runbooks.service AS runbook_service,
    incidents.incident_id,
    incidents.service AS incident_service
FROM incidents
JOIN incident_runbooks
    ON incidents.incident_id = incident_runbooks.incident_id
JOIN runbooks
    ON runbooks.runbook_id = incident_runbooks.runbook_id
WHERE incidents.incident_id = 'INC-1002'
  AND incident_runbooks.relationship_type = 'candidate';

