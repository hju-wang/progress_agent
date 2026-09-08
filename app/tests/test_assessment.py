"""能力自测核心逻辑的单元测试（纯标准库）。"""

import unittest

from progress_agent.assessment import build_report, validate_answers
from progress_agent.model import load_model


class AssessmentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model = load_model()

    def test_model_has_expected_shape(self) -> None:
        self.assertEqual(len(self.model.dimensions), 6)
        self.assertEqual(len(self.model.items), 31)

    def test_all_level_two_means_fifty_percent(self) -> None:
        answers = {item.id: 2 for item in self.model.items}
        self.assertEqual(validate_answers(self.model, answers), [])
        report = build_report(self.model, answers)
        self.assertEqual(report["summary"]["overall_percent"], 50.0)
        self.assertEqual(report["scope"]["answered"], 31)

    def test_weakest_first_ordering(self) -> None:
        answers = {item.id: 2 for item in self.model.items}
        answers["B1"] = 0
        answers["E6"] = 1
        report = build_report(self.model, answers)
        self.assertEqual(report["weakest_first"][0]["id"], "B1")
        self.assertEqual(report["weakest_first"][1]["id"], "E6")

    def test_validation_rejects_bad_values(self) -> None:
        errors = validate_answers(self.model, {"A1": 5, "NOT_EXIST": 1})
        self.assertEqual(len(errors), 2)


if __name__ == "__main__":
    unittest.main()
