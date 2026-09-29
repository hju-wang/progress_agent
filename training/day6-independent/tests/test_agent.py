"""Day 6 测试文件：原有 5 个用例 + 限流相关的 2 个用例。

运行（在 training/day6-independent 目录下）：

    python3 -m unittest discover -s tests -v

说明：下面 Day6Tests 的两个用例由教练代写（用户选择 B 方案），
非独立完成；真正的独立检验顺延到下一周计划里重做。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

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


# ===== Day 6 限流测试（教练代写，非独立完成）=====

WEATHER_CALL = {
    "id": "call_weather",
    "type": "function",
    "function": {"name": "get_weather", "arguments": '{"city": "上海"}'},
}


def weather_script(tool_rounds: int, final_text: str) -> list[dict]:
    """构造按顺序返回的假模型脚本：前 N 轮要 get_weather，最后给最终回答。"""

    script = [
        {"content": None, "tool_calls": [WEATHER_CALL]} for _ in range(tool_rounds)
    ]
    script.append({"content": final_text, "tool_calls": None})
    return script


def make_scripted_llm(responses: list[dict]):
    """按顺序返回预设响应的假 llm；脚本用完还被调用就报错，暴露轮数超预期。"""

    queue = list(responses)

    def fake_llm(messages: list[dict]) -> dict:
        if not queue:
            raise AssertionError("假模型被调用次数超出脚本预期")
        return queue.pop(0)

    return fake_llm


class Day6Tests(unittest.TestCase):
    def test_gives_up_after_two_consecutive_failures(self) -> None:
        executed: list[str] = []

        def failing_execute_tool(name: str, args: dict) -> str:
            executed.append(name)
            raise RuntimeError(f"天气服务暂时不可用（city={args.get('city')}）")

        fake_llm = make_scripted_llm(
            weather_script(3, "天气查不到，已放弃重试，请稍后再试。")
        )

        with mock.patch.object(agent, "execute_tool", side_effect=failing_execute_tool):
            messages = agent.run_agent("上海天气怎么样？", llm=fake_llm)

        # 真正执行只有 2 次，第 3 次请求被限流拦下
        self.assertEqual(executed, ["get_weather", "get_weather"])

        tool_messages = [m for m in messages if m["role"] == "tool"]
        self.assertEqual(len(tool_messages), 3)  # 2 次失败 + 1 次放弃

        give_up = tool_messages[-1]
        self.assertTrue(give_up["content"].startswith("[工具错误]"))
        self.assertIn("放弃重试", give_up["content"])
        self.assertIn("get_weather", give_up["content"])
        self.assertEqual(give_up["tool_call_id"], "call_weather")

        self.assertEqual(messages[-1]["role"], "assistant")
        self.assertIn("稍后再试", messages[-1]["content"])

    def test_success_resets_failure_counter(self) -> None:
        executed: list[str] = []
        outcomes: list = [
            RuntimeError("第一次失败"),
            "晴，25℃",
            RuntimeError("第三次失败"),
            RuntimeError("第四次失败"),
        ]

        def flaky_execute_tool(name: str, args: dict) -> str:
            executed.append(name)
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        fake_llm = make_scripted_llm(weather_script(4, "根据结果回答：晴，25℃"))

        with mock.patch.object(agent, "execute_tool", side_effect=flaky_execute_tool):
            messages = agent.run_agent(
                "上海天气怎么样？", llm=fake_llm, max_attempts=6
            )

        # 失败→成功（清零）→失败→失败：第 4 次仍真正执行，说明成功那次把计数清零了
        self.assertEqual(executed, ["get_weather"] * 4)
        self.assertEqual(outcomes, [])

        tool_messages = [m for m in messages if m["role"] == "tool"]
        self.assertEqual(len(tool_messages), 4)
        self.assertEqual(tool_messages[1]["content"], "晴，25℃")
        self.assertFalse(
            any("放弃重试" in str(m["content"]) for m in tool_messages)
        )
        self.assertEqual(messages[-1]["role"], "assistant")


if __name__ == "__main__":
    unittest.main()
