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
        "implemented": False,
        "soul_path": None,
        "allowed_targets": ["cabinet.coordinator", "cabinet.reviewer"],
    },
    {
        "agent_id": "cabinet.reviewer",
        "display_name": "校核复审 Agent",
        "department": "cabinet",
        "style_id": "reviewer",
        "summary": "负责逻辑校验、补证建议与返工意见。",
        "implemented": False,
        "soul_path": None,
        "allowed_targets": ["cabinet.coordinator", "cabinet.drafter"],
    },
    {
        "agent_id": "cabinet.dispatcher",
        "display_name": "执行调度 Agent",
        "department": "cabinet",
        "style_id": "dispatcher",
        "summary": "把已批准方案派发给动态执行池。",
        "implemented": False,
        "soul_path": None,
        "allowed_targets": ["dynamic_pool", "cabinet.reporter"],
    },
    {
        "agent_id": "cabinet.reporter",
        "display_name": "回奏反馈 Agent",
        "department": "cabinet",
        "style_id": "reporter",
        "summary": "汇总执行结果、回奏摘要与归档结论。",
        "implemented": False,
        "soul_path": None,
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
        "implemented": False,
        "soul_path": None,
        "allowed_targets": ["cabinet.dispatcher", "imperial_user"],
    },
    {
        "agent_id": "silijian.rejector",
        "display_name": "封驳记录 Agent",
        "department": "silijian",
        "style_id": "rejector",
        "summary": "记录驳回原因、返工要求和版本差异。",
        "implemented": False,
        "soul_path": None,
        "allowed_targets": ["cabinet.coordinator", "imperial_user"],
    },
    {
        "agent_id": "censorship.personnel",
        "display_name": "吏科监察 Agent",
        "department": "censorship",
        "style_id": "oversight",
        "summary": "监督角色配置、权限使用和调度边界。",
        "implemented": False,
        "soul_path": None,
        "allowed_targets": ["censorship.inspector", "imperial_user"],
    },
    {
        "agent_id": "censorship.finance",
        "display_name": "户科监察 Agent",
        "department": "censorship",
        "style_id": "oversight",
        "summary": "监督资源、成本、配额和用量异常。",
        "implemented": False,
        "soul_path": None,
        "allowed_targets": ["censorship.inspector", "imperial_user"],
    },
    {
        "agent_id": "censorship.protocol",
        "display_name": "礼科监察 Agent",
        "department": "censorship",
        "style_id": "oversight",
        "summary": "监督格式、接口、协议和消息规范。",
        "implemented": False,
        "soul_path": None,
        "allowed_targets": ["censorship.inspector", "imperial_user"],
    },
    {
        "agent_id": "censorship.military",
        "display_name": "兵科监察 Agent",
        "department": "censorship",
        "style_id": "oversight",
        "summary": "监督执行顺序、并发调度和链路偏航。",
        "implemented": False,
        "soul_path": None,
        "allowed_targets": ["censorship.inspector", "imperial_user"],
    },
    {
        "agent_id": "censorship.justice",
        "display_name": "刑科监察 Agent",
        "department": "censorship",
        "style_id": "oversight",
        "summary": "监督违规动作、越权调用和策略突破。",
        "implemented": False,
        "soul_path": None,
        "allowed_targets": ["censorship.inspector", "imperial_user"],
    },
    {
        "agent_id": "censorship.engineering",
        "display_name": "工科监察 Agent",
        "department": "censorship",
        "style_id": "oversight",
        "summary": "监督工具链、工程质量和执行稳定性。",
        "implemented": False,
        "soul_path": None,
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
        "implemented": False,
        "soul_path": None,
        "allowed_targets": ["jinyiwei.analyzer", "imperial_user"],
    },
    {
        "agent_id": "jinyiwei.analyzer",
        "display_name": "影响分析 Agent",
        "department": "jinyiwei",
        "style_id": "impact_analyzer",
        "summary": "识别影响范围、传播链和风险扩散路径。",
        "implemented": False,
        "soul_path": None,
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
        self._agents = {agent["agent_id"]: agent for agent in GOVERNANCE_AGENTS}

    def list_styles(self) -> list[dict]:
        return [deepcopy(style) for style in self._styles.values()]

    def get_style(self, style_id: str) -> dict | None:
        style = self._styles.get(style_id)
        return deepcopy(style) if style else None

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
            agent = deepcopy(raw_agent)
            agent["style"] = self.get_style(agent["style_id"])
            agent["supported_model_sources"] = [
                source["source_id"] for source in MODEL_RUNTIME_CAPABILITIES["sources"]
            ]
            agent["local_model_size_limit"] = "none_by_system"
            agent["workspace_slug"] = agent["agent_id"].replace(".", "-")
            agents.append(agent)
        return sorted(agents, key=lambda item: item["agent_id"])

    def get_agent(self, agent_id: str) -> dict | None:
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        enriched = deepcopy(agent)
        enriched["style"] = self.get_style(enriched["style_id"])
        enriched["supported_model_sources"] = [
            source["source_id"] for source in MODEL_RUNTIME_CAPABILITIES["sources"]
        ]
        enriched["local_model_size_limit"] = "none_by_system"
        enriched["workspace_slug"] = enriched["agent_id"].replace(".", "-")
        return enriched

    def model_runtime_capabilities(self) -> dict:
        return deepcopy(MODEL_RUNTIME_CAPABILITIES)


governance_agent_registry = GovernanceAgentRegistry()
