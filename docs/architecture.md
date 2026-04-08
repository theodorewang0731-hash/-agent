# RegentOS Architecture

## 文档目的

这份文档把 RegentOS 从首页叙事进一步展开成正式架构说明。
README 负责回答“这是什么、解决什么问题、当前做到哪一步”，这里负责回答“系统如何分层、角色如何协作、状态如何流转、哪些能力已经落地、哪些仍属于设计目标”。

本文档以当前仓库实现为准，同时保留完整设计的方向说明。
凡是尚未写进代码的内容，都会明确标成“规划中”或“设计目标”。

## 1. 系统定位

RegentOS 是一个治理型多智能体系统原型。
它的核心不是让多个 Agent 更高效地讨论，而是把长链任务中的五类权力拆开：

- 任务入口权
- 方案起草权
- 正式审批权
- 过程监督权
- 修复建议与修复授权权

系统的基本假设是：

- 生成不等于批准
- 批准不等于监督
- 监督不等于修复
- 建议修复不等于有权执行修复

## 2. 五层治理结构

### 2.1 通政司

职责：

- 接收用户输入
- 建立案件
- 生成统一 `case_id`
- 固化原始旨意、任务摘要和元信息

工程映射：

- `apps/api/routes/cases.py`
- `core/registry/cases.py`
- `core/events/schemas.py`

### 2.2 内阁

职责：

- 将原始旨意转写为正式执行草案
- 完成票拟、复审、执行协调与回奏组织
- 把自然语言任务变成可审批、可执行、可追责的结构化方案

当前实现：

- `core/orchestrator/engine.py` 中的最小编排逻辑
- `agents/cabinet/coordinator/SOUL.md`

设计目标：

- 首辅协调
- 票拟草拟
- 校核复审
- 执行调度
- 回奏反馈

### 2.3 司礼监

职责：

- 对内阁票拟稿进行正式审批
- 决定批准、封驳或升级
- 确保未经批准的方案不能进入执行

当前实现：

- `submitted_for_approval -> approved / rejected`
- `agents/silijian/approver/SOUL.md`

设计目标：

- 掌印审批
- 秉笔批令
- 封驳记录

### 2.4 台谏院

职责：

- 监督是否跳步、漏审、越权或偏航
- 记录异常、滞塞和违规迹象
- 与生成、审批和修复层保持独立

当前实现：

- 权限矩阵草案
- 状态机约束
- `agents/censorship/inspector/SOUL.md`

设计目标：

- 吏科监察
- 户科监察
- 礼科监察
- 兵科监察
- 刑科监察
- 工科监察
- 都察总巡

### 2.5 锦衣卫

职责：

- 定位异常智能体、模块和步骤
- 分析影响范围与传播链
- 生成补丁、回滚或重跑建议
- 将修复建议提交给用户审批

当前实现：

- `repair_pending -> repair_authorized`
- `repair-order` 接口
- `agents/jinyiwei/advisor/SOUL.md`

设计目标：

- 问题定位
- 影响分析
- 修复建议

## 3. 角色编制

RegentOS 的完整设计目标包含 18 个固定治理 Agent。
当前仓库尚未实现全部角色，但完整编制如下：

### 通政司

- 受理建档
- 卷宗登记

### 内阁

- 首辅协调
- 票拟草拟
- 校核复审
- 执行调度
- 回奏反馈

### 司礼监

- 掌印审批
- 秉笔批令
- 封驳记录

### 台谏院

- 吏科监察
- 户科监察
- 礼科监察
- 兵科监察
- 刑科监察
- 工科监察
- 都察总巡

### 锦衣卫

- 问题定位
- 影响分析
- 修复建议

除固定治理层外，系统还存在动态执行池。
动态执行池只属于执行层，不属于治理层。

设计中的动态执行角色包括：

- Code Executor
- Research Worker
- Data Analyst
- API Builder
- QA Validator
- Infra Operator
- Writer / Editor
- Domain Specialist

## 4. 控制面

