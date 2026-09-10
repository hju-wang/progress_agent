# Day 5：工程化收尾——结构、可测试性、测试

前四天你已经能写出「能跑的 Agent」：工具循环（Day 1）、错误恢复（Day 2）、
RAG 检索工具（Day 3）、LangGraph 对照（Day 4）。今天不学新功能，
而是把“能跑的脚本”往“能被别人接手、能被测试”的方向推一步。

**本 Day 含 3 个不同知识点的 TODO：**

| TODO | 知识点 | 你要写的 |
| --- | --- | --- |
| TODO-1 | Python 惯用法：数据结构替代分支 | 工具注册表 `TOOL_HANDLERS` + 改造 `execute_tool` |
| TODO-2 | 依赖注入与可测试性 | `run_agent` 支持注入 `llm` 并返回 `messages` |
| TODO-3 | 单元测试（stdlib `unittest`） | `tests/test_agent.py` 里两个测试 |

## 现状：先跑一遍

```bash
cd /Users/wangfang/progress_agent/training/day5-structure-tests
python3 agent.py "今天是几号？"
python3 agent.py "上海天气怎么样？"
```

现在就能跑（和 Day 2 行为一致）。测试现状：

```bash
python3 -m unittest discover -s tests -v
```

示例测试 `test_unknown_tool_raises` 通过；两个 `TODO-3` 测试是 red（失败）——
这是你的起点，目标是把它们变绿。

## TODO-1：工具注册表（结构）

`execute_tool` 现在是一串 `if/elif`。要求改成“查表 + 调用”：

1. 建模块级字典 `TOOL_HANDLERS: dict[str, Callable[[dict], str]]`，键是工具名；
2. `execute_tool` 只负责查表、调用、处理未知工具（`ValueError`）；
3. 三个工具行为不变。

自检（应输出三个工具名）：

```bash
python3 -c "import agent; print(sorted(agent.TOOL_HANDLERS))"
# ['get_current_date', 'get_current_time', 'get_weather']
```

想清楚一个问题：以后新增一个工具，用注册表要改几处？用 if/elif 又要改几处？

## TODO-2：依赖注入 + 返回消息（可测试性）

现在 `run_agent` 写死了 `call_llm`，而且只 `print`、不返回，测试没法断言。

1. 签名改成 `run_agent(question, llm=call_llm, max_attempts=4)`；
2. 循环里调用 `llm(...)`；
3. 正常结束时 `return messages`；
4. 命令行行为不变：直接运行仍然只打印，不多输出一行。

为什么这样改就能“离不开网络也能测”？想清楚再往下写测试。

## TODO-3：两个单元测试（测试）

打开 [tests/test_agent.py](tests/test_agent.py)，照示例测试的写法补两个：

1. `test_tool_error_is_fed_back_as_tool_message`：工具报错时，错误必须以
   `role="tool"` 的消息回填，`tool_call_id` 不能丢，内容以 `[工具错误]` 开头，
   最终回答是诚实收尾；
2. `test_date_question_returns_final_answer`：日期问题能走完循环，最后一条是
   带内容的 assistant 消息，且基于工具结果。

提示：用 `agent._mock_llm` 作为注入的 `llm`（离线、确定性）。

## 验证（三个 TODO + README 都完成后）

```bash
cd /Users/wangfang/progress_agent/training/day5-structure-tests
python3 -c "import agent; print(sorted(agent.TOOL_HANDLERS))"
python3 agent.py "今天是几号？"
python3 agent.py "上海天气怎么样？"
python3 -m unittest discover -s tests -v
```

通过标准：

- 注册表包含三个工具，`execute_tool` 不再有 if/elif 分支；
- 两条命令行输出与 Day 2 一致（日期正常、天气走 `[工具错误]` 诚实收场）；
- 三个测试全绿，且不联网、不需要 API Key。

## 交付物 4：补一节 README（文档）

在本 README 末尾自己加一节 `## 运行与测试`，用几行写清：怎么跑、怎么测、
结构是什么（哪个函数负责什么）。标准是“没看过代码的人照着能跑起来”。

## 自检（合上代码答，写在回复里）

1. 用注册表替代 if/elif，除了“少写分支”，对**新增工具**和**测试**分别有什么好处？
2. 为什么测试要注入 `llm`？`run_agent` 返回 `messages` 解决了什么问题？
3. 这两个测试测的是“行为契约”还是“实现细节”？把 `execute_tool` 从 if/elif 换回注册表，
   测试为什么仍然应该通过？

代码 + 测试 + README 通过后，我会按新规则出一张**满分 100**的 Day 5 验收卷。
