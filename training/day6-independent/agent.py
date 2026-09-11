"""Day 6 独立检验：在工程化后的 Agent 上加“坏工具连续失败限流”。

基线代码已经写完、5 个单元测试全绿，**不需要再改其他地方**。
你只需要在 `run_agent` 里实现唯一的一件事（见同目录 README.md）：
同一工具连续失败不超过 2 次，超限后不再真正执行，而是回填一条说明
“放弃重试”的 role="tool" 结果。

规则：限时 90 分钟、少 AI（可看自己的代码和官方文档，不许问 AI 要答案）。
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import urllib.request
from typing import Any, Callable

MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")

SYSTEM_PROMPT = (
    "你是 Agent 演示助手。需要实时信息时使用工具；"
    "工具执行结果会以 role='tool' 的消息返回给你，请基于结果作答。"
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前的日期和时间",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_date",
            "description": "获取当前的日期",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气（注意：该服务不稳定，可能执行失败）",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# 工具实现
# ---------------------------------------------------------------------------


def get_current_time(args: dict[str, Any]) -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_current_date(args: dict[str, Any]) -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")


def get_weather(args: dict[str, Any]) -> str:
    """模拟一个不稳定的第三方服务：固定抛错。"""

    city = args.get("city", "未知城市")
    raise RuntimeError(f"天气服务暂时不可用（city={city}）")


TOOL_HANDLERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "get_current_time": get_current_time,
    "get_current_date": get_current_date,
    "get_weather": get_weather,
}


def execute_tool(name: str, args: dict[str, Any]) -> str:
    """执行工具并返回字符串结果。"""

    tool = TOOL_HANDLERS.get(name)
    if tool is None:
        raise ValueError(f"未知工具：{name}")
    return tool(args)


def build_tool_result(tool_call_id: str, content: str) -> dict[str, Any]:
    """构造“工具结果”消息：role 必须是 "tool"，并携带对应的 tool_call_id。"""

    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }


# ---------------------------------------------------------------------------
# 模型调用：有 API Key 调真实 DeepSeek，否则用离线 mock
# ---------------------------------------------------------------------------


def call_llm(messages: list[dict[str, Any]]) -> dict[str, Any]:
    if os.getenv("DEEPSEEK_API_KEY"):
        return _call_deepseek(messages)
    return _mock_llm(messages)


def _call_deepseek(messages: list[dict[str, Any]]) -> dict[str, Any]:
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]


def _mock_llm(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """离线假模型：先请求工具，看到 role=tool 的结果后给出最终回答（确定性，供测试用）。"""

    tool_results = [m for m in messages if m.get("role") == "tool"]
    if tool_results:
        last_result = str(tool_results[-1]["content"])
        if last_result.startswith("[工具错误]"):
            return {
                "content": (
                    f"工具执行失败：{last_result}。"
                    "我无法获取信息，请如实告诉用户稍后再试。"
                ),
                "tool_calls": None,
            }
        return {
            "content": f"根据工具结果回答：{last_result}",
            "tool_calls": None,
        }

    user_question = next(
        message["content"] for message in messages if message.get("role") == "user"
    )
    if "天气" in user_question:
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
                "id": "call_date",
                "type": "function",
                "function": {"name": "get_current_date", "arguments": "{}"},
            }
        ],
    }


# ---------------------------------------------------------------------------
# Agent 循环
# ---------------------------------------------------------------------------


def run_agent(
    question: str,
    llm: Callable[[list[dict[str, Any]]], dict[str, Any]] = call_llm,
    max_attempts: int = 4,
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for attempt in range(1, max_attempts + 1):
        print(f"\n--- 第 {attempt} 轮 ---")
        message = llm(messages)

        messages.append(
            {
                "role": "assistant",
                "content": message.get("content"),
                "tool_calls": message.get("tool_calls"),
            }
        )

        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            print(f"[最终回答] {message.get('content')}")
            return messages

        for tool_call in tool_calls:
            function = tool_call["function"]
            name = function["name"]
            arguments = json.loads(function.get("arguments") or "{}")
            print(f"[工具] {name}({arguments})")

            # ===== Day 6 TODO：本次唯一要改的地方 =====
            # 在这里实现“同一工具连续失败不超过 2 次”的限流（要求见 README.md）：
            #   1. 连续失败计数要跨轮累计（计数器不能定义在轮次循环里面）；
            #   2. 已失败满 2 次的工具不再调用 execute_tool，直接构造放弃重试的结果；
            #   3. 真正执行成功一次，要把该工具的失败计数清零；
            #   4. 无论执行还是放弃，都要用 build_tool_result 回填 role="tool" 消息。
            try:
                result = execute_tool(name, arguments)
            except Exception as error:
                result = f"[工具错误] {error}"
            print(f"[结果] {result}")

            tool_result = build_tool_result(tool_call["id"], result)
            if tool_result.get("role") != "tool":
                raise AssertionError(
                    "工具结果消息的 role 必须是 'tool'，"
                    f"当前是 {tool_result.get('role')!r}"
                )
            messages.append(tool_result)

    raise RuntimeError(f"超过最大轮数 {max_attempts}，Agent 未能给出最终回答。")


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "今天是几号？"
    run_agent(question)
