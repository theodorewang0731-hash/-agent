from copy import deepcopy


AGENT_STYLES = {
    "coordinator": {
        "style_id": "coordinator",
        "name": "Coordinator Agent",
        "description": "负责跨步骤协调、升级判断与下一目标选择。",
        "interaction_mode": "event-driven",
        "output_mode": "structured-json",
        "execution_boundary": "不能直接审批，也不能直接修复。",
    },
    "drafter": {
        "style_id": "drafter",
        "name": "Drafter Agent",
        "description": "负责票拟草案，把原始任务转成可审批的正式稿。",
        "interaction_mode": "task-to-plan",
        "output_mode": "plan-json",
        "execution_boundary": "不能自行批准，也不能直接执行高风险动作。",
    },
    "reviewer": {
        "style_id": "reviewer",
        "name": "Reviewer Agent",
        "description": "负责复审、逻辑校验、风险识别和补证建议。",
        "interaction_mode": "plan-review",
        "output_mode": "review-json",
        "execution_boundary": "不能跳过审批门放行方案。",
    },
    "dispatcher": {
        "style_id": "dispatcher",
        "name": "Dispatcher Agent",
        "description": "负责把已批准方案拆成执行指令并派发给动态执行池。",
        "interaction_mode": "instruction-routing",
        "output_mode": "dispatch-json",
        "execution_boundary": "不能自己写批准意见。",
    },
    "reporter": {
        "style_id": "reporter",
        "name": "Reporter Agent",
        "description": "负责汇总执行结果、整理回奏与归档摘要。",
        "interaction_mode": "result-synthesis",
        "output_mode": "report-json",
        "execution_boundary": "不能覆盖原始事件记录。",
    },
    "approver": {
        "style_id": "approver",
        "name": "Approver Agent",
        "description": "负责正式审批、驳回或升级，不参与执行。",
        "interaction_mode": "approval-gate",
        "output_mode": "approval-json",
        "execution_boundary": "不能直接执行任务或修复系统。",
    },
    "decree_writer": {
        "style_id": "decree_writer",
        "name": "Decree Writer Agent",
        "description": "负责把审批结果转写成正式批令和执行约束。",
        "interaction_mode": "approval-to-decree",
        "output_mode": "decree-json",
        "execution_boundary": "不能替代审批本身。",
    },
    "rejector": {
        "style_id": "rejector",
        "name": "Rejector Agent",
        "description": "负责封驳记录、返工要求和版本差异说明。",
        "interaction_mode": "append-only-review",
        "output_mode": "rejection-json",
        "execution_boundary": "只能追加，不应覆盖历史记录。",
    },
    "oversight": {
        "style_id": "oversight",
        "name": "Oversight Agent",
        "description": "负责某一监督维度的持续监听、违规识别和告警生成。",
        "interaction_mode": "event-subscription",
        "output_mode": "alert-json",
        "execution_boundary": "不能审批、不能执行、不能直接修复。",
    },
    "chief_oversight": {
        "style_id": "chief_oversight",
        "name": "Chief Oversight Agent",
        "description": "负责跨模块巡检、合并告警、决定是否升级到用户或锦衣卫。",
        "interaction_mode": "cross-stream-audit",
        "output_mode": "oversight-json",
        "execution_boundary": "不能直接干预执行链，只能上报或建议。",
    },
    "diagnostician": {
        "style_id": "diagnostician",
        "name": "Diagnostician Agent",
        "description": "负责定位问题源头和受影响步骤。",
        "interaction_mode": "incident-analysis",
        "output_mode": "diagnosis-json",
        "execution_boundary": "不能直接改系统。",
    },
    "impact_analyzer": {
        "style_id": "impact_analyzer",
        "name": "Impact Analyzer Agent",
        "description": "负责识别传播链、影响范围和潜在风险扩散。",
        "interaction_mode": "impact-analysis",
        "output_mode": "impact-json",
        "execution_boundary": "不能越过用户直接做修复决策。",
    },
    "repair_advisor": {
        "style_id": "repair_advisor",
        "name": "Repair Advisor Agent",
        "description": "负责生成补丁、回滚或重跑建议，但不直接执行。",
        "interaction_mode": "repair-recommendation",
        "output_mode": "repair-json",
        "execution_boundary": "修复必须受令，不能直接修改系统。",
    },
}

