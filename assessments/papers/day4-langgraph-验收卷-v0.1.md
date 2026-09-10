# Day 4 LangGraph 对照 · 验收卷 v0.1

- 前置条件：先完成 [Day 4 代码任务](../../training/day4-langgraph/README.md)（TODO-1/2/3）并运行通过。
- 考试方式：闭卷。允许看自己的代码、允许运行命令；**不许问 AI 要答案**。
- 提交方式：把你的选项和文字答案直接贴回来。

---

**Q1（单选）** LangGraph 里一个节点函数的返回值，正确要求是？

A. 返回一个“状态更新字典”，键必须是状态 schema 里定义的字段（如 `{"messages": ...}`）
B. 直接修改模块级全局变量，让别的节点自己去读
C. 返回一个字符串，框架会把它自动塞进状态

对应能力项：B1、E1

答：

---

**Q2（单选）** 条件路由返回 `"end"`，对应手写循环（Day 1–3）里的哪一步？

A. `if not tool_calls:` 时打印最终回答并 `return`，结束循环
B. 执行工具那一步
C. 把 assistant 消息 append 进 `messages` 那一步

对应能力项：B1、A4

答：

---

**Q3（单选）** `tools_node` 里执行了工具，但忘记把结果以 `role="tool"` 回填进 `messages`，会发生什么？

A. 状态没有变化，最后一条仍是带 `tool_calls` 的 assistant 消息，条件边一直返回 `"continue"`，`tools → agent` 死循环，直到触发 recursion limit 报错
B. 图会正常走到 `END`，只是最终回答少一句
C. 模型会自动改用 `user` 消息继续对话

对应能力项：B2、B1

答：

---

**Q4（读代码）** 下面是 `agent_node` 的错误写法：

```python
def agent_node(state: AgentState) -> dict[str, Any]:
    messages = state["messages"]
    reply = call_llm(messages)
    assistant_message = {
        "role": "assistant",
        "content": reply.get("content"),
        "tool_calls": reply.get("tool_calls"),
    }
    new_messages = messages + [assistant_message]
    return {"message": new_messages}   # ← 注意键名
```

`AgentState` 里定义的字段是 `messages`。请回答：

1. 运行 `agent.py "今天是几号？"` 会看到什么现象？
2. 根因是什么？为什么它不会报错？
3. 你会用什么方法快速确认“状态到底有没有更新”？
4. 正确的返回应该怎么写？

对应能力项：E6、B1

答：

---

**Q5（写一小段）** 对照说明：同一个 Agent 循环，手写版（Day 1–3）和 LangGraph 版各环节怎么对应；再用两三句说清“框架替你做了什么、你还得自己做什么”。

提示对照环节：问模型 / 执行工具 / 回填结果 / 判断是否继续 / 结束。

对应能力项：B1、A4、E6

答：

---

> 批注区（教练填写）
