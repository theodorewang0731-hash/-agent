import type { Agent } from "../types";

type AgentRosterProps = {
  agents: Agent[];
};

export function AgentRoster({ agents }: AgentRosterProps) {
  const topAgents = agents.slice(0, 6);

  return (
    <div className="roster-grid">
      {topAgents.map((agent) => (
        <article key={agent.agent_id} className="roster-card">
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
        </article>
      ))}
    </div>
  );
}
