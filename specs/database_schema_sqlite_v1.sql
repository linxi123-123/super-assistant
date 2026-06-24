-- SQLite schema v1 for the personal strategic advisor loop.
-- This schema persists the tested V1 loop, not a generic CRUD backend.

PRAGMA foreign_keys = ON;

-- schema_version: records the current local persistence schema version.
CREATE TABLE IF NOT EXISTS schema_version (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  version TEXT NOT NULL,
  created_at TEXT NOT NULL
);

-- events: raw event layer in the advisor loop.
-- Loop: user/manual sensing -> raw event.
CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  source TEXT NOT NULL,
  event_type TEXT NOT NULL,
  content TEXT NOT NULL,
  related_phase TEXT,
  related_goal TEXT,
  related_project TEXT,
  importance_score REAL NOT NULL DEFAULT 0,
  confidence REAL NOT NULL DEFAULT 0,
  evidence TEXT,
  raw_input TEXT
);

-- candidate_memories: memory candidates extracted from events.
-- Loop: raw event -> candidate memory.
CREATE TABLE IF NOT EXISTS candidate_memories (
  id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  memory_type TEXT NOT NULL,
  content TEXT NOT NULL,
  evidence TEXT,
  confidence REAL NOT NULL DEFAULT 0,
  importance_score REAL NOT NULL DEFAULT 0,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'candidate',
  FOREIGN KEY (event_id) REFERENCES events(id)
);

-- personal_model_hypotheses: dynamic personal model hypotheses.
-- Loop: memories/events/feedback -> dynamic personal model.
CREATE TABLE IF NOT EXISTS personal_model_hypotheses (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  hypothesis_key TEXT NOT NULL,
  content TEXT NOT NULL,
  evidence TEXT,
  counter_evidence TEXT,
  confidence REAL NOT NULL DEFAULT 0,
  validation_plan TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  related_event_id TEXT,
  FOREIGN KEY (related_event_id) REFERENCES events(id)
);

-- signals: meaningful signals derived from events, memory, and model context.
-- Loop: dynamic model/current phase -> signal recognition.
CREATE TABLE IF NOT EXISTS signals (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  signal_type TEXT NOT NULL,
  description TEXT NOT NULL,
  evidence TEXT,
  related_event_id TEXT,
  related_phase TEXT,
  related_goal TEXT,
  importance_score REAL NOT NULL DEFAULT 0,
  urgency_score REAL NOT NULL DEFAULT 0,
  actionability_score REAL NOT NULL DEFAULT 0,
  confidence REAL NOT NULL DEFAULT 0,
  interrupt_score REAL NOT NULL DEFAULT 0,
  recommended_action TEXT,
  counter_argument TEXT,
  touch_required INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'open',
  FOREIGN KEY (related_event_id) REFERENCES events(id)
);

-- touchpoints: advisor reminders/proactive contact generated from signals.
-- Loop: signal -> proactive touchpoint.
CREATE TABLE IF NOT EXISTS touchpoints (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  signal_id TEXT NOT NULL,
  message TEXT NOT NULL,
  reason TEXT,
  phase_relation TEXT,
  counter_argument TEXT,
  recommended_action TEXT,
  consequence_if_ignored TEXT,
  delivery_status TEXT NOT NULL DEFAULT 'created',
  user_response TEXT,
  FOREIGN KEY (signal_id) REFERENCES signals(id)
);

-- user_feedback: explicit user feedback on touchpoints, memories, hypotheses, or actions.
-- Loop: touchpoint/output -> user feedback.
CREATE TABLE IF NOT EXISTS user_feedback (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  feedback_type TEXT NOT NULL,
  feedback_note TEXT,
  accuracy_score REAL,
  usefulness_score REAL
);

-- outcomes: result tracking for signals/actions/touchpoints.
-- Loop: recommendation/action -> outcome tracking.
CREATE TABLE IF NOT EXISTS outcomes (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  related_action TEXT,
  related_signal_id TEXT,
  expected_result TEXT,
  actual_result TEXT,
  outcome_status TEXT NOT NULL DEFAULT 'pending',
  review_note TEXT,
  FOREIGN KEY (related_signal_id) REFERENCES signals(id)
);

-- model_revisions: audit history of model corrections.
-- Loop: feedback/outcome -> model revision.
CREATE TABLE IF NOT EXISTS model_revisions (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  hypothesis_id TEXT NOT NULL,
  feedback_id TEXT,
  old_confidence REAL,
  new_confidence REAL,
  revision_reason TEXT NOT NULL,
  revision_type TEXT NOT NULL,
  FOREIGN KEY (hypothesis_id) REFERENCES personal_model_hypotheses(id),
  FOREIGN KEY (feedback_id) REFERENCES user_feedback(id)
);

-- test_runs: scored test batch records.
-- Loop QA: records whether advisor-loop tests remain valid after persistence changes.
CREATE TABLE IF NOT EXISTS test_runs (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  test_name TEXT NOT NULL,
  total_cases INTEGER NOT NULL DEFAULT 0,
  average_score REAL NOT NULL DEFAULT 0,
  signal_score REAL NOT NULL DEFAULT 0,
  counter_alignment_score REAL NOT NULL DEFAULT 0,
  passed INTEGER NOT NULL DEFAULT 0,
  report_path TEXT
);

-- test_cases: individual case scores for audit.
-- Loop QA: preserves detailed scoring evidence.
CREATE TABLE IF NOT EXISTS test_cases (
  id TEXT PRIMARY KEY,
  test_run_id TEXT NOT NULL,
  input_text TEXT NOT NULL,
  event_understanding_score REAL NOT NULL DEFAULT 0,
  memory_extraction_score REAL NOT NULL DEFAULT 0,
  model_hypothesis_score REAL NOT NULL DEFAULT 0,
  signal_recognition_score REAL NOT NULL DEFAULT 0,
  advisor_touch_score REAL NOT NULL DEFAULT 0,
  counter_alignment_score REAL NOT NULL DEFAULT 0,
  total_score REAL NOT NULL DEFAULT 0,
  notes TEXT,
  FOREIGN KEY (test_run_id) REFERENCES test_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_candidate_memories_event ON candidate_memories(event_id);
CREATE INDEX IF NOT EXISTS idx_hypotheses_key ON personal_model_hypotheses(hypothesis_key);
CREATE INDEX IF NOT EXISTS idx_signals_event ON signals(related_event_id);
CREATE INDEX IF NOT EXISTS idx_signals_touch_required ON signals(touch_required);
CREATE INDEX IF NOT EXISTS idx_touchpoints_signal ON touchpoints(signal_id);
CREATE INDEX IF NOT EXISTS idx_feedback_target ON user_feedback(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_signal ON outcomes(related_signal_id);
CREATE INDEX IF NOT EXISTS idx_model_revisions_hypothesis ON model_revisions(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_test_cases_run ON test_cases(test_run_id);

