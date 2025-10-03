from typing import List
from dataclasses import dataclass
from .indexer import RAGIndexer, DocumentChunk


@dataclass
class RetrievedContext:
    """Small, minimal payload to send to LLM to reduce tokens."""
    formatted: str  # Pre-formatted context with source labels and chunk ids
    ids: List[str]  # e.g., ["pre:1", "post:3"]


class Retriever:
    def __init__(self, indexer: RAGIndexer) -> None:
        self.indexer = indexer

    def retrieve(self, query: str, k: int) -> RetrievedContext:
        top: List[DocumentChunk] = self.indexer.top_k(query, k)
        ids: List[str] = [f"{c.source}:{c.chunk_id}" for c in top]
        blocks: List[str] = [f"[{c.source.upper()} #{c.chunk_id}]\n{c.text}" for c in top]
        return RetrievedContext(formatted="\n\n".join(blocks), ids=ids)