AGENT_STYLE_CONTRACTS = {
    "coordinator": {
        "input_fields": [
            {"name": "case_summary", "type": "string", "required": True, "description": "案件摘要和当前目标。"},
            {"name": "current_state", "type": "string", "required": True, "description": "案件当前状态。"},
            {"name": "prior_events", "type": "array", "required": True, "description": "关键历史事件与审批痕迹。"},
            {"name": "reviewer_comments", "type": "array", "required": False, "description": "复审意见与补证建议。"},
        ],
        "output_fields": [
            {"name": "decision", "type": "string", "description": "submit_for_approval | rework | escalate"},
            {"name": "summary", "type": "string", "description": "协调结论摘要。"},
            {"name": "next_target", "type": "string", "description": "下一个治理目标。"},
            {"name": "risk_level", "type": "string", "description": "low | medium | high | critical"},
        ],
        "example_input": {
            "case_summary": "重构案件已完成票拟，需要判断是否上呈审批。",
            "current_state": "planning",
            "prior_events": ["case.created", "case.state.accepted", "case.planning.started"],
            "reviewer_comments": ["测试范围需补充", "需标注回滚路径"],
        },
        "example_output": {
            "decision": "submit_for_approval",
            "summary": "票拟稿结构完整，可上呈司礼监审批。",
            "next_target": "silijian.approver",
            "risk_level": "medium",
        },
    },
    "drafter": {
        "input_fields": [
            {"name": "imperial_intent", "type": "string", "required": True, "description": "原始旨意或任务描述。"},
            {"name": "constraints", "type": "array", "required": False, "description": "必须遵守的约束和边界。"},
            {"name": "available_tools", "type": "array", "required": False, "description": "可调用工具与资源。"},
        ],
        "output_fields": [
            {"name": "objective", "type": "string", "description": "明确的执行目标。"},
            {"name": "plan", "type": "array", "description": "分步骤执行草案。"},
            {"name": "dependencies", "type": "array", "description": "关键依赖与前置条件。"},
            {"name": "risks", "type": "array", "description": "草案中识别的风险项。"},
        ],
        "example_input": {
            "imperial_intent": "设计企业知识库系统并明确权限分级。",
            "constraints": ["需保留审计追踪", "不得直接变更生产数据库"],
            "available_tools": ["FastAPI", "PostgreSQL", "vector search"],
        },
        "example_output": {
            "objective": "产出可审批的系统设计草案和实施步骤。",
            "plan": ["拆解检索链路", "设计权限模型", "补齐测试与回滚方案"],
            "dependencies": ["数据库 schema", "向量索引方案"],
            "risks": ["检索性能抖动", "权限继承复杂度"],
        },
    },
    "reviewer": {
        "input_fields": [
            {"name": "draft_plan", "type": "object", "required": True, "description": "票拟草案全文。"},
            {"name": "acceptance_criteria", "type": "array", "required": False, "description": "验收标准与约束。"},
            {"name": "risk_context", "type": "array", "required": False, "description": "额外风险背景。"},
        ],
        "output_fields": [
            {"name": "issues", "type": "array", "description": "发现的问题列表。"},
            {"name": "required_rework", "type": "array", "description": "必须返工项。"},
            {"name": "confidence", "type": "number", "description": "对草案完整性的置信度。"},
        ],
        "example_input": {
            "draft_plan": {"objective": "设计系统", "plan": ["建模", "实现", "测试"]},
            "acceptance_criteria": ["必须可回滚", "必须给出监控指标"],
            "risk_context": ["上线窗口有限"],
        },
        "example_output": {
            "issues": ["缺少回滚方案", "未说明数据迁移影响"],
            "required_rework": ["补充回滚步骤", "补充迁移风险说明"],
            "confidence": 0.72,
        },
    },
    "dispatcher": {
        "input_fields": [
            {"name": "approved_plan", "type": "object", "required": True, "description": "已批准的执行计划。"},
            {"name": "decree_constraints", "type": "array", "required": False, "description": "批令中的执行限制。"},
            {"name": "worker_pool", "type": "array", "required": True, "description": "可分配的动态执行 Agent 列表。"},
        ],
        "output_fields": [
            {"name": "dispatch_plan", "type": "array", "description": "派发指令列表。"},
            {"name": "targets", "type": "array", "description": "目标执行 Agent。"},
            {"name": "ordering", "type": "array", "description": "执行顺序或并行批次。"},
        ],
        "example_input": {
            "approved_plan": {"plan": ["生成迁移脚本", "执行测试", "整理报告"]},
            "decree_constraints": ["禁止直接写生产库", "先在沙箱验证"],
            "worker_pool": ["code-executor", "qa-validator"],
        },
        "example_output": {
            "dispatch_plan": ["code-executor: 生成迁移脚本", "qa-validator: 运行回归测试"],
            "targets": ["code-executor", "qa-validator"],
            "ordering": ["batch-1", "batch-2"],
        },
    },
    "reporter": {
        "input_fields": [
            {"name": "execution_logs", "type": "array", "required": True, "description": "执行期日志和事件。"},
            {"name": "artifacts", "type": "array", "required": False, "description": "产物、报告和附件。"},
            {"name": "final_state", "type": "string", "required": True, "description": "案件最终状态。"},
        ],
        "output_fields": [
            {"name": "report", "type": "string", "description": "回奏摘要。"},
            {"name": "outcome", "type": "string", "description": "执行结果判断。"},
            {"name": "artifacts", "type": "array", "description": "归档产物列表。"},
        ],
        "example_input": {
            "execution_logs": ["dispatch.completed", "execution.finished", "reporting.started"],
            "artifacts": ["design.md", "test-report.json"],
            "final_state": "reporting",
        },
        "example_output": {
            "report": "方案已执行完毕，测试通过并完成归档建议。",
            "outcome": "success",
            "artifacts": ["design.md", "test-report.json"],
        },
    },
    "approver": {
        "input_fields": [
            {"name": "submission", "type": "object", "required": True, "description": "待批票拟稿。"},
            {"name": "risk_notes", "type": "array", "required": False, "description": "风险说明或监督备注。"},
            {"name": "policy_checks", "type": "array", "required": False, "description": "审批策略检查结果。"},
        ],
        "output_fields": [
            {"name": "decision", "type": "string", "description": "approve | reject | escalate"},
            {"name": "reason", "type": "string", "description": "审批结论原因。"},
            {"name": "required_rework", "type": "array", "description": "封驳后必须返工项。"},
            {"name": "risk_level", "type": "string", "description": "low | medium | high | critical"},
        ],
        "example_input": {
            "submission": {"objective": "升级检索链路", "plan": ["灰度发布", "验证日志"]},
            "risk_notes": ["涉及权限收敛", "需保留回滚开关"],
            "policy_checks": ["state-machine-ok", "permission-matrix-ok"],
        },
        "example_output": {
            "decision": "approve",
            "reason": "步骤完整且风险可控。",
            "required_rework": [],
            "risk_level": "medium",
        },
    },
    "decree_writer": {
        "input_fields": [
            {"name": "approval_decision", "type": "object", "required": True, "description": "掌印审批结论。"},
            {"name": "execution_scope", "type": "string", "required": True, "description": "批令生效范围。"},
            {"name": "constraints", "type": "array", "required": False, "description": "执行限制与注意事项。"},
        ],
        "output_fields": [
            {"name": "decree", "type": "string", "description": "正式批令文本。"},
            {"name": "constraints", "type": "array", "description": "必须遵守的执行约束。"},
            {"name": "effective_scope", "type": "string", "description": "批令生效范围。"},
        ],
        "example_input": {
            "approval_decision": {"decision": "approve", "risk_level": "medium"},
            "execution_scope": "executor_pool/api_builder",
            "constraints": ["先灰度验证", "保留冻结入口"],
        },
        "example_output": {
            "decree": "准予执行，并限于既定沙箱范围内推进。",
            "constraints": ["先灰度验证", "保留冻结入口"],
            "effective_scope": "executor_pool/api_builder",
        },
    },
    "rejector": {
        "input_fields": [
            {"name": "submission", "type": "object", "required": True, "description": "被封驳的票拟稿。"},
            {"name": "approval_reason", "type": "string", "required": True, "description": "驳回理由。"},
            {"name": "version_diff", "type": "array", "required": False, "description": "版本差异与未达标点。"},
        ],
        "output_fields": [
            {"name": "rejection_reason", "type": "string", "description": "正式封驳说明。"},
            {"name": "diff_summary", "type": "array", "description": "关键差异摘要。"},
            {"name": "rework_items", "type": "array", "description": "返工要求。"},
        ],
        "example_input": {
            "submission": {"objective": "上线改造", "plan": ["直接替换服务"]},
            "approval_reason": "缺少回滚与测试说明。",
            "version_diff": ["未提供灰度方案", "缺少风险评估"],
        },
        "example_output": {
            "rejection_reason": "票拟稿证据不足，不准放行。",
            "diff_summary": ["缺少灰度方案", "缺少风险评估"],
            "rework_items": ["补齐回滚步骤", "补齐测试覆盖报告"],
        },
    },
    "oversight": {
        "input_fields": [
            {"name": "event_stream", "type": "array", "required": True, "description": "订阅到的案件事件流。"},
            {"name": "watch_scope", "type": "string", "required": True, "description": "当前监督维度。"},
            {"name": "policy_rules", "type": "array", "required": False, "description": "监督规则集。"},
        ],
        "output_fields": [
            {"name": "alert_type", "type": "string", "description": "监督告警类型。"},
            {"name": "severity", "type": "string", "description": "low | medium | high | critical"},
            {"name": "summary", "type": "string", "description": "告警摘要。"},
            {"name": "recommendation", "type": "string", "description": "observe | escalate | trigger_diagnosis"},
        ],
        "example_input": {
            "event_stream": ["case.state.approved", "dispatch.sent", "worker.error"],
            "watch_scope": "protocol",
            "policy_rules": ["接口返回必须结构化", "跨模块消息必须带 trace_id"],
        },
        "example_output": {
            "alert_type": "policy_risk",
            "severity": "high",
            "summary": "发现执行结果未附带完整 trace_id。",
            "recommendation": "escalate",
        },
    },
    "chief_oversight": {
        "input_fields": [
            {"name": "alerts", "type": "array", "required": True, "description": "六科监察上报的告警集合。"},
            {"name": "case_snapshot", "type": "object", "required": True, "description": "案件当前快照。"},
            {"name": "previous_actions", "type": "array", "required": False, "description": "既往监督处置记录。"},
        ],
        "output_fields": [
            {"name": "oversight_decision", "type": "string", "description": "observe | escalate | trigger_diagnosis"},
            {"name": "alerts", "type": "array", "description": "合并后的核心告警。"},
            {"name": "escalation_target", "type": "string", "description": "imperial_user | jinyiwei.locator | none"},
        ],
        "example_input": {
            "alerts": ["protocol violation", "resource spike"],
            "case_snapshot": {"state": "executing", "priority": "critical"},
            "previous_actions": ["observe-once"],
        },
        "example_output": {
            "oversight_decision": "trigger_diagnosis",
            "alerts": ["协议违规伴随资源异常，疑似链路偏航"],
            "escalation_target": "jinyiwei.locator",
        },
    },
    "diagnostician": {
        "input_fields": [
            {"name": "incident_report", "type": "object", "required": True, "description": "问题报告或总巡升级信息。"},
            {"name": "event_trace", "type": "array", "required": True, "description": "案件关键事件链。"},
            {"name": "system_context", "type": "array", "required": False, "description": "运行时上下文。"},
        ],
        "output_fields": [
            {"name": "root_cause", "type": "string", "description": "根因判断。"},
            {"name": "affected_step", "type": "string", "description": "受影响步骤。"},
            {"name": "evidence", "type": "array", "description": "证据链。"},
        ],
        "example_input": {
            "incident_report": {"summary": "执行阶段依赖损坏", "severity": "high"},
            "event_trace": ["execution.started", "worker.error", "repair.pending"],
            "system_context": ["executor_pool/api_builder", "dependency lock mismatch"],
        },
        "example_output": {
            "root_cause": "依赖锁文件与运行时版本不一致。",
            "affected_step": "executor_pool/api_builder",
            "evidence": ["worker.error", "dependency checksum mismatch"],
        },
    },
    "impact_analyzer": {
        "input_fields": [
            {"name": "diagnosis", "type": "object", "required": True, "description": "问题定位结论。"},
            {"name": "dependency_graph", "type": "array", "required": False, "description": "依赖关系或传播链。"},
            {"name": "active_sessions", "type": "array", "required": False, "description": "受影响会话或案件。"},
        ],
        "output_fields": [
            {"name": "impact_scope", "type": "array", "description": "影响范围。"},
            {"name": "blast_radius", "type": "string", "description": "small | medium | large"},
            {"name": "downstream_risks", "type": "array", "description": "下游扩散风险。"},
        ],
        "example_input": {
            "diagnosis": {"root_cause": "依赖损坏", "affected_step": "api_builder"},
            "dependency_graph": ["api_builder -> qa_validator", "api_builder -> deploy_check"],
            "active_sessions": ["case-a", "case-b"],
        },
        "example_output": {
            "impact_scope": ["api_builder", "qa_validator"],
            "blast_radius": "medium",
            "downstream_risks": ["测试结果不可信", "部署前校验失败"],
        },
    },
    "repair_advisor": {
        "input_fields": [
            {"name": "diagnosis", "type": "object", "required": True, "description": "问题定位结果。"},
            {"name": "impact_analysis", "type": "object", "required": True, "description": "影响分析结果。"},
            {"name": "repair_options", "type": "array", "required": False, "description": "可选修复路径。"},
        ],
        "output_fields": [
            {"name": "repair_strategy", "type": "string", "description": "patch | rollback | rerun | freeze"},
            {"name": "reason", "type": "string", "description": "建议原因。"},
            {"name": "scope", "type": "string", "description": "修复范围。"},
            {"name": "risk_level", "type": "string", "description": "low | medium | high | critical"},
            {"name": "requires_user_order", "type": "boolean", "description": "是否需要用户正式下令。"},
        ],
        "example_input": {
            "diagnosis": {"root_cause": "依赖损坏", "affected_step": "api_builder"},
            "impact_analysis": {"impact_scope": ["api_builder"], "blast_radius": "medium"},
            "repair_options": ["patch_then_rerun", "rollback"],
        },
        "example_output": {
            "repair_strategy": "patch",
            "reason": "补丁后重跑可最小化影响范围。",
            "scope": "executor_pool/api_builder",
            "risk_level": "medium",
            "requires_user_order": True,
        },
    },
}


