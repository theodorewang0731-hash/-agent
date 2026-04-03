import json
from pathlib import Path

from core.orchestrator.engine import orchestrator
from core.registry.cases import case_registry


def seed(output_path: str = "data/demo_cases.json") -> str:
    case_registry.reset()

    case1 = case_registry.create_case(
        title="企业知识库系统设计",
        content="FastAPI + PostgreSQL + 全文搜索 + 权限分级",
        priority="high",
        submitted_by="imperial_user",
    )
    orchestrator.accept_case(case1["case_id"])
    orchestrator.submit_for_approval(case1["case_id"])
    orchestrator.approve_case(case1["case_id"])

    case2 = case_registry.create_case(
        title="代码重构任务",
        content="重构 API 模块并补充测试",
        priority="normal",
        submitted_by="imperial_user",
    )
    orchestrator.accept_case(case2["case_id"])
    orchestrator.submit_for_approval(case2["case_id"])
    orchestrator.reject_case(case2["case_id"], reason="测试覆盖不足")

    case3 = case_registry.create_case(
        title="依赖污染修复",
        content="检测并修复 executor_pool 中的依赖污染",
        priority="critical",
        submitted_by="imperial_user",
    )
    orchestrator.accept_case(case3["case_id"])
    orchestrator.submit_for_approval(case3["case_id"])
    orchestrator.approve_case(case3["case_id"])
    orchestrator.mark_repair_pending(case3["case_id"], reason="dependency corruption")
    orchestrator.authorize_repair(
        case_id=case3["case_id"],
        strategy="patch_then_rerun",
        reason="critical dependency issue",
        scope="executor_pool/api_builder",
    )

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(case_registry.export_snapshot(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Demo data seeded to {target}.")
    return str(target)


if __name__ == "__main__":
    seed()
