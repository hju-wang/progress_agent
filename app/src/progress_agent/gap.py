"""基准差距分析：把自测报告与岗位画像权重对比，生成差距报告。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .model import AbilityModel, repo_root

DEFAULT_MARKET_WEIGHTS = "jd_library/profiles/market-weights.v0.1.json"


def default_market_weights_path() -> Path:
    return repo_root() / DEFAULT_MARKET_WEIGHTS


def load_market_weights(path: Path | None = None) -> dict[str, Any]:
    weights_file = path or default_market_weights_path()
    return json.loads(weights_file.read_text(encoding="utf-8"))


def load_assessment_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_gap_report(
    model: AbilityModel,
    assessment: dict[str, Any],
    market_weights: dict[str, Any],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """计算每个能力项的缺口与优先级。

    缺口 = 市场目标档位 - 当前档位（不小于 0）
    紧急度 = 市场权重 × 缺口
    """

    reported_at = assessment["generated_at"]
    targets = market_weights["target_level_by_tier"]
    weights = market_weights["weights"]

    level_by_id = {
        item["id"]: item.get("level")
        for item in assessment["items"]
    }

    rows: list[dict[str, Any]] = []
    dimension_rollup: dict[str, list[float]] = {}
    total_weighted_gap = 0.0
    total_weighted_target = 0.0

    for dimension in model.dimensions:
        for item in dimension.items:
            item_id = item.id
            meta = weights.get(item_id, {"weight": 1, "tier": 3})
            weight = float(meta.get("weight", 1))
            tier = str(meta.get("tier", 3))
            target = int(targets.get(tier, 1))
            current = level_by_id.get(item_id)
            if current is None:
                current = 0
                answered = False
            else:
                answered = True

            gap = max(target - current, 0)
            urgency = round(weight * gap, 1)
            total_weighted_gap += weight * gap
            total_weighted_target += weight * target
            dimension_rollup.setdefault(dimension.id, []).append(gap)

            rows.append(
                {
                    "id": item_id,
                    "name": item.name,
                    "dimension_id": dimension.id,
                    "dimension_name": dimension.name,
                    "tier": meta.get("tier", 3),
                    "weight": weight,
                    "target_level": target,
                    "current_level": current,
                    "gap": gap,
                    "urgency": urgency,
                    "answered": answered,
                    "evidence": meta.get("evidence", ""),
                }
            )

    rows.sort(key=lambda row: (-row["urgency"], row["tier"], row["gap"], row["id"]))

    readiness = (
        round((1 - total_weighted_gap / total_weighted_target) * 100, 1)
        if total_weighted_target
        else None
    )

    dimension_rows = []
    for dimension in model.dimensions:
        gaps = dimension_rollup.get(dimension.id, [])
        dimension_rows.append(
            {
                "id": dimension.id,
                "name": dimension.name,
                "avg_gap": round(sum(gaps) / len(gaps), 2) if gaps else None,
            }
        )

    return {
        "report_type": "baseline-gap",
        "schema": "progress-agent/gap/v1",
        "role_label": model.role_label,
        "model_version": model.model_version,
        "profile_version": market_weights.get("profile_version"),
        "generated_at": generated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "based_on_assessment": assessment.get("report_type"),
        "assessment_generated_at": reported_at,
        "summary": {
            "readiness_percent": readiness,
            "weighted_gap": round(total_weighted_gap, 1),
            "weighted_target": round(total_weighted_target, 1),
            "target_level_by_tier": targets,
        },
        "dimensions": dimension_rows,
        "items": rows,
        "notes": (
            "紧急度 = 市场权重 × (目标档位 - 自评档位)。"
            "档位越高表示越接近独立掌握；自评分仍需独立任务复核。"
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    """把差距报告渲染成 Markdown。"""

    lines: list[str] = []
    lines.append(f"# 基准差距报告：{report['role_label']}")
    lines.append("")
    lines.append(f"- 生成时间：{report['generated_at']}")
    lines.append(f"- 依据自测：{report['assessment_generated_at']}")
    lines.append(
        f"- 画像版本：{report['profile_version']}（4 份已入库真实 JD）"
    )
    lines.append(f"- 岗位准备度：**{report['summary']['readiness_percent']} / 100**")
    lines.append("")
    lines.append(f"> {report['notes']}")
    lines.append("")

    lines.append("## 各维度平均缺口")
    lines.append("")
    lines.append("| 维度 | 平均缺口（档） |")
    lines.append("| --- | --- |")
    for dimension in report["dimensions"]:
        avg = dimension["avg_gap"]
        lines.append(f"| {dimension['id']} {dimension['name']} | {avg if avg is not None else '—'} |")
    lines.append("")

    lines.append("## 待补清单（按紧急度排序）")
    lines.append("")
    lines.append("| 能力 | 当前 | 目标 | 缺口 | 权重 | 紧急度 | 证据 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for row in report["items"][:20]:
        lines.append(
            f"| {row['id']} {row['name']} | "
            f"{row['current_level']} | {row['target_level']} | "
            f"{row['gap']} | {row['weight']} | {row['urgency']} | "
            f"{row['evidence']} |"
        )
    lines.append("")

    return "\n".join(lines)