MODEL_RUNTIME_CAPABILITIES = {
    "sources": [
        {
            "source_id": "remote_api",
            "name": "Remote API Models",
            "description": "云端或私有 API 提供的模型服务。",
        },
        {
            "source_id": "local_distilled",
            "name": "Local Distilled Models",
            "description": "本地蒸馏、量化或专门配置后的模型运行时。",
        },
        {
            "source_id": "local_full",
            "name": "Local Full-size Models",
            "description": "本地部署的完整大模型或指令模型。",
        },
    ],
    "policy": {
        "system_limit": "RegentOS 设计本身不限制本地模型大小。",
        "practical_limit": "实际可用上限取决于本机硬件、推理后端、量化方式、上下文长度与运行配置。",
        "binding_strategy": "每个治理 Agent 最终都应可独立绑定模型来源，而不是全局绑定单一模型。",
    },
}


GOVERNANCE_AGENTS = [
    {
        "agent_id": "cabinet.coordinator",
        "display_name": "首辅协调 Agent",
        "department": "cabinet",
        "style_id": "coordinator",
        "summary": "统筹票拟、复审、提案成形与审批上呈。",
        "implemented": True,
        "soul_path": "agents/cabinet/coordinator/SOUL.md",
        "allowed_targets": [
            "cabinet.drafter",
            "cabinet.reviewer",
            "silijian.approver",
            "cabinet.dispatcher",
            "imperial_user",
        ],
    },
    {
        "agent_id": "cabinet.drafter",
        "display_name": "票拟草拟 Agent",
        "department": "cabinet",
        "style_id": "drafter",
        "summary": "把原始旨意转成结构化执行草案。",
        "implemented": True,
        "soul_path": "agents/cabinet/drafter/SOUL.md",
        "allowed_targets": ["cabinet.coordinator", "cabinet.reviewer"],
    },
    {
        "agent_id": "cabinet.reviewer",
        "display_name": "校核复审 Agent",
        "department": "cabinet",
        "style_id": "reviewer",
        "summary": "负责逻辑校验、补证建议与返工意见。",
        "implemented": True,
        "soul_path": "agents/cabinet/reviewer/SOUL.md",
        "allowed_targets": ["cabinet.coordinator", "cabinet.drafter"],
    },
    {
        "agent_id": "cabinet.dispatcher",
        "display_name": "执行调度 Agent",
        "department": "cabinet",
        "style_id": "dispatcher",
        "summary": "把已批准方案派发给动态执行池。",
        "implemented": True,
        "soul_path": "agents/cabinet/dispatcher/SOUL.md",
        "allowed_targets": ["dynamic_pool", "cabinet.reporter"],
    },
    {
        "agent_id": "cabinet.reporter",
        "display_name": "回奏反馈 Agent",
        "department": "cabinet",
        "style_id": "reporter",
        "summary": "汇总执行结果、回奏摘要与归档结论。",
        "implemented": True,
        "soul_path": "agents/cabinet/reporter/SOUL.md",
        "allowed_targets": ["cabinet.coordinator", "imperial_user"],
    },
    {
        "agent_id": "silijian.approver",
        "display_name": "掌印审批 Agent",
        "department": "silijian",
        "style_id": "approver",
        "summary": "负责正式审批、封驳或升级。",
        "implemented": True,
        "soul_path": "agents/silijian/approver/SOUL.md",
        "allowed_targets": [
            "silijian.decree_writer",
            "silijian.rejector",
            "cabinet.coordinator",
            "imperial_user",
        ],
    },
    {
        "agent_id": "silijian.decree_writer",
        "display_name": "秉笔批令 Agent",
        "department": "silijian",
        "style_id": "decree_writer",
        "summary": "把批准意见写成正式批令与执行约束。",
        "implemented": True,
        "soul_path": "agents/silijian/decree_writer/SOUL.md",
        "allowed_targets": ["cabinet.dispatcher", "imperial_user"],
    },
    {
        "agent_id": "silijian.rejector",
        "display_name": "封驳记录 Agent",
        "department": "silijian",
        "style_id": "rejector",
        "summary": "记录驳回原因、返工要求和版本差异。",
        "implemented": True,
        "soul_path": "agents/silijian/rejector/SOUL.md",
        "allowed_targets": ["cabinet.coordinator", "imperial_user"],
    },
    {
        "agent_id": "censorship.personnel",
        "display_name": "吏科监察 Agent",
        "department": "censorship",
        "style_id": "oversight",
        "summary": "监督角色配置、权限使用和调度边界。",
        "implemented": True,
        "soul_path": "agents/censorship/personnel/SOUL.md",
        "allowed_targets": ["censorship.inspector", "imperial_user"],
    },
    {
        "agent_id": "censorship.finance",
        "display_name": "户科监察 Agent",
        "department": "censorship",
        "style_id": "oversight",
        "summary": "监督资源、成本、配额和用量异常。",
        "implemented": True,
        "soul_path": "agents/censorship/finance/SOUL.md",
        "allowed_targets": ["censorship.inspector", "imperial_user"],
    },
    {
        "agent_id": "censorship.protocol",
        "display_name": "礼科监察 Agent",
        "department": "censorship",
        "style_id": "oversight",
        "summary": "监督格式、接口、协议和消息规范。",
        "implemented": True,
        "soul_path": "agents/censorship/protocol/SOUL.md",
        "allowed_targets": ["censorship.inspector", "imperial_user"],
    },
    {
        "agent_id": "censorship.military",
        "display_name": "兵科监察 Agent",
        "department": "censorship",
        "style_id": "oversight",
        "summary": "监督执行顺序、并发调度和链路偏航。",
        "implemented": True,
        "soul_path": "agents/censorship/military/SOUL.md",
        "allowed_targets": ["censorship.inspector", "imperial_user"],
    },
    {
        "agent_id": "censorship.justice",
        "display_name": "刑科监察 Agent",
        "department": "censorship",
        "style_id": "oversight",
        "summary": "监督违规动作、越权调用和策略突破。",
        "implemented": True,
        "soul_path": "agents/censorship/justice/SOUL.md",
        "allowed_targets": ["censorship.inspector", "imperial_user"],
    },
    {
        "agent_id": "censorship.engineering",
        "display_name": "工科监察 Agent",
        "department": "censorship",
        "style_id": "oversight",
        "summary": "监督工具链、工程质量和执行稳定性。",
        "implemented": True,
        "soul_path": "agents/censorship/engineering/SOUL.md",
        "allowed_targets": ["censorship.inspector", "imperial_user"],
    },
    {
        "agent_id": "censorship.inspector",
        "display_name": "都察总巡 Agent",
        "department": "censorship",
        "style_id": "chief_oversight",
        "summary": "跨模块合并告警、升级异常并触发诊断。",
        "implemented": True,
        "soul_path": "agents/censorship/inspector/SOUL.md",
        "allowed_targets": ["jinyiwei.locator", "imperial_user"],
    },
    {
        "agent_id": "jinyiwei.locator",
        "display_name": "问题定位 Agent",
        "department": "jinyiwei",
        "style_id": "diagnostician",
        "summary": "定位问题来源、受影响模块和故障步骤。",
        "implemented": True,
        "soul_path": "agents/jinyiwei/locator/SOUL.md",
        "allowed_targets": ["jinyiwei.analyzer", "imperial_user"],
    },
    {
        "agent_id": "jinyiwei.analyzer",
        "display_name": "影响分析 Agent",
        "department": "jinyiwei",
        "style_id": "impact_analyzer",
        "summary": "识别影响范围、传播链和风险扩散路径。",
        "implemented": True,
        "soul_path": "agents/jinyiwei/analyzer/SOUL.md",
        "allowed_targets": ["jinyiwei.advisor", "imperial_user"],
    },
    {
        "agent_id": "jinyiwei.advisor",
        "display_name": "修复建议 Agent",
        "department": "jinyiwei",
        "style_id": "repair_advisor",
        "summary": "生成补丁、回滚、重跑或冻结建议。",
        "implemented": True,
        "soul_path": "agents/jinyiwei/advisor/SOUL.md",
        "allowed_targets": ["imperial_user"],
    },
]


