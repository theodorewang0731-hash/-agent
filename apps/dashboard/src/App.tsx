import { useEffect, useState, startTransition } from "react";

import { getAgents, getCase, getCases, getDashboardSummary, getModelCapabilities, getTimeline } from "./lib/api";
import type { Agent, Case, CaseEvent, DashboardSummary, ModelRuntimeCapabilities } from "./types";
import { CaseDetail } from "./components/CaseDetail";
import { KanbanBoard } from "./components/KanbanBoard";
import { AgentRoster } from "./components/AgentRoster";
import { ModelPolicy } from "./components/ModelPolicy";
import { StatCard } from "./components/StatCard";

export default function App() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [cases, setCases] = useState<Case[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [modelCapabilities, setModelCapabilities] = useState<ModelRuntimeCapabilities | null>(null);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [timeline, setTimeline] = useState<CaseEvent[]>([]);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const [nextSummary, nextCases, nextAgents, nextModels] = await Promise.all([
          getDashboardSummary(),
          getCases(),
          getAgents(),
          getModelCapabilities(),
        ]);
        if (!active) {
          return;
        }
        setSummary(nextSummary);
        setCases(nextCases);
        setAgents(nextAgents);
        setModelCapabilities(nextModels);
        if (nextCases.length) {
          startTransition(() => {
            setSelectedCaseId(nextCases[0].case_id);
          });
        }
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "加载失败");
        }
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    if (!selectedCaseId) {
      return;
    }
    const caseId = selectedCaseId;

    async function loadDetail() {
      setLoadingDetail(true);
      try {
        const [detail, events] = await Promise.all([getCase(caseId), getTimeline(caseId)]);
        if (!active) {
          return;
        }
        setSelectedCase(detail);
        setTimeline(events);
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "卷宗加载失败");
        }
      } finally {
        if (active) {
          setLoadingDetail(false);
        }
      }
    }

    loadDetail();
    return () => {
      active = false;
    };
  }, [selectedCaseId]);

  return (
    <main className="dashboard-shell">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Governance-first Prototype</p>
          <h1>文渊阁中枢</h1>
          <p className="hero-copy">
            这是 RegentOS 的 React 前端原型。它用于展示案件流转、卷宗时间线、18 个治理 Agent 编制和模型接入边界，
            但当前仍只是原型骨架，并不能直接投入使用，后续会持续更新。
          </p>
        </div>
        <div className="notice-card">
          <div className="notice-label">原型声明</div>
          <div className="notice-text">
            仅为原型骨架，并不能直接使用。
            当前前端重点是让治理链、卷宗视角和模型绑定边界清晰可见。
          </div>
        </div>
      </section>

      {error ? <div className="error-banner">加载失败：{error}</div> : null}

      <section className="stats-grid">
        <StatCard label="案件总数" value={summary?.counts.cases_total ?? "-"} />
        <StatCard label="治理 Agent" value={summary?.counts.agents_total ?? "-"} />
        <StatCard label="已有骨架" value={summary?.counts.agents_implemented ?? "-"} tone="accent" />
        <StatCard label="模型来源" value={modelCapabilities?.sources.length ?? "-"} />
      </section>

      <section className="main-layout">
        <section className="panel">
          <div className="panel-head">
            <div>
              <div className="panel-label">案件看板</div>
              <h2>Kanban</h2>
            </div>
            <div className="panel-caption">案件化、票拟、审批、执行、修复受令</div>
          </div>
          <KanbanBoard cases={cases} selectedCaseId={selectedCaseId} onSelectCase={setSelectedCaseId} />
        </section>

        <section className="panel side-panel">
          <div className="panel-head">
            <div>
              <div className="panel-label">卷宗详情</div>
              <h2>Memorials</h2>
            </div>
            <div className="panel-caption">按时间线回看关键事件</div>
          </div>
          <CaseDetail caseItem={selectedCase} timeline={timeline} loading={loadingDetail} />
        </section>
      </section>

      <section className="secondary-layout">
        <section className="panel">
          <div className="panel-head">
            <div>
              <div className="panel-label">治理编制</div>
              <h2>18 个固定治理 Agent</h2>
            </div>
            <div className="panel-caption">先展示编制与边界，再逐步补齐 worker</div>
          </div>
          <AgentRoster agents={agents} />
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <div className="panel-label">模型运行时</div>
              <h2>Runtime Policy</h2>
            </div>
            <div className="panel-caption">远程 API / 本地蒸馏 / 本地完整大模型</div>
          </div>
          <ModelPolicy modelCapabilities={modelCapabilities} />
        </section>
      </section>
    </main>
  );
}
