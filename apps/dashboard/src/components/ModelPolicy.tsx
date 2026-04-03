import type { ModelRuntimeCapabilities } from "../types";

type ModelPolicyProps = {
  modelCapabilities: ModelRuntimeCapabilities | null;
};

export function ModelPolicy({ modelCapabilities }: ModelPolicyProps) {
  if (!modelCapabilities) {
    return <div className="panel-muted">正在加载模型运行时信息…</div>;
  }

  return (
    <div className="policy-stack">
      <div className="policy-sources">
        {modelCapabilities.sources.map((source) => (
          <article key={source.source_id} className="policy-card">
            <div className="policy-source-name">{source.name}</div>
            <div className="detail-meta">{source.source_id}</div>
            <p>{source.description}</p>
          </article>
        ))}
      </div>
      <div className="policy-note">
        <strong>声明：</strong> 这是原型骨架，并不能直接投入实际使用，后续会持续更新。
        当前系统设计支持远程 API、本地蒸馏模型和本地完整大模型，且不在系统层面对本地模型大小做硬性限制。
      </div>
    </div>
  );
}