class GovernanceAgentRegistry:
    def __init__(self) -> None:
        self._styles = AGENT_STYLES
        self._style_contracts = AGENT_STYLE_CONTRACTS
        self._agents = {agent["agent_id"]: agent for agent in GOVERNANCE_AGENTS}

    def list_styles(self) -> list[dict]:
        styles = []
        for style_id, style in self._styles.items():
            enriched = deepcopy(style)
            enriched["contract"] = self.get_style_contract(style_id)
            styles.append(enriched)
        return sorted(styles, key=lambda item: item["style_id"])

    def get_style(self, style_id: str) -> dict | None:
        style = self._styles.get(style_id)
        return deepcopy(style) if style else None

    def list_style_contracts(self) -> list[dict]:
        contracts = []
        for style_id, style in self._styles.items():
            contracts.append(
                {
                    "style_id": style_id,
                    "style_name": style["name"],
                    "contract": self.get_style_contract(style_id),
                }
            )
        return sorted(contracts, key=lambda item: item["style_id"])

    def get_style_contract(self, style_id: str) -> dict | None:
        contract = self._style_contracts.get(style_id)
        return deepcopy(contract) if contract else None

    def _supported_model_sources(self) -> list[str]:
        return [source["source_id"] for source in MODEL_RUNTIME_CAPABILITIES["sources"]]

    def _enrich_agent(self, raw_agent: dict) -> dict:
        agent = deepcopy(raw_agent)
        agent["style"] = self.get_style(agent["style_id"])
        agent["style_contract"] = self.get_style_contract(agent["style_id"])
        agent["supported_model_sources"] = self._supported_model_sources()
        agent["local_model_size_limit"] = "none_by_system"
        agent["workspace_slug"] = agent["agent_id"].replace(".", "-")
        return agent

    def list_agents(
        self,
        department: str | None = None,
        style_id: str | None = None,
        implemented_only: bool = False,
    ) -> list[dict]:
        agents = []
        for raw_agent in self._agents.values():
            if department and raw_agent["department"] != department:
                continue
            if style_id and raw_agent["style_id"] != style_id:
                continue
            if implemented_only and not raw_agent["implemented"]:
                continue
            agents.append(self._enrich_agent(raw_agent))
        return sorted(agents, key=lambda item: item["agent_id"])

    def get_agent(self, agent_id: str) -> dict | None:
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        return self._enrich_agent(agent)

    def model_runtime_capabilities(self) -> dict:
        return deepcopy(MODEL_RUNTIME_CAPABILITIES)


governance_agent_registry = GovernanceAgentRegistry()