RegentOS 的核心不只是角色集合，还包括一个最小控制面。

### 4.1 Gateway

作用：

- 接旨
- 建档
- 统一输入格式

当前映射：

- `POST /api/cases`

### 4.2 Orchestrator

作用：

- 驱动案件状态流转
- 衔接建档、票拟、审批、修复受令等关键环节

当前映射：

- `core/orchestrator/engine.py`

### 4.3 Event Bus

作用：

- 记录案件事件
- 提供统一时间线
- 为后续真实事件总线做抽象占位

当前映射：

- `core/events/bus.py`
- `core/events/schemas.py`

当前状态：

- 已实现内存版事件总线
- Redis Streams / NATS 仍在规划中

### 4.4 State Machine

作用：

- 强制合法状态转换
- 阻止跳步、绕审和未授权修复

当前映射：

- `core/state_machine/transitions.py`
- `core/state_machine/guards.py`

### 4.5 Permission Matrix

作用：

- 限制谁能给谁发消息
- 为监督和越权检测提供规则基础

当前映射：

- `core/permissions/matrix.py`

### 4.6 Case Registry

作用：

- 保存案件对象
- 维护当前状态、元信息和时间线索引

当前映射：

- `core/registry/cases.py`

### 4.7 Replay / Archive

作用：

- 导出案件时间线
- 为卷宗回放和审计提供基础

当前映射：

- `core/replay/recorder.py`

### 4.8 Model Runtime Layer

作用：

- 为每个治理 Agent 绑定模型来源
- 支持远程 API、本地蒸馏模型和本地完整大模型
- 保持模型绑定与治理角色解耦

当前映射：

- `core/registry/agents.py`
- `GET /api/models/runtime-capabilities`

设计原则：

- 18 个治理 Agent 都应支持独立模型绑定
- RegentOS 的设计本身不限制本地模型大小
- 实际运行上限由硬件、推理后端、量化配置和上下文窗口决定

当前配置样例：

- `config/.env.example`
- `config/model-bindings.example.json`

## 5. 主流程

```text
用户
→ 通政司（案件化）
→ 内阁（票拟）
→ 司礼监（审批 / 封驳）
→ 动态执行池（执行，规划中）
→ 台谏院（全过程监督）
→ 锦衣卫（异常诊断与修复建议）
→ 用户（批准修复 / 重跑 / 冻结 / 终止）
```

当前原型中的编排捷径：

- `accept_case` 会把案件从 `created` 推进到 `planning`
- `submit_for_approval` 会把案件从 `planning` 推进到 `submitted_for_approval`
- `approve_case` 会把案件从 `submitted_for_approval` 直接推进到 `executing`

最后这一点是出于 MVP 简化。
因为真实动态执行池还没有实现，所以批准后的 `dispatched -> executing` 目前由编排器直接推进。

## 6. 状态机

### 6.1 主流程

```text
created
→ accepted
→ planning
→ internal_review
→ submitted_for_approval
→ approved / rejected / escalated
→ dispatched
→ executing
→ reporting
→ archived
```

### 6.2 异常分支

```text
executing
→ repair_pending
→ repair_authorized
→ rerunning
→ executing
```

### 6.3 人工干预

当前原型已支持的人工干预包括：

- pause
- resume
- freeze
- cancel
- repair-order

当前规则：

- `pause` 仅允许在运行态使用
- `resume` 只从 `paused` 恢复到先前运行态
- `repair-order` 仅能在 `repair_pending` 之后生效

### 6.4 核心约束

- 未经 `approved`，不得进入 `dispatched`
- 未经 `repair_authorized`，不得进入 `rerunning`
- 非法状态跳转必须被拒绝

## 7. 权限矩阵

当前权限矩阵是最小草案：

| From | To |
|------|----|
| `imperial_user` | `gateway` |
| `gateway` | `cabinet` |
| `cabinet` | `silijian`, `dynamic_pool`, `imperial_user` |
| `silijian` | `cabinet`, `imperial_user` |
| `censorship` | `jinyiwei`, `imperial_user` |
| `jinyiwei` | `imperial_user` |
| `dynamic_pool` | `cabinet` |

