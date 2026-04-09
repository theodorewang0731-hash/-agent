# RegentOS API

## 文档范围

这份文档描述当前仓库中已经存在的 API，以及围绕 18 个固定治理 Agent 的结构化元数据接口。
凡是尚未实现的控制能力，都会明确标记为“规划中”。

## 1. API 设计原则

- 先案件化，再流转
- 关键状态必须显式推进，避免隐式跳步
- Agent 元数据和案件数据分离
- 模型绑定能力按 Agent 独立设计，而不是全局单模型

## 2. 当前已实现的 REST API

### 2.1 Cases

| Method | Path | 说明 |
|--------|------|------|
| `GET` | `/api/cases` | 列出案件 |
| `POST` | `/api/cases` | 创建案件，保持在 `created` |
| `GET` | `/api/cases/{case_id}` | 查询案件详情 |
| `GET` | `/api/cases/{case_id}/timeline` | 查看案件时间线 |
| `POST` | `/api/cases/{case_id}/accept` | 进入受理与票拟起点 |
| `POST` | `/api/cases/{case_id}/submit-for-approval` | 提交司礼监审批 |
| `POST` | `/api/cases/{case_id}/approve` | 批准并推进到执行前状态 |
| `POST` | `/api/cases/{case_id}/reject` | 封驳并附带原因 |
| `POST` | `/api/cases/{case_id}/repair-pending` | 标记进入修复待令阶段 |
| `POST` | `/api/cases/{case_id}/rework` | 明确进入返工态 |
| `POST` | `/api/cases/{case_id}/pause` | 暂停运行态案件 |
| `POST` | `/api/cases/{case_id}/resume` | 从暂停恢复到先前运行态 |
| `POST` | `/api/cases/{case_id}/freeze` | 冻结案件 |
| `POST` | `/api/cases/{case_id}/cancel` | 取消案件 |
| `POST` | `/api/cases/{case_id}/repair-order` | 用户正式下修复令 |
| `POST` | `/api/cases/{case_id}/rerun` | 执行已授权修复并返回执行态 |
| `POST` | `/api/cases/{case_id}/report` | 进入回奏与报告整理阶段 |
| `POST` | `/api/cases/{case_id}/archive` | 完成归档 |

### 2.2 Agents

| Method | Path | 说明 |
|--------|------|------|
| `GET` | `/api/agents` | 列出 18 个固定治理 Agent |
| `GET` | `/api/agents/styles` | 查看 Agent 样式类型定义 |
| `GET` | `/api/agents/contracts` | 查看全部 Agent 样式契约 |
| `GET` | `/api/agents/{agent_id}` | 查看单个 Agent 的元数据、样式和模型来源支持 |
| `GET` | `/api/agents/{agent_id}/contract` | 查看单个 Agent 的输入输出契约 |

支持查询参数：

- `department`
- `style_id`
- `implemented_only`

### 2.3 Models

| Method | Path | 说明 |
|--------|------|------|
| `GET` | `/api/models/runtime-capabilities` | 查看远程 API、本地蒸馏模型、本地完整大模型的能力说明 |

### 2.4 Dashboard

| Method | Path | 说明 |
|--------|------|------|
| `GET` | `/api/dashboard/summary` | 返回看板摘要、案件数量、治理 Agent 数量和最近案件 |
| `GET` | `/api/dashboard/jinyiwei-board` | 返回锦衣卫问题看板、等级统计和修复建议 |

## 3. 18 个固定治理 Agent

下面这 18 个 Agent 是 RegentOS 的固定治理层。
它们和动态执行池不同，固定治理层负责权力边界，而动态执行池负责任务执行。

