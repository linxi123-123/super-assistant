# W5D 第一屏最小页面改造边界草案

注意：

这不是开发授权。

只有用户明确确认进入 W5D 后，才允许执行本计划。

## 1. W5D 目标

把个人作战室第一屏从“模块列表 / dashboard”改造成“军师简报式当前局势面板”。

W5D 只做最小页面改造，不做完整产品升级。

## 2. W5D 只允许

- 修改 `app/war_room.html`
- 修改 `app/war_room.js`
- 修改 `app/war_room.css`
- 只读加载 `data/real_war_room_snapshot_v1.json`
- 重构第一屏
- 保留原下方模块作为次级区
- 不改 SQLite
- 不改 real snapshot
- 不接新数据源
- 不引 npm/框架

## 3. W5D 禁止

- 外部情报
- 执行代理
- 新数据源
- 编辑 / 新增 / 删除
- 聊天
- 后端服务
- UI 大美化
- SQLite 写入
- 修改 `data/real_war_room_snapshot_v1.json`

## 4. W5D 页面结构要求

第一屏必须包含：

- 局势一句话
- 军师直接判断
- 今日唯一动作
- 不要做清单
- 当前最大矛盾
- 不行动后果

下方保留：

- High-value Signals
- Personal Model Hypotheses
- Recent History
- Audit Entry
- Source Metadata / Audit

## 5. W5D 验收标准

- 第一屏回答五个关键问题
- 页面不像列表
- 今日唯一动作突出
- 不要做清单突出
- 原有模块仍可访问
- validate 脚本通过
- 不破坏 history/index 页面
- 不接新数据源
- 不引 npm/框架
- 不写 SQLite

## 6. W5D 输出建议

如果用户确认 W5D，建议输出：

- 更新后的 `app/war_room.html`
- 更新后的 `app/war_room.js`
- 更新后的 `app/war_room.css`
- 更新后的验证脚本
- W5D 页面改造说明
- W5D 测试报告

## 7. 进入条件

进入 W5D 前必须由用户确认：

- 接受 W5C 第一屏规格
- 允许修改 `app/war_room.html/js/css`
- 继续保持只读
- 继续禁止新数据源、外部情报、执行代理、npm/框架
