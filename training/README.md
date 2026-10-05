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

## Day 7：周复盘（已完成）

- [README + 复盘数据](day7-weekly-review/README.md)：自评 45.1 / 校正 41.1（基线 15.4），
  逐项批阅出 5 处高报与 2 处低估；结论 A：继续收口阶段 1。

## Day 8：独立检验（⚠️ 辅导下完成，非独立）

- [README + Day 8 记录](day8-independent-check/README.md)：带 3 个缺陷的迷你 Agent 工具循环；
  三处缺陷全部修复、新增 2 个测试、6 例全绿，卷面 **92/100** 通过；
  但**独立完成度 0/10**（期间索要过测试代码、教练给过定位提示）→ 不计入独立证据，
  独立检验顺延 W41 用**全新任务**重做（本题已看参考，不能复用）。
- 评分卡：[Day 8 独立检验评分卡](../assessments/papers/day8-independent-评分卡-v0.1.md)（满分 100，通过线 80）。
- 教练参考（非本人作答）：[REFERENCE-coach-notes-v0.1.md](day8-independent-check/REFERENCE-coach-notes-v0.1.md)。

## Day 9：RAG 进阶 1 · 向量检索（✅ 通过 85/100）

- [README + Day 9 记录](day9-vector-retrieval/README.md)：把 Day 3 的 toy 检索升级成
  TF-IDF 向量 + 余弦相似度（本地索引、零依赖、离线）；3 个 TODO 全部实现、8 测试全绿、
  `evaluate.py` 对比实验达标（向量 100%@1 / MRR 1.000 vs 关键词 80%@1 / 0.900）。
- 复述三题为未完成项：Q1、Q2 各半答，Q3 基本达标 → **A5 维持 1 档**，
  升 2 档以 Day 10（混合检索 / rerank / 引用溯源 / 小 eval）验收为准。
