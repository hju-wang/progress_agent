# Day 8 根因分析 · 教练参考（v0.1）

> **性质声明：本文件是教练参考答案，非学习者本人作答。**
> 用途：给学习者做「范例模仿」的样本 —— 看它的颗粒度、句式、具体程度，然后用自己的话写进 `NOTES.md`。
> 如果直接把本文件内容誊写进 `NOTES.md`，该部分须按仓库规则标记为「参考后重写·非独立作答」
> （与 Day 5 的处理一致），不计入 E1 / E4 / E6 独立证据。

---

## 缺陷 1：熔断边界

- 现象：同一工具连续失败会真正执行 3 次，第 3 次请求没有被拦住，比契约规定的 2 次多跑了一次。
- 根因：判断写成了 `if fails > 2`，等于把契约读成"失败次数**超过** 2 次才熔断"。计数在失败分支里自增，
  所以判断那一刻取到的值是 0、1、2：取到 2 时条件仍为假，于是又多执行了一次。
  契约的原意是"已经失败满 2 次就不要再试"，边界值本身应当是**命中**而不是**超过**。
- 修复：`if fails > 2` 改为 `if fails >= 2`。
- 如何防复发：
  - 阈值提成具名常量 `MAX_CONSECUTIVE_FAILURES = 2`，条件写成 `fails >= MAX_CONSECUTIVE_FAILURES`，
    让"2"只出现一次、含义写在名字里。散落在条件里的字面量数字是差一错误的高发区。
  - **边界两侧各留一条用例**：恰好失败 2 次 → 下一次请求必须熔断；只失败 1 次 → 下一次仍必须真正执行。
    只测一侧的话，`>` 和 `>=` 都能让测试变绿，这正是本缺陷能溜过去的原因。
  - 代码评审清单加一条：条件表达式里出现字面量边界值时，要求能指出"另一侧"由哪条用例覆盖。

## 缺陷 2：成功未清零

- 现象：失败 → 成功 → 失败 → 失败，第 4 次仍然被熔断；但中间已经成功过一次，这两次失败不构成"连续失败"。
- 根因：成功路径上写的是 `fail_counts[name] = fail_counts.get(name, 0) + 1`，把成功也当失败在累加。
  计数字段只有一个变量、却被成功和失败两条分支各自维护，成功分支漏了归零，于是"连续失败"退化成"累计失败"。
- 修复：成功路径改为 `fail_counts[name] = 0`。
- 如何防复发：
  - **把更新收敛到唯一出口**：`try` 里只放"执行"这一个动作，执行完之后在 `try/except` 之外按结果统一更新计数
    （成功置 0、失败加 1）。两个分支共用一处赋值，结构上就不存在"只改了一边"的可能。
  - 或者把计数封装成一个小类型（例如 `ConsecutiveFailures`，对外只暴露 `record_success()` / `record_failure()`），
    调用方拿不到裸字典，也就没机会只更新一边。
  - 用**状态序列**用例锁住语义：失败 → 成功 → 失败 → 失败，断言 4 次全部真正执行。
    单点用例只能验证一个瞬间，序列用例才能抓住状态机里的错误迁移。

## 缺陷 3：注册表共享内部字典

- 现象：新建的第二个 `ToolRegistry` 能看到第一个实例注册过的工具；往 A 注册会污染 B，
  A 的工具表里出现了只在 B 注册过的 `get_weather`。
- 根因：`__init__` 的默认参数 `tools: dict[...] = {}` 是可变对象，Python 只在**函数定义时**求值一次，
  因此所有未传参的实例共用同一个字典对象；`self._tools = tools` 又直接引用了它，
  `register()` 写进去的就是这一份共享数据。
- 修复：`self._tools = dict(tools) if tools is not None else {}`，保证每个实例持有自己的字典。
- 如何防复发：
  - **从签名上消灭这类默认值**：默认写成 `tools: dict[...] | None = None`，函数体里再创建空字典。
    这样"共享默认值"根本没有存在机会，比依赖"记得拷贝"可靠 —— 拷贝只是绕着坑走，改签名是把坑填掉。
  - 用测试锁住契约：两个实例各注册一个工具，断言互相看不到。**必须配正向断言**
    （各自确实拥有自己那个工具），否则实现坏到 `names()` 返回空列表时，负向断言依然会全绿。
  - 引入静态检查：ruff 的 flake8-bugbear 中 `B006` 正是拦截"可变默认参数"的规则
    （本仓库目前尚未配置 ruff，属于后续可加的工具链机制）。
  - 评审清单加一条：函数默认值出现 `[]`、`{}`、`set()` 时，一律要求改写为 `None` + 函数体内初始化。

## 测试设计说明（新增用例为什么能暴露问题）

- **断言落在对外可见的行为上**：断言对象是 `names()` 返回的工具列表，而不是实例内部的 `_tools` 字段。
  所以实现将来换数据结构、改属性名、重构内部逻辑，都不影响这条用例的有效性 —— 它测的是契约，不是抄了一遍实现。
- **同一份用例验证了两个状态**：修复前它是红的
  （`AssertionError: 'get_weather' unexpectedly found in ['get_today', 'get_weather']`），修复后变绿。
  "只在坏代码上红、只在好代码上绿"才构成它测的是行为契约的证据。
- **最小场景**：两个空注册表、各注册一个工具、只断言"我看不到你的、你看不到我的"，
  没有牵扯 `run_agent` 和假模型。失败时指向明确，不掺无关变量。

---

## 附：边界测试的一条参考写法（熔断阈值下侧）

> 同样是教练参考。用途是让你看到"边界另一侧"的用例长什么样，
> 建议先自己按这个形状写一遍再看答案对照。

```python
class CircuitBreakerBoundaryTests(unittest.TestCase):
    def test_single_failure_does_not_trip_the_breaker(self) -> None:
        registry = app.build_registry()
        executed: list[str] = []
        outcomes: list = [RuntimeError("第一次失败"), "晴，25℃"]

        def flaky_execute(name: str, args: dict) -> str:
            executed.append(name)
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        llm = make_scripted_llm(weather_script(2, "根据结果回答：晴，25℃"))
        with mock.patch.object(registry, "execute", side_effect=flaky_execute):
            messages = app.run_agent("上海天气怎么样？", llm, registry)

        # 只失败 1 次 → 不该熔断，第 2 次请求必须真正执行
        self.assertEqual(executed, ["get_weather", "get_weather"])

        tool_messages = [m for m in messages if m["role"] == "tool"]
        self.assertFalse(
            any("放弃重试" in str(m["content"]) for m in tool_messages)
        )
```

这条用例覆盖的是现有测试没有覆盖的一侧：现有用例验证"满 2 次要熔断"，
它验证"只失败 1 次不许熔断"。两条合起来才把阈值钉死。
