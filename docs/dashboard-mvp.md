# Dashboard MVP

## 目标

v0.1 的界面目标不是一次做出完整控制台，而是先把两件最关键的东西可视化：

- `Kanban`：看见案件当前在哪个状态
- `Memorials`：看见案件卷宗和时间线

这份文档既是 `文渊阁中枢` 的最小设计稿，也是当前 React 原型的说明文档。

## 页面范围

### 1. Kanban

展示：

- 案件编号
- 标题
- 当前状态
- 优先级
- 最近更新时间
- 可用干预动作

### 2. Memorials

展示：

- 原始旨意
- 状态时间线
- 关键事件
- 修复令
- 导出入口

## 数据来源

- `/api/cases`
- `/api/cases/{case_id}`
- `/api/cases/{case_id}/timeline`
- `/api/agents`
- `/api/models/runtime-capabilities`

## 页面结构

```mermaid
flowchart TB
    A["文渊阁中枢"] --> B["顶部状态条"]
    A --> C["Kanban 页面"]
    A --> D["Memorials 页面"]

    C --> C1["Created / Accepted"]
    C --> C2["Planning / Review"]
    C --> C3["Approval"]
    C --> C4["Executing"]
    C --> C5["Repair / Frozen / Archived"]

    D --> D1["案件摘要"]
    D --> D2["时间线事件流"]
    D --> D3["审批与封驳记录"]
    D --> D4["修复建议与修复令"]
    D --> D5["导出 JSON / 后续扩展 PDF"]
```

## 模拟展示图

下面这张图是当前 React 原型所采用的信息布局。

```mermaid
flowchart LR
    subgraph Left["Kanban"]
        K1["created"]
        K2["planning"]
        K3["submitted_for_approval"]
        K4["executing"]
        K5["repair_pending"]
    end

    subgraph Right["Memorial Detail"]
        M1["案件标题 / 优先级 / case_id"]
        M2["状态时间线"]
        M3["关键事件列表"]
        M4["修复令与备注"]
    end

    K3 --> M1
    K3 --> M2
    K4 --> M3
    K5 --> M4
```

## 前端建议结构

建议目录：

```text
apps/dashboard/
  src/
    pages/
      KanbanPage.tsx
      MemorialsPage.tsx
    components/
      CaseColumn.tsx
      CaseCard.tsx
      TimelinePanel.tsx
      EventList.tsx
      RepairOrderPanel.tsx
    lib/
      api.ts
      mock.ts
```

## MVP 交互

### Kanban

- 点击案件卡片
- 右侧打开卷宗详情
- 从卡片直接触发 `pause / resume / freeze / cancel`

### Memorials

- 按时间顺序展示事件
- 高亮审批、封驳、修复受令事件
- 支持导出 JSON

## 与 18 个 Agent 的关系

Dashboard 不需要在 v0.1 就做出 18 个 Agent 的独立控制面。
但建议至少展示：

- 固定治理 Agent 总数
- 已有骨架的 Agent
- 每个 Agent 的样式类型
- 每个 Agent 支持的模型来源

这样界面就能和 Agent Catalog API 对齐。
