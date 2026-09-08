# Day 1：工具调用循环（mini-agent）

这是一个最小的 Agent 骨架：用户提问 → 模型决定调用工具 → 系统执行工具 → 结果回填 → 模型给出最终回答。

## 你的任务

### TODO-1（改错）

打开 [agent.py](agent.py)，找到 `build_tool_result` 函数。里面有一处 **role 故意写错了**，导致程序运行报错。

运行看看：

```bash
cd /Users/wangfang/progress_agent
python3 training/day1-mini-agent/agent.py
```

读报错信息 → 改成正确值 → 再运行，直到它成功回答“现在几点了”。

> 规则：TODO-1 不许问 AI 答案，可以查 OpenAI/DeepSeek function calling 文档。

### TODO-2（加一个新工具）

运行成功后，给 Agent 增加一个 `get_current_date` 工具，要求：

1. 在 `TOOLS` 里补上 schema；
2. 在 `execute_tool` 里补上执行分支；
3. 让程序能回答“今天是几号”。

这个允许参考现有 `get_current_time` 的写法，但**代码要自己敲**。

## 复述（看完后合上代码回答，写在回复里即可）

1. 这个循环里，消息有哪几种 `role`？工具执行结果为什么必须用 `role="tool"`？
2. 如果模型一直要求调用工具，程序靠什么停下来？为什么这个机制必须有？
3. 模型返回 `tool_calls` 之后，程序做了哪几步才把结果“喂”回给模型？

## 运行模式

- 默认是 **离线 mock 模式**：不联网、不需要 API Key，适合学循环逻辑。
- 如果你有 DeepSeek API Key，运行前 `export DEEPSEEK_API_KEY=你的key`，同一份代码会直接调用真实模型（可自行对比差异）。
