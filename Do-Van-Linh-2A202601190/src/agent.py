import re
from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def _format_content(self, content: str) -> str:
        # Headings help humans scan documents but can distract extractive answer stubs.
        return re.sub(r"^\s*#{1,6}\s+.+?(?:\n+|\s{2,})", "", content).strip()

    def answer(self, question: str, top_k: int = 3, metadata_filter: dict | None = None) -> str:
        if metadata_filter:
            results = self.store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = self.store.search(question, top_k=top_k)
        context_blocks = []
        for index, result in enumerate(results[:1], start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source_url") or metadata.get("source") or metadata.get("doc_id") or result.get("document_id")
            content = self._format_content(result.get("content", ""))
            context_blocks.append(
                f"[{index}] source={source} score={result.get('score', 0):.4f}\n{content}"
            )

        context = "\n\n".join(context_blocks) if context_blocks else "No relevant context was retrieved."
        prompt = (
            "Answer the question using only the retrieved context below. "
            "If the context is insufficient, say that the available context is insufficient.\n\n"
            f"Context:\n{context}\n\n"
            f"Question:\n{question}\n\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
