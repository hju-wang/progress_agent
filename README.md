# ProgressAgent

一个由目标岗位 JD 驱动、以真实检测为依据、能够**自我演进**的个人求职能力成长系统。平时系统自动研究市场带你巡航训练；收到你发来的意向 JD 后进入攻坚模式，达标面试准入线才建议投递。技术栈以 Python / Agent 生态为主。

## 当前进度（M0）

- 产品设计：[求职Agent_MVP设计文档](docs/求职Agent_MVP设计文档.md)
- 能力模型 v0.1（草稿）：[abilities/agent-app-developer.v0.1.json](abilities/agent-app-developer.v0.1.json)
- 已入库 JD（4 份，猎聘/前程无忧来源）：[jd_library/approved](jd_library/approved/)
- 岗位画像 v0.1：[jd_library/profiles/岗位画像-Agent应用开发-v0.1.md](jd_library/profiles/岗位画像-Agent应用开发-v0.1.md)
- 自测 CLI（M1）：`cd app && PYTHONPATH=src python3 -m progress_agent assess`

## 里程碑

- [x] M0：设计文档 + 能力模型 v0.1 + JD 种子库 + 岗位画像
- [x] M1：本地自测 CLI（问卷 → 结构化水平报告）
- [x] M2（基准部分）：JD 采集（猎聘/前程无忧）+ 岗位画像 + 基准差距报告
- [ ] M3：按岗位画像 / 用户 JD 出 mock 面试题并打分

## 训练计划

- [第 1 周：手写最小 Agent 循环（2026-09-08 起）](plans/2026-W37-第一周-最小Agent循环.md)

设计文档：[求职Agent_MVP设计文档](docs/求职Agent_MVP设计文档.md)

原始想法：[想法.md](想法.md)
