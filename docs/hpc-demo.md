# HPC Demo Export

这个文档对应“随机数组多排序”治理链测试的本地/HPC 导出脚本。

## 一条命令运行

```bash
bash scripts/run_hpc_demo.sh
```

默认会在 `runtime/hpc_exports/sorting_case_demo/` 产出：

- `dashboards/wenyuange_main_board.html`
- `dashboards/jinyiwei_board.html`
- `artifacts/sorting_multi_method.py`
- `artifacts/sorting_results.json`
- `model_bindings.resolved.json`
- `HPC_OUTPUT_MARKERS.txt`
- `test_report.md`
- `test_report.json`

## 可选参数

```bash
bash scripts/run_hpc_demo.sh \
  --output-dir runtime/hpc_exports/my_hpc_run \
  --model-inventory config/hpc-model-inventory.example.json \
  --upload-target rpwang@<HPC_HOST>:/home/rpwang/
```

说明：

- `--model-inventory`：可选的 HPC 模型清单 JSON。脚本会根据 RegentOS 的治理角色自动挑选模型。
- `--upload-target`：可选的 `rsync` 目标。当前已知目标根路径是 `rpwang@<HPC_HOST>:/home/rpwang/`，其中 `<HPC_HOST>` 需要替换为真实主机名。
- `--instruction`：可覆盖默认测试指令。

当前仓库整理出的 HPC 模型清单样例见 `config/hpc-model-inventory.example.json`，模型根目录为 `/home/share/models`。

## 默认测试指令

```text
编写一段代码，对随机数组可以进行多种排序的选择，要求至少4种排序方法。
```

## 模型选择策略

脚本默认会为 5 个关键治理角色选择模型：

- `cabinet.coordinator`
- `silijian.approver`
- `censorship.inspector`
- `jinyiwei.advisor`
- `cabinet.reporter`

选择原则：

- 票拟与修复建议优先使用更强的推理/代码模型
- 审批优先使用稳定的指令跟随模型
- 监督优先使用更轻量、更快的巡检模型
- 回奏优先使用适合结构化总结的模型

如果没有提供 HPC 模型清单，脚本会使用仓库内置的 fallback inventory 生成一份可运行的样例绑定结果。

针对当前 HPC 清单，脚本会优先从两条活跃模型线中选用模型：

- `Qwen3.5 9B -> 4B`：主线，适合票拟、轻量监督和回奏。
- `Ministral-3 14B -> 3B`：二级验证线，适合审批与修复建议交叉验证。

归档或 legacy 模型默认作为候补；如果某个治理角色明确需要代码/修复能力，而 active line 中没有更合适的代码专项模型，脚本可以为该角色选择更匹配的 legacy 大模型。
