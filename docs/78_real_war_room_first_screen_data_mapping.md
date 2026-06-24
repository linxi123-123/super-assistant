# 真实事件作战室第一屏数据映射

所有字段只能来自：

`data/real_war_room_snapshot_v1.json`

不得接入其他新数据源。

## 1. 局势一句话

来源字段：

`current_situation.one_sentence_situation`

是否必填：

是。

缺失时如何降级：

显示“真实局势一句话缺失，不能进入第一屏页面改造。”

## 2. 当前最大矛盾

来源字段：

`current_situation.main_tension`

是否必填：

是。

缺失时如何降级：

显示“当前最大矛盾缺失，不能证明作战室价值。”

## 3. 军师直接判断

来源字段：

`advisor_brief.direct_judgment`

是否必填：

是。

缺失时如何降级：

显示“军师直接判断缺失，页面会退化为 dashboard。”

## 4. 今日唯一动作

来源字段：

`today_action.only_action`

是否必填：

是。

缺失时如何降级：

显示“今日唯一动作缺失，不能进入页面改造。”

## 5. 不要做清单

来源字段：

- `current_situation.what_not_to_do`
- `today_action.avoid_list`

合并规则：

先读取 `current_situation.what_not_to_do`，再追加 `today_action.avoid_list`。

去重规则：

按文本完全一致去重，保留首次出现顺序。

缺失时如何降级：

如果两个来源都为空，显示“不要做清单缺失，反迎合能力不足。”

## 6. 不行动后果

来源字段：

`advisor_brief.consequence_if_ignored`

是否必填：

是。

缺失时如何降级：

显示“未定义不行动后果，军师提醒力度不足。”

## 7. 完成标准

来源字段：

`today_action.done_definition`

是否必填：

是。

缺失时如何降级：

显示“完成标准缺失，今日动作不可验收。”

## 8. 辅助字段

### 为什么重要

来源字段：

`advisor_brief.why_this_matters`

用途：

解释为什么当前判断现在必须处理。

### 反方判断

来源字段：

`advisor_brief.counter_argument`

用途：

防止页面只迎合用户当前想法。

### 决策焦点

来源字段：

`decision_focus`

用途：

作为首屏下方或展开区，解释当前真正要回答的问题。

## 9. 数据映射结论

真实事件第一屏所需 P0/P1 字段均可从 `data/real_war_room_snapshot_v1.json` 获得。

如果以上任一 P0 字段缺失，不允许进入 W5D 页面最小改造。
