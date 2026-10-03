"""Day 8 项目的现有测试：有 2 个用例失败，暴露其中两个缺陷。

隐藏缺陷没有用例覆盖——需要你自己补一个测试把它逼出来。
运行：

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app  # noqa: E402


WEATHER_CALL = {
    "id": "call_weather",
    "type": "function",
    "function": {"name": "get_weather", "arguments": '{"city": "上海"}'},
}


def weather_script(tool_rounds: int, final_text: str) -> list[dict]:
    """前 N 轮都请求 get_weather，最后给出最终回答。"""

    script = [
        {"content": None, "tool_calls": [WEATHER_CALL]} for _ in range(tool_rounds)
    ]
    script.append({"content": final_text, "tool_calls": None})
    return script


def make_scripted_llm(responses: list[dict]):
    """按顺序返回预设响应的假 llm；脚本用完还被调用就报错。"""

    queue = list(responses)

    def fake_llm(messages: list[dict]) -> dict:
        if not queue:
            raise AssertionError("假模型被调用次数超出脚本预期")
        return queue.pop(0)

    return fake_llm


class HappyPathTests(unittest.TestCase):
    def test_today_question_returns_final_answer(self) -> None:
        registry = app.build_registry()
        messages = app.run_agent("今天是几号？", app.mock_llm, registry)

        tool_messages = [m for m in messages if m["role"] == "tool"]
        self.assertEqual(len(tool_messages), 1)
        self.assertIn(tool_messages[0]["content"], messages[-1]["content"])

    def test_unknown_tool_raises(self) -> None:
        registry = app.build_registry()
        with self.assertRaises(ValueError):
            registry.execute("no_such_tool", {})


class FailureHandlingTests(unittest.TestCase):
    def test_gives_up_after_two_consecutive_failures(self) -> None:
        registry = app.build_registry()
        executed: list[str] = []
        real_execute = registry.execute
        def counting_execute(name: str, args: dict) -> str:
            executed.append(name)
            return real_execute(name, args)

        llm = make_scripted_llm(weather_script(3, "天气查不到，请稍后再试。"))
        with mock.patch.object(registry, "execute", side_effect=counting_execute):
            messages = app.run_agent("上海天气怎么样？", llm, registry)

        # 真正执行恰好 2 次，第 3 次请求应被熔断
        self.assertEqual(executed, ["get_weather", "get_weather"])

        tool_messages = [m for m in messages if m["role"] == "tool"]
        self.assertEqual(len(tool_messages), 3)  # 2 次失败 + 1 次放弃
        give_up = tool_messages[-1]
        self.assertTrue(give_up["content"].startswith("[工具错误]"))
        self.assertIn("放弃重试", give_up["content"])
        self.assertEqual(give_up["tool_call_id"], "call_weather")
        self.assertEqual(messages[-1]["role"], "assistant")

    def test_success_resets_failure_counter(self) -> None:
        registry = app.build_registry()
        executed: list[str] = []
        outcomes: list = [
            RuntimeError("第一次失败"),
            "晴，25℃",
            RuntimeError("第三次失败"),
            RuntimeError("第四次失败"),
        ]

        def flaky_execute(name: str, args: dict) -> str:
            executed.append(name)
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        llm = make_scripted_llm(weather_script(4, "根据结果回答：晴，25℃"))
        with mock.patch.object(registry, "execute", side_effect=flaky_execute):
            messages = app.run_agent(
                "上海天气怎么样？", llm, registry, max_attempts=6
            )

        # 失败→成功（清零）→失败→失败：4 次都应真正执行
        self.assertEqual(executed, ["get_weather"] * 4)
        self.assertEqual(outcomes, [])

        tool_messages = [m for m in messages if m["role"] == "tool"]
        self.assertEqual(len(tool_messages), 4)
        self.assertFalse(
            any("放弃重试" in str(m["content"]) for m in tool_messages)
        )



#自己写的测试

# def get_today(args: dict[str, Any]) -> str:
#     return datetime.date.today().isoformat()


# def get_weather(args: dict[str, Any]) -> str:
#     """模拟不稳定的第三方服务：固定抛错。"""

#     city = args.get("city", "未知城市")
#     raise RuntimeError(f"天气服务暂时不可用（city={city}）")

class SameToolRegistryObj(unittest.TestCase):
    def test_tool_registry(self)->None:
        registry_a = app.ToolRegistry()
        registry_b = app.ToolRegistry()
        registry_a.register("get_today", app.get_today)
        registry_b.register("get_weather",app.get_weather)
        
        #这时候a 中不应该有 get_weather ,b 不应该污染 a
        self.assertNotIn("get_weather",registry_a.names())
        self.assertNotIn("get_today",registry_b.names())


class CircuitBreakerBoundaryTests(unittest.TestCase):
    def test_single_failure_does_not_trip_the_breaker(self) -> None:
        registry = app.build_registry()
        executed: list[str] = []
        outcomes: list = [RuntimeError("第一次失败"), "晴，25℃"]

        def flaky_execute(name: str, args: dict) -> str:
            executed.append(name)
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        llm = make_scripted_llm(weather_script(2, "根据结果回答：晴，25℃"))
        with mock.patch.object(registry, "execute", side_effect=flaky_execute):
            messages = app.run_agent("上海天气怎么样？", llm, registry)

        # 只失败 1 次 → 不该熔断，第 2 次必须真正执行
        self.assertEqual(executed, ["get_weather", "get_weather"])
        tool_messages = [m for m in messages if m["role"] == "tool"]
        self.assertFalse(
            any("放弃重试" in str(m["content"]) for m in tool_messages)
        )
        
        
if __name__ == "__main__":
    unittest.main()