| Agent ID | 名称 | 部门 | 样式 | 当前状态 |
|----------|------|------|------|----------|
| `cabinet.coordinator` | 首辅协调 Agent | 内阁 | `coordinator` | 已有骨架 |
| `cabinet.drafter` | 票拟草拟 Agent | 内阁 | `drafter` | 已有骨架 |
| `cabinet.reviewer` | 校核复审 Agent | 内阁 | `reviewer` | 已有骨架 |
| `cabinet.dispatcher` | 执行调度 Agent | 内阁 | `dispatcher` | 已有骨架 |
| `cabinet.reporter` | 回奏反馈 Agent | 内阁 | `reporter` | 已有骨架 |
| `silijian.approver` | 掌印审批 Agent | 司礼监 | `approver` | 已有骨架 |
| `silijian.decree_writer` | 秉笔批令 Agent | 司礼监 | `decree_writer` | 已有骨架 |
| `silijian.rejector` | 封驳记录 Agent | 司礼监 | `rejector` | 已有骨架 |
| `censorship.personnel` | 吏科监察 Agent | 台谏院 | `oversight` | 已有骨架 |
| `censorship.finance` | 户科监察 Agent | 台谏院 | `oversight` | 已有骨架 |
| `censorship.protocol` | 礼科监察 Agent | 台谏院 | `oversight` | 已有骨架 |
| `censorship.military` | 兵科监察 Agent | 台谏院 | `oversight` | 已有骨架 |
| `censorship.justice` | 刑科监察 Agent | 台谏院 | `oversight` | 已有骨架 |
| `censorship.engineering` | 工科监察 Agent | 台谏院 | `oversight` | 已有骨架 |
| `censorship.inspector` | 都察总巡 Agent | 台谏院 | `chief_oversight` | 已有骨架 |
| `jinyiwei.locator` | 问题定位 Agent | 锦衣卫 | `diagnostician` | 已有骨架 |
| `jinyiwei.analyzer` | 影响分析 Agent | 锦衣卫 | `impact_analyzer` | 已有骨架 |
| `jinyiwei.advisor` | 修复建议 Agent | 锦衣卫 | `repair_advisor` | 已有骨架 |

## 4. Agent 样式定义

“样式”在这里不是 UI 皮肤，而是 Agent 的行为形态和 I/O 合约。

| Style ID | 适用 Agent | 核心职责 | 推荐输出 |
|----------|------------|----------|----------|
| `coordinator` | 首辅协调 | 跨步骤协调、升级判断 | `decision`, `summary`, `next_target`, `risk_level` |
| `drafter` | 票拟草拟 | 生成待批草案 | `objective`, `plan`, `dependencies`, `risks` |
| `reviewer` | 校核复审 | 检查完整性与返工项 | `issues`, `required_rework`, `confidence` |
| `dispatcher` | 执行调度 | 派发执行任务 | `dispatch_plan`, `targets`, `ordering` |
| `reporter` | 回奏反馈 | 汇总结果与归档摘要 | `report`, `outcome`, `artifacts` |
| `approver` | 掌印审批 | 正式批准 / 驳回 / 升级 | `decision`, `reason`, `required_rework` |
| `decree_writer` | 秉笔批令 | 输出正式批令 | `decree`, `constraints`, `effective_scope` |
| `rejector` | 封驳记录 | 记录驳回与版本差异 | `rejection_reason`, `diff_summary`, `rework_items` |
| `oversight` | 六科监察 | 单维度监督与告警 | `alert_type`, `severity`, `summary` |
| `chief_oversight` | 都察总巡 | 跨流巡检与升级 | `oversight_decision`, `alerts`, `escalation_target` |
| `diagnostician` | 问题定位 | 故障定位 | `root_cause`, `affected_step`, `evidence` |
| `impact_analyzer` | 影响分析 | 传播链分析 | `impact_scope`, `blast_radius`, `downstream_risks` |
| `repair_advisor` | 修复建议 | 生成补丁 / 回滚 / 重跑建议 | `repair_strategy`, `scope`, `risk_level`, `requires_user_order` |

## 5. 18 个 Agent 需要什么样的模型

每个固定治理 Agent 都应当能独立绑定模型来源，至少支持三类：

