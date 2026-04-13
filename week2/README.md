# Week 2 · 物料

## 文章

- [OpenSpec 的 7+ 命令哪个最值得学](./advance/01-OpenSpec命令优先级.md)
- [/opsx:new 和手写 spec 的区别](./advance/02-opsx-new和手写的区别.md)
- [Hooks 什么时候不用写](./advance/03-Hooks什么时候不用写.md)
- [CI/CD 里 spec 的角色](./advance/04-CI-CD里spec的角色.md)
- [成本超标的 spec 应该长什么样](./advance/05-成本超标spec长什么样.md)

## 工具

Week 2 装 OpenSpec（Week 1 的三个 skill 继续保留）：

```bash
npm install -g @fission-ai/openspec@latest
openspec --version

cd your-project
openspec init
```

OpenSpec 的 10 个命令里 · Week 2 用 7 个：

```
/opsx:new <name>      创建新 change
/opsx:ff              fast-forward 推进所有 artifact
/opsx:apply           按 tasks.md 生成代码
/opsx:verify          对照 spec 检查实现
/opsx:sync            合并 delta 到主规范
/opsx:archive         归档完成的 change
/opsx:onboard <dir>   老项目增量接入
```
