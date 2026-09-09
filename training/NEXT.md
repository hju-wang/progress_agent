# NEXT —— 当前进度与下一步

> 每次新对话开始时，先读这个文件，就知道接下来让用户干什么。

> 总地图与阶段说明见 [plans/README.md](../plans/README.md)。

## 当前状态（2026-09-09）

- Day 1（工具调用循环）：✅ 已完成
- Day 2（错误恢复）：✅ 已完成，总结已写入 [day2-error-recovery/README.md](day2-error-recovery/README.md)
- Day 3（RAG 检索工具）：🔄 进行中，练习在 [day3-rag-tool/](day3-rag-tool/)

## 接下来要做什么

1. 让用户实现 `training/day3-rag-tool/agent.py` 里 `score_chunk`（TODO-3）：
   统计问题 token 与资料块 token 的共同数量，无共同 token 返回 0。
2. 用户运行验证：
   - `python3 training/day3-rag-tool/agent.py "RAG 的流程是什么？"`（应命中 `doc-2-1` 并基于资料作答）
   - `python3 training/day3-rag-tool/agent.py "工具调用时有哪些消息角色？"`（应命中 `doc-1-1`）
   - `python3 training/day3-rag-tool/agent.py "今天是几号？"`（Day 1/2 功能不坏）
3. 用户口头复述三问（检索结果为何 role=tool 回填 / 0 命中怎么办 / 玩具索引在大规模下哪里崩）。
4. 用户作答 [Day 3 验收卷](../assessments/papers/day3-rag-tool-验收卷-v0.1.md)。
5. 教练批改 + review 通过后：总结进 `day3-rag-tool/README.md` → 更新本文件指向 Day 4 → `git commit`。

## 遗留提示（诚实记录）

- Day 2 试卷 Q5.2（坏工具限流）为教练提供参考答案，用户**非独立完成**，D5 暂不记为已掌握。
- Day 6 独立检验需复测“同一坏工具重试不超过 2 次”的容错设计，防止该缺口被跳过。

## 规则提醒

- 辅导模式：给脚手架、提示、review，**不替用户写 TODO 答案**，不夸大真实水平。
- 每个 Day 完成后：总结进当天 README → 更新 `training/README.md` 和本文件 → git 提交。
