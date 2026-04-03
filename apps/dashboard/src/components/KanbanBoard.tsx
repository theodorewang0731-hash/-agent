import type { Case } from "../types";

const groups = [
  { title: "建档", states: ["created", "accepted"] },
  { title: "票拟", states: ["planning", "internal_review"] },
  { title: "审批", states: ["submitted_for_approval", "approved", "rejected", "escalated"] },
  { title: "执行", states: ["dispatched", "executing", "reporting", "rerunning"] },
  {
    title: "修复 / 归档",
    states: ["repair_pending", "repair_authorized", "paused", "frozen", "failed", "archived", "cancelled"],
  },
];

type KanbanBoardProps = {
  cases: Case[];
  selectedCaseId: string | null;
  onSelectCase: (caseId: string) => void;
};

export function KanbanBoard({ cases, selectedCaseId, onSelectCase }: KanbanBoardProps) {
  return (
    <div className="kanban-grid">
      {groups.map((group) => {
        const casesInGroup = cases.filter((item) => group.states.includes(item.state));
        return (
          <section key={group.title} className="kanban-column">
            <div className="kanban-title">{group.title}</div>
            <div className="kanban-cases">
              {casesInGroup.length ? (
                casesInGroup.map((item) => (
                  <button
                    key={item.case_id}
                    className={`case-card ${selectedCaseId === item.case_id ? "is-selected" : ""}`}
                    type="button"
                    onClick={() => onSelectCase(item.case_id)}
                  >
                    <div className="case-title">{item.title}</div>
                    <div className="case-meta">{item.case_id}</div>
                    <div className="case-meta">状态：{item.state}</div>
                    <div className="case-footer">
                      <span className="case-pill">{item.priority}</span>
                      <span className="case-meta">返工 {item.rework_count}</span>
                    </div>
                  </button>
                ))
              ) : (
                <div className="kanban-empty">暂无案件</div>
              )}
            </div>
          </section>
        );
      })}
    </div>
  );
}
