# CI/CD 里 spec 的角色

学员写 workflow 写多了会发现一件事：`.github/workflows/*.yml` 是项目里**改得最勤的文件之一**。加 cache、加 matrix、加 secrets、加 timeout、加 notification——每个月都要动几次。但也是项目里**最少被 review 的文件**——因为大家觉得"YAML 能跑就行"。

这个错配会在半年后给你一个大惊喜。你回头看 daily-run.yml，发现有三行 `continue-on-error: true`，你不记得什么时候加的、为什么加的；有一个 `if: github.event_name == 'workflow_dispatch'`，你不确定它是防止什么的；有一段 `if: failure()` 指向一个不存在的 Slack 频道。这不是你的问题，这是 CI workflow 缺乏真相源的必然结果。

spec 在这个场景下的价值不是"管生成"，是"管漂移"。workflow 改得勤，但 spec 只要改得对，就永远能告诉你"workflow 现在应该长什么样"。CI 漂移是 SDD 能救的最典型的一个场景。

具体怎么做？我的习惯是每个 workflow 配一份 spec，就放在 `specs/ci/<workflow-name>.md`。这份 spec 只写四件事：**触发条件**（schedule / push / manual）、**成功标准**（workflow 正常跑完应该看到什么副作用）、**失败路径**（什么情况下应该告警、告警发给谁）、**不变约束**（密钥必须走 Secrets 不能硬编码之类）。

写完之后每次改 workflow 都做两件事：一是改 workflow yaml，二是跑 `/opsx:verify` 对照 spec。verify 是这套流程的关键——它会告诉你"你刚才加的 `continue-on-error: true` 和 spec 里的'失败要告警'条款冲突"。没有 verify，spec 会很快沦为装饰。

我还会做一件看似画蛇添足的事：**在 workflow yaml 的第一行加一个注释，指向 spec 路径**。

```yaml
# Spec: ./specs/ci/daily-run.md
# To change this workflow · edit the spec first · then /opsx:apply
name: daily-run
```

这个注释的作用是"提醒未来的自己"。三个月后你打开这个 yaml 想改什么，先看注释就知道去哪找真相源。没有这个注释的 workflow，九成会变成"我现场改改就好了"的那种文件。

CI/CD 这件事 SDD 的投入产出比是最高的。因为你对 workflow 的真实关心程度是"炸了才修"，越是低关心的东西，越需要 spec 帮你记忆。
