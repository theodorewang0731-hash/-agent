import json
from pathlib import Path

from core.demo.hpc_demo import build_sorting_hpc_demo, normalize_model_inventory, select_model_bindings


def test_select_model_bindings_prefers_role_specific_models() -> None:
    inventory = {
        "models": [
            {"name": "deepseek-r1:70b", "provider": "ollama", "source": "local_full"},
            {"name": "qwen2.5-coder:32b-instruct", "provider": "ollama", "source": "local_full"},
            {"name": "gpt-5.4-mini", "provider": "openai", "source": "remote_api"},
            {"name": "qwen2.5:14b-instruct", "provider": "ollama", "source": "local_distilled"},
            {"name": "qwen2.5:7b-instruct-q4_k_m", "provider": "ollama", "source": "local_distilled"},
        ]
    }

    bindings = select_model_bindings(inventory, inventory_source="fixture")

    assert bindings["agents"]["cabinet.coordinator"]["model"] == "deepseek-r1:70b"
    assert bindings["agents"]["silijian.approver"]["source"] == "remote_api"
    assert bindings["agents"]["censorship.inspector"]["source"] == "local_distilled"
    assert bindings["selection_summary"]["selected_model_count"] >= 4


def test_hpc_inventory_shape_is_flattened_for_model_selection() -> None:
    inventory = {
        "active_model_lines": [
            {
                "name": "Qwen3.5 9B -> 4B",
                "teacher": "/home/share/models/Qwen3.5-9B",
                "student": "/home/share/models/Qwen3.5-4B",
                "status": "active mainline",
            },
            {
                "name": "Ministral-3 14B -> 3B",
                "teacher": "/home/share/models/Ministral-3-14B-Reasoning-2512",
                "student": "/home/share/models/Ministral-3-3B-Reasoning-2512",
                "status": "secondary validation line",
            },
        ],
        "archival_or_legacy_models": ["/home/share/models/Qwen2.5-32B-Instruct"],
    }

    normalized = normalize_model_inventory(inventory)
    bindings = select_model_bindings(inventory, inventory_source="hpc fixture")

    assert len(normalized) == 5
    assert any(item["name"] == "/home/share/models/Qwen3.5-9B" for item in normalized)
    assert bindings["selection_summary"]["inventory_count"] == 5
    assert bindings["agents"]["cabinet.coordinator"]["model"].startswith("/home/share/models/")


def test_build_sorting_hpc_demo_writes_expected_outputs(tmp_path: Path) -> None:
    report = build_sorting_hpc_demo(tmp_path / "bundle")

    output_dir = Path(report["output_dir"])
    main_board_path = output_dir / "dashboards" / "wenyuange_main_board.html"
    assert (output_dir / "dashboards" / "wenyuange_main_board.html").exists()
    assert (output_dir / "dashboards" / "jinyiwei_board.html").exists()
    assert (output_dir / "artifacts" / "sorting_multi_method.py").exists()
    assert (output_dir / "model_bindings.resolved.json").exists()
    assert (output_dir / "HPC_OUTPUT_MARKERS.txt").exists()
    assert (output_dir / "test_report.json").exists()

    marker_text = (output_dir / "HPC_OUTPUT_MARKERS.txt").read_text(encoding="utf-8")
    assert "文渊阁主看板" in marker_text
    assert "锦衣卫看板" in marker_text
    assert "测试报告(JSON)" in marker_text

    results = json.loads((output_dir / "artifacts" / "sorting_results.json").read_text(encoding="utf-8"))
    assert results["all_algorithms_match_builtin_sorted"] is True
    assert results["execution_order"] == ["bubble", "insertion", "selection", "merge", "quick"]
    assert [step["algorithm"] for step in results["steps"]] == results["execution_order"]
    assert len(results["results"]) >= 4
    assert (output_dir / "artifacts" / "steps" / "01_bubble.json").exists()
    assert (output_dir / "artifacts" / "steps" / "05_quick.json").exists()

    payload = json.loads((output_dir / "test_report.json").read_text(encoding="utf-8"))
    assert payload["summary"]["counts"]["cases_total"] == 1
    assert payload["jinyiwei_board"]["counts"]["issues_total"] == 1
    assert payload["jinyiwei_board"]["counts"]["auto_handled"] == 1
    issue = payload["jinyiwei_board"]["items"][0]
    assert issue["decision_authority"] == "jinyiwei.advisor"
    assert issue["handling_mode"] == "auto"
    assert issue["affected_stage"] == "执行"
    assert issue["affected_step"] == "dual_dashboard_export"
    assert issue["audited_stages"] == ["建档", "票拟", "审批", "执行", "修复 / 归档", "执行", "修复 / 归档"]

    main_board = main_board_path.read_text(encoding="utf-8")
    assert "历史轨迹" in main_board
    assert "bubble" in main_board
    assert "insertion" in main_board
    assert "selection" in main_board
    assert "merge" in main_board
    assert "quick" in main_board
    assert "created -&gt; accepted" in main_board

    jinyiwei_board = (output_dir / "dashboards" / "jinyiwei_board.html").read_text(encoding="utf-8")
    assert "流程审计" in jinyiwei_board
    assert "问题环节" in jinyiwei_board
    assert "锦衣卫自行处理" in jinyiwei_board
    assert "pending_user_decision: 0" in jinyiwei_board
