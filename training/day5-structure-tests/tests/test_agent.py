"""Day 5 单元测试：离线、确定性、不依赖 API Key。

运行（在 training/day5-structure-tests 目录下）：

    python3 -m unittest discover -s tests -v

下面第一个测试是“示例”，照着它的写法补 TODO-3 的两个测试。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# 让测试能 import 上一层的 agent.py（不引入打包/安装流程）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agent  # noqa: E402


class ExecuteToolTests(unittest.TestCase):
    """示例测试：未知工具必须抛 ValueError。"""

    def test_unknown_tool_raises(self) -> None:
        with self.assertRaises(ValueError):
            agent.execute_tool("no_such_tool", {})


class RunAgentTests(unittest.TestCase):
    # TODO-3（知识点：用 unittest 测“行为契约”，不测实现细节）
    # 依赖 TODO-2：run_agent 要能注入 llm，并返回 messages。
    #
    # 提示：
    #   - 用 agent._mock_llm 作为注入的 llm，测试就不联网、结果确定；
    #   - run_agent 会打印过程日志，测试里不用管，只断言返回的 messages。
    #
    # 测试 1：工具报错时，错误必须以 role="tool" 的消息回填
    #   messages = agent.run_agent("上海天气怎么样？", llm=agent._mock_llm)
    #   断言：存在 role == "tool" 的消息；
    #         tool_call_id 对应模型的调用 id；
    #         content 以 "[工具错误]" 开头；
    #         最后一条 assistant 消息是诚实的收尾（不是编造天气）。
    def test_tool_error_is_fed_back_as_tool_message(self) -> None:
        raise NotImplementedError("TODO-3：按上面的提示补这个测试")

    # 测试 2：日期问题能走完循环并给出最终回答
    #   messages = agent.run_agent("今天是几号？", llm=agent._mock_llm)
    #   断言：最后一条消息 role == "assistant" 且有 content；
    #         最终回答基于工具结果（包含上一次工具返回的日期）。
    def test_date_question_returns_final_answer(self) -> None:
        raise NotImplementedError("TODO-3：按上面的提示补这个测试")


if __name__ == "__main__":
    unittest.main()
