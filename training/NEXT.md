# NEXT —— 当前进度与下一步

> 每次新对话开始时，先读这个文件，就知道接下来让用户干什么。

## 当前状态（2026-09-08）

- Day 1（工具调用循环）：✅ 已完成，总结已写入 [day1-mini-agent/README.md](day1-mini-agent/README.md)
- Day 2（错误恢复）：🔄 进行中，练习在 [day2-error-recovery/](day2-error-recovery/)

## 接下来要做什么

1. 让用户修改 `training/day2-error-recovery/agent.py` 的 `run_agent`：在调用 `execute_tool` 处加 `try / except`，把异常转成 `"[工具错误] ..."`，仍以 `role="tool"` 喂回模型。
2. 用户运行验证：
   - `python3 training/day2-error-recovery/agent.py "上海天气怎么样？"`（应优雅回答，不再崩）
   - `python3 training/day2-error-recovery/agent.py "今天是几号？"`（Day 1 功能不能坏）
3. 用户回答三个复述题（为什么喂错误给模型 / 会不会无限重试 / 如何限制重试坏工具）。
4. review 通过后：把 Day 2 总结补进 `day2-error-recovery/README.md`，更新本文件指向 Day 3，然后 `git commit`。

## 规则提醒

- 辅导模式：给脚手架、提示、review，**不替用户写 TODO 答案**，不夸大真实水平。
- 每个 Day 完成后：总结进当天 README → 更新 `training/README.md` 和本文件 → git 提交。
