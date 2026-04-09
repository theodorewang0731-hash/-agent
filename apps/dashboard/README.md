# Dashboard Prototype

这里是 RegentOS 的 `文渊阁中枢` React 前端原型。
当前页面除了文渊阁案件 Kanban 和卷宗视角，也会单独展示一个锦衣卫看板，
用于查看内部问题、等级划分和修复建议；此外还会展示 18 个治理 Agent 的编制与样式契约。

当前已提供：

- `src/`：React + TypeScript 前端源码
- `server.py`：用于发布构建产物的轻量静态服务器
- `index.html` / `vite.config.ts`：Vite 入口与构建配置
- 依赖现有 API 实时取数

v0.1 的目标不是一次做完整控制台，而是先实现：

- Kanban
- Memorials

设计稿见 `../../docs/dashboard-mvp.md`。
注意：当前仍是原型骨架，并不能直接投入使用。
