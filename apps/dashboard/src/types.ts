export type Case = {
  case_id: string;
  title: string;
  content: string;
  priority: string;
  submitted_by: string;
  state: string;
  rework_count: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type CaseEvent = {
  event_id: string;
  case_id: string;
  topic: string;
  producer: string;
  timestamp: string;
  payload: Record<string, unknown>;
  meta: Record<string, unknown>;
};

export type AgentStyle = {
  style_id: string;
  name: string;
  description: string;
  interaction_mode: string;
  output_mode: string;
  execution_boundary: string;
  contract?: AgentStyleContract;
};

export type AgentStyleContractField = {
  name: string;
  type: string;
  required?: boolean;
  description: string;
};

export type AgentStyleContract = {
  input_fields: AgentStyleContractField[];
  output_fields: AgentStyleContractField[];
  example_input: Record<string, unknown>;
  example_output: Record<string, unknown>;
};

export type Agent = {
  agent_id: string;
  display_name: string;
  department: string;
  style_id: string;
  style: AgentStyle;
  summary: string;
  implemented: boolean;
  soul_path: string | null;
  supported_model_sources: string[];
  local_model_size_limit: string;
  workspace_slug: string;
  style_contract: AgentStyleContract | null;
  allowed_targets?: string[];
};

export type DashboardSummary = {
  counts: {
    cases_total: number;
    agents_total: number;
    agents_implemented: number;
  };
  cases_by_state: Record<string, number>;
  agents_by_department: Record<string, number>;
  recent_cases: Case[];
};

export type JinyiweiIssue = {
  issue_id: string;
  case_id: string;
  case_title: string;
  current_state: string;
  severity: string;
  risk_level: string;
  status: string;
  detected_by: string;
  summary: string;
  repair_strategy: string;
  repair_scope: string;
  recommendation: string;
  affected_stage: string;
  affected_step: string;
  requires_user_order: boolean;
  decision_authority: string;
  handling_mode: string;
  process_trace: string[];
  audited_stages: string[];
  evidence_topics: string[];
  updated_at: string;
};

export type JinyiweiBoard = {
  counts: {
    issues_total: number;
    critical: number;
    high: number;
    auto_handled: number;
    pending_user_decision: number;
  };
  issues_by_severity: Record<string, number>;
  issues_by_status: Record<string, number>;
  issues_by_handling_mode: Record<string, number>;
  items: JinyiweiIssue[];
};

export type ModelRuntimeCapabilities = {
  sources: {
    source_id: string;
    name: string;
    description: string;
  }[];
  policy: {
    system_limit: string;
    practical_limit: string;
    binding_strategy: string;
  };
};
