INSERT INTO incidents
(incident_id, service, severity, status, opened_at, resolved_at, summary)
VALUES
('INC-1001', 'checkout-api', 'SEV2', 'resolved',
 '2026-09-15T10:15:00Z', '2026-09-15T11:05:00Z',
 'Checkout requests timing out against a downstream dependency'),

('INC-1002', 'checkout-api', 'SEV2', 'investigating',
 '2026-10-10T14:30:00Z', NULL,
 'Elevated checkout latency and intermittent failures'),

('INC-1003', 'payments-api', 'SEV1', 'resolved',
 '2026-08-20T08:00:00Z', '2026-08-20T09:25:00Z',
 'Payment authorization failures after dependency change'),

('INC-1004', 'checkout-api', 'SEV3', 'resolved',
 '2026-07-05T16:10:00Z', '2026-07-05T16:40:00Z',
 'Incorrect checkout health status reported');

INSERT INTO runbooks
(runbook_id, service, title, version, last_reviewed_at, status)
VALUES
('RB-CHK-001', 'checkout-api',
 'Checkout Dependency Timeout', 3, '2026-09-01', 'active'),

('RB-CHK-002', 'checkout-api',
 'Legacy Checkout Rollback', 1, '2024-02-15', 'active'),

('RB-PAY-001', 'payments-api',
 'Payment Dependency Failure', 2, '2026-08-01', 'active'),

('RB-OBS-001', 'checkout-api',
 'Checkout Health Verification', 2, '2026-06-15', 'active');

INSERT INTO incident_runbooks
(incident_id, runbook_id, relationship_type)
VALUES
('INC-1001', 'RB-CHK-001', 'used'),
('INC-1001', 'RB-CHK-002', 'referenced'),
('INC-1002', 'RB-CHK-001', 'candidate'),
('INC-1002', 'RB-OBS-001', 'candidate'),
('INC-1003', 'RB-PAY-001', 'used'),
('INC-1004', 'RB-OBS-001', 'used');
