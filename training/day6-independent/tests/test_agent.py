"""Day 6 独立检验的测试文件：原有 5 个用例已经全绿，不需要动。

运行（在 training/day6-independent 目录下）：

    python3 -m unittest discover -s tests -v

Day 6 任务：在这里新增至少两个测试，覆盖“连续失败限流”的行为契约。
规则：使用注入的假 llm，离线、确定性，不许问 AI 要测试代码。
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
    def test_tool_error_is_fed_back_as_tool_message(self) -> None:
        messages = agent.run_agent("上海天气怎么样？", llm=agent._mock_llm)

        tool_messages = [m for m in messages if m["role"] == "tool"]
        self.assertGreaterEqual(len(tool_messages), 1)
        self.assertEqual(tool_messages[0]["tool_call_id"], "call_weather")
        self.assertTrue(tool_messages[0]["content"].startswith("[工具错误]"))

        last_message = messages[-1]
        self.assertEqual(last_message["role"], "assistant")
        self.assertIn("无法", last_message["content"])
        self.assertNotIn("晴天", last_message["content"])

    def test_date_question_returns_final_answer(self) -> None:
        messages = agent.run_agent("今天是几号？", llm=agent._mock_llm)

        # 先拿到工具返回的日期，后面用它来证明“回答基于工具结果”
        tool_messages = [m for m in messages if m["role"] == "tool"]
        self.assertEqual(len(tool_messages), 1)
        date_result = tool_messages[0]["content"]

        # 最后一条消息：assistant，且 content 是非空字符串
        last = messages[-1]
        self.assertEqual(last["role"], "assistant")
        self.assertIsInstance(last["content"], str)
        self.assertTrue(last["content"], "最终回答不能为空")

        # 最终回答包含工具返回的日期 → 说明答案来自工具结果
        self.assertIn(date_result, last["content"])


# 基线测试：纯函数与注册表一致性（已完成，不需要改）

class PracticeTests(unittest.TestCase):
    # 纯函数测试：日期工具返回合法日期
    def test_exce_tool(self)-> None:
        tool_result =agent.execute_tool("get_current_date",{})
        date =agent.get_current_date({})
        self.assertEqual(tool_result,date)

    # 注册表一致性测试：注册表键 == TOOLS schema 里的名字
    def test_reg(self):
        handler_set = set(agent.TOOL_HANDLERS)
        handler_exp = { t["function"]["name"] for t in agent.TOOLS}
        self.assertEqual(handler_exp,handler_set)


# ===== Day 6 TODO：在下面新增测试（至少两个）=====
# 1) 同一工具连续失败满 2 次后进入“放弃重试”：
#    断言恰好真正执行了 2 次，之后是放弃消息，且放弃消息仍以 role="tool" 回填、带原 tool_call_id。
# 2) 成功一次会把失败计数清零（或你自己设计的等价边界）。
# 提示：现有 _mock_llm 看到 [工具错误] 就收尾，触发不了连续失败，
#       需要自己写一个“反复请求同一个工具”的假 llm。
class Day6Tests(unittest.TestCase):
    def test_gives_up_after_two_consecutive_failures(self) -> None:
        raise NotImplementedError("Day 6 TODO：补这个测试")

    def test_success_resets_failure_counter(self) -> None:
        raise NotImplementedError("Day 6 TODO：补这个测试")


if __name__ == "__main__":
    unittest.main()
