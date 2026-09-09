"""Day 3 mini-agent + RAG 检索工具：知识类问题先检索资料，再基于资料作答。

在 Day 2 的工具调用循环（含错误恢复）基础上，新增一个 search_knowledge
工具：本地资料库 -> 分块 -> 检索打分 -> 命中结果以 role="tool" 回填。
纯 Python 标准库，无第三方依赖，默认离线 mock，可配 DeepSeek 真实模型。
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
import urllib.request

MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")

SYSTEM_PROMPT = (
    "你是 Agent 演示助手。需要实时信息时使用工具；"
    "知识/概念/流程/术语类问题优先使用 search_knowledge 检索本地资料，"
    "必须基于检索到的资料作答，并标注来源（如 doc-2-1）。"
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
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "在本地知识库检索与问题最相关的资料，返回命中的资料编号、标题与原文；知识/概念/流程/术语类问题使用它",
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# 1) 本地资料库（文档）
# ---------------------------------------------------------------------------

DOCUMENTS = [
    {
        "id": "doc-1",
        "title": "工具调用与消息角色",
        "content": (
            "工具调用（function calling）过程中有四种消息角色：system 描述系统设定，"
            "user 是用户提问，assistant 携带模型回复或工具调用请求，tool 是工具执行结果。"
            "assistant 请求调用工具后，应用必须把每条结果以 role=tool、并带对应 "
            "tool_call_id 的消息回填给模型，模型才能基于结果继续回答。"
        ),
    },
    {
        "id": "doc-2",
        "title": "RAG 检索增强的流程",
        "content": (
            "RAG（检索增强生成）分三步：先对文档分块并建立检索索引；"
            "再根据用户问题检索最相关的资料块；最后把检索到的资料放入上下文，"
            "让模型基于资料作答并标注来源，从而减少幻觉。"
        ),
    },
    {
        "id": "doc-3",
        "title": "工具出错时的恢复",
        "content": (
            "真实世界的第三方工具或 API 一定会失败。Agent 的做法不是让进程崩溃，"
            "而是捕获异常、把错误转成一条普通工具结果喂回模型，让模型诚实告诉用户稍后再试。"
            "为了防止坏工具被反复调用，还要限制同一工具的失败重试次数。"
        ),
    },
    {
        "id": "doc-4",
        "title": "引用溯源",
        "content": (
            "引用溯源要求模型回答时指出依据的资料编号或来源，例如 doc-2-1。"
            "这样用户能核对答案是否真的来自检索结果，也是排查幻觉的重要手段："
            "如果模型答不出或资料不足，应承认不知道，而不是编造。"
        ),
    },
]


# ---------------------------------------------------------------------------
# 2) 文本处理：切词、分块、建索引
# ---------------------------------------------------------------------------

_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    """把文本切成可比较的 token：英文/数字按词，中文按相邻二元组。"""

    text = text.lower()
    tokens: list[str] = re.findall(r"[a-z0-9]+", text)
    for run in _CJK_RE.findall(text):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i : i + 2] for i in range(len(run) - 1))
    return tokens


def split_chunks(text: str, max_chars: int = 70) -> list[str]:
    """按句子把文档切成小块，相邻句子尽量合并到接近 max_chars。"""

    sentences = re.split(r"(?<=[。！？])", text.strip())
    chunks: list[str] = []
    buffer = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(buffer) + len(sentence) <= max_chars:
            buffer += sentence
        else:
            if buffer:
                chunks.append(buffer)
            buffer = sentence
    if buffer:
        chunks.append(buffer)
    return chunks


def build_chunks() -> list[dict]:
    """把 DOCUMENTS 切成小块，并预计算每块的 token，作为简易“索引”。"""

    chunks: list[dict] = []
    for doc in DOCUMENTS:
        for idx, text in enumerate(split_chunks(doc["content"]), start=1):
            chunks.append(
                {
                    "id": f"{doc['id']}-{idx}",
                    "doc_id": doc["id"],
                    "title": doc["title"],
                    "text": text,
                    "tokens": tokenize(text),
                }
            )
    return chunks


CHUNKS = build_chunks()


def score_chunk(question_tokens: list[str], chunk_tokens: list[str]) -> int:
    """返回资料块与问题的相关度：question 的 token 有多少个也出现在资料块里。"""

    # TODO-3：实现打分逻辑（一到两行即可）
    # 要求：共同 token 越多得分越高；完全没有共同 token 时返回 0。
    # 提示：chunk_tokens 是否包含某个 token 用 `in` 判断。
    raise NotImplementedError(
        "TODO-3 还没实现：请先写 score_chunk，让知识类问题能检索到资料。"
    )


def retrieve(question: str, k: int = 2) -> list[dict]:
    """检索与 question 最相关的 k 个资料块，按得分降序返回。"""

    question_tokens = tokenize(question)
    scored = [(score_chunk(question_tokens, chunk["tokens"]), chunk) for chunk in CHUNKS]
    hits = [item for item in scored if item[0] > 0]
    hits.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [
        {
            "id": chunk["id"],
            "title": chunk["title"],
            "text": chunk["text"],
            "score": score,
        }
        for score, chunk in hits[:k]
    ]


def search_knowledge(question: str) -> str:
    """检索工具的执行函数：把命中结果格式化成文本，供模型阅读。"""

    hits = retrieve(question)
    if not hits:
        return "[检索] 未命中任何资料：知识库里没有与问题匹配的内容。"
    lines = []
    for hit in hits:
        lines.append(
            f"[命中] {hit['id']}（score={hit['score']}）《{hit['title']}》\n{hit['text']}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 3) 时间/天气工具（沿用 Day 1/2）
# ---------------------------------------------------------------------------


def get_current_date() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")


def get_current_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
    elif name == "search_knowledge":
        return search_knowledge(args.get("question", ""))
    raise ValueError(f"未知工具：{name}")


def build_tool_result(tool_call_id: str, content: str) -> dict:
    """构造“工具结果”消息：role 必须是 "tool"，并携带对应的 tool_call_id。"""

    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }


# ---------------------------------------------------------------------------
# 4) 模型调用：有 API Key 调真实 DeepSeek，否则用离线 mock
# ---------------------------------------------------------------------------

_KNOWLEDGE_TRIGGERS = (
    "rag",
    "工具调用",
    "角色",
    "引用",
    "溯源",
    "幻觉",
    "流程",
    "分块",
    "索引",
    "资料",
    "检索",
    "什么是",
    "是什么",
    "如何",
    "为什么",
    "怎么办",
)


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
    """离线假模型：先决定用哪个工具，看到工具结果后给出最终回答。"""

    tool_results = [
        message for message in messages if message.get("role") == "tool"
    ]
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
        if last_result.startswith("[检索] 未命中"):
            return {
                "content": (
                    "检索结果为空。应如实告诉用户：本地知识库中没有与问题匹配的"
                    "资料，无法回答，而不是编造。"
                ),
                "tool_calls": None,
            }
        if last_result.startswith("[命中]"):
            return {
                "content": f"根据检索到的资料作答：\n{last_result}",
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
    elif "几号" in question or "日期" in question or "date" in question:
        tool_name = "get_current_date"
        tool_id = "call_demo_date"
        tool_args = "{}"
    elif any(trigger in question for trigger in _KNOWLEDGE_TRIGGERS):
        tool_name = "search_knowledge"
        tool_id = "call_demo_search"
        tool_args = json.dumps({"question": user_question}, ensure_ascii=False)
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


# ---------------------------------------------------------------------------
# 5) Agent 运行循环（沿用 Day 2：工具错误会转成 [工具错误] 回填）
# ---------------------------------------------------------------------------


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
            except NotImplementedError:
                raise
            except Exception as error:
                result = f"[工具错误] {error}"
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
    question = sys.argv[1] if len(sys.argv) > 1 else "RAG 的流程是什么？"
    try:
        run_agent(question)
    except (AssertionError, NotImplementedError) as error:
        print(f"\n[报错] {error}")
        print("提示：打开 agent.py，找到 TODO-3，实现 score_chunk 后再运行。")
