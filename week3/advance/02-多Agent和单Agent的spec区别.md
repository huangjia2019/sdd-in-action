# 多 Agent 协作的 spec 和单 Agent 有什么不一样

学员写了一个月的单 Agent spec 之后，到 Week 3 开始写多 Agent 系统，第一反应是"把单 Agent 的 spec 模板复制三份，一个 agent 一份"。能跑，但漏掉了多 Agent 最关键的那一层。

单 Agent 的 spec 管的是 **agent 本身的行为**——要做什么、不做什么、边界、验收。多 Agent 系统在这之外，还要管 **agent 之间的契约**。这一层是独立的、第四份 spec。

契约 spec 长什么样？它回答五个问题。

第一个是**数据形状**。Agent A 给 Agent B 传什么？什么字段必填，什么字段可选，什么字段的类型。最好直接用 JSON Schema 写，而不是在 markdown 里描述。JSON Schema 能被代码直接 validate，markdown 描述只能靠人记忆。

第二个是**时序假设**。Agent A 写完数据到 B 开始读，中间有没有"等待"？是 B 轮询，还是 A 主动通知？如果 B 先启动了 A 还没写完怎么办？这些都是时序契约。多 Agent 最常见的故障就是时序假设不对——A 假设"B 会等我"，B 假设"A 会 ping 我"，中间就是 race condition。

第三个是**失败传播规则**。A 失败了 B 做什么？是跟着失败、还是跳过当次、还是跑一个 fallback？这个规则不写在 contract spec 里，每个 agent 各自实现就会出现"A 觉得 B 会自愈，B 觉得 A 会重试"的僵局。

第四个是**可观测性要求**。A 到 B 的每一次传递，应该暴露哪个 trace span？哪些 attribute 必须带？这不是个 nice-to-have，是 contract 的一部分——因为生产环境排障时，你需要"这次 pipeline run 里 A 到 B 的数据是什么"这种回放能力。

第五个是**变更流程**。如果我要改 A 的输出格式，B 怎么知道？是 breaking change 还是 additive change？破坏性修改要提前几天通知？这个问题在单 Agent 项目里不存在，但多 Agent 项目里，不写清楚就会变成"每次 A 改一下 B 就炸"。

所以多 Agent 项目的 spec 目录不是三份 agent spec，是**三份 agent spec + 一份 collaboration spec**。前三份管各自的行为，最后一份管他们之间的契约。缺了最后一份，多 Agent 系统就只是三个独立脚本被串在一起，不是一个真正的协作系统。

Week 1 第 3 节让你写 `specs/agents-collaboration.md` 的时候用的就是这个分层——现在回头看，你应该更能理解为什么那份 spec 和其他 agent spec 分开放了。
