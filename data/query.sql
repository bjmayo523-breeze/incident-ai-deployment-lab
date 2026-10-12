-- GATE-03 D2
-- Operational question:
--
-- Write your learner-owned SQL below after stating the question

SELECT
    incidents.incident_id,
    incidents.service,
    runbooks.service,
    runbooks.title,
    runbooks.version,
    runbooks.last_reviewed_at,
    runbooks.status
FROM incidents
JOIN incident_runbooks
    ON incidents.incident_id = incident_runbooks.incident_id
JOIN runbooks
    ON incident_runbooks.runbook_id = runbooks.runbook_id
WHERE incidents.incident_id = 'INC-1002'
  AND incident_runbooks.relationship_type = 'candidate';
