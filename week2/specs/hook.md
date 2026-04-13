# spec · pre-commit schema 校验 hook · 参考版 v1.0

> Week 2 · 第 5 节 · B 路产出
> `/opsx:ff` + grill-me 3 轮后的终态

## 要做什么

- 在 git commit 前检查被修改的 `knowledge/raw/*.json` 文件
- 对每个文件用 `specs/schemas/collector-output.json` 做 JSON Schema 校验
- 不符合 schema 则 reject commit · 输出具体错误定位（文件名 + 字段路径）
- schema 本身被改动时 · hook 只 warn 不 reject（避免"改 schema 的 commit 自己被拦"）

## 不做什么

- 不校验 `knowledge/raw/` 以外的任何 JSON（避免误伤 package.json 等）
- 不校验 git stash / amend 操作（只管 commit）
- 不执行任何网络请求

## 边界 & 验收

- 单文件校验超时 500ms · 总超时 3s（并行校验）
- 仅 staged 文件进入校验（不扫全仓）
- 用户可加 `git commit --no-verify` 跳过（标准 git 机制）
- hook 依赖：`jsonschema` CLI 工具（安装时说明）

## 怎么验证

- 故意在 `knowledge/raw/2026-01-01.json` 删掉一个必填字段 · commit 应失败
- commit 一个合法 JSON · 应通过
- 同一次 commit 同时改 schema 和 raw · 应 warn 不 reject
- 性能测试：一次 commit 10 个 JSON · 总耗时 < 3s
