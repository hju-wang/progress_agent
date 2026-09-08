"""Day 1 mini-agent：用户提问 → 工具调用 → 结果回填 → 最终回答。"""

from __future__ import annotations

import datetime
import json
import os
import sys
import urllib.request

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


def get_current_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_current_date() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")


def get_weather(city: str) -> str:
    """模拟一个不稳定的第三方服务：固定抛错。"""

    raise RuntimeError(f"天气服务暂时不可用（city={city}）")


def execute_tool(name: str, args: dict) -> str:
    """执行工具并返回字符串结果。"""

    if name == "get_current_time":
        return get_current_time()
    elif name == "get_current_date":
        return get_current_date()
    elif name == "get_weather":
        return get_weather(args.get("city", "未知城市"))
    raise ValueError(f"未知工具：{name}")


def build_tool_result(tool_call_id: str, content: str) -> dict:
    """构造“工具结果”消息：role 必须是 "tool"，并携带对应的 tool_call_id。"""

    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }


def call_llm(messages: list[dict]) -> dict:
    """有 API Key 时调用真实 DeepSeek，否则使用内置 mock。"""

    if os.getenv("DEEPSEEK_API_KEY"):
        return _call_deepseek(messages)
    return _mock_llm(messages)


def _call_deepseek(messages: list[dict]) -> dict:
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


def _mock_llm(messages: list[dict]) -> dict:
    """离线假模型：先请求工具，看到工具结果后给出最终回答。"""

    tool_results = [
        message for message in messages if message.get("role") == "tool"
    ]
    if tool_results:
        last_result = tool_results[-1]["content"]
        if str(last_result).startswith("[工具错误]"):
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
        message["content"]
        for message in messages
        if message.get("role") == "user"
    )
    question = user_question.lower()
    if "天气" in question:
        tool_name = "get_weather"
        tool_id = "call_demo_weather"
        tool_args = '{"city": "上海"}'
    elif "日期" in question or "几号" in question or "date" in question:
        tool_name = "get_current_date"
        tool_id = "call_demo_date"
        tool_args = "{}"
    else:
        tool_name = "get_current_time"
        tool_id = "call_demo_time"
        tool_args = "{}"
    return {
        "content": None,
        "tool_calls": [
            {
                "id": tool_id,
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": tool_args,
                },
            }
        ],
    }


def run_agent(question: str, max_attempts: int = 4) -> None:
    messages: list[dict] = [
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
            except Exception as e:
                result = f"[工具错误] {e}"
                     
            print(f"[结果] {result}")
            tool_result = build_tool_result(tool_call["id"], result)
            if tool_result.get("role") != "tool":
                raise AssertionError(
                    "TODO-1 还没改对：工具结果消息的 role 必须是 'tool'，"
                    f"当前是 {tool_result.get('role')!r}"
                )
            messages.append(tool_result)

    raise RuntimeError(f"超过最大轮数 {max_attempts}，Agent 未能给出最终回答。")


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "今天是几号"
    try:
        run_agent(question)
    except AssertionError as error:
        print(f"\n[报错] {error}")
        print("提示：打开 agent.py，找到 TODO-1，改正 role 后再运行。")
