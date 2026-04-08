import type { Agent } from "../types";

type AgentRosterProps = {
  agents: Agent[];
  selectedAgentId: string | null;
  onSelectAgent: (agentId: string) => void;
};

export function AgentRoster({ agents, selectedAgentId, onSelectAgent }: AgentRosterProps) {
  return (
    <div className="roster-grid">
      {agents.map((agent) => (
        <button
          key={agent.agent_id}
          type="button"
          className={`roster-card ${selectedAgentId === agent.agent_id ? "is-selected" : ""}`}
          onClick={() => onSelectAgent(agent.agent_id)}
        >
          <div className="roster-head">
            <strong>{agent.display_name}</strong>
            <span className={`status-pill ${agent.implemented ? "is-live" : "is-planned"}`}>
              {agent.implemented ? "已有骨架" : "规划中"}
            </span>
          </div>
          <div className="detail-meta">
            {agent.department} · {agent.style.name}
          </div>
          <p className="roster-summary">{agent.summary}</p>
          <div className="roster-tags">
            {agent.supported_model_sources.map((source) => (
              <span key={source} className="roster-tag">
                {source}
              </span>
            ))}
          </div>
        </button>
      ))}
    </div>
  );
}
