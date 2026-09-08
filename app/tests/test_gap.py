"""基准差距分析核心逻辑的单元测试。"""

import json
import unittest
from pathlib import Path

from progress_agent.gap import (
    build_gap_report,
    default_market_weights_path,
)
from progress_agent.model import load_model


def _fake_assessment() -> dict:
    return {
        "report_type": "self-assessment",
        "role_label": "Agent 应用开发工程师",
        "model_version": "0.1",
        "generated_at": "2026-09-08 00:00:00",
        "items": [
            {
                "id": "A4",
                "dimension_id": "A",
                "dimension_name": "大模型基础与应用",
                "name": "Function Calling / 工具调用",
                "level": 1,
            },
            {
                "id": "B1",
                "dimension_id": "B",
                "dimension_name": "Agent 核心与编排",
                "name": "Agent 运行循环",
                "level": 0,
            },
            {
                "id": "E1",
                "dimension_id": "E",
                "dimension_name": "Python 工程能力",
                "name": "Python 语言惯用法",
                "level": 2,
            },
        ],
    }


class GapTest(unittest.TestCase):
    def setUp(self) -> None:
        self.model = load_model()
        weights_file: Path = default_market_weights_path()
        self.weights = json.loads(weights_file.read_text(encoding="utf-8"))

    def test_urgency_prefers_core_gaps(self) -> None:
        report = build_gap_report(self.model, _fake_assessment(), self.weights)
        rows = {row["id"]: row for row in report["items"] if row["answered"]}
        # B1 是 Tier1 且 0 分：urgency = 3*3=9；A4 是 Tier1 且 1 分：3*2=6
        self.assertEqual(rows["B1"]["urgency"], 9)
        self.assertEqual(rows["A4"]["urgency"], 6)
        # E1 已到 2：Tier1 target=3 => urgency=3*1=3
        self.assertEqual(rows["E1"]["urgency"], 3)

    def test_unanswered_counts_as_unknown(self) -> None:
        report = build_gap_report(self.model, _fake_assessment(), self.weights)
        self.assertLess(report["summary"]["readiness_percent"], 20)


if __name__ == "__main__":
    unittest.main()
