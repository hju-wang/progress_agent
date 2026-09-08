# Day 2 错误恢复 · 验收卷 v0.1

- 前置条件：先完成 [Day 2 代码任务](../../training/day2-error-recovery/README.md)（TODO-2：工具报错不崩、错误喂回模型），运行通过。
- 考试方式：闭卷。允许看自己的代码、允许运行命令；**不许问 AI 要答案**。
- 提交方式：把你的选项、运行输出、代码/设计答案直接贴回来。

---

**Q1（单选）** 模型返回 `tool_calls` 后，正确的处理顺序是？

A. 先追加一条带 `tool_calls` 的 `assistant` 消息 → 逐个执行工具 → 把每条结果以 `role="tool"` 追加（带对应 `tool_call_id`）→ 再次调用模型
B. 直接执行工具 → 把结果拼进下一条 `user` 消息 → 再次调用模型
C. 先追加工具结果 → 再追加 `assistant` 消息 → 再次调用模型

对应能力项：A4、B1

答：选 A 但是我有点疑惑，没看到有追加 assistant 消息

批注（教练）：A 正确。带 `tool_calls` 的 `assistant` 消息在 `run_agent` 里 `call_llm` 之后、执行工具之前就已追加（`training/day2-error-recovery/agent.py` 第 179 行起）；运行日志只打印 `[工具]` / `[结果]`，不打印 messages，所以“看不到”。

---

**Q2（单选）** 下面是 Day 1 里故意埋错的代码（现在你应已改正）：

```python
return {
    "role": "assistant",  # ← 错误
    "tool_call_id": tool_call_id,
    "content": content,
}
```

这段代码错在哪？

A. `role` 应该是 `"tool"`，模型才能认出这是工具执行结果
B. `role` 应该是 `"function"`
C. `content` 必须用 JSON 编码
D. 工具结果消息不应该带 `tool_call_id`

对应能力项：A4、B2

答：A

---

**Q3（单选）** 如果 Q2 的错误没改（结果消息的 role 一直是 `"assistant"`），并且有人把最大轮数保护删掉了，Agent 会发生什么？

A. 模型看不到工具结果，会一直重复请求同一个工具，无限循环
B. 模型会正常给出最终回答
C. 程序立刻崩溃

对应能力项：B1、B2

答：A

---

**Q4（实操）** 贴出你完成 Day 2 代码任务后的**真实运行输出**（两段都要）：

```bash
python3 training/day2-error-recovery/agent.py "上海天气怎么样？"
python3 training/day2-error-recovery/agent.py "今天是几号？"
```

验收标准：第一段不出现异常堆栈，能看到 `[工具错误] ...` 和一句诚实的最终回答；第二段仍能正常回答日期。

对应能力项：B2、E6

答：
```shell
 python3 training/day2-error-recovery/agent.py "上海天气怎么样"

--- 第 1 轮 ---
[工具] get_weather({'city': '上海'})
[结果] [工具错误] 天气服务暂时不可用（city=上海）

--- 第 2 轮 ---
[最终回答] 抱歉，天气服务目前暂时不可用，我暂时无法查询到上海的实时天气情况。

由于天气服务不稳定，我无法为你提供准确的天气预报。建议你可以：

1. **稍后再试**——我随时可以帮你重新查询
2. **访问天气网站或App**——如中国天气网、天气预报等官方渠道获取准确信息

如果你需要的话，我可以再帮你尝试一次查询，或者帮你获取当前的时间信息。有什么其他可以帮你的吗？
❯ python3 training/day2-error-recovery/agent.py "今天是几号"

--- 第 1 轮 ---
[工具] get_current_date({})
[结果] 2026-09-08

--- 第 2 轮 ---
[最终回答] 今天是 **2026年9月8日**（星期二）。

```

---

**Q5（设计与代码）** 如果一个工具**每次都失败**（比如天气服务持续宕机），只靠“把错误喂回模型”够吗？请回答两个小问：

1. 这个 Agent 会无限重试吗？如果不会，是靠什么停下来的？
   答：不会无限重试，当模型不在返回 tool_calls 的时候，会停止，并且通过 attempt 兜底
2. 写一小段思路或伪代码（≤8 行），说明你会如何限制“同一把坏工具不要反复重试超过 2 次”。
   答：
   ```python
   # 定义一个tool 调用计数器
   tool_call_count = {}

    for tool_call in tool_calls:

        function = tool_call["function"]
        name = function["name"]
        
        if name not in tool_call_count or tool_count_count[name] > 2:
            执行工具
            追加message
               
   
   ```

教练参考答案（用户要求直接给答案；本题**非独立完成**，D5 需在 Day 6 复验）：
```python
tool_call_count = {}  # 放在所有轮次之外：{工具名: 已失败次数}

for tool_call in tool_calls:
    name = tool_call["function"]["name"]
    if tool_call_count.get(name, 0) >= 2:
        result = "[工具错误] 该工具已连续失败 2 次，放弃重试"
    else:
        try:
            result = execute_tool(name, arguments)
        except Exception as e:
            tool_call_count[name] = tool_call_count.get(name, 0) + 1
            result = f"[工具错误] {e}"
    messages.append(build_tool_result(tool_call["id"], result))
```

对应能力项：B2、D5（成本/容错意识）
