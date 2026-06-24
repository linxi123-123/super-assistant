-- 个人局势军师 V1 数据库结构
-- V1 先使用结构化数据，向量检索后续再加。

CREATE TABLE user_profiles (
  user_id TEXT PRIMARY KEY,
  basic_background TEXT,
  current_city TEXT,
  career_stage TEXT,
  capability_structure TEXT,
  resource_structure TEXT,
  long_term_goals TEXT,
  values_text TEXT,
  risk_preference TEXT,
  communication_preference TEXT,
  privacy_preference TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE goals (
  goal_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  time_horizon TEXT,
  importance INTEGER NOT NULL DEFAULT 3,
  status TEXT NOT NULL DEFAULT 'active',
  success_criteria TEXT,
  failure_criteria TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE projects (
  project_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  goal_id TEXT,
  stage TEXT,
  progress TEXT,
  key_risks TEXT,
  next_action TEXT,
  related_files TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (goal_id) REFERENCES goals(goal_id)
);

CREATE TABLE events (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  source TEXT NOT NULL,
  content TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  captured_at TEXT NOT NULL,
  related_goal_id TEXT,
  related_project_id TEXT,
  related_person TEXT,
  related_file TEXT,
  importance INTEGER NOT NULL DEFAULT 3,
  confidence REAL NOT NULL DEFAULT 0.7,
  sensitivity TEXT NOT NULL DEFAULT 'P0',
  raw_reference TEXT,
  evidence_type TEXT NOT NULL DEFAULT 'manual_input',
  evidence_summary TEXT,
  processed_status TEXT NOT NULL DEFAULT 'new',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (related_goal_id) REFERENCES goals(goal_id),
  FOREIGN KEY (related_project_id) REFERENCES projects(project_id)
);

CREATE TABLE memories (
  memory_id TEXT PRIMARY KEY,
  memory_type TEXT NOT NULL,
  content TEXT NOT NULL,
  source_event_ids TEXT NOT NULL,
  evidence TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.7,
  importance INTEGER NOT NULL DEFAULT 3,
  sensitivity TEXT NOT NULL DEFAULT 'P0',
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  valid_until TEXT,
  is_expired INTEGER NOT NULL DEFAULT 0,
  counter_evidence TEXT,
  related_goal_id TEXT,
  related_project_id TEXT,
  allow_for_advice INTEGER NOT NULL DEFAULT 1,
  last_used_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (related_goal_id) REFERENCES goals(goal_id),
  FOREIGN KEY (related_project_id) REFERENCES projects(project_id)
);

CREATE TABLE personal_model_hypotheses (
  hypothesis_id TEXT PRIMARY KEY,
  content TEXT NOT NULL,
  evidence TEXT NOT NULL,
  counter_evidence TEXT,
  confidence REAL NOT NULL DEFAULT 0.6,
  validation_plan TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  source_memory_ids TEXT,
  source_signal_ids TEXT,
  last_validated_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE intelligence_items (
  intel_id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  key_change TEXT,
  relevance_to_user TEXT,
  opportunity TEXT,
  risk TEXT,
  recommended_action TEXT,
  confidence REAL NOT NULL DEFAULT 0.6,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE signals (
  signal_id TEXT PRIMARY KEY,
  signal_type TEXT NOT NULL,
  description TEXT NOT NULL,
  evidence TEXT NOT NULL,
  related_goal_id TEXT,
  related_project_id TEXT,
  importance_score REAL NOT NULL DEFAULT 0,
  urgency_score REAL NOT NULL DEFAULT 0,
  goal_relevance_score REAL NOT NULL DEFAULT 0,
  actionability_score REAL NOT NULL DEFAULT 0,
  confidence_score REAL NOT NULL DEFAULT 0,
  false_positive_risk REAL NOT NULL DEFAULT 0,
  interrupt_cost REAL NOT NULL DEFAULT 0,
  should_touch INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'open',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (related_goal_id) REFERENCES goals(goal_id),
  FOREIGN KEY (related_project_id) REFERENCES projects(project_id)
);

CREATE TABLE touchpoints (
  touch_id TEXT PRIMARY KEY,
  signal_id TEXT NOT NULL,
  message TEXT NOT NULL,
  reason TEXT NOT NULL,
  recommended_action TEXT NOT NULL,
  delivery_channel TEXT NOT NULL DEFAULT 'dashboard',
  user_response TEXT,
  result TEXT,
  feedback_status TEXT NOT NULL DEFAULT 'pending',
  outcome_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (signal_id) REFERENCES signals(signal_id)
);

CREATE TABLE actions (
  action_id TEXT PRIMARY KEY,
  goal_id TEXT,
  project_id TEXT,
  description TEXT NOT NULL,
  execution_level TEXT NOT NULL DEFAULT 'E0',
  requires_confirmation INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'pending',
  expected_result TEXT,
  completion_criteria TEXT,
  result TEXT,
  review TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (goal_id) REFERENCES goals(goal_id),
  FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE user_feedback (
  feedback_id TEXT PRIMARY KEY,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  feedback_value TEXT NOT NULL,
  feedback_note TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE outcomes (
  outcome_id TEXT PRIMARY KEY,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  expected_result TEXT,
  actual_result TEXT,
  result_status TEXT NOT NULL DEFAULT 'pending',
  review_note TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE model_revisions (
  revision_id TEXT PRIMARY KEY,
  hypothesis_id TEXT,
  feedback_id TEXT,
  previous_content TEXT,
  new_content TEXT NOT NULL,
  revision_reason TEXT NOT NULL,
  confidence_before REAL,
  confidence_after REAL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (hypothesis_id) REFERENCES personal_model_hypotheses(hypothesis_id),
  FOREIGN KEY (feedback_id) REFERENCES user_feedback(feedback_id)
);

CREATE INDEX idx_events_occurred_at ON events(occurred_at);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_memories_type ON memories(memory_type);
CREATE INDEX idx_memories_confirmed ON memories(user_confirmed);
CREATE INDEX idx_signals_should_touch ON signals(should_touch);
CREATE INDEX idx_signals_status ON signals(status);
CREATE INDEX idx_touchpoints_feedback_status ON touchpoints(feedback_status);
CREATE INDEX idx_feedback_target ON user_feedback(target_type, target_id);
CREATE INDEX idx_outcomes_target ON outcomes(target_type, target_id);
CREATE INDEX idx_model_revisions_hypothesis ON model_revisions(hypothesis_id);
