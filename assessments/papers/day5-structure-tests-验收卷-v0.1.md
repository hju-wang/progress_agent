# Day 5 工程化收尾 · 验收卷 v0.1

- 前置条件：先完成 [Day 5 代码任务](../../training/day5-structure-tests/README.md)（TODO-1/2/3 + README 交付物），`python3 -m unittest discover -s tests -v` 三个测试全绿。
- 考试方式：闭卷。允许看自己的代码、允许运行命令；**不许问 AI 要答案**。
- 提交方式：把你的选项、代码、文字答案直接贴回来。
- 满分 100 分，通过线 80 分。分值分布：Q1 10 / Q2 10 / Q3 10 / Q4 20 / Q5 25 / Q6 25。

---

**Q1（单选，10 分）** 用 `TOOL_HANDLERS` 注册表替代 `execute_tool` 里的 if/elif，最关键的收益是？

A. 扩展点从控制流变成数据：`execute_tool` 不用再改，还能遍历注册表做一致性测试、替换单个 handler 构造测试场景
B. 运行速度比 if/elif 快很多
C. 需要写的工具实现变少了

对应能力项：E1、E4

答：

---

**Q2（单选，10 分）** `run_agent(question, llm=call_llm, ...)` 允许注入 `llm`，对测试的意义是？

A. 把“与外部世界交互的边界”变成可替换参数，测试可注入 mock，做到离线、确定、不需要 API Key
B. 能提高真实模型回答的准确率
C. 能少写一层循环

对应能力项：E4、B2

答：

---

**Q3（单选，10 分）** 要断言“最终回答里包含『无法』”，下面哪一行正确？

A. `self.assertIn("无法", last_message["content"])`
B. `self.assertIn(last_message["content"], "无法")`
C. `self.assertEqual("无法", last_message["content"])`

对应能力项：E4

答：

---

**Q4（读代码，20 分）** 重构后的 `execute_tool` 有一段：

```python
tool = TOOL_HANDLERS.get(name)
return tool(args)
```

请回答：

1. （6 分）调用 `execute_tool("no_such_tool", {})` 会发生什么？为什么？
2. （8 分）`test_unknown_tool_raises` 为什么能抓到这个缺陷？说明测试在这里的价值。
3. （6 分）正确的行为应该是什么？用一句话说明改法方向（不用写代码）。

对应能力项：E4、E6

答：

---

**Q5（写测试，25 分）** 在 `tests/test_agent.py` 里补两个测试（可新建测试类），写完贴出代码：

1. （12 分）纯函数测试：`execute_tool("get_current_date", {})` 返回合法日期字符串
   （提示：用 `datetime.date.fromisoformat` 解析），且与 `agent.get_current_date({})` 一致；
2. （13 分）注册表一致性测试：`set(agent.TOOL_HANDLERS)` 与 `{t["function"]["name"] for t in agent.TOOLS}` 相等
   （工具注册表的键 == 给模型看的 schema 名字集合）。

并回答一句：为什么一致性测试对“以后新增工具”特别有价值？

对应能力项：E4、E1

答：

---

**Q6（文档，25 分）** 用自己的话重写 `training/day5-structure-tests/README.md` 的《运行与测试》一节（教练代写版可以不看）：

1. 怎么跑（命令）；
2. 怎么测（命令 + 三个测试分别验证什么）；
3. 结构与职责（至少写清 3 个函数/模块各负责什么）；
4. 为什么这套测试“不联网也能测”。

标准：没看过代码的人照着能跑起来；内容准确、不照抄。

对应能力项：E4、E1

答：

---

> 批注区（教练填写）
