# COMMERCIAL-V1 用户手册

## 如何使用

打开前端后，优先使用第一屏的“跟军师说”。

可以直接输入：

- 今天股市怎么样
- 腾讯今天怎么样
- 我这个项目下一步该怎么做
- 我纠结要不要继续做这个产品
- 我今天很烦，不知道该先做什么

系统会自动判断问题类型，不需要你手动选择事件。

## 如何看回答

一次回答重点看这些区域：

- 正文：军师判断和行动建议
- 情报与记忆：是否用了外部数据、来源数量、记忆数量
- 回答质量：评分、是否降级、降级原因
- 调用边界：provider、model、llm_mode、local_judge_status
- 来源列表：最多展示部分外部来源及可信度、时效性、使用策略

## 如何反馈

如果回答不对，可以点：

- 回答有问题
- 回答有疑问

如果感觉记忆不对，可以点：

- 这个记忆不对
- 这个已经过期
- 不要再用这个判断

反馈会进入后端记录。与该回答相关的候选记忆会被标记为待复审、过期或隔离，避免长期污染后续判断。

## 市场问题边界

系统可以回答市场观察类问题，但必须遵守：

- 有来源才说事实
- 来源不可信只能当信号
- 过期数据不能当实时
- 不输出直接买入或卖出指令
- 对没有总览 provider 的泛市场问题，会自动降级为“需要补充来源”的回答

## 长期使用注意事项

长期使用的关键不是“什么都记住”，而是：

- 只沉淀高质量、可复审的记忆
- 对旧记忆保留 caveat
- 错误判断可以被用户纠正
- 过期或不适用的记忆可以被隔离
- 系统回答必须显示审计和质量状态

## 本地运行说明

如果系统 `python` 命令不可用，可以使用 Codex 自带 Python：

```powershell
& 'C:\Users\刘书桐\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest server\tests -q
```

烟测：

```powershell
& 'C:\Users\刘书桐\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\commercial_v1_smoke_test.py
```

如果已经启动后端，也可以设置：

```powershell
$env:ADVISOR_BASE_URL='http://127.0.0.1:8000'
& 'C:\Users\刘书桐\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\commercial_v1_smoke_test.py
```
