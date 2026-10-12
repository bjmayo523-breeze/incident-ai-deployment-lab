PRAGMA foreign_keys = ON;

CREATE TABLE incidents (
    incident_id TEXT PRIMARY KEY,
    service TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    resolved_at TEXT,
    summary TEXT NOT NULL
);

CREATE TABLE runbooks (
    runbook_id TEXT PRIMARY KEY,
    service TEXT NOT NULL,
    title TEXT NOT NULL,
    version INTEGER NOT NULL,
    last_reviewed_at TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE incident_runbooks (
    incident_id TEXT NOT NULL,
    runbook_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    PRIMARY KEY (incident_id, runbook_id),
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id),
    FOREIGN KEY (runbook_id) REFERENCES runbooks(runbook_id)
);
