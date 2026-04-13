# Week 3 · 物料

## 文章

- [BMAD 的 12+ 角色不是越多越好 · 怎么挑](./advance/01-BMAD的12角色怎么挑.md)
- [多 Agent 协作的 spec 和单 Agent 有什么不一样](./advance/02-多Agent和单Agent的spec区别.md)
- [BMAD 和 OpenSpec 怎么配合 · 不要当成替代关系](./advance/03-BMAD和OpenSpec怎么配合.md)
- [Agent 间的"对话历史"要不要写进 spec](./advance/04-Agent间对话历史要不要写进spec.md)
- [什么情况下应该退回单 Agent](./advance/05-什么情况该退回单Agent.md)

## 工具

Week 3 装 BMAD（Week 1 的 skill 和 Week 2 的 OpenSpec 继续保留）：

```bash
cd your-project && npx bmad-method install
```

BMAD 不替代 OpenSpec。BMAD 管视角（多角色 review）· OpenSpec 管流程（change 生命周期）。

## 📦 物料 · B 路参考答案

> 怎么用？见 [Week 1 README](../week1/README.md#-这个目录里的文件怎么用)。**先自己跑，再对照，不 CV**。

**specs/ · 4 份**

- `multi-agent-patterns.md` · N9 · Supervisor vs Swarm vs Hierarchical 选型
- `state-graph.md` · N10 · LangGraph 状态机 + failure transition
- `planning-review.md` · N11 · Party Mode 共识 · 质量阈值功能
- `observability.md` · N12 · 8 个必须暴露的 span

**code/**

- `workflow.py` · LangGraph Supervisor 模式骨架
