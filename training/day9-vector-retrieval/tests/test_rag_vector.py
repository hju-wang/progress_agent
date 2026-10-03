"""Day 9 验收测试：把 TODO 实现完，这 4 条应该全绿。

现在跑会是红的——它们都在 `NotImplementedError` 上失败，这就是你的验收门。
测试断言的是**行为契约**（权重单调、相似度边界、能命中、0 命中要如实返回空），
不绑定你的实现细节：tf 用原始计数还是 1+log(tf)，都不影响这些断言。

运行：

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import rag_vector  # noqa: E402


class EmbedTests(unittest.TestCase):
    def test_weight_grows_with_term_frequency(self) -> None:
        idf = {"检索": 2.0}
        once = rag_vector.embed(["检索"], idf)
        thrice = rag_vector.embed(["检索", "检索", "检索"], idf)

        self.assertGreater(once["检索"], 0)
        self.assertGreater(thrice["检索"], once["检索"])

    def test_unknown_token_contributes_nothing(self) -> None:
        idf = {"检索": 2.0}
        vector = rag_vector.embed(["这个词资料库里没有"], idf)

        self.assertEqual(sum(vector.values()), 0)

    def test_empty_input_gives_empty_vector(self) -> None:
        self.assertEqual(rag_vector.embed([], {"检索": 2.0}), {})


class CosineTests(unittest.TestCase):
    def test_same_direction_is_one_and_disjoint_is_zero(self) -> None:
        vector = {"检索": 1.5, "资料": 0.8}

        self.assertAlmostEqual(
            rag_vector.cosine_similarity(vector, dict(vector)), 1.0
        )
        self.assertEqual(
            rag_vector.cosine_similarity({"检索": 1.5}, {"天气": 2.0}), 0.0
        )

    def test_empty_vector_is_zero_not_crash(self) -> None:
        self.assertEqual(rag_vector.cosine_similarity({}, {"检索": 1.0}), 0.0)
        self.assertEqual(rag_vector.cosine_similarity({"检索": 1.0}, {}), 0.0)

    def test_similarity_is_symmetric(self) -> None:
        left = {"检索": 1.5, "资料": 0.8}
        right = {"检索": 0.9, "向量": 1.1}

        self.assertAlmostEqual(
            rag_vector.cosine_similarity(left, right),
            rag_vector.cosine_similarity(right, left),
        )


class IndexSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = rag_vector.VectorIndex.build(rag_vector.DOCUMENTS)

    def test_retrieves_expected_document(self) -> None:
        hits = self.index.search("RAG 的流程是什么？", k=2)

        self.assertTrue(hits)
        self.assertEqual(hits[0].doc_id, "doc-2")

    def test_unknown_question_returns_no_hit(self) -> None:
        hits = self.index.search("zzzz", k=2)

        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
