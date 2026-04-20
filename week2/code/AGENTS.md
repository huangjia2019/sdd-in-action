# AGENTS.md · Week 2 基线

> 本文件是 OpenCode / Claude Code 启动时自动加载的"项目大脑"。`/opsx:*` 和 `@grill-me` 都会读这份。

## 项目定义

**AI 知识库 · Week 2 基线版本**。在 Week 1 的 3 个 Agent（collector/analyzer/organizer）基础上，串成一条四步流水线：`collect → analyze → organize → save`。

**⚠️ 当前已知问题（Week 2 要解决的痛点）**：

- `pipeline/model_client.py::chat()` 调 LLM 时**不做 retry**
- 任何瞬时故障（timeout / rate limit / 5xx / connection reset）→ `step_analyze` 直接中断 → 前面花的 token 沉没 → 当天知识库为空
- 本周用 OpenSpec 走一个 `add-analyzer-retry-policy` change 把这个洞补上

## 项目结构

```
week2/code/
├── AGENTS.md              # 本文件 · 项目大脑
├── .env.example           # 环境变量模板
├── requirements.txt       # Python 依赖
├── pipeline/
│   ├── __init__.py
│   ├── model_client.py    # LLM 调用层（⚠️ 无 retry · 本周要补）
│   └── pipeline.py        # 四步流水线
├── knowledge/
│   ├── raw/               # Step 1 原始采集数据
│   └── articles/          # Step 3 整理后的知识条目
├── tests/                 # pytest 测试（本周会填）
├── openspec/              # OpenSpec 工件目录
│   ├── project.md         # OpenSpec 全局上下文
│   ├── changes/           # 进行中的 change
│   └── specs/             # 归档后的主规范
├── .claude/               # Claude Code 集成（opsx 命令 + skills）
└── .opencode/             # OpenCode 集成（opsx 命令 + skills）
```

## 关键数据契约

- `knowledge/raw/github-{YYYY-MM-DD}.json` · Collector 产出 · 列表 of `{title, url, description, stars, collected_at}`
- `knowledge/articles/{YYYY-MM-DD}-{NNN}.json` · Organizer 产出 · 标准 article 结构
- LLM 输出约定 · JSON with `{summary, tags, relevance_score, category, key_insight}`

## 编码约定

- Python 3.11+ · 无框架 · `from __future__ import annotations`
- 路径用 `pathlib.Path`
- 日志用 `logging.getLogger(__name__)`
- LLM 成本估算单位为人民币（元）
- 错误处理原则 · 瞬时故障该 retry · 内容层错误（JSONDecodeError/KeyError）不 retry

## 技术栈

- **LLM**: OpenAI 兼容 API（DeepSeek/Qwen/OpenAI 任选 · 通过 .env 配置）
- **依赖**: `openai`, `python-dotenv`, `httpx`, `pytest`
- **工程化**: OpenSpec（本周引入）· git · GitHub

## 本周要做的 change

```
add-analyzer-retry-policy
  ├─ capability · analyzer-retry-policy
  ├─ 影响文件 · pipeline/model_client.py（新增 with_retry 装饰器）
  ├─ 影响文件 · pipeline/pipeline.py（step_analyze 处理 degraded item）
  └─ 测试 · tests/test_retry.py
```

走完 `/opsx:new → proposal → ff → grill-me → apply → verify → archive` 一遍，感受 SDD 在真实 PR 里的节奏。
