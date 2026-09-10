# Day 4 LangGraph 对照 · 验收卷 v0.1

- 前置条件：先完成 [Day 4 代码任务](../../training/day4-langgraph/README.md)（TODO-1/2/3）并运行通过。
- 考试方式：闭卷。允许看自己的代码、允许运行命令；**不许问 AI 要答案**。
- 提交方式：把你的选项和文字答案直接贴回来。
- 满分 100 分，通过线 80 分。分值分布：Q1 10 / Q2 10 / Q3 15 / Q4 30 / Q5 35。

---

**Q1（单选，10 分）** LangGraph 里一个节点函数的返回值，正确要求是？

A. 返回一个“状态更新字典”，键必须是状态 schema 里定义的字段（如 `{"messages": ...}`）
B. 直接修改模块级全局变量，让别的节点自己去读
C. 返回一个字符串，框架会把它自动塞进状态

对应能力项：B1、E1

答：A

---

**Q2（单选，10 分）** 条件路由返回 `"end"`，对应手写循环（Day 1–3）里的哪一步？

A. `if not tool_calls:` 时打印最终回答并 `return`，结束循环
B. 执行工具那一步
C. 把 assistant 消息 append 进 `messages` 那一步

对应能力项：B1、A4

答：A

---

**Q3（单选，15 分）** `tools_node` 里执行了工具，但忘记把结果以 `role="tool"` 回填进 `messages`，会发生什么？

A. 状态没有变化，最后一条仍是带 `tool_calls` 的 assistant 消息，条件边一直返回 `"continue"`，`tools → agent` 死循环，直到触发 recursion limit 报错
B. 图会正常走到 `END`，只是最终回答少一句
C. 模型会自动改用 `user` 消息继续对话

对应能力项：B2、B1

答：A

---

**Q4（读代码，30 分）** 下面是 `agent_node` 的错误写法：

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

1. （6 分）运行 `agent.py "今天是几号？"` 会看到什么现象？
   答：直接结束，显示 今天是 几号
2. （12 分）根因是什么？为什么它不会报错？
   答：因为直接结束了，走的是 end 那条边,因为这是多余的 schema 里不存在的key，当前版本直接丢弃，不非法
3. （8 分）你会用什么方法快速确认“状态到底有没有更新”？
    答：用 app.stream(..., stream_mode="updates") 看每个节点往状态里提交了什么
4. （4 分）正确的返回应该怎么写？
   答：`return {"messages":new_messages}`

对应能力项：E6、B1

答：

---

**Q5（写一小段，35 分）** 对照说明：同一个 Agent 循环，手写版（Day 1–3）和 LangGraph 版各环节怎么对应；再用两三句说清“框架替你做了什么、你还得自己做什么”。（对照表 20 分，每行 4 分；框架边界 15 分）

提示对照环节：问模型 / 执行工具 / 回填结果 / 判断是否继续 / 结束。

对应能力项：B1、A4、E6

答：
问模型 - 运行graph
执行工具-
回填结果-更AgentState 中的 messages Schema
判断是否继续-route_after_agent用一个条件判断边来代替
结束- 就是结束吧
| 环节 | 手写版（Day 1–3） | LangGraph |
| --- | --- | --- |
| 问模型 | 直接将question 以 role = user 的方式追加到 message 中| 调用构建好的 graph |
| 执行工具 | 直接根据 模型响应的 tool call 结果去执行 excute_tool() | 将excute_tool（）封装成一个 tool_node,然后编排进 graph 中，根据 graph 的逻辑条用|
| 回填结果 | 每次追加 message | 通过更AgentState 中的 message Schema 来控制 |
| 判断是否继续 | 直接判断 模型返回的message 中是否还有 tool_call | route_after_agent用一个条件判断边来代替 |
| 结束 | 不继续直接结束或者 超过最大循环次数结束 | 根据 route_after_agent 来判断是否结束，操作不当有可能陷入死循环 |


框架替我做了什么：状态管理与合并、节点调度和边的跳转、条件分之、流式观察与检查点、递归上线兜底
我还需要做什么：节点内部逻辑（调模型，执行工具，错误恢复），状态字段设计，路由判断规则
---

> 批注区（教练填写）

**教练批注（2026-09-10）**

| 题 | 分值 | 得分 | 说明 |
| --- | --- | --- | --- |
| Q1 | 10 | 10 | 正确。 |
| Q2 | 10 | 10 | 正确。 |
| Q3 | 15 | 15 | 正确，抓住了“状态不变 → 路由不变 → 死循环”。 |
| Q4.1 | 6 | 6 | 现象说对（直接结束、回显问题）。 |
| Q4.2 | 12 | 8 | “多余 key 被静默丢弃”答对；但根因表述仍停在结果（走 end），没点明“返回键 message ≠ 状态字段 messages → 状态未更新”。 |
| Q4.3 | 8 | 8 | 正确：`stream_mode="updates"` 观察节点提交值。 |
| Q4.4 | 4 | 4 | 正确。 |
| Q5 对照表 | 20 | 15 | “执行工具/判断继续/结束”三行正确；“问模型”“回填结果”两行不准确（问模型是 call_llm / agent_node；回填是 append 后 return {"messages": ...}）。 |
| Q5 框架边界 | 15 | 15 | 框架职责与自身职责都对（有几处错别字）。 |

**总分：91 / 100 → 通过（≥80）**

诚实记录：Q4.2、Q4.3 与 Q5 框架边界部分为教练参考内容后由用户誊写，非完全独立作答；Day 6 独立检验会抽查 LangGraph 状态契约与条件边。
