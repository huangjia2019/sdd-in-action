# Week 2 · 物料

## 文章

- [OpenSpec 的 7+ 命令哪个最值得学](./advance/01-OpenSpec命令优先级.md)
- [/opsx:new 和手写 spec 的区别](./advance/02-opsx-new和手写的区别.md)
- [Hooks 什么时候不用写](./advance/03-Hooks什么时候不用写.md)
- [CI/CD 里 spec 的角色](./advance/04-CI-CD里spec的角色.md)
- [成本超标的 spec 应该长什么样](./advance/05-成本超标spec长什么样.md)

## 工具

Week 2 装 OpenSpec（Week 1 的 skill 保留）：

```bash
npm install -g @fission-ai/openspec@latest
cd your-project && openspec init
```

Week 2 用到 7 个 `/opsx:*` 命令：`new · ff · apply · verify · sync · archive · onboard`。

## 📦 物料 · B 路参考答案

> 怎么用？见 [Week 1 README](../week1/README.md#-这个目录里的文件怎么用) 有完整说明。简而言之：**先自己跑，再对照，不是 CV**。

**specs/ · 4 份 change 的 spec 部分**

- `hook.md` · N5 · pre-commit schema 校验 hook
- `pipeline.md` · N6 · 三 agent 串行流水线
- `ci.md` · N7 · GitHub Actions daily-run
- `cost-budget.md` · N8 · 成本治理（横切关注点）

**code/ · 可运行示例**

- `hook/pre-commit` · shell 脚本 · `chmod +x` 后放 `.git/hooks/`
- `pipeline/pipeline.py` · Python 流水线 runner
- `workflow/daily-run.yml` · GitHub Actions workflow
- `cost/cost_tracker.py` · 成本追踪 + 自动降级
