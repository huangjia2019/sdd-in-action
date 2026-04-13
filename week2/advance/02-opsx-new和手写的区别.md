# /opsx:new 和手写 spec 的区别

Week 1 教你手写 spec——打开编辑器新建一个 `specs/xxx.md`，按四个二级标题填。简单直接。到 Week 2 我让你跑 `/opsx:new`，学员会问："这俩有啥区别？我自己写一个文件不就得了吗？"

有区别，但不是你第一眼想的那种区别。

手写 spec 的好处是"零门槛"。你不用装任何工具，不用记命令，编辑器里新建文件就能开始。适合刚学 SDD 的人建立"我真的在写 spec"这个心智。Week 1 用手写是对的，因为重点是培养习惯，不是练工具。

`/opsx:new` 看起来也是创建一个 markdown 文件，差别在于它建的不是一个文件，是一个**结构化的 change 目录**：

```
openspec/changes/add-precommit-schema-hook/
├── proposal.md     （为什么做这个变更）
├── specs/
│   └── hook.md     （具体规范）
├── design.md       （技术方案 · 架构图）
└── tasks.md        （任务清单 · 带 checkbox）
```

这四份文件的关系是有顺序的。proposal 回答"为什么"，specs 回答"什么"，design 回答"怎么做"，tasks 回答"分几步做"。手写 spec 你也可以搞出这四份，但很少有人坚持——手写时大家都会偷懒，只写个 "hook.md" 就开动手了。OpenSpec 强制你停下来思考这四个层次。

另一个差别是**可追溯性**。`openspec/changes/` 下是"进行中的变更"，`openspec/archive/` 下是"已完成的变更"。每一个 PR 对应一个 change，每个 change 完整归档。半年后你问"这个 feature 当时为什么这样设计？"——你不用翻 git log 猜，直接去 `openspec/archive/2026-04-add-pipeline/proposal.md` 读原始动机。手写 spec 没有这个自然的归档机制。

还有一个很实际的差别：`/opsx:ff` 的存在让"生成首稿"变得几乎零成本。手写时你会盯着空文件发呆 20 分钟，`/opsx:ff` 帮你把四份 artifact 都填到 70% 然后你 review 和修改——心理阻力小很多。

所以我推荐的节奏是：Week 1 手写，培养"写 spec"的习惯；Week 2 切换到 `/opsx:new`，培养"管理 spec 生命周期"的习惯。两个习惯配合起来才是完整的 SDD。

如果你团队里只有你一个人用 SDD，手写就够了。但一旦团队超过三个人，你就需要 OpenSpec 这种工具——因为你需要让同事打开 `openspec/changes/` 就能看到"现在在进行的变更有哪几个"、"每个变更的 spec 是什么"。散落的 markdown 文件做不到这件事。
