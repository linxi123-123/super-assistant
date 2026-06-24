# 大模型调用与隐私网关设计

生成时间：2026-06-11

## 1. LLM Gateway 作用

所有大模型调用必须经过 LLM Gateway。

LLM Gateway 负责：

- 构造任务包
- 脱敏
- 上下文最小化
- 选择模型
- 记录调用日志
- 检查输出风险
- 返回给本地军师判断层

## 2. 模型任务包结构

```json
{
  "task_id": "",
  "user_query": "",
  "task_type": "",
  "external_context": [],
  "sanitized_user_context": {},
  "private_context_policy": {},
  "constraints": [],
  "required_output_schema": {},
  "forbidden_outputs": [],
  "audit_metadata": {}
}
```

## 3. 上下文最小化原则

问题：

```text
今天股市怎么样，我持有的腾讯怎么办？
```

禁止直接发送：

```text
用户真实姓名、账户、具体仓位、精确成本。
```

允许发送：

```text
用户持有一只港股大型互联网平台股，仓位偏重，关注中期逻辑，风险偏好未确认。
```

## 4. 输出审查

模型输出必须检查：

- 是否泄露隐私
- 是否编造行情
- 是否无来源
- 是否直接建议买卖
- 是否忽略风险
- 是否没有区分事实/推断/建议
