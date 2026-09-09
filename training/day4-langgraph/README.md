# Day 4：LangGraph 对照实现工具循环

目标：前三天你手写了工具循环；今天用 LangGraph（图式框架）实现**同一个循环**，
并体会“框架替你做了什么、你还得自己做什么”。

**本 Day 含 3 个 TODO，知识点互不相同：**

| TODO | 知识点 | 你要写的 |
| --- | --- | --- |
| TODO-1 | LangGraph 节点契约与状态更新 | `agent_node` 的返回值 |
| TODO-2 | 工具节点：执行 + 错误恢复 + 回填 | `tools_node` 的核心循环 |
| TODO-3 | 条件边：继续调工具 or 结束 | `route_after_agent` 的返回值 |

## 先装依赖（只需要一次）

```bash
cd /Users/wangfang/progress_agent/training/day4-langgraph
python3 -m venv .venv
.venv/bin/python -m pip install "langgraph>=0.2"
```

> 后续运行命令都在 `training/day4-langgraph/` 目录里，用 `.venv/bin/python` 执行，
> 不要用全局 python，避免污染环境。

## 先读代码

打开 [agent.py](agent.py)，按这个顺序读：

1. `AgentState`：图的状态——目前只有 `messages` 一个字段。
2. `agent_node`：负责“问模型”，把模型的回复**追加到状态里**。
3. `tools_node`：负责“执行工具”，把结果以 `role="tool"` 回填。
4. `route_after_agent`：负责“下一步去哪”——还有工具调用就回 `tools`，否则结束。
5. `build_graph`：把上面这些粘成一张图：`START → agent → tools → agent → … → END`。

## 三个 TODO

### TODO-1（节点状态）

`agent_node` 已经算好了 `new_messages`，但你还没把“新状态”返回给图。
LangGraph 的规则：**节点必须返回一个状态字典**，比如 `{"messages": new_messages}`。

把 `raise NotImplementedError("TODO-1 ...")` 替换成正确的 `return`。

### TODO-2（工具节点）

在 `tools_node` 里补上每个工具调用的处理：

1. `try: result = execute_tool(name, arguments)`
2. `except Exception as error:` 时 `result = f"[工具错误] {error}"`（Day 2 学过的恢复）
3. `messages.append(build_tool_result(tool_call["id"], result))`

写完删除 `raise NotImplementedError("TODO-2 ...")`。

### TODO-3（条件路由）

`route_after_agent` 要根据**最后一条消息**决定：

- 最后一条消息还带 `tool_calls` → 返回 `"continue"`（图里会路由到 `tools`）；
- 否则 → 返回 `"end"`（图里会路由到 `END`）。

写完删除 `raise NotImplementedError("TODO-3 ...")`。

## 验证（三个 TODO 都完成后跑）

```bash
cd /Users/wangfang/progress_agent/training/day4-langgraph
.venv/bin/python agent.py "今天是几号？"
.venv/bin/python agent.py "上海天气怎么样？"
```

预期：

- 第一段：`[工具] get_current_date(...)` + 基于工具结果的最终回答；
- 第二段：`[工具] get_weather(...)` → `[工具错误] ...` → 诚实的“无法获取天气，请稍后再试”；
- 两段都不出现 `TODO-1/2/3` 报错，也不出现异常堆栈。

## 自检（三个知识点各答一次，写在回复里）

1. 为什么 LangGraph 节点要返回状态字典而不是直接改全局变量？
2. `tools_node` 里如果不把结果回填进 `messages`，图的下一步会发生什么？
3. 条件路由的 `"continue" / "end"` 和手写循环里的 `if not tool_calls: return` 是什么对应关系？

> 代码通过后，我会发 Day 4 验收卷——选择题 + 读代码 + 写一小段，不会问“你懂了吗”。
