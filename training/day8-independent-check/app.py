"""Day 8 独立检验项目：一个迷你 Agent 工具循环（含 3 个缺陷）。

项目结构：

- ToolRegistry：工具注册表（名字 -> 处理函数）
- run_agent：调用模型 -> 执行工具 -> 回填结果 -> 再决策
- mock_llm：离线假模型，供命令行运行

规则与交付要求见 README.md：限时 90 分钟、少 AI。
"""

from __future__ import annotations

import datetime
import json
import sys
from typing import Any, Callable

MAX_CONSECUTIVE_FAILURES = 2

SYSTEM_PROMPT = (
    "你是工具调用助手。需要实时信息时使用工具；"
    "工具执行结果会以 role='tool' 的消息返回给你，请基于结果作答。"
)

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_today",
            "description": "获取今天的日期",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气（该服务不稳定，可能失败）",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    },
]


def get_today(args: dict[str, Any]) -> str:
    return datetime.date.today().isoformat()


def get_weather(args: dict[str, Any]) -> str:
    """模拟不稳定的第三方服务：固定抛错。"""

    city = args.get("city", "未知城市")
    raise RuntimeError(f"天气服务暂时不可用（city={city}）")


class ToolRegistry:
    """工具注册表：维护工具名到处理函数的映射。"""

    def __init__(
        self, tools: dict[str, Callable[[dict[str, Any]], str]] | None = None
    ) -> None:
        self._tools = {} if tools is None else tools

    def register(
        self, name: str, handler: Callable[[dict[str, Any]], str]
    ) -> None:
        self._tools[name] = handler

    def names(self) -> list[str]:
        return sorted(self._tools)

    def execute(self, name: str, args: dict[str, Any]) -> str:
        handler = self._tools.get(name)
        if handler is None:
            raise ValueError(f"未知工具：{name}")
        return handler(args)


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("get_today", get_today)
    registry.register("get_weather", get_weather)
    return registry


def run_agent(
    question: str,
    llm: Callable[[list[dict[str, Any]]], dict[str, Any]],
    registry: ToolRegistry,
    max_attempts: int = 4,
) -> list[dict[str, Any]]:
    """运行工具循环：同一工具连续失败满 2 次后放弃重试。"""

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    fail_counts = {name: 0 for name in registry.names()}

    for attempt in range(1, max_attempts + 1):
        print(f"\n--- 第 {attempt} 轮 ---")
        reply = llm(messages)
        messages.append(
            {
                "role": "assistant",
                "content": reply.get("content"),
                "tool_calls": reply.get("tool_calls"),
            }
        )

        tool_calls = reply.get("tool_calls") or []
        if not tool_calls:
            print(f"[最终回答] {reply.get('content')}")
            return messages

        for tool_call in tool_calls:
            function = tool_call["function"]
            name = function["name"]
            arguments = json.loads(function.get("arguments") or "{}")
            print(f"[工具] {name}({arguments})")

            fails = fail_counts.get(name, 0)
            if fails >= MAX_CONSECUTIVE_FAILURES:
                result = (
                    f"[工具错误] 该工具已连续失败 2 次，放弃重试（tool={name}）"
                )
            else:
                try:
                    result = registry.execute(name, arguments)
                    fail_counts[name] = 0
                except Exception as error:
                    fail_counts[name] = fail_counts.get(name, 0) + 1
                    result = (
                        f"[工具错误] {error}"
                        f"（已连续失败 {fail_counts[name]} 次）"
                    )
            print(f"[结果] {result}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result,
                }
            )

    raise RuntimeError(f"超过最大轮数 {max_attempts}，Agent 未能给出最终回答。")


def mock_llm(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """离线假模型：天气问题要天气工具，其他问题要日期工具，看到结果后收尾。"""

    tool_results = [m for m in messages if m.get("role") == "tool"]
    if tool_results:
        last = str(tool_results[-1]["content"])
        if last.startswith("[工具错误]"):
            return {
                "content": f"无法获取信息，请稍后再试。原因：{last}",
                "tool_calls": None,
            }
        return {"content": f"根据工具结果回答：{last}", "tool_calls": None}

    question = next(
        m["content"] for m in messages if m.get("role") == "user"
    )
    if "天气" in question:
        return {
            "content": None,
            "tool_calls": [
                {
                    "id": "call_weather",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": json.dumps({"city": "上海"}),
                    },
                }
            ],
        }
    return {
        "content": None,
        "tool_calls": [
            {
                "id": "call_today",
                "type": "function",
                "function": {"name": "get_today", "arguments": "{}"},
            }
        ],
    }


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "今天是几号？"
    run_agent(question, mock_llm, build_registry())
