# progress-agent CLI（M1：自测 → 水平报告）

第一个可运行版本：基于能力模型逐项自评（0–4 档），输出结构化水平报告（JSON + Markdown）。

## 运行方式（无需安装依赖，纯标准库）

```bash
cd app
PYTHONPATH=src python3 -m progress_agent assess
```

也可以从答案文件直接跑（方便脚本/测试）：

```bash
PYTHONPATH=src python3 -m progress_agent assess --answers answers.json
```

答案文件示例结构：

```json
{ "A1": 2, "A2": 1, "B1": 0 }
```

报告默认写到仓库根目录 `data/reports/`，可用 `--output-dir` 指定。

## 差距分析（M2）

```bash
PYTHONPATH=src python3 -m progress_agent gap \
  --assessment ../data/reports/self-assessment-YYYYmmdd-HHMMSS.json
```

会基于已入库 JD 的岗位画像权重（`jd_library/profiles/market-weights.v0.1.json`）
输出“岗位准备度 + 按紧急度排序的待补清单”。

## 诚实声明

这是 **自评基线**，不是真实能力检测。得分 ≥3 的能力项会被标记为“疑似已掌握”，
必须经过后续“限时、少 AI 辅助的独立任务”验证后才会被采信（M4 实现）。

## 开发

```bash
cd app
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
