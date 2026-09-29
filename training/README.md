# 手把手训练目录

模式：**系统给可运行示例 → 每个 Day 含 2–3 个 TODO → 各自验收 → 解释 → 独立复述**。
纪律：示例代码可以由 AI/系统生成；每个 TODO 对应**不同知识点**（例如状态定义、
节点实现、条件路由、测试），不能同一知识点重复凑数；所有 TODO 验收通过才算 Day 完成。

## Day 0：环境与第一次运行

- [hello.py](day0/hello.py)：第一段 Python 程序。

## Day 1：工具调用循环（已通过）

- [mini-agent + Day 1 总结](day1-mini-agent/README.md)：用户提问 → 工具调用 → 结果回填 → 最终回答。

## Day 2：错误恢复（已通过）

- [README + Day 2 总结](day2-error-recovery/README.md)：工具报错时 Agent 不崩、会自救。

## Day 3：RAG 检索工具（已通过）

- [README + Day 3 总结](day3-rag-tool/README.md)：把 RAG 做成“检索工具”接进 Agent。

## Day 4：LangGraph 对照（已通过）

- [README + Day 4 总结](day4-langgraph/README.md)：用 LangGraph 对照实现工具循环；
  含 3 个不同知识点的 TODO（节点状态 / 工具节点 / 条件路由），验收卷 91/100。
- [debug_stream.py](day4-langgraph/debug_stream.py)：用 `stream_mode="updates"` 观察每步状态更新。

## Day 5：工程化收尾（✅ 补考通过 81/100）

- [README + Day 5 总结](day5-structure-tests/README.md)：首考 64/100，补考（Q4 三问 + Q5.1 补强）后 81/100 通过；
  Q4 为参考后重写、Q6 部分教练代填，独立程度以 Day 6 检验为准。

## Day 6：独立检验（⚠️ 记为练习日，非独立）

- [README + Day 6 记录](day6-independent/README.md)：坏工具“连续失败 ≤2 次”限流——功能由用户完成，
  两个测试与设计说明由教练代写（B 方案）；7 个测试全绿，按评分卡等价 90/100 但**独立完成度 0**，
  独立检验顺延到下一周用新任务重做。
