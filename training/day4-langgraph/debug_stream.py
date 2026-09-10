"""调试辅助：用 stream_mode="updates" 观察每个节点提交的状态更新。

用法（在 training/day4-langgraph 目录下）：

    .venv/bin/python debug_stream.py "今天是几号？"

输出里每一步会显示是哪个节点、往状态里提交了什么。
如果某个节点显示 None，说明它的返回值没有被状态接收（常见原因：键名写错）。
"""

from __future__ import annotations

import sys

from agent import SYSTEM_PROMPT, build_graph


def main() -> None:
    question = sys.argv[1] if len(sys.argv) > 1 else "今天是几号？"
    app = build_graph()
    initial_state = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
    }
    for step, chunk in enumerate(
        app.stream(initial_state, stream_mode="updates"),
        start=1,
    ):
        print(f"--- 第 {step} 步节点更新 ---")
        print(chunk)


if __name__ == "__main__":
    main()
