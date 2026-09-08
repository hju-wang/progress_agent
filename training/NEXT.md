# NEXT —— 当前进度与下一步

> 每次新对话开始时，先读这个文件，就知道接下来让用户干什么。

> 总地图与阶段说明见 [plans/README.md](../plans/README.md)。

## 当前状态（2026-09-08）

- Day 1（工具调用循环）：✅ 已完成
- Day 2（错误恢复）：✅ 已完成，总结已写入 [day2-error-recovery/README.md](day2-error-recovery/README.md)
- Day 3（RAG 检索工具）：⬜ 待开始（尚无 `training/day3-*` 目录）

## 接下来要做什么

1. 先按 [2026-W37 周计划](../plans/2026-W37-第一周-最小Agent循环.md) 创建 `training/day3-rag-tool/` 脚手架（可运行示例 + TODO + 验证命令 + 验收卷），再让用户开跑。
2. Day 3 目标：把 RAG 做成“检索工具”接进 Agent——复用 Day 1/2 的工具循环，新增检索类工具，让模型在需要资料时调用它。
3. 用户完成任务并运行验证后作答 Day 3 验收卷。
4. 教练批改 + review 通过后：总结进当天 README → 更新本文件指向 Day 4 → `git commit`。

## 遗留提示（诚实记录）

- Day 2 试卷 Q5.2（坏工具限流）为教练提供参考答案，用户**非独立完成**，D5 暂不记为已掌握。
- Day 6 独立检验需复测“同一坏工具重试不超过 2 次”的容错设计，防止该缺口被跳过。

## 规则提醒

- 辅导模式：给脚手架、提示、review，**不替用户写 TODO 答案**，不夸大真实水平。
- 每个 Day 完成后：总结进当天 README → 更新 `training/README.md` 和本文件 → git 提交。
