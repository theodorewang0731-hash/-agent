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
