"""Day 4：LangGraph 对照实现工具循环。

前三天手写的 Agent 循环（提问 -> 模型 -> 工具 -> 回填 -> 再问 -> 最终回答）
今天用 LangGraph 的图来表达。含 3 个不同知识点的 TODO。
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import urllib.request
from typing import Any, TypedDict

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # 兼容旧版本
    from langgraph.graph import END, StateGraph

    START = "__start__"

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


def get_current_date() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")


def get_weather(city: str) -> str:
    raise RuntimeError(f"天气服务暂时不可用（city={city}）")


def execute_tool(name: str, args: dict) -> str:
    if name == "get_current_date":
        return get_current_date()
    if name == "get_weather":
        return get_weather(args.get("city", "未知城市"))
    raise ValueError(f"未知工具：{name}")


def build_tool_result(tool_call_id: str, content: str) -> dict:
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }


def call_llm(messages: list[dict]) -> dict:
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
    """离线假模型：先请求工具，看到 role=tool 的结果后给出最终回答。"""

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
                "function": {
                    "name": "get_current_date",
                    "arguments": "{}",
                },
            }
        ],
    }


# ---------------------------------------------------------------------------
# LangGraph 部分：State / 节点 / 条件路由
# ---------------------------------------------------------------------------


class AgentState(TypedDict):
    """图的状态：目前只有消息列表。后续可扩展失败计数、记忆等字段。"""

    messages: list[dict[str, Any]]


def agent_node(state: AgentState) -> dict[str, Any]:
    """问模型，并把 assistant 的回复追加到状态里。"""

    messages = state["messages"]
    reply = call_llm(messages)
    assistant_message = {
        "role": "assistant",
        "content": reply.get("content"),
        "tool_calls": reply.get("tool_calls"),
    }
    new_messages = messages + [assistant_message]

    # TODO-1（知识点：LangGraph 节点契约与状态更新）
    # LangGraph 规定：节点必须返回“状态字典”，格式为 {"messages": new_messages}。
    # 请把下面这行替换成正确的 return。
    return {"messages": new_messages}


def tools_node(state: AgentState) -> dict[str, Any]:
    """执行最后一条 assistant 消息里请求的工具，并把结果回填。"""

    messages = list(state["messages"])
    last_message = messages[-1]

    for tool_call in last_message.get("tool_calls") or []:
        function = tool_call["function"]
        name = function["name"]
        arguments = json.loads(function.get("arguments") or "{}")
        print(f"[工具] {name}({arguments})")

        # TODO-2（知识点：工具节点执行 + 错误恢复 + role=tool 回填）
        # 要求：
        #   1. try: result = execute_tool(name, arguments)
        #   2. except Exception as error: result = f"[工具错误] {error}"
        #   3. messages.append(build_tool_result(tool_call["id"], result))

        try:
            result = execute_tool(name, arguments)
        except Exception as e:
            result = f"[工具错误] {e}"

        messages.append(build_tool_result(tool_call["id"], result))

    return {"messages": messages}


def route_after_agent(state: AgentState) -> str:
    """条件路由：还有工具调用就继续去 tools，否则结束。"""

    last_message = state["messages"][-1]

    # TODO-3（知识点：条件边与终止）
    # 要求：last_message 里还有 tool_calls 时返回 "continue"，否则返回 "end"。
    tool_calls = last_message.get("tool_calls")
    if tool_calls:
        return "continue"
    return "end"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        route_after_agent,
        {"continue": "tools", "end": END},
    )
    graph.add_edge("tools", "agent")
    return graph.compile()


def run_agent(question: str) -> None:
    app = build_graph()
    result = app.invoke(
        {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ]
        }
    )
    final_message = result["messages"][-1]
    print(f"[最终回答] {final_message.get('content')}")


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "今天是几号？"
    try:
        run_agent(question)
    except NotImplementedError as error:
        print(f"\n[报错] {error}")
        print("提示：打开 agent.py，把 TODO-1/2/3 依次实现后再运行。")
