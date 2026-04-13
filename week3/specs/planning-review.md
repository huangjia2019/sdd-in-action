# spec · 质量阈值功能 · Party Mode 共识版 v1.0

> Week 3 · 第 11 节 · B 路产出
> BMAD Party Mode (PM × Architect × QA) 讨论后的共识

## 功能概述

analyzer 输出的每条知识点有 `confidence ∈ [0, 1]`。低于阈值的条目不直接发布 · 进入人工复核队列 · 复核后再合入。

## Party Mode 讨论共识

### 阈值（PM + QA）

- **confidence < 0.6** → 进复核队列
- 0.6 这个数字初版拍定 · 一个月后根据实际复核数据调整

### 处理容量（PM 关注）

- 复核人（即项目负责人）每天最多 50 条
- 超 50 条积压 · 进入溢出策略
- 3 天未复核的条目自动过期

### 溢出策略（Architect 补）

- 队列长度 > 150 · 新进条目 · 自动标记 `auto-approved`（绕过复核）
- 同时触发告警 · 人工决定是否调高 confidence 阈值

### 存储（Architect 主导）

- **当前队列** · Redis · key: `review_queue:{date}`
  - 字段：item_id / title / confidence / queued_at
- **历史复核** · SQLite · 长期保留
  - 字段：item_id / original_labels / reviewed_labels / reviewer / reviewed_at / notes

### Feedback Loop（QA 坚持）

- 复核产出数据 30 天后作为 fine-tune 样本 · 改进 analyzer
- 复核动作必须记录：
  - 正确标签（如果原标签错）
  - 复核人 ID · 时间戳
  - 复核备注（可选）

## 要做什么

- 在 analyzer 输出阶段 · 按 confidence 分流
- 构建复核队列和 UI（本期 CLI · Week 4 考虑 Bot 化）
- 记录复核结果到 SQLite
- 实现溢出策略和告警
- 30 天后导出 fine-tune 样本

## 不做什么

- 不做实时通知（复核人主动拉 · 不 push）
- 不做多人协作复核（本期单人）
- 不做复核质量评估（哪个复核人靠谱）

## 边界 & 验收

- 队列读写 p99 延迟 < 50ms
- SQLite 写入失败不阻塞 analyzer
- 溢出告警不重复发送（同日不超过一次）
- fine-tune 样本导出脚本独立 · 不耦合 pipeline

## 怎么验证

- mock confidence 分布 · 验证分流正确
- 填满 150 条 · 验证 auto-approved 触发
- 过期 3 天 · 验证自动 expire
- 复核一条 · 验证 SQLite 记录完整
