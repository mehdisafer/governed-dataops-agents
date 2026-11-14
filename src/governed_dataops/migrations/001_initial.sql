CREATE TABLE IF NOT EXISTS targets (
 target_id TEXT PRIMARY KEY, environment TEXT NOT NULL CHECK(environment IN ('dev','staging','prod')),
 scope TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0 CHECK(revision>=0),
 source_schema INTEGER NOT NULL, accepted_schema INTEGER NOT NULL,
 transient_failure INTEGER NOT NULL DEFAULT 0, freshness_lag_seconds INTEGER NOT NULL DEFAULT 0,
 batch_id TEXT NOT NULL, batch_status TEXT NOT NULL, pending_delivery INTEGER NOT NULL DEFAULT 1,
 policy_version TEXT NOT NULL DEFAULT '1.0', scenario TEXT NOT NULL,
 inject_log INTEGER NOT NULL DEFAULT 0, evidence_complete INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS source_rows (
 target_id TEXT NOT NULL REFERENCES targets(target_id), row_id INTEGER NOT NULL,
 amount INTEGER NOT NULL, valid INTEGER NOT NULL, PRIMARY KEY(target_id,row_id)
);
CREATE TABLE IF NOT EXISTS curated_rows (
 target_id TEXT NOT NULL REFERENCES targets(target_id), row_id INTEGER NOT NULL,
 batch_id TEXT NOT NULL, amount INTEGER NOT NULL, PRIMARY KEY(target_id,row_id)
);
CREATE TABLE IF NOT EXISTS quarantine_rows (
 target_id TEXT NOT NULL REFERENCES targets(target_id), row_id INTEGER NOT NULL,
 amount INTEGER NOT NULL, reason TEXT NOT NULL, PRIMARY KEY(target_id,row_id)
);
CREATE TABLE IF NOT EXISTS evidence (
 evidence_id TEXT PRIMARY KEY, target_id TEXT NOT NULL REFERENCES targets(target_id),
 revision INTEGER NOT NULL, body_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS evidence_target_revision ON evidence(target_id,revision);
CREATE TABLE IF NOT EXISTS incidents (
 incident_id TEXT PRIMARY KEY, event_id TEXT NOT NULL UNIQUE, target_id TEXT NOT NULL,
 body_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'received', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS incident_events (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT, incident_id TEXT NOT NULL REFERENCES incidents(incident_id),
 phase TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS incident_event_order ON incident_events(incident_id,sequence);
CREATE TABLE IF NOT EXISTS approvals (
 approval_hash TEXT PRIMARY KEY, plan_hash TEXT NOT NULL, incident_id TEXT NOT NULL,
 body_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS approvals_plan ON approvals(plan_hash);
CREATE TABLE IF NOT EXISTS effect_ledger (
 idempotency_key TEXT PRIMARY KEY, target_id TEXT NOT NULL REFERENCES targets(target_id),
 incident_id TEXT NOT NULL, plan_hash TEXT NOT NULL, action_index INTEGER NOT NULL,
 result_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS effect_incident ON effect_ledger(incident_id);
