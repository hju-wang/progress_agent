"""progress-agent 命令行入口。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .assessment import (
    MAX_LEVEL,
    build_report,
    render_markdown,
    validate_answers,
)
from .gap import (
    build_gap_report,
    default_market_weights_path,
    load_assessment_report,
    load_market_weights,
    render_markdown as render_gap_markdown,
)
from .model import AbilityModel, load_model, repo_root


def _ask_level(item_id: str, item_name: str, item_description: str, detection_note: str) -> int | None:
    """向用户询问一个能力项的档位；返回 None 表示跳过。"""

    print(f"\n[{item_id}] {item_name}")
    print(f"  说明：{item_description}")
    print(f"  检测参考：{detection_note}")
    print("  档位：0 未知 / 1 概念 / 2 照做 / 3 独立 / 4 调优（输入 s 跳过）")
    while True:
        try:
            raw = input(f"  {item_id} 当前档位 [0-4]: ").strip().lower()
        except EOFError:
            raise
        if raw in {"s", "skip"}:
            return None
        if raw.isdigit() and 0 <= int(raw) <= MAX_LEVEL:
            return int(raw)
        print("  请输入 0–4 或 s（跳过）。")


def _run_interactive(model: AbilityModel) -> dict[str, int]:
    answers: dict[str, int] = {}
    print(f"ProgressAgent 自测：{model.role_label}（能力模型 v{model.model_version}）")
    print("请对每个能力项如实自评。这个分数不会被直接采信——高分会用独立任务复核。")

    for dimension in model.dimensions:
        print(f"\n===== [{dimension.id}] {dimension.name} =====")
        for index, item in enumerate(dimension.items, start=1):
            level = _ask_level(
                item.id,
                item.name,
                item.description,
                item.detection_note,
            )
            if level is not None:
                answers[item.id] = level
            print(f"    已记录：{index}/{len(dimension.items)}")

    print(f"\n自测完成，共作答 {len(answers)}/{len(model.items)} 项。")
    return answers


def _read_answers(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("答案文件必须是 JSON 对象：{ \"A1\": 2, ... }")
    return raw


def _save_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / f"self-assessment-{stamp}.json"
    md_path = output_dir / f"self-assessment-{stamp}.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _print_summary(report: dict[str, Any]) -> None:
    scope = report["scope"]
    summary = report["summary"]
    print("\n---------- 水平报告摘要 ----------")
    print(f"总体自评分：{summary['overall_percent']} / 100")
    print(f"作答覆盖：{scope['answered']}/{scope['total_items']} 项")
    for dimension in report["dimensions"]:
        average = dimension["average_percent"]
        if average is not None:
            print(f"[{dimension['id']}] {dimension['name']}: {average} / 100")
    print("----------------------------------")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="progress-agent",
        description="ProgressAgent：求职成长 Agent 命令行",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    assess = subparsers.add_parser("assess", help="跑一次能力自测并生成水平报告")
    assess.add_argument("--model", help="能力模型 JSON 路径（默认仓库内 v0.1 模型）")
    assess.add_argument("--answers", type=Path, help="从答案 JSON 生成报告，跳过交互问答")
    assess.add_argument("--output-dir", type=Path, help="报告输出目录（默认 data/reports/）")

    gap = subparsers.add_parser("gap", help="把自测报告与岗位画像对比，生成基准差距报告")
    gap.add_argument("--assessment", type=Path, required=True, help="自测报告 JSON（assess 的输出）")
    gap.add_argument("--model", help="能力模型 JSON 路径（默认仓库内 v0.1 模型）")
    gap.add_argument("--market-weights", type=Path, help="岗位画像权重 JSON（默认 v0.1）")
    gap.add_argument("--output-dir", type=Path, help="报告输出目录（默认 data/reports/）")
    return parser


def _run_assess(args: argparse.Namespace) -> int:
    model = load_model(args.model)
    try:
        if args.answers:
            raw_answers = _read_answers(args.answers)
            errors = validate_answers(model, raw_answers)
            if errors:
                print("答案校验失败：", file=sys.stderr)
                for error in errors:
                    print(f"  - {error}", file=sys.stderr)
                return 2
            answers = {item_id: int(level) for item_id, level in raw_answers.items()}
            interactive = False
        else:
            answers = _run_interactive(model)
            interactive = True
    except KeyboardInterrupt:
        print("\n已中断，本次结果未保存。")
        return 130

    report = build_report(model, answers)
    json_path, md_path = _save_report(report, output_dir)

    if interactive:
        _print_summary(report)
    else:
        print(render_markdown(report))
    print(f"\n报告已保存：")
    print(f"  JSON：{json_path}")
    print(f"  MD：  {md_path}")
    return 0


def _run_gap(args: argparse.Namespace) -> int:
    model = load_model(args.model)
    assessment = load_assessment_report(args.assessment)
    if assessment.get("report_type") != "self-assessment":
        print(f"不是有效的自测报告：{args.assessment}", file=sys.stderr)
        return 2

    market_weights = load_market_weights(args.market_weights)
    report = build_gap_report(model, assessment, market_weights)

    output_dir = args.output_dir or (repo_root() / "data" / "reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / f"baseline-gap-{stamp}.json"
    md_path = output_dir / f"baseline-gap-{stamp}.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(render_gap_markdown(report), encoding="utf-8")

    print(render_gap_markdown(report))
    print("\n差距报告已保存：")
    print(f"  JSON：{json_path}")
    print(f"  MD：  {md_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "gap":
        return _run_gap(args)
    return _run_assess(args)


if __name__ == "__main__":
    raise SystemExit(main())
