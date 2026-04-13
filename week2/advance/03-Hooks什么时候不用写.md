# Hooks 什么时候不用写

Week 2 第一节刚讲完怎么写 pre-commit hook，就有学员在群里问："那我是不是应该给所有事情都加 hook？每次 commit、每次 push、每次部署都挂几个 hook 上去？"

答案是不应该。hook 是有成本的，只是这个成本你第一次用的时候体会不到。

hook 的隐性成本有三个。

第一个是**时间税**。每次 commit 你挂一个 500ms 的 schema 校验，单次看不出来；但一天你提 30 次 commit，等于每天被抽走 15 秒。别的开发者会开始 `git commit --no-verify` 绕过，然后你的 hook 就失去了意义。所以 hook 要么快到无感（100ms 以内），要么有充足的理由慢。

第二个是**边界模糊**。一个 hook 管一件事很清楚，两个 hook 开始有交叉。你加了一个"格式化 JSON"的 hook，又加了一个"校验 schema"的 hook，第三次 commit 失败你都不知道是哪个 hook 报的错。我见过一个项目在 pre-commit 里挂了六个 hook，debug 一次 commit failure 要 20 分钟。

第三个是**维护成本**。hook 跑在每个开发者的本地机器上，你要考虑跨平台（Windows / macOS / Linux）、跨版本（Python 3.9 vs 3.12）、依赖缺失时的行为。hook 挂了比 CI 挂了更难发现——因为它只影响"触发它的那个人"，你可能半年都不知道张三那台机器上 hook 早就坏了。

所以 hook 我只给两种场景用。**第一种是"防线"**——拒绝明显错误的代码/数据进入仓库，比如 schema 不对的 JSON、有明文密码的 commit、main 分支的直接 push。这类 hook 失败就失败，让你知道问题在哪。**第二种是"自动化的 chores"**——格式化代码、排序 import、自动加版权头。这类 hook 是"静默做完"，不会挡你的路。

其他所有"我希望在某个时机自动做一件事"的需求，我都建议先想想能不能放在 CI 里。CI 的好处是集中管理、版本统一、debug 方便。"每次 commit 都跑单元测试"——CI 里做；"每次 push 生成 changelog"——CI 里做；"每次 PR 都 run lint"——CI 里做。放在 hook 里的理由只有一个：**这件事必须在代码进入 git 之前就完成**。满足这个条件的事不多。

这就是为什么 Week 2 只让你写一个 pre-commit hook（schema 校验）。不是我不想多教，是多了就废。
