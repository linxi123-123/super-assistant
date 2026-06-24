# 真实作战室快照规格

## 1. 目标

定义新的真实作战室快照：

`data/real_war_room_snapshot_v1.json`

注意：

本阶段只写规格，不生成 JSON。

真实作战室快照必须基于用户真实事件，而不是测试 case。

## 2. 顶层结构

```json
{
  "real_events": [],
  "current_situation": {
    "one_sentence_situation": "",
    "current_phase": "",
    "main_tension": "",
    "main_risk": "",
    "main_opportunity": "",
    "what_not_to_do": [],
    "current_best_action": ""
  },
  "advisor_brief": {
    "direct_judgment": "",
    "why_this_matters": "",
    "counter_argument": "",
    "recommended_action": "",
    "consequence_if_ignored": ""
  },
  "decision_focus": {
    "question": "",
    "options": [],
    "recommended_option": "",
    "reason": ""
  },
  "today_action": {
    "only_action": "",
    "done_definition": "",
    "time_box": "",
    "avoid_list": []
  },
  "evidence_chain": [],
  "stage_gate": {},
  "audit": {}
}
```

## 3. real_events

用途：

记录用户输入的真实事件。

每条建议包含：

- event_id
- happened_today
- worry
- desired_action
- uncertainty
- actual_progress
- phase_drift
- expected_advisor_reminder
- should_not_do

## 4. current_situation

第一屏必须优先回答：

- 现在局势一句话是什么？
- 最大矛盾是什么？
- 今天唯一动作是什么？
- 现在不该做什么？
- 如果继续错方向会怎样？

字段：

- `one_sentence_situation`：一句话局势。
- `current_phase`：当前阶段。
- `main_tension`：当前最大矛盾。
- `main_risk`：当前最大风险。
- `main_opportunity`：当前机会，不是外部市场机会，而是项目内可行动机会。
- `what_not_to_do`：当前不要做的事项。
- `current_best_action`：当前最重要动作。

## 5. advisor_brief

用途：

把真实事件转成军师直接判断。

字段：

- `direct_judgment`：直接判断，不绕弯。
- `why_this_matters`：为什么重要。
- `counter_argument`：反方判断。
- `recommended_action`：建议动作。
- `consequence_if_ignored`：忽略后果。

## 6. decision_focus

用途：

把当前局势收敛成一个决策问题。

字段：

- `question`：当前真正需要回答的问题。
- `options`：可选路径。
- `recommended_option`：推荐路径。
- `reason`：推荐理由。

## 7. today_action

用途：

让作战室不只是看板，而是行动收敛器。

字段：

- `only_action`：今天唯一动作。
- `done_definition`：做到什么算完成。
- `time_box`：建议时间盒。
- `avoid_list`：今天不要做什么。

## 8. evidence_chain

用途：

证明判断来自真实事件，而不是空泛生成。

每条建议包含：

- source_event_id
- evidence_text
- supports
- confidence

## 9. stage_gate

用途：

防止项目跳步。

应包含：

- current_gate
- pass_conditions
- failed_conditions
- forbidden_next_steps
- can_move_forward

## 10. audit

用途：

记录真实快照是否可审计。

应包含：

- source_count
- missing_real_context
- assumptions
- blockers
- can_validate_war_room_value

## 11. 特别要求

真实作战室快照第一屏必须优先回答：

- 现在局势一句话是什么？
- 最大矛盾是什么？
- 今天唯一动作是什么？
- 现在不该做什么？
- 如果继续错方向会怎样？

如果这些问题无法回答，不允许进入页面重构。
