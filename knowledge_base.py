"""
knowledge_base.py
------------------
Same TF-IDF retriever from the earlier RAG project — reused here so the
agent's "search_facts" tool has something real to search.
"""

import re
import math
from collections import Counter
from pathlib import Path


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
    return chunks


class KnowledgeBase:
    def __init__(self, docs_dir: str):
        self.docs_dir = Path(docs_dir)
        self.chunks: list[dict] = []
        self._doc_freq: Counter = Counter()
        self._chunk_vectors: list[Counter] = []
        self._load()

    def _load(self):
        for path in sorted(self.docs_dir.glob("*.txt")):
            text = path.read_text(encoding="utf-8")
            for chunk in _chunk_text(text):
                self.chunks.append({"source": path.name, "text": chunk})

        for chunk in self.chunks:
            tokens = set(_tokenize(chunk["text"]))
            self._doc_freq.update(tokens)

        n_docs = max(len(self.chunks), 1)
        for chunk in self.chunks:
            tokens = _tokenize(chunk["text"])
            tf = Counter(tokens)
            vec = Counter()
            for term, count in tf.items():
                idf = math.log(1 + n_docs / (1 + self._doc_freq[term]))
                vec[term] = count * idf
            self._chunk_vectors.append(vec)

    def _vectorize_query(self, query: str) -> Counter:
        n_docs = max(len(self.chunks), 1)
        tokens = _tokenize(query)
        tf = Counter(tokens)
        vec = Counter()
        for term, count in tf.items():
            idf = math.log(1 + n_docs / (1 + self._doc_freq.get(term, 0)))
            vec[term] = count * idf
        return vec

    @staticmethod
    def _cosine(a: Counter, b: Counter) -> float:
        if not a or not b:
            return 0.0
        common = set(a) & set(b)
        dot = sum(a[t] * b[t] for t in common)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if not self.chunks:
            return []
        q_vec = self._vectorize_query(query)
        scored = [
            (self._cosine(q_vec, chunk_vec), i)
            for i, chunk_vec in enumerate(self._chunk_vectors)
        ]
        scored.sort(reverse=True, key=lambda x: x[0])
        results = []
        for score, i in scored[:top_k]:
            if score > 0:
                results.append({**self.chunks[i], "score": round(score, 4)})
        return results
