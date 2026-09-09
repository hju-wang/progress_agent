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

## Day 4：LangGraph 对照（待开始）

- [README + 脚手架](day4-langgraph/README.md)：用 LangGraph 对照实现工具循环；
  含 3 个不同知识点的 TODO（节点状态 / 工具节点 / 条件路由）。
