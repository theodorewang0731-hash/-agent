from __future__ import annotations

import argparse
from pathlib import Path

from core.demo.hpc_demo import DEFAULT_INSTRUCTION, DEFAULT_OUTPUT_ROOT, build_sorting_hpc_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RegentOS sorting-case HPC demo exporter.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT / "sorting_case_demo",
        help="Directory used to store exported dashboards, reports and artifacts.",
    )
    parser.add_argument(
        "--instruction",
        default=DEFAULT_INSTRUCTION,
        help="Instruction injected into the governance flow test case.",
    )
    parser.add_argument(
        "--model-inventory",
        type=Path,
        default=None,
        help="Optional JSON inventory describing the models available on HPC.",
    )
    parser.add_argument(
        "--upload-target",
        default=None,
        help="Optional rsync target, for example user@host:/path/to/project_root",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root used when --upload-target is enabled.",
    )
    args = parser.parse_args()

    report = build_sorting_hpc_demo(
        args.output_dir,
        instruction=args.instruction,
        model_inventory_path=args.model_inventory,
        upload_target=args.upload_target,
        project_root=args.project_root,
    )

    print(f"case_id={report['case_id']}")
    print(f"output_dir={report['output_dir']}")
    print("marked_outputs:")
    for label, path in report["artifacts"].items():
        print(f"  - {label}: {path}")
    if report.get("upload"):
        print(f"upload_target={report['upload']['target']}")


if __name__ == "__main__":
    main()
