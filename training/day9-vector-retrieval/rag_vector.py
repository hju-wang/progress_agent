"""Day 9：把 Day 3 的玩具检索升级成「向量检索」（本地索引 · 纯标准库 · 离线可跑）。

Day 3 的打分是「问题 token 与资料块 token 的**共同个数**」，有两个已知毛病：

  1. 没有归一化：资料块越长，越容易靠撞上常见词堆出高分；
  2. 所有 token 等权：「的」「如何」这种哪都有的词，和真正的关键词同权。

今天换成向量空间的做法（这也是所有向量库的最小骨架）：

    分块 → 每个块编码成向量 → 查询也编码成向量 → 算余弦相似度 → 取 top-k

**诚实说明（不要夸大）**：这里的向量是**稀疏词频向量（TF-IDF）**，
不是神经网络 embedding。两者共享同一套工程骨架
（编码器 → 向量 → 索引 → 相似度 → top-k），差别只在编码器：
神经 embedding 能把同义词、换述映射到相近的位置；稀疏 TF-IDF 做不到——
词不重叠就近似正交。`evaluate.py` 里专门有一条「换述提问」用例，
就是让你亲眼看到这条能力边界。

运行：

    python3 rag_vector.py "RAG 的流程是什么？"
    python3 rag_vector.py "分块太大有什么问题？" --explain
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# 1) 本地资料库：沿用 Day 3 的四篇，另加两篇用来考验排序区分度
# ---------------------------------------------------------------------------

DOCUMENTS = [
    {
        "id": "doc-1",
        "title": "工具调用与消息角色",
        "content": (
            "工具调用（function calling）过程中有四种消息角色：system 描述系统设定，"
            "user 是用户提问，assistant 携带模型回复或工具调用请求，tool 是工具执行结果。"
            "assistant 请求调用工具后，应用必须把每条结果以 role=tool、并带对应 "
            "tool_call_id 的消息回填给模型，模型才能基于结果继续回答。"
        ),
    },
    {
        "id": "doc-2",
        "title": "RAG 检索增强的流程",
        "content": (
            "RAG（检索增强生成）分三步：先对文档分块并建立检索索引；"
            "再根据用户问题检索最相关的资料块；最后把检索到的资料放入上下文，"
            "让模型基于资料作答并标注来源，从而减少幻觉。"
        ),
    },
    {
        "id": "doc-3",
        "title": "工具出错时的恢复",
        "content": (
            "真实世界的第三方工具或 API 一定会失败。Agent 的做法不是让进程崩溃，"
            "而是捕获异常、把错误转成一条普通工具结果喂回模型，让模型诚实告诉用户稍后再试。"
            "为了防止坏工具被反复调用，还要限制同一工具的失败重试次数。"
        ),
    },
    {
        "id": "doc-4",
        "title": "引用溯源",
        "content": (
            "引用溯源要求模型回答时指出依据的资料编号或来源，例如 doc-2-1。"
            "这样用户能核对答案是否真的来自检索结果，也是排查幻觉的重要手段："
            "如果模型答不出或资料不足，应承认不知道，而不是编造。"
        ),
    },
    {
        "id": "doc-5",
        "title": "分块策略与索引更新",
        "content": (
            "分块决定检索质量的上限。块切得太大，一个块里混着好几个主题，"
            "命中的位置不精确、喂给模型的噪声也多；块切得太小，上下文被切碎，"
            "模型拿到的信息不完整。常见做法是按段落、小标题这类语义边界切分，"
            "并让相邻块保留少量重叠，避免答案刚好被切在边界上。"
            "文档更新之后，索引还要能增量重建，而不是每次全量重算。"
        ),
    },
    {
        "id": "doc-6",
        "title": "检索质量的评测指标",
        "content": (
            "没有评测就无法判断检索有没有变好。常用指标：命中率看 top-k 里有没有正确答案；"
            "召回率看应该被找到的资料有多少真的被找到；MRR 看第一个正确结果排在第几位，"
            "越接近 1 越好。做法是先准备一小份带标准答案的问题集，"
            "改完检索逻辑就重跑一遍对比，而不是凭感觉说好像准了。"
        ),
    },
]


# ---------------------------------------------------------------------------
# 2) 文本处理：切词、分块（与 Day 3 保持一致，便于对比）
# ---------------------------------------------------------------------------

_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    """切词：英文/数字按词，中文按相邻二元组（沿用 Day 3）。"""

    text = text.lower()
    tokens: list[str] = re.findall(r"[a-z0-9]+", text)
    for run in _CJK_RE.findall(text):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i : i + 2] for i in range(len(run) - 1))
    return tokens


def split_chunks(text: str, max_chars: int = 70) -> list[str]:
    """按句子把文档切成小块，相邻句子尽量合并到接近 max_chars（沿用 Day 3）。"""

    sentences = re.split(r"(?<=[。！？])", text.strip())
    chunks: list[str] = []
    buffer = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(buffer) + len(sentence) <= max_chars:
            buffer += sentence
        else:
            if buffer:
                chunks.append(buffer)
            buffer = sentence
    if buffer:
        chunks.append(buffer)
    return chunks


@dataclass
class Chunk:
    """一个资料块：文本 + 它的 token + 它的向量（向量在建索引时填）。"""

    id: str
    doc_id: str
    title: str
    text: str
    tokens: list[str]
    vector: dict[str, float] = field(default_factory=dict)


@dataclass
class Hit:
    """一条检索结果。"""

    id: str
    doc_id: str
    title: str
    text: str
    score: float


# ---------------------------------------------------------------------------
# 3) 向量化与相似度：今天的两块新积木
# ---------------------------------------------------------------------------


def compute_idf(chunks: list[Chunk]) -> dict[str, float]:
    """算每个 token 的 idf（逆文档频率）：越常见的词越接近 0，越稀有的词越大。

    公式用平滑版本 `ln((N+1)/(df+1)) + 1`：N 是块总数，df 是"包含该 token 的块数"。
    加 1 是为了让权重永远为正——否则一个词出现在每个块里时会得到 0，
    连同它的微小信息一起被抹掉。

    这个函数已经写好，不用改。注意它只覆盖"资料库里出现过的 token"：
    查询里出现但它们没见过的词，查不到 idf，也就不参与打分。
    """

    total = len(chunks)
    df: dict[str, int] = {}
    for chunk in chunks:
        for token in set(chunk.tokens):
            df[token] = df.get(token, 0) + 1
    return {
        token: math.log((total + 1) / (count + 1)) + 1
        for token, count in df.items()
    }


def embed(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    """把 token 列表编码成稀疏 TF-IDF 向量：``{token: 权重}``。

    TODO-1（向量化）—— 你来写：

      1. 统计每个 token 在这段文本里出现了几次，记为 tf；
      2. 该 token 的权重 = tf × idf[token]（idf 里查不到的 token 直接跳过，
         因为它对任何向量都是 0 贡献）；
      3. 返回 ``{token: 权重}``；输入为空时返回 ``{}``。

    想一想：这里为什么**不**做归一化？（提示：归一化是 TODO-2 里分母的活，
    职责分开，将来用未归一化的向量调用余弦函数也不会算错。）
    """

    raise NotImplementedError("TODO-1 还没实现：embed() 现在编码不出向量")


def cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """两个稀疏向量的余弦相似度：``点积 / (|a| × |b|)``。

    TODO-2（相似度）—— 你来写：

      1. 分子 = 两个向量**共有** token 的权重乘积之和（点积）；
      2. 分母 = 两个向量各自的 L2 范数（``sqrt(权重平方和)``）相乘；
      3. 任一向量为空、或范数为 0 时返回 ``0.0``（避免除零）。

    权重非负时结果落在 0.0 ~ 1.0：完全一样的方向是 1.0，没有任何共同 token 是 0.0。
    提示：遍历两个字典里较短的那个来算点积，比遍历全部更省。
    """

    raise NotImplementedError("TODO-2 还没实现：cosine_similarity() 还算不出分数")


@dataclass
class VectorIndex:
    """向量索引：持有 idf 表与每个块的向量，负责回答「给我最相关的 k 个块」。"""

    chunks: list[Chunk]
    idf: dict[str, float]

    @classmethod
    def build(cls, documents: list[dict]) -> "VectorIndex":
        """建索引：分块 → 算 idf → 给每个块编码向量。"""

        chunks: list[Chunk] = []
        for doc in documents:
            for idx, text in enumerate(split_chunks(doc["content"]), start=1):
                chunks.append(
                    Chunk(
                        id=f"{doc['id']}-{idx}",
                        doc_id=doc["id"],
                        title=doc["title"],
                        text=text,
                        tokens=tokenize(text),
                    )
                )

        index = cls(chunks=chunks, idf=compute_idf(chunks))
        for chunk in index.chunks:
            chunk.vector = embed(chunk.tokens, index.idf)
        return index

    def search(
        self, question: str, k: int = 2, min_score: float = 0.05
    ) -> list[Hit]:
        """检索与 question 最相关的 k 个块。

        TODO-3（检索与 0 命中）—— 你来写：

          1. 用 ``self.idf`` 把 question 编码成查询向量；
          2. 与每个块的 ``vector`` 算余弦相似度；
          3. 按分数**降序**排序；同分时按 chunk id 升序，保证结果稳定可复现；
          4. 丢掉分数低于 ``min_score`` 的结果，再取前 k 个；
          5. 一个都不剩就返回**空列表**——这就是「0 命中」，
             调用方要据此如实告诉用户"知识库里没有相关内容"，而不是硬凑一条。

        ``min_score`` 是门槛：没有它，任何问题都能撞到一条低分资料，
        RAG 的防幻觉就失效了。
        """

        raise NotImplementedError("TODO-3 还没实现：search() 现在检索不出结果")


# ---------------------------------------------------------------------------
# 4) 检索工具：把命中结果格式化成长文本，供模型阅读
# ---------------------------------------------------------------------------


def search_knowledge(question: str, index: VectorIndex) -> str:
    """检索工具的执行函数：命中就带编号/标题/原文，0 命中就如实说没找到。"""

    hits = index.search(question)
    if not hits:
        return "[检索] 未命中任何资料：知识库里没有与问题匹配的内容。"
    lines = []
    for hit in hits:
        lines.append(
            f"[命中] {hit.id}（score={hit.score:.3f}）《{hit.title}》\n{hit.text}"
        )
    return "\n".join(lines)


def explain(question: str, index: VectorIndex, top_n: int = 6) -> str:
    """调试卷用：打印查询向量里权重最高的 token，帮你看清 idf 在干什么。"""

    query_vector = embed(tokenize(question), index.idf)
    if not query_vector:
        return "[解释] 查询编码后是空向量：问题里的词在资料库里一个都没出现过。"
    ranked = sorted(query_vector.items(), key=lambda item: (-item[1], item[0]))
    shown = "、".join(f"{token}({weight:.2f})" for token, weight in ranked[:top_n])
    return f"[解释] 查询向量权重最高的 {top_n} 个 token：{shown}"


if __name__ == "__main__":
    arguments = [arg for arg in sys.argv[1:] if arg != "--explain"]
    show_explain = "--explain" in sys.argv
    question = arguments[0] if arguments else "RAG 的流程是什么？"

    try:
        knowledge_index = VectorIndex.build(DOCUMENTS)
        print(f"[问题] {question}")
        print(search_knowledge(question, knowledge_index))
        if show_explain:
            print(explain(question, knowledge_index))
    except NotImplementedError as error:
        print(f"[报错] {error}")
        print("提示：打开 rag_vector.py，按 TODO-1 → TODO-2 → TODO-3 的顺序实现后再运行。")
