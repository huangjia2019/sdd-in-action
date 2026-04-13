# spec · v3 多 Agent 设计模式选型 · 参考版 v1.0

> Week 3 · 第 9 节 · B 路产出
> BMAD PM + Architect 两角色 review 后的共识

## 要做什么

- 为 v3-multi-agent 的 collector/analyzer/organizer 选定主协作模式
- 选定 · Supervisor 模式（明确调度者 + 三 worker）
- 给出选型理由 · 拒绝理由

## 选型对比

| 维度 | Supervisor | Swarm | Hierarchical |
|-----|-----------|-------|--------------|
| 调度 | 中心式 | 去中心 | 树形 |
| 延迟 | 串行较慢 | 并行快 | 中等 |
| 可解释性 | 高（有调度决策日志） | 低 | 中 |
| 单点故障 | Supervisor 挂全停 | 高可用 | 根节点单点 |
| 实现复杂度 | 低 | 高 | 中 |

## 选型理由（Supervisor）

**PM 视角**：v3 是内容类产品 · 用户不在乎 5 秒延迟 · 但在乎错排。Supervisor 可解释性高 · 出错能精确定位。

**Architect 视角**：单点故障风险用"Supervisor 无状态 + 失败即重启"化解。worker 延迟用"每 worker 30s 超时"约束。错误用 `Result<T, E>` 统一契约 · E 分 `NetworkErr / LogicErr / BudgetErr`。

## 拒绝理由

- **Swarm**：本项目只有 3 个 agent · 去中心化价值不大 · 反而增加调试难度
- **Hierarchical**：没有真实的多层需求 · 两层的 Hierarchical 等价于 Supervisor 但命名更复杂

## 不做什么

- 不引入消息队列（Redis/RabbitMQ 等）· 本期用文件 done 标记足够
- 不做 leader election（Supervisor 无状态 · 挂了重启即可）
- 不做跨节点部署（单机 · docker compose 级别即可）

## 边界 & 验收

- Supervisor 调用 worker 超时 30s
- worker 返回必须符合 `Result[T, E]` schema
- 任一 worker 失败 · Supervisor 写 incident 文件
- Supervisor 本身挂 · CI 层面的 healthcheck 负责告警（Week 3 N12 的 observability spec 处理）

## 怎么验证

- mock 三 worker 全 ok · Supervisor 应完整跑完
- mock collector 超时 · Supervisor 应标记失败 · 不触发下游
- mock analyzer 抛 LogicErr · retry 1 次后继续
- Supervisor 进程被 kill · 应无残留状态（重启即可从头跑）
