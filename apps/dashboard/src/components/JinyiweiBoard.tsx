import type { JinyiweiBoard as JinyiweiBoardPayload } from "../types";

type JinyiweiBoardProps = {
  board: JinyiweiBoardPayload | null;
};

export function JinyiweiBoard({ board }: JinyiweiBoardProps) {
  if (!board) {
    return <div className="panel-muted">正在整理锦衣卫问题面板…</div>;
  }

  if (!board.items.length) {
    return <div className="panel-muted">当前没有进入锦衣卫视野的内部问题。</div>;
  }

  return (
    <div className="jinyiwei-stack">
      <div className="jinyiwei-stats">
        <div className="jinyiwei-stat">
          <div className="panel-label">问题总数</div>
          <strong>{board.counts.issues_total}</strong>
        </div>
        <div className="jinyiwei-stat">
          <div className="panel-label">Critical</div>
          <strong>{board.counts.critical}</strong>
        </div>
        <div className="jinyiwei-stat">
          <div className="panel-label">High</div>
          <strong>{board.counts.high}</strong>
        </div>
        <div className="jinyiwei-stat">
          <div className="panel-label">自行处置</div>
          <strong>{board.counts.auto_handled}</strong>
        </div>
        <div className="jinyiwei-stat">
          <div className="panel-label">待用户决策</div>
          <strong>{board.counts.pending_user_decision}</strong>
        </div>
      </div>

      <div className="jinyiwei-grid">
        {board.items.map((item) => (
          <article key={item.issue_id} className={`issue-card severity-${item.severity}`}>
            <div className="issue-head">
              <div>
                <strong>{item.case_title}</strong>
                <div className="detail-meta">
                  {item.case_id} · {item.current_state}
                </div>
              </div>
              <div className="issue-badges">
                <span className={`status-pill severity-pill severity-${item.severity}`}>{item.severity}</span>
                <span className="status-pill is-planned">{item.status}</span>
              </div>
            </div>

            <p className="roster-summary">{item.summary}</p>

            <div className="issue-recommendation">
              <div className="panel-label">流程审计</div>
              <div className="detail-meta">
                {item.audited_stages.join(" -> ")}
              </div>
              <div className="detail-meta">
                {item.process_trace.join(" -> ")}
              </div>
            </div>

            <div className="issue-meta-grid">
              <div>
                <div className="panel-label">问题环节</div>
                <div className="detail-meta">
                  {item.affected_stage} · {item.affected_step}
                </div>
              </div>
              <div>
                <div className="panel-label">处置权限</div>
                <div className="detail-meta">
                  {item.decision_authority === "jinyiwei.advisor" ? "锦衣卫自行处理" : item.requires_user_order ? "用户决定" : "持续观察"}
                </div>
              </div>
            </div>

            <div className="issue-meta-grid">
              <div>
                <div className="panel-label">修复策略</div>
                <div className="detail-meta">{item.repair_strategy}</div>
              </div>
              <div>
                <div className="panel-label">修复范围</div>
                <div className="detail-meta">{item.repair_scope}</div>
              </div>
            </div>

            <div className="issue-recommendation">
              <div className="panel-label">修复建议</div>
              <div className="detail-meta">{item.recommendation}</div>
            </div>

            <div className="roster-tags">
              {item.evidence_topics.map((topic) => (
                <span key={topic} className="roster-tag">
                  {topic}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
