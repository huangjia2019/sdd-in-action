# Week 1 · code/ · B 路产出物参考版

按节次分目录 · 每个文件是跑完 B 路后的示例产出。

## 怎么用

不是"跑到这里 CV"——是"自己跑完对照"。详见 [../README.md](../README.md#-这个目录里的文件怎么用)。

## 目录

```
code/
├── 02/
│   └── AGENTS-coding-standards-section.md
│       · N2 的 AGENTS.md 编码规范段 · 供合并参考
├── 03/
│   └── agents/
│       ├── collector.md   · Sub-Agent 配置
│       ├── analyzer.md
│       └── organizer.md
└── 04/
    └── skills/
        └── github-trending/
            └── SKILL.md   · 可直接用的 skill
```

## 可直接 CV 的

只有一个：`04/skills/github-trending/SKILL.md`——这是**基础设施代码**不是设计产物。

安装:

```bash
# OpenCode
mkdir -p ~/.opencode/skills/github-trending/
cp week1/code/04/skills/github-trending/SKILL.md ~/.opencode/skills/github-trending/

# Claude Code
mkdir -p ~/.claude/skills/github-trending/
cp week1/code/04/skills/github-trending/SKILL.md ~/.claude/skills/github-trending/
```

装完重启 CLI · 说"今天 github 有什么 AI 热门"应自动触发。
