# Day 3：把 RAG 做成“检索工具”接进 Agent

目标：把“检索增强”变成 Agent 的一个普通工具。前面 Day 1/2 你已经会
**提问 → 模型选工具 → 执行 → role=tool 回填 → 基于结果回答**；
今天让其中一把工具变成 `search_knowledge`（本地知识库检索），
并理解“为什么检索结果要先进上下文、模型才能基于资料作答”。

## 先跑一下现状

```bash
cd /Users/wangfang/progress_agent
python3 training/day3-rag-tool/agent.py "RAG 的流程是什么？"
```

会看到 `[工具] search_knowledge(...)` 后跟一行
`[报错] TODO-3 还没实现`——这正是你今天要补的地方。

## 代码结构（先看懂再动手）

`agent.py` 里已经写好了完整的“最小 RAG 骨架”，按顺序读：

1. `DOCUMENTS`：4 篇本地资料（不是从网上抓，是写死的示例知识库）。
2. `tokenize()`：把文本切成可比较的 token（英文按词、中文按相邻二元组）。
3. `split_chunks()`：按句子把长文档切成小块——**分块**。
4. `build_chunks()`：遍历文档，生成小块并预计算 token——这就是本 demo 的简易**索引**。
5. `score_chunk()`：**TODO-3**，给“问题”和“某个资料块”算相关度。
6. `retrieve()`：对每个资料块打分，取最高的 k 个返回——**检索**。
7. `search_knowledge()`：工具执行函数，把命中结果格式化成长文本。
8. 再往下就是 Day 1/2 的循环：`execute_tool` → `build_tool_result` →
   `role="tool"` 回填 → 模型基于资料作答（mock 会带上 `[命中] doc-x` 的来源）。

## 任务（TODO-3）

在 `score_chunk` 里实现打分，只要一两行：

- 输入：问题的 token 列表、某个资料块的 token 列表；
- 输出：一个整数——问题里有多少个 token 也出现在这个资料块里；
- 完全没共同 token 就返回 0，retrieve 就不会返回它。

提示：逐个检查 `question_tokens` 里的 token 在不在 `chunk_tokens` 里，命中就 +1。
代码自己敲，写完后把函数上面那行注释保留或删掉都可以，但 `NotImplementedError`
必须被你的实现替换掉。

## 验证（改完后跑这三段）

```bash
python3 training/day3-rag-tool/agent.py "RAG 的流程是什么？"
python3 training/day3-rag-tool/agent.py "工具调用时有哪些消息角色？"
python3 training/day3-rag-tool/agent.py "今天是几号？"
```

验收标准：

- 前两段不再报 `TODO-3`；能看到 `[工具] search_knowledge(...)` 和
  `[结果]` 里的 `[命中] doc-2-1` / `doc-1-1`（score 大于 0）；
- 最终回答明确基于检索资料，并带来源编号（离线 mock 会把命中的资料原文带回）；
- 第三段仍正常回答日期——Day 1/2 的循环不能改坏。

如果你有 DeepSeek API Key，可以 `export DEEPSEEK_API_KEY=...` 后重跑前两段，
对比真实模型“基于资料作答”的效果。

## 复述（答完代码任务后在对话里回答，合上代码）

1. 检索工具的结果为什么也要 `role="tool"`、带 `tool_call_id` 回填？和其他工具
   （比如 `get_current_date`）有什么不同？
2. 如果知识库里没有答案（检索 0 命中），Agent 应该怎么回答？为什么？
3. 这个 demo 的“索引”是什么？如果换成 1 万篇真实文档，这套打分哪里会崩？

## 验收卷

代码任务通过后作答：[Day 3 验收卷](../../assessments/papers/day3-rag-tool-验收卷-v0.1.md)。
规则：闭卷，允许看自己的代码和运行结果，不许问 AI 要答案。