这张矩阵当前主要承担两个作用：

- 表达系统分权意图
- 为后续越权检测留下结构化规则基础

## 8. 卷宗化与回放

RegentOS 不把任务视为零散日志，而把它视为案件卷宗。

卷宗在设计上包含：

- 原始旨意
- 内阁票拟版本
- 司礼监批令 / 封驳记录
- 台谏院监督日志
- 锦衣卫诊断报告
- 用户修复令 / 冻结令 / 终止令
- 最终回奏
- 状态时间线
- 相关事件索引

当前已落地的最小能力：

- 每个案件有独立 `case_id`
- 状态变更会写入事件时间线
- 时间线可导出为 JSON

当前尚未落地：

- Markdown / PDF 审计包
- 多版本对比
- 风险路径追踪
- 图形化回放

## 9. 人工干预模型

在 RegentOS 里，人工干预不是“直接打断线程”，而是应当表现为正式命令。

当前接口包括：

- `POST /api/cases/{case_id}/pause`
- `POST /api/cases/{case_id}/resume`
- `POST /api/cases/{case_id}/freeze`
- `POST /api/cases/{case_id}/cancel`
- `POST /api/cases/{case_id}/repair-order`

这组接口的意图是把人工干预纳入同一条治理链，而不是留在系统之外。

## 10. 文渊阁中枢

旧 README 里曾经列过较完整的 Dashboard 设想。
这些内容仍然保留为设计稿，但不应在首页被描述成既成事实。

当前保留的界面方向：

- Kanban
- Memorials
- Monitor
- Officials
- Models
- Skills
- Sessions
- Repair Desk

当前状态：

- 已有 React 原型
- v0.1 已优先落下 Kanban + Memorials 的最小版本
- 设计稿见 `docs/dashboard-mvp.md`

## 11. 项目结构

当前仓库结构：

```text
agents.json
config/
apps/
  api/
  dashboard/
  worker/
agents/
  cabinet/
  silijian/
  censorship/
  jinyiwei/
core/
  events/
  orchestrator/
  permissions/
  registry/
  replay/
  state_machine/
docs/
  architecture.md
  api.md
  getting-started.md
examples/
scripts/
tests/
```

这个结构不是为了“看起来完整”，而是为了对应治理链上的关键职责。

## 12. 当前实现与设计目标的边界

### 已实现

- API 骨架
- 案件注册表
- 事件时间线
- 基础状态机
- 基础权限矩阵
- 最小编排器
- 18 个固定治理 `SOUL.md` 骨架
- Agent 样式契约与输入输出示例
- 基础测试
- `agents.json` manifest
- React Dashboard 原型
- 安装脚本、运行脚本、配置样例、案例文档

### 开发中

- 更完整的审批 / 封驳 / 返工闭环
- 更细的错误处理和案件约束
- 更完整的卷宗导出能力

### 规划中

- 动态执行池
- 更完整的文渊阁中枢控制台
- 真实事件总线
- 模型中心
- Skills Registry
- 风险策略 DSL

## 13. 分阶段开发路线

### 第一阶段：基础控制面

- `core/state_machine`
- `core/permissions`
- `core/events`
- `apps/api/main.py`

### 第二阶段：治理角色骨架

- `core/orchestrator`
- `agents/cabinet`
- `agents/silijian`
- `agents/censorship`
- `agents/jinyiwei`

### 第三阶段：回放与界面

- `core/replay`
- 文渊阁中枢
- 更完整的可观测性

## 14. 非目标

当前 v0.1 原型不追求：

- 完整 Dashboard
- 真实执行池并发调度
- 模型热切换
- Skills 管理中心
- 多租户
- 一次性实现全部 18 个 Agent 的真实 worker

当前目标是先把治理主线做成可验证的系统骨架。
