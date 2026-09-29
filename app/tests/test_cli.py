"""CLI 入口回归测试：assess 生成的报告必须能写入 --output-dir。"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from progress_agent import cli
from progress_agent.model import load_model


class AssessCommandTest(unittest.TestCase):
    def test_assess_saves_report_to_output_dir(self) -> None:
        answers = {item.id: 1 for item in load_model().items}

        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            with mock.patch.object(cli, "_run_interactive", return_value=answers):
                code = cli.main(["assess", "--output-dir", str(output_dir)])

            self.assertEqual(code, 0)
            self.assertEqual(len(list(output_dir.glob("self-assessment-*.json"))), 1)
            self.assertEqual(len(list(output_dir.glob("self-assessment-*.md"))), 1)


if __name__ == "__main__":
    unittest.main()
