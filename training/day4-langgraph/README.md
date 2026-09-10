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

## 调试辅助：[debug_stream.py](debug_stream.py)

`.invoke()` 只能看到最终状态；排查“状态有没有被更新”时用 `.stream()` 看每一步：

```bash
cd /Users/wangfang/progress_agent/training/day4-langgraph
.venv/bin/python debug_stream.py "今天是几号？"
```

- `stream_mode="updates"`：只吐每个节点提交的状态更新，形状 `{节点名: 更新}`；
- 正常应看到 agent 提交 assistant 消息 → tools 提交 `role="tool"` 结果 → agent 提交最终回答；
- 若某节点显示 `{'agent': None}`，说明它执行了但返回值没被状态接收（键名/schema 不匹配）。

## 自检（三个知识点各答一次，写在回复里）

1. 为什么 LangGraph 节点要返回状态字典而不是直接改全局变量？
    因为每经过一次节点，状态字典都会更新，这样更有利于检查，流式观察每一步的状态
2. `tools_node` 里如果不把结果回填进 `messages`，图的下一步会发生什么？
    答：图的下一步持续调用 tool 节点，进而会陷入死循环
3. 条件路由的 `"continue" / "end"` 和手写循环里的 `if not tool_calls: return` 是什么对应关系？
   答：就是 if not call == end,有 tool_call 就 continue

> 代码通过后，我会发 Day 4 验收卷——选择题 + 读代码 + 写一小段，不会问“你懂了吗”。

---

## Day 4 总结（2026-09-10）✅

### 完成情况

- 三个 TODO 均实现并通过验证：
  - TODO-1：`agent_node` 返回 `{"messages": new_messages}`（状态 schema 契约）；
  - TODO-2：`tools_node` 执行工具、异常转 `[工具错误]`、以 `role="tool"` 回填；
  - TODO-3：`route_after_agent` 依据最后一条消息的 `tool_calls` 返回 `"continue"` / `"end"`。
- 验证输出：日期正常；天气走 `[工具错误]` 后诚实收场。
- 验收卷得分：**91 / 100（通过，≥80）**。扣分点：Q4.2 根因只答到“走 end”这一结果，未点明键名不匹配导致状态未更新；Q5 对照表“问模型 / 回填结果”两行不准确。

### 学会/巩固的点

- LangGraph 节点契约：节点返回状态更新字典，键必须是状态 schema 里的字段；未知键会被静默忽略。
- 图的构成：`add_node` 注册节点、`add_edge` 固定跳转、`add_conditional_edges` 按路由函数返回值分支、`compile()` 生成可运行对象。
- 条件边与手写循环的对应：`continue → tools → agent` 是下一轮；`end → END` 是 `if not tool_calls: return`。
- 忘回填 `role="tool"` 会导致状态不变、路由永远 `continue`，最终触发 `recursion_limit`（实测 `GraphRecursionError`）。
- 观测手段：`app.stream(..., stream_mode="updates")` 看每步提交了什么，`"values"` 看完整状态演进。

### 诚实记录

- 试卷 Q4.2 / Q4.3 与 Q5 的“框架边界”部分为教练参考内容后由用户誊写，**非完全独立作答**。
- Q5 对照表中“问模型 / 回填结果”两行仍未达标（得分 15/20）。
- Day 6 独立检验需抽查 LangGraph 状态契约、条件边与 `role="tool"` 回填。

### 下一步

- Day 5：收尾——整理 `training/` 代码结构、补测试、把 README 写清楚（待开始）。
