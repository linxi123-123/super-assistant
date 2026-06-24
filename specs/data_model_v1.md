# 数据模型 v1

## UserProfile

```text
user_id
basic_background
current_city
career_stage
capability_structure
resource_structure
long_term_goals
values
risk_preference
communication_preference
privacy_preference
created_at
updated_at
```

## Goal

```text
goal_id
name
type
time_horizon
importance
status
success_criteria
failure_criteria
created_at
updated_at
```

## Project

```text
project_id
name
description
goal_id
stage
progress
key_risks
next_action
related_files
created_at
updated_at
```

## Event

```text
event_id
event_type
source
content
occurred_at
captured_at
related_goal_id
related_project_id
related_person
related_file
importance
confidence
sensitivity
raw_reference
evidence_type
evidence_summary
processed_status
created_at
updated_at
```

## Memory

```text
memory_id
memory_type
content
source_event_ids
evidence
confidence
importance
sensitivity
user_confirmed
valid_until
is_expired
counter_evidence
related_goal_id
related_project_id
allow_for_advice
last_used_at
created_at
updated_at
```

## PersonalModelHypothesis

```text
hypothesis_id
content
evidence
counter_evidence
confidence
validation_plan
status
source_memory_ids
source_signal_ids
last_validated_at
created_at
updated_at
```

## IntelligenceItem

```text
intel_id
source
title
summary
key_change
relevance_to_user
opportunity
risk
recommended_action
confidence
created_at
updated_at
```

## Signal

```text
signal_id
signal_type
description
evidence
related_goal_id
related_project_id
importance_score
urgency_score
goal_relevance_score
actionability_score
confidence_score
false_positive_risk
interrupt_cost
should_touch
status
created_at
updated_at
```

## Touchpoint

```text
touch_id
signal_id
message
reason
recommended_action
delivery_channel
user_response
result
feedback_status
outcome_id
created_at
updated_at
```

## Action

```text
action_id
goal_id
project_id
description
execution_level
requires_confirmation
status
expected_result
completion_criteria
result
review
created_at
updated_at
```

## UserFeedback

```text
feedback_id
target_type
target_id
feedback_value
feedback_note
created_at
updated_at
```

## Outcome

```text
outcome_id
target_type
target_id
expected_result
actual_result
result_status
review_note
created_at
updated_at
```

## ModelRevision

```text
revision_id
hypothesis_id
feedback_id
previous_content
new_content
revision_reason
confidence_before
confidence_after
created_at
```
