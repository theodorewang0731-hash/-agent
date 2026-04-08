import type { Agent } from "../types";

type AgentContractProps = {
  agent: Agent | null;
};

function renderValue(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

export function AgentContract({ agent }: AgentContractProps) {
  if (!agent) {
    return <div className="panel-muted">请选择一个治理 Agent 查看契约。</div>;
  }

  return (
    <div className="contract-stack">
      <div className="contract-overview">
        <div className="contract-title-row">
          <h3>{agent.display_name}</h3>
          <span className={`status-pill ${agent.implemented ? "is-live" : "is-planned"}`}>
            {agent.implemented ? "骨架已齐" : "规划中"}
          </span>
        </div>
        <div className="detail-meta">
          {agent.department} · {agent.style.name} · {agent.agent_id}
        </div>
        <p className="roster-summary">{agent.summary}</p>
        <div className="contract-mini-grid">
          <div>
            <div className="panel-label">通信边界</div>
            <div className="detail-meta">{agent.style.execution_boundary}</div>
          </div>
          <div>
            <div className="panel-label">SOUL 文件</div>
            <div className="detail-meta">{agent.soul_path ?? "未提供"}</div>
          </div>
        </div>
        <div className="roster-tags">
          {(agent.allowed_targets ?? []).map((target) => (
            <span key={target} className="roster-tag">
              {target}
            </span>
          ))}
        </div>
      </div>

      <div className="contract-grid">
        <section className="contract-card">
          <div className="panel-label">输入契约</div>
          <ul className="contract-list">
            {agent.style_contract?.input_fields.map((field) => (
              <li key={field.name}>
                <strong>{field.name}</strong> · {field.type}
                {field.required ? " · required" : " · optional"}
                <div className="detail-meta">{field.description}</div>
              </li>
            ))}
          </ul>
        </section>

        <section className="contract-card">
          <div className="panel-label">输出契约</div>
          <ul className="contract-list">
            {agent.style_contract?.output_fields.map((field) => (
              <li key={field.name}>
                <strong>{field.name}</strong> · {field.type}
                <div className="detail-meta">{field.description}</div>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <div className="contract-grid">
        <section className="contract-card">
          <div className="panel-label">示例输入</div>
          <pre className="contract-code">{renderValue(agent.style_contract?.example_input ?? {})}</pre>
        </section>

        <section className="contract-card">
          <div className="panel-label">示例输出</div>
          <pre className="contract-code">{renderValue(agent.style_contract?.example_output ?? {})}</pre>
        </section>
      </div>
    </div>
  );
}
