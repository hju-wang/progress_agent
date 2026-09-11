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

答：A

---

**Q2（单选，10 分）** `run_agent(question, llm=call_llm, ...)` 允许注入 `llm`，对测试的意义是？

A. 把“与外部世界交互的边界”变成可替换参数，测试可注入 mock，做到离线、确定、不需要 API Key
B. 能提高真实模型回答的准确率
C. 能少写一层循环

对应能力项：E4、B2

答：A

---

**Q3（单选，10 分）** 要断言“最终回答里包含『无法』”，下面哪一行正确？

A. `self.assertIn("无法", last_message["content"])`
B. `self.assertIn(last_message["content"], "无法")`
C. `self.assertEqual("无法", last_message["content"])`

对应能力项：E4

答：A

---

**Q4（读代码，20 分）** 重构后的 `execute_tool` 有一段：

```python
tool = TOOL_HANDLERS.get(name)
return tool(args)
```

请回答：

1. （6 分）调用 `execute_tool("no_such_tool", {})` 会发生什么？为什么？
   答：会抛出异常 TypeError: 'NoneType' object is not callable
   因为 TOOL_HANDLERS.get(name)查不到对应的key 值的时候会返回None,所以tool就变成了None，None 是不可被调用的
2. （8 分）`test_unknown_tool_raises` 为什么能抓到这个缺陷？说明测试在这里的价值。
   答：传进去一个为定义的工具名就会
3. （6 分）正确的行为应该是什么？用一句话说明改法方向（不用写代码）。
   答：这个我不太懂是什么意思
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

```python
class PracticeTests(unittest.TestCase):
    #Q5 题目1 纯函数测试
    def test_exce_tool(self)-> None:
        tool_result =agent.execute_tool("get_current_date",{})
        date =agent.get_current_date()
        self.assertEqual(tool_result,date)

    #Q5 题目2 注册表一致性测试
    def test_reg(self):
        # 使用两种方式取key
        handler_set = set(agent.TOOL_HANDLERS)
        handler_exp = { t["function"]["name"] for t in agent.TOOLS}
        self.assertEqual(handler_exp,handler_set)
```


因为 agent.TOOLS 是发送给LLM的，而注册表中是真正要执行的，要保证LLM返回tool_call 的时候，其中的函数名，真正的在注册表中存在

---

**Q6（文档，25 分）** 用自己的话重写 `training/day5-structure-tests/README.md` 的《运行与测试》一节（教练代写版可以不看）：

1. 怎么跑（命令）；
2. 怎么测（命令 + 三个测试分别验证什么）；
3. 结构与职责（至少写清 3 个函数/模块各负责什么）；
4. 为什么这套测试“不联网也能测”。

标准：没看过代码的人照着能跑起来；内容准确、不照抄。

对应能力项：E4、E1

答：
1:
```shell
cd /Users/wangfang/progress_agent/training/day5-structure-tests
python3 agent.py "今天是几号？"
python3 agent.py "上海天气怎么样？"
```
2:`python3 -m unittest discover -s tests -v`

---

> 批注区（教练填写）

**教练批改 v1（2026-09-11）**

| 题 | 分值 | 得分 | 说明 |
| --- | --- | --- | --- |
| Q1 | 10 | 10 | 正确：扩展点变数据、可遍历/可替换。 |
| Q2 | 10 | 10 | 正确：注入 mock 得到离线确定性。 |
| Q3 | 10 | 10 | 正确：`assertIn(member, container)`。 |
| Q4.1 | 6 | 2 | 只说“抛异常”，没点名是 `TypeError: 'NoneType' object is not callable`，也没说清 `dict.get` 查不到返回 `None`。 |
| Q4.2 | 8 | 1 | 没答出“测试把契约固化为可执行断言、能立刻发现重构回归”。 |
| Q4.3 | 6 | 0 | 未作答。 |
| Q5.1 | 12 | 10 | 测试可跑通过；但没用 `datetime.date.fromisoformat` 独立校验日期格式，且两次调用同一函数比较存在跨零点风险。 |
| Q5.2 | 13 | 13 | 集合一致性断言正确；一致性测试价值的解释正确。 |
| Q6 | 25 | 8 | 只写了怎么跑、怎么测；缺“三个测试各验证什么、结构与职责、为什么能离线测”。 |

**总分：64 / 100 → 未通过（通过线 80）**

需重做（可只做失分题）：
1. Q4 三个小问（现象/根因、测试价值、正确行为与改法方向）；
2. Q5.1 补日期格式的独立校验；
3. Q6 补齐第 2/3/4 部分（三个测试各验证什么、结构与职责、离线原因）。

诚实记录：Q5 测试为用户独立编写；本卷 Q1–Q3 独立完成，Q1–Q3 满分。
