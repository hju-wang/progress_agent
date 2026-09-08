"""自评打分与水平报告生成。"""

from __future__ import annotations

from datetime import datetime
from statistics import fmean
from typing import Any

from .model import AbilityModel

MAX_LEVEL = 4

LEVEL_LABELS = {
    0: "未知",
    1: "概念",
    2: "照做",
    3: "独立",
    4: "调优",
}

LEVEL_ADVICE = {
    0: "先补概念：读 2–3 份权威资料（官方文档优先），直到能向别人讲清它是什么、解决什么问题。",
    1: "概念不稳：补足原理后做一次“讲给自己听”的复述，再进入小任务。",
    2: "能照做：进入实操验证，独立完成一个最小可运行任务，并记录设计取舍。",
    3: "疑似已掌握：安排一次限时、少 AI 辅助的独立任务验证，防止高估。",
    4: "可调优：用它完成一个端到端落地任务，练习把权衡和坑讲清楚。",
}

NOT_ANSWERED_ADVICE = "未作答：下次自测前先做一次快速自查，避免形成盲区。"


def validate_answers(model: AbilityModel, answers: dict[str, Any]) -> list[str]:
    """校验答案；返回错误信息列表，空列表表示通过。"""

    valid_ids = {item.id for item in model.items}
    errors: list[str] = []
    for item_id, level in answers.items():
        if item_id not in valid_ids:
            errors.append(f"未知能力项：{item_id}")
            continue
        if not isinstance(level, int) or level < 0 or level > MAX_LEVEL:
            errors.append(f"{item_id} 档位必须为 0–4 的整数，收到：{level!r}")
    return errors


def build_report(
    model: AbilityModel,
    answers: dict[str, int],
    *,
    completed_at: str | None = None,
    interrupted: bool = False,
) -> dict[str, Any]:
    """根据自评答案生成结构化报告（0–100 分制）。"""

    generated_at = completed_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item_rows: list[dict[str, Any]] = []
    dimension_rows: list[dict[str, Any]] = []

    for dimension in model.dimensions:
        dim_answered: list[dict[str, Any]] = []
        for item in dimension.items:
            level = answers.get(item.id)
            row = {
                "id": item.id,
                "dimension_id": dimension.id,
                "dimension_name": dimension.name,
                "name": item.name,
                "answered": level is not None,
                "level": level,
                "level_label": LEVEL_LABELS.get(level, "未作答") if level is not None else "未作答",
                "percent": round(level * 25, 1) if level is not None else None,
                "advice": LEVEL_ADVICE.get(level, NOT_ANSWERED_ADVICE) if level is not None else NOT_ANSWERED_ADVICE,
            }
            item_rows.append(row)
            if level is not None:
                dim_answered.append(row)

        dimension_rows.append(
            {
                "id": dimension.id,
                "name": dimension.name,
                "answered": len(dim_answered),
                "total": len(dimension.items),
                "average_percent": (
                    round(fmean(row["percent"] for row in dim_answered), 1)
                    if dim_answered
                    else None
                ),
                "weakest_first": [row["id"] for row in sorted(dim_answered, key=lambda r: r["level"])],
            }
        )

    answered_rows = [row for row in item_rows if row["answered"]]
    not_answered = [row["id"] for row in item_rows if not row["answered"]]

    weakest_first = sorted(answered_rows, key=lambda row: (row["level"], row["id"]))
    overall = (
        round(fmean(row["percent"] for row in answered_rows), 1)
        if answered_rows
        else None
    )

    return {
        "report_type": "self-assessment",
        "schema": "progress-agent/assessment/v1",
        "role_label": model.role_label,
        "model_version": model.model_version,
        "generated_at": generated_at,
        "interrupted": interrupted,
        "scope": {
            "total_items": len(item_rows),
            "answered": len(answered_rows),
            "not_answered": not_answered,
        },
        "summary": {
            "overall_percent": overall,
            "overall_level": round(overall / 25, 2) if overall is not None else None,
        },
        "dimensions": dimension_rows,
        "items": item_rows,
        "weakest_first": weakest_first[:10],
        "notes": (
            "本报告为自评基线，未经独立任务验证；"
            "得分 >=3 只代表“疑似已掌握”，需在受控限时任务（少 AI 辅助）中复核。"
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    """把报告渲染成人可读的 Markdown。"""

    lines: list[str] = []
    lines.append(f"# 自测报告：{report['role_label']}")
    lines.append("")
    lines.append(f"- 生成时间：{report['generated_at']}")
    lines.append(f"- 能力模型：v{report['model_version']}")
    lines.append(f"- 作答覆盖：{report['scope']['answered']}/{report['scope']['total_items']} 项")
    overall = report["summary"]["overall_percent"]
    lines.append(f"- 总体自评分：**{overall if overall is not None else '—'} / 100**")
    lines.append("")
    lines.append(f"> {report['notes']}")
    lines.append("")

    lines.append("## 各维度平均分")
    lines.append("")
    lines.append("| 维度 | 作答 | 平均分（0–100） | 最弱项 |")
    lines.append("| --- | --- | --- | --- |")
    for dimension in report["dimensions"]:
        average = dimension["average_percent"]
        weakest = dimension["weakest_first"][:2]
        lines.append(
            f"| {dimension['id']} {dimension['name']} | "
            f"{dimension['answered']}/{dimension['total']} | "
            f"{average if average is not None else '—'} | "
            f"{'、'.join(weakest) if weakest else '—'} |"
        )
    lines.append("")

    lines.append("## 最薄弱能力项（Top 10）")
    lines.append("")
    lines.append("| 能力 | 档位 | 百分比 | 建议 |")
    lines.append("| --- | --- | --- | --- |")
    for row in report["weakest_first"]:
        lines.append(
            f"| {row['id']} {row['name']} | "
            f"{row['level_label']}（{row['level']}） | "
            f"{row['percent']} | {row['advice']} |"
        )
    lines.append("")

    if report["scope"]["not_answered"]:
        lines.append("## 未作答")
        lines.append("")
        lines.append("、".join(report["scope"]["not_answered"]))
        lines.append("")

    return "\n".join(lines)
