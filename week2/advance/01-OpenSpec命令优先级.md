# OpenSpec 的 7+ 命令哪个最值得学

OpenSpec 官方 README 列了十条命令，学员读完就头大："这么多，我从哪学起？"

我用下来的结论是：这十条里真正高频的就四条，剩下六条是"有就有、没也不至于卡壳"。

高频四条是 `/opsx:new`、`/opsx:ff`、`/opsx:apply`、`/opsx:verify`。你可以把它们想象成 Git 里的 `clone`、`commit`、`push`、`status`——工具再多，真正每天都用的就这几个。`/opsx:new` 开一个新 change，`/opsx:ff` 一口气把 proposal / specs / design / tasks 四份 artifact 推进到首稿，`/opsx:apply` 按任务生成代码，`/opsx:verify` 反向对照 spec 检查实现。这四个走下来就是一个完整的 PR 周期，99% 的场景够用。

次高频两条是 `/opsx:onboard` 和 `/opsx:archive`。`/opsx:onboard` 是老项目的救命稻草——给一块没走过 SDD 的代码自动反推出 spec baseline，Week 2 最后一节你会用到。`/opsx:archive` 是周期结束的收尾，把完成的 change 从 `openspec/changes/` 挪到 `openspec/archive/`，主规范那边 auto sync。这两个不每天用，但需要时很关键。

剩下四条我用得很少。`/opsx:continue` 是断点重连，一次 session 做不完下次接着做——实际上你 `/opsx:ff` 后改改文件再 `/opsx:apply` 一样能接上。`/opsx:sync` 是把 change delta 显式合回主规范，99% 情况 `/opsx:archive` 会顺便帮你做。`/opsx:propose` 是旧版遗留的命令，现在基本被 `/opsx:new` + `/opsx:ff` 替代。`/opsx:bulk-archive` 是批量归档——除非你半年没归档积了二十个，一般用不上。

所以如果你时间有限，就学四条：`new / ff / apply / verify`。剩下六条等你遇到具体场景再翻文档，OpenSpec 的文档不长，查得很快。

这也是我反复跟学员强调的一件事：工具列得多不代表你要全学。找它的"主干四条"，围着主干走顺，其他的是枝叶，按需长。
