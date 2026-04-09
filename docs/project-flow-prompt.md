# 项目流程与画图 Prompt

## 1. 项目整体流程

RegentOS 当前是一个治理型多智能体系统原型，不是完整生产系统。
它的核心不是“多个 Agent 一起协作”，而是把长链任务拆成：

- 案件化
- 票拟
- 审批
- 执行
- 监督
- 诊断
- 修复受令
- 回奏归档

### 主流程

```text
用户
-> 通政司（案件创建）
-> 内阁（票拟 / 协调 / 复审）
-> 司礼监（审批 / 封驳）
-> 动态执行层（执行）
-> 台谏院（监督）
-> 锦衣卫（问题定位 / 影响分析 / 修复建议）
-> 用户（授权修复）
-> 重跑 / 回奏 / 归档
```

### 当前 API 已能跑通的一条完整治理链

```text
created
-> accepted
-> planning
-> internal_review
-> submitted_for_approval
-> approved
-> dispatched
-> executing
-> repair_pending
-> repair_authorized
-> rerunning
-> executing
-> reporting
-> archived
```

### 关键治理原则

- 生成权和批准权分离
- 批准权和监督权分离
- 监督权和修复建议权分离
- 修复建议权和修复执行权分离

## 2. 当前代码结构

### 后端控制面

- `apps/api/main.py`
- `apps/api/routes/cases.py`
- `apps/api/routes/agents.py`
- `apps/api/routes/dashboard.py`
- `apps/api/routes/models.py`

### 核心治理逻辑

- `core/orchestrator/engine.py`
- `core/state_machine/transitions.py`
- `core/state_machine/guards.py`
- `core/registry/cases.py`
- `core/registry/agents.py`
- `core/events/bus.py`
- `core/events/schemas.py`

### Agent 骨架

- `agents/`
  当前已经有 18 个固定治理 Agent 的 `SOUL.md`

### 前端

- `apps/dashboard/src/App.tsx`
- `apps/dashboard/src/components/KanbanBoard.tsx`
- `apps/dashboard/src/components/CaseDetail.tsx`
- `apps/dashboard/src/components/JinyiweiBoard.tsx`
- `apps/dashboard/src/components/AgentContract.tsx`

## 3. 当前前端的两个分离看板

### 文渊阁主看板

负责展示：

- 案件 Kanban
- Memorials 卷宗详情
- 18 个治理 Agent 编制
- Agent 契约
- 模型运行时边界

### 锦衣卫看板

负责展示：

- 执行过程中暴露的内部问题
- 问题等级
- 当前处置状态
- 修复策略
- 修复范围
- 证据事件

注意：
锦衣卫看板和文渊阁主看板是分开显示的，不混在同一个 Kanban 里。

## 4. 当前仓库里“已经有”和“还没有”的边界

### 已经有

- 18 个治理 Agent 骨架
- 状态机
- 案件注册表
- 最小编排器
- 文渊阁 React 原型
- 独立锦衣卫看板
- 端到端完整治理链验证脚本
- 测试

### 还没有完全落地

- 真实动态执行池
- 真实模型绑定执行
- 持久化数据库
- 真实消息总线
- 完整的 incident / repair desk 系统
- 生产可用控制台

## 5. 给别的 Agent 的操作 Prompt

下面这个 prompt 可以直接交给别的 agent，让它基于当前仓库生成新的流程图。

```text
你现在要为 RegentOS 生成一版新的项目流程图与架构图。

请严格基于当前仓库已有实现来画，不要把“规划中”能力画成“已完成”。

你需要先理解这个项目的定位：
RegentOS 是一个治理型多智能体系统原型，核心是把任务纳入审批、监督、诊断和修复受令链，而不是普通的多 Agent 协作框架。

请基于下面事实作图：

1. 当前项目有五层治理结构：
- 通政司：案件入口
- 内阁：票拟 / 协调 / 复审 / 调度 / 回奏
- 司礼监：审批 / 封驳 / 批令
- 台谏院：监督
- 锦衣卫：问题定位 / 影响分析 / 修复建议

2. 当前 API 已能跑通一条完整治理链：
created
-> accepted
-> planning
-> internal_review
-> submitted_for_approval
-> approved
-> dispatched
-> executing
-> repair_pending
-> repair_authorized
-> rerunning
-> executing
-> reporting
-> archived

3. 当前前端有两个分离视图：
- 文渊阁主看板：Kanban + Memorials + Agent 契约 + 模型边界
- 锦衣卫看板：内部问题、等级、处置状态、修复建议、证据事件

4. 当前已经有 18 个固定治理 Agent 的骨架和 SOUL 文件，但真实 worker 和真实模型绑定还没有全部落地。

5. 当前仍是原型骨架，不是生产可用系统。

请输出 3 部分内容：

A. 一张“项目总流程图”
要求：
- 用 Mermaid flowchart
- 从“用户提交任务”开始，到“归档”结束
- 明确表现审批、监督、诊断、修复受令的分离

B. 一张“前端看板结构图”
要求：
- 明确分开画“文渊阁主看板”和“锦衣卫看板”
- 不要把锦衣卫看板画成文渊阁 Kanban 的一个小模块

C. 一张“代码结构与数据流图”
要求：
- 标出 apps/api、core/orchestrator、core/registry、core/state_machine、agents、apps/dashboard
- 标出 cases API、dashboard API、agent registry、timeline、jinyiwei-board 之间的数据流

额外要求：
- 所有图都要中文说明
- 图风格清晰、不要过度装饰
- 用“已实现 / 开发中 / 规划中”三种状态标识
- 不要虚构数据库、消息总线、worker 集群等当前未落地能力
```

## 6. 如果你想让别的 Agent 画得更像“展示图”

你可以再追加一句：

```text
请在 Mermaid 图之后，再补一版适合 README 展示的简化图，要求更适合 GitHub 首页阅读，节点更少、主线更突出。
```
