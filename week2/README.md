# Week 2

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

# 关键 · 启用 expanded 命令（默认 core 只有 4 条）
# v1.3.0 暂无预设 · 直接改 ~/.config/openspec/config.json 的 workflows 数组：
# ["propose","explore","apply","archive","new","continue","ff","verify","sync","bulk-archive","onboard"]
openspec update
```

改完重启 IDE。本周用到 7 个 `/opsx:*` 命令：`new · ff · apply · verify · sync · archive · onboard`（默认 core 只有 `propose · explore · apply · archive` 四条，不够用）。
