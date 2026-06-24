# COMMERCIAL-V1-INSIGHT：军师认知压缩与主结论系统

## 什么是 Cognitive Compression

Cognitive Compression 是把复杂信息压缩成一个可执行、可理解、可复盘的判断。

当前系统已经有外部情报、记忆、评分、降级、行动和学习。如果这些都直接展示给用户，系统会变成信息面板，而不是军师。

认知压缩层把复杂输入压缩成：

1. CORE INSIGHT：唯一主结论
2. KEY EVIDENCE：最多 3 条关键依据
3. ACTIONS：最多 3 个行动

## 为什么 AI 必须有唯一主判断

用户问军师，不是为了得到一堆并列可能性，而是为了降低决策负担。

多结论会制造新的犹豫：

- 结论 A 也对
- 结论 B 也对
- 结论 C 也可能

这类输出看似全面，实际把决策压力还给了用户。

军师必须给出一个主判断，并标注置信度和理由。

## 为什么多结论系统会降低决策质量

多结论的问题不是“不准确”，而是“不负责”：

- 用户不知道哪个最重要
- 前端无法建立视觉优先级
- 行动建议会互相竞争
- 后续结果学习无法归因
- 长期记忆会记录多个方向，导致未来判断漂移

单结论规则让系统在不确定时也保持清楚：低置信度就输出观察结论，而不是堆叠分析。

## 军师 vs 信息助手

信息助手的目标是提供更多信息。

军师的目标是帮助用户做更好的判断。

区别在于：

- 信息助手展示信息
- 军师压缩信息
- 信息助手列选项
- 军师给主判断
- 信息助手回答结束
- 军师连接行动闭环

## 认知压缩原理

系统新增：

- `server/services/judgment_rules.py`
- `server/services/core_judgment_engine.py`
- `server/services/insight_compression_service.py`

流程：

```text
decision_layer_output
  + external_data
  + memory
  + actions
  + scoring
  + conflicts
      ↓
core_judgment_engine
      ↓
insight_compression_service
      ↓
insight contract
```

## Response Contract

新增：

```json
{
  "insight": {
    "core_judgment": {
      "summary": "唯一主结论",
      "confidence": "high | medium | low",
      "reason": "短理由",
      "category": "market | project | decision | general | observation"
    },
    "key_evidence": [],
    "compressed_actions": []
  }
}
```

同时 `decision_layer_output.core_judgment` 也会存在。

## UI 原则

第一屏必须按这个顺序展示：

1. 军师核心判断
2. 关键依据
3. 行动建议

其余内容折叠：

- raw evidence
- scoring
- memory detail
- audit log

## 核心原则

> AI 军师的价值不在于信息多少，  
> 而在于能否给出唯一清晰的判断。

## 验收

- 每个回答只有一个 `core_judgment`
- `key_evidence <= 3`
- `compressed_actions <= 3`
- conflict 时降级为观察结论
- UI 包含“军师核心判断”
