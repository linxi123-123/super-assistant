# FAST-E4 Evidence Pack Design

## evidence_pack 的作用

`evidence_pack` 是外部情报进入 LLM 前的安全证据包。它把来源按可信度、时效和使用策略分层，避免模型把线索说成事实。

## usable_facts / signals_only / excluded_items

- `usable_facts`：可信、未过期、无冲突，可作为事实。
- `signals_only`：低可信、需确认、过期或冲突，只能作为线索。
- `excluded_items`：无来源或不可用，不得进入回答依据。

## stale 信息如何处理

stale 信息不能作为实时事实，只能作为线索，并要求回答明确提示“可能过期”。

## conflict 信息如何处理

存在冲突时，`conflict_summary` 会提示来源冲突，LLM 指令要求不得输出强结论。官方来源可优先，但仍要说明冲突。

## LLM 如何使用 evidence_pack

`llm_gateway` 的 task_package 包含 `evidence_pack`，系统 prompt 明确要求：

- 只能把 `usable_facts` 当事实。
- `signals_only` 只能作为线索。
- `excluded_items` 不能使用。
- 没有 `usable_facts` 时不得声称知道最新情况。

## local_judge 如何复查

`local_judge` 检查回答是否：

- 无 fresh/realtime 来源却声称最新/实时。
- 市场数据不可用却给确定涨跌。
- 忽略冲突。
- 把 signals_only 当事实。
- 缺少来源或时间说明。
- 对 stale 信息未提示过期。
