# NEXT —— 当前进度与下一步

> 每次新对话开始时，先读这个文件，就知道接下来让用户干什么。

> 总地图与阶段说明见 [plans/README.md](../plans/README.md)。

## 当前状态（2026-09-10）

- Day 1（工具调用循环）：✅ 已完成
- Day 2（错误恢复）：✅ 已完成
- Day 3（RAG 检索工具）：✅ 已完成
- Day 4（LangGraph 对照）：✅ 已完成（验收卷 91/100）
- Day 5（工程化收尾）：🔄 进行中，练习在 [day5-structure-tests/](day5-structure-tests/)

## 接下来要做什么

1. 用户完成 [day5-structure-tests/README.md](day5-structure-tests/README.md) 的 3 个 TODO：
   - TODO-1（结构）：`TOOL_HANDLERS` 注册表 + 改造 `execute_tool`，不再用 if/elif；
   - TODO-2（可测试性）：`run_agent(question, llm=call_llm, ...)` 注入 llm 并 `return messages`；
   - TODO-3（测试）：补 `tests/test_agent.py` 两个用例（错误回填契约、日期问答）。
2. 交付物 4：在当天 README 末尾补一节《运行与测试》。
3. 用户运行验证（注册表打印三个工具名；两条命令行行为不变；`python3 -m unittest discover -s tests -v` 三个测试全绿）。
4. 教练出 **满分 100 分**的 Day 5 验收卷（题面标注每题分值），批改输出逐题得分 + 总分。
5. 通过后：总结进当天 README → 更新本文件指向 Day 6 → `git commit`。

## 评分规则（2026-09-10 起）

- 每张试卷满分 100，题面标注每题分值；客观题对错二元，主观题按要点给分；通过线 80。
- 每次批改输出：逐题得分 + 总分 + 是否通过 + 失分点；教练参考/代写内容必须标注为非独立作答。
- 详见 [assessments/README.md](../assessments/README.md)。

## 遗留提示（诚实记录）

- Day 2 Q5.2（坏工具限流）为教练参考答案，非独立完成，D5 未记为掌握。
- Day 3 三道口头复述未作答，概念由验收卷覆盖。
- Day 4 得分 91/100；Q4.2、Q4.3 与 Q5 框架边界为教练参考后誊写，Q5 对照表 15/20。
- Day 6 独立检验需复测：坏工具限流设计、RAG 工具 role=tool 回填与 0 命中处理、LangGraph 状态契约与条件边。

## 规则提醒

- 辅导模式：给脚手架、提示、review，**不替用户写 TODO 答案**，不夸大真实水平。
- 每个 Day 完成后：总结进当天 README → 更新 `training/README.md` 和本文件 → git 提交。
