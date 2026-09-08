# Day 2：工具报错时，Agent 要会自救

场景：真实世界里第三方工具/API 一定会失败。一个生产级 Agent 不能让一次工具报错把整个进程打崩。

## 先看现状

```bash
cd /Users/wangfang/progress_agent
python3 training/day2-error-recovery/agent.py "上海天气怎么样？"
```

会看到一个 `RuntimeError` 堆栈——`get_weather` 模拟了不稳定的第三方服务，固定抛错。

## 任务（TODO-2）

修改 `run_agent` 里**调用 `execute_tool` 的那一段**，目标：

1. 工具执行**抛异常时，程序不能崩**；
2. 把异常转成字符串结果：`"[工具错误] 天气服务暂时不可用（city=上海）"`；
3. 这个错误结果仍然要以 `role="tool"` 的消息喂回给模型（`tool_call_id` 不能丢）；
4. 让模型基于错误给出“我无法获取天气信息，请稍后再试”这类诚实回答。

提示方向：Python 的 `try / except`。可以查资料，但代码自己写。

> 验证：改完后问“上海天气怎么样？”不再报堆栈，而是看到 `[工具错误]` 和一句诚实的最终回答；同时问“今天是几号？”仍正常工作（不要改坏 Day 1 的功能）。

## 验收卷（做完代码任务后作答）

不是问“会不会”，是具体题目：[Day 2 错误恢复 · 验收卷](../../assessments/papers/day2-error-recovery-验收卷-v0.1.md)

规则：闭卷作答，允许看自己的代码和运行结果，不许问 AI 要答案。
