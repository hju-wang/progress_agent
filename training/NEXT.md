# NEXT —— 当前进度与下一步

> 每次新对话开始时，先读这个文件，就知道接下来让用户干什么。

> 总地图与阶段说明见 [plans/README.md](../plans/README.md)。

## 当前状态（2026-09-09）

- Day 1（工具调用循环）：✅ 已完成
- Day 2（错误恢复）：✅ 已完成
- Day 3（RAG 检索工具）：✅ 已完成，总结已写入 [day3-rag-tool/README.md](day3-rag-tool/README.md)
- Day 4（LangGraph 对照）：🔄 脚手架已就绪，待完成

## 接下来要做什么

1. 安装依赖并阅读 [day4-langgraph/README.md](day4-langgraph/README.md)：
   `cd training/day4-langgraph && python3 -m venv .venv && .venv/bin/python -m pip install "langgraph>=0.2"`。
2. 用户完成 3 个不同知识点的 TODO：TODO-1 节点返回与状态更新 → TODO-2 工具节点执行与错误回填 → TODO-3 条件路由（继续 / 终止）。
3. 用户作答 [Day 4 验收卷](../assessments/papers/day4-langgraph-验收卷-v0.1.md)（已发放；代码与自检已通过）。
4. 批改 + review 通过后：总结进当天 README → 更新本文件指向 Day 5 → 提交。

> 新规则：每个 Day 含 2–3 个 TODO，每个 TODO 必须对应不同知识点，不允许同知识点重复凑数。

## 遗留提示（诚实记录）

- Day 2 试卷 Q5.2（坏工具限流）为教练提供参考答案，用户**非独立完成**，D5 暂不记为已掌握。
- Day 3 的三道口头复述未在对话中作答（用户选择直接收尾），概念由验收卷覆盖；Day 6 独立检验需抽查“检索工具 role=tool 回填 / 0 命中处理 / 索引升级方向”。
- Day 6 独立检验需复测“同一坏工具重试不超过 2 次”的容错设计。

## 规则提醒

- 辅导模式：给脚手架、提示、review，**不替用户写 TODO 答案**，不夸大真实水平。
- 每个 Day 完成后：总结进当天 README → 更新 `training/README.md` 和本文件 → git 提交。
