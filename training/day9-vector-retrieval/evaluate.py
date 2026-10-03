"""Day 9 对比实验：关键词计数（Day 3 的做法） vs TF-IDF 向量检索。

为什么要这个脚本：W41 的验收要求你「讲清向量检索与关键词检索的差别」。
差别不能靠感觉说，得跑出来看——这也是 Day 10 做小 eval（召回率 / MRR）的预演。

用法（把 rag_vector.py 的三个 TODO 实现完之后）：

    python3 evaluate.py

输出三块：
  1. 每个用例下两种检索的排序和分数；
  2. 汇总指标：命中率 @1 / @k、MRR；
  3. 两条边界用例：一条换述提问（两种检索都难），一条知识库外的问题
     （正确行为是 0 命中，而不是硬凑一条资料）。

**这个实验最重要的一课**：在 6 篇文档的小语料上，两边的差距并不来自
「谁更懂语义」——稀疏词频向量和关键词计数一样，都看不懂同义词。
差距来自两件工程上的事：
  - 打平时怎么办：关键词计数给不出区分度，只能按 id 兜底，于是**长块**容易意外胜出；
  - 长度偏置：余弦把向量长度除掉了，短而主题集中的块不再吃亏。
所以小语料上别急着说"向量更好"，先把用例和指标摆出来看（Day 10 会继续放大这一步）。
"""

from __future__ import annotations

from dataclasses import dataclass

from rag_vector import Chunk, DOCUMENTS, Hit, VectorIndex, tokenize


def keyword_score(question_tokens: list[str], chunk_tokens: list[str]) -> int:
    """Day 3 的原始打分：问句 token 有多少个也出现在资料块里。不归一化、不加权。"""

    score = 0
    for token in question_tokens:
        if token in chunk_tokens:
            score += 1
    return score


def keyword_search(question: str, chunks: list[Chunk], k: int) -> list[tuple[float, Chunk]]:
    """Day 3 式检索：按共同 token 个数降序，同分按 chunk id 升序。"""

    question_tokens = tokenize(question)
    scored = [(keyword_score(question_tokens, chunk.tokens), chunk) for chunk in chunks]
    hits = [item for item in scored if item[0] > 0]
    hits.sort(key=lambda item: (-item[0], item[1].id))
    return hits[:k]


K = 3


@dataclass
class Case:
    question: str
    expected_doc: str
    kind: str = "normal"  # normal | paraphrase | out_of_scope
    note: str = ""


CASES = [
    Case("RAG 的流程是什么？", "doc-2"),
    Case("工具调用时有哪些消息角色？", "doc-1"),
    Case("引用溯源有什么作用？", "doc-4"),
    Case("怎么评测检索效果？", "doc-6"),
    Case(
        "分块太大有什么坏处？",
        "doc-5",
        note="三个块都只共用一个 token（都算 1 分），打平后按 id 兜底 → 最长的 doc-2-1 意外排第一",
    ),
    Case(
        "怎么防止模型胡说八道？",
        "doc-4",
        kind="paraphrase",
        note="资料里写的是“幻觉 / 编造 / 溯源”，问句里一个都没有",
    ),
    Case(
        "怎么申请年假？",
        "",
        kind="out_of_scope",
        note="知识库压根没有这类内容，正确行为是 0 命中",
    ),
]


def as_pairs(hits: list[Hit]) -> list[tuple[float, Hit]]:
    return [(hit.score, hit) for hit in hits]


def format_pairs(pairs: list[tuple[float, object]]) -> str:
    if not pairs:
        return "无命中"
    return " > ".join(f"{obj.id}({score:.3g})" for score, obj in pairs)


def first_rank(pairs: list[tuple[float, object]], expected_doc: str) -> int:
    """标准答案出现在第几位（1 起）；没出现返回 0。"""

    for rank, (_, obj) in enumerate(pairs, start=1):
        if obj.doc_id == expected_doc:
            return rank
    return 0


def summarize(name: str, ranks: list[int]) -> str:
    total = len(ranks)
    hit1 = sum(1 for rank in ranks if rank == 1) / total
    hitk = sum(1 for rank in ranks if rank >= 1) / total
    mrr = sum((1 / rank) if rank else 0 for rank in ranks) / total
    return f"{name}：命中率@1 = {hit1:.0%}，命中率@{K} = {hitk:.0%}，MRR = {mrr:.3f}"


def main() -> None:
    index = VectorIndex.build(DOCUMENTS)
    print(f"资料库：{len(DOCUMENTS)} 篇文档，共 {len(index.chunks)} 个资料块")

    keyword_ranks: list[int] = []
    vector_ranks: list[int] = []

    for number, case in enumerate(CASES, start=1):
        keyword_pairs = keyword_search(case.question, index.chunks, K)
        vector_pairs = as_pairs(index.search(case.question, k=K))

        keyword_rank = first_rank(keyword_pairs, case.expected_doc)
        vector_rank = first_rank(vector_pairs, case.expected_doc)

        if case.kind == "normal":
            keyword_ranks.append(keyword_rank)
            vector_ranks.append(vector_rank)

        target = f"期望 {case.expected_doc}" if case.expected_doc else "期望 0 命中"
        print(f"\n[{number}] {case.question}    （{target}）")
        print(f"    关键词  {format_pairs(keyword_pairs)}")
        print(f"    向量    {format_pairs(vector_pairs)}")
        if case.kind == "normal":
            print(f"    判定    关键词命中@1 {'✓' if keyword_rank == 1 else '✗'}"
                  f" ｜ 向量命中@1 {'✓' if vector_rank == 1 else '✗'}")
        if case.note:
            print(f"    ↳ {case.note}")

    print("\n" + "=" * 60)
    print("汇总（只统计 5 条常规用例）：")
    print("  " + summarize("关键词计数（Day 3）", keyword_ranks))
    print("  " + summarize("TF-IDF 向量（Day 9）", vector_ranks))

    print("\n边界用例说明：")
    print(
        "  · 换述提问：两种检索都靠不住——词不重叠就近似正交，这是稀疏词频向量的软肋，\n"
        "    也正是神经 embedding 要解决的问题；Day 10 的 rerank / 混合检索能缓解一部分。"
    )
    print(
        "  · 知识库外的问题：两边都应该 0 命中。向量的 min_score 阈值让这件事变成\n"
        "    可判定的契约，而不是靠 score > 0 这种巧合——这正是 RAG 防幻觉的第一道闸门。"
    )


if __name__ == "__main__":
    try:
        main()
    except NotImplementedError as error:
        print(f"[报错] {error}")
        print("提示：先把 rag_vector.py 的 TODO-1 / TODO-2 / TODO-3 实现完，再跑这个对比实验。")