- `remote_api`
- `local_distilled`
- `local_full`

这意味着：

- 可以接入云端或私有 API 模型
- 可以接入本地蒸馏、量化或专项配置模型
- 可以接入本地完整大模型

重要边界：

- RegentOS 的设计本身不限制本地模型大小
- 真正的上限由本机硬件、推理后端、量化方式、上下文长度和运行配置决定

换句话说，18 个治理 Agent 不要求全部走云 API，也不要求只能跑轻量模型。

## 6. 示例：查询单个 Agent

```bash
curl http://127.0.0.1:8000/api/agents/cabinet.coordinator
```

示例返回：

```json
{
  "agent_id": "cabinet.coordinator",
  "display_name": "首辅协调 Agent",
  "department": "cabinet",
  "style_id": "coordinator",
  "summary": "统筹票拟、复审、提案成形与审批上呈。",
  "implemented": true,
  "soul_path": "agents/cabinet/coordinator/SOUL.md",
  "style": {
    "style_id": "coordinator",
    "name": "Coordinator Agent",
    "description": "负责跨步骤协调、升级判断与下一目标选择。",
    "interaction_mode": "event-driven",
    "output_mode": "structured-json",
    "execution_boundary": "不能直接审批，也不能直接修复。"
  },
  "style_contract": {
    "input_fields": [
      {
        "name": "case_summary",
        "type": "string",
        "required": true,
        "description": "案件摘要和当前目标。"
      }
    ],
    "output_fields": [
      {
        "name": "decision",
        "type": "string",
        "description": "submit_for_approval | rework | escalate"
      }
    ],
    "example_input": {
      "case_summary": "重构案件已完成票拟，需要判断是否上呈审批。"
    },
    "example_output": {
      "decision": "submit_for_approval"
    }
  },
  "supported_model_sources": [
    "remote_api",
    "local_distilled",
    "local_full"
  ],
  "local_model_size_limit": "none_by_system"
}
```

## 7. 示例：查看样式契约

```bash
curl http://127.0.0.1:8000/api/agents/cabinet.coordinator/contract
```

这个接口返回：

- 当前 Agent 的样式 ID
- 该样式的输入字段
- 该样式的输出字段
- 示例输入与示例输出

如果想一次列出全部契约，可使用：

```bash
curl http://127.0.0.1:8000/api/agents/contracts
```

## 8. 示例：查看模型运行时能力

```bash
curl http://127.0.0.1:8000/api/models/runtime-capabilities
```

这个接口返回三类模型来源说明：

- 远程 API 模型
- 本地蒸馏模型
- 本地完整大模型

以及系统级策略：

- 系统本身不限制本地模型大小
- 实际可用上限取决于硬件和推理运行时

## 9. 规划中的 Agent 控制 API

下面这些接口目前还没有实现，但建议未来按这套形态落地：

| Method | Path | 用途 | 状态 |
|--------|------|------|------|
| `POST` | `/api/agents/{agent_id}/invoke` | 触发单个治理 Agent 处理输入 | 规划中 |
| `POST` | `/api/agents/{agent_id}/bind-model` | 为 Agent 绑定远程或本地模型 | 规划中 |
| `POST` | `/api/agents/{agent_id}/bind-skill` | 为 Agent 绑定技能包 | 规划中 |
| `GET` | `/api/agents/{agent_id}/health` | 查看 Agent 心跳和可用性 | 规划中 |
| `GET` | `/api/agents/{agent_id}/history` | 查看 Agent 历史决策或告警 | 规划中 |

这些接口应当建立在当前的 Agent 元数据层之上，而不是先做 UI 再回头补控制面。

## 10. Manifest 文件

仓库根目录的 `agents.json` 是当前 18 个固定治理 Agent 的静态 manifest 快照。
它适合被前端、外部运行时或集成脚本直接消费。

可通过下面命令重新导出：

```bash
python scripts/export_agent_manifest.py
```
