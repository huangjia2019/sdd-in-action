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
cd your-project
npx bmad-method install
# 选 claude-code 或 opencode
# 选 brownfield (老项目) 或 greenfield (新项目)

# 验证
ls .bmad-core/
cat .bmad-core/core-config.yaml
```

BMAD 不替代 OpenSpec。两者配合：
- BMAD 管**视角**（多角色对同一问题 review）
- OpenSpec 管**流程**（一个 change 从 proposal 到 archive）

常用组合：先 `/party pm architect qa` 吵共识 → 再 `/opsx:new` 把共识落成 change。
