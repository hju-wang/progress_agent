"""Day 5：把前几天的单文件 Agent 做工程化收尾——结构、可测试性、测试。

本文件是目前“能跑但不够工程化”的版本，含 3 个不同知识点的 TODO：

- TODO-1（结构）：用“工具注册表”字典分发替代 if/elif 分支；
- TODO-2（可测试性）：允许注入 llm 函数，并让 run_agent 返回 messages；
- TODO-3（测试）：在 tests/test_agent.py 里补两个单元测试。
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


# TODO-1（知识点：Python 惯用法——用数据结构替代分支）
# 要求：
#   1. 新增一个模块级字典 TOOL_HANDLERS: dict[str, Callable[[dict[str, Any]], str]]，
#      键是工具名，值是“接收 args、返回字符串”的函数；
#   2. 让 execute_tool 只做“查表 + 调用”，未知工具 raise ValueError；
#   3. 三个工具的行为必须和现在完全一致。
# 自检：python3 -c "import agent; print(sorted(agent.TOOL_HANDLERS))"
#       应输出 ['get_current_date', 'get_current_time', 'get_weather']
TOOL_HANDLERS: dict[str, Callable[[dict[str, Any]], str]] = {}


def execute_tool(name: str, args: dict[str, Any]) -> str:
    """执行工具并返回字符串结果。"""

    if name == "get_current_time":
        return get_current_time(args)
    if name == "get_current_date":
        return get_current_date(args)
    if name == "get_weather":
        return get_weather(args)
    raise ValueError(f"未知工具：{name}")


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


# TODO-2（知识点：依赖注入与可测试性）
# 现在 run_agent 写死了 call_llm，而且只 print、不返回值，测试没法断言中间消息。
# 要求：
#   1. 签名改成 run_agent(question, llm=call_llm, max_attempts=4)；
#   2. 循环里调 llm(...) 而不是 call_llm(...)；
#   3. 正常结束（打印最终回答）时 return messages，让调用方能检查整段消息；
#   4. 外部行为不变：命令行直接运行仍然只打印，不因为返回多了一行输出。
def run_agent(question: str, max_attempts: int = 4) -> None:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for attempt in range(1, max_attempts + 1):
        print(f"\n--- 第 {attempt} 轮 ---")
        message = call_llm(messages)

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
            return

        for tool_call in tool_calls:
            function = tool_call["function"]
            name = function["name"]
            arguments = json.loads(function.get("arguments") or "{}")
            print(f"[工具] {name}({arguments})")

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
