from typing import List, Dict, Tuple
import os
import re
from dataclasses import dataclass


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _chunk_xml(text: str, max_chars: int) -> List[str]:
    chunks: List[str] = []
    current: List[str] = []
    size = 0
    for line in text.splitlines():
        current.append(line)
        size += len(line) + 1
        if size >= max_chars and line.strip().endswith('>'):
            chunks.append("\n".join(current))
            current = []
            size = 0
    if current:
        chunks.append("\n".join(current))
    return chunks


@dataclass
class DocumentChunk:
    source: str
    chunk_id: int
    text: str


class SimpleBM25:
    """Lightweight BM25-like scorer to reduce dependencies and keep payload minimal."""

    def __init__(self, docs: List[str]):
        self.docs = docs
        self.doc_terms: List[List[str]] = [self._tokenize(d) for d in docs]
        self.term_df: Dict[str, int] = {}
        for terms in self.doc_terms:
            seen = set(terms)
            for t in seen:
                self.term_df[t] = self.term_df.get(t, 0) + 1
        self.avgdl = sum(len(t) for t in self.doc_terms) / max(len(self.doc_terms), 1)
        self.k1 = 1.5
        self.b = 0.75

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[A-Za-z0-9_\-]+", text.lower())

    def score_query(self, query: str) -> List[Tuple[int, float]]:
        q_terms = self._tokenize(query)
        scores: Dict[int, float] = {}
        N = len(self.docs)
        for qi in set(q_terms):
            df = self.term_df.get(qi, 0) or 0
            if df == 0:
                continue
            idf = max(0.0, ( (N - df + 0.5) / (df + 0.5) ))
            for idx, terms in enumerate(self.doc_terms):
                tf = terms.count(qi)
                if tf == 0:
                    continue
                dl = len(terms)
                denom = tf + self.k1 * (1 - self.b + self.b * (dl / max(self.avgdl, 1e-6)))
                scores[idx] = scores.get(idx, 0.0) + idf * ((tf * (self.k1 + 1)) / denom)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)


class RAGIndexer:
    def __init__(self, max_chars_per_chunk: int) -> None:
        self.max_chars_per_chunk = max_chars_per_chunk
        self.chunks: List[DocumentChunk] = []
        self.bm25: SimpleBM25 | None = None

    def build(self, pre_path: str, post_path: str) -> None:
        self.chunks.clear()
        pre_text = _read_text(pre_path)
        post_text = _read_text(post_path)
        pre_chunks = _chunk_xml(pre_text, self.max_chars_per_chunk)
        post_chunks = _chunk_xml(post_text, self.max_chars_per_chunk)
        for i, c in enumerate(pre_chunks):
            self.chunks.append(DocumentChunk("pre", i, _normalize_space(c)))
        for i, c in enumerate(post_chunks):
            self.chunks.append(DocumentChunk("post", i, _normalize_space(c)))
        self.bm25 = SimpleBM25([c.text for c in self.chunks])

    def top_k(self, query: str, k: int) -> List[DocumentChunk]:
        if not self.bm25:
            return []
        scored = self.bm25.score_query(query)
        top = [self.chunks[idx] for idx, _ in scored[:k]]
        return top


