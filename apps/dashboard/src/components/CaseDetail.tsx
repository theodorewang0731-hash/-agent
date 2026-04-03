import type { Case, CaseEvent } from "../types";

type CaseDetailProps = {
  caseItem: Case | null;
  timeline: CaseEvent[];
  loading: boolean;
};

export function CaseDetail({ caseItem, timeline, loading }: CaseDetailProps) {
  if (loading) {
    return <div className="panel-muted">正在加载卷宗详情…</div>;
  }

  if (!caseItem) {
    return <div className="panel-muted">请选择一个案件查看时间线与卷宗详情。</div>;
  }

  return (
    <div className="detail-stack">
      <div>
        <h2 className="detail-title">{caseItem.title}</h2>
        <div className="detail-meta">case_id: {caseItem.case_id}</div>
        <div className="detail-meta">
          当前状态: {caseItem.state} · 优先级: {caseItem.priority} · 提交者: {caseItem.submitted_by}
        </div>
      </div>
      <div className="detail-body">{caseItem.content}</div>
      <div className="timeline">
        {timeline.map((event) => (
          <article key={event.event_id} className="timeline-event">
            <div className="timeline-topic">{event.topic}</div>
            <div className="detail-meta">
              {event.producer} · {new Date(event.timestamp).toLocaleString("zh-CN", { hour12: false })}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
