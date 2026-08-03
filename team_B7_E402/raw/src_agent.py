from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore

PROMPT_TEMPLATE = """Báº¡n lÃ  trá»£ lÃ½ tri thá»©c. Chá» ÄÆ°á»£c tráº£ lá»i Dá»°A TRÃN ngá»¯ cáº£nh bÃªn dÆ°á»i.

Quy táº¯c:
- Náº¿u ngá»¯ cáº£nh khÃ´ng Äá»§ thÃ´ng tin, hÃ£y nÃ³i rÃµ lÃ  khÃ´ng tÃ¬m tháº¥y trong tÃ i liá»u; tuyá»t Äá»i khÃ´ng bá»a.
- Khi tráº£ lá»i, trÃ­ch dáº«n sá» hiá»u Äoáº¡n ngá»¯ cáº£nh ÄÃ£ dÃ¹ng, vÃ­ dá»¥ [1], [2].
- Tráº£ lá»i ngáº¯n gá»n, bÃ¡m sÃ¡t cÃ¢u chá»¯ cá»§a tÃ i liá»u.

NGá»® Cáº¢NH:
{context}

CÃU Há»I: {question}

TRáº¢ Lá»I:"""

NO_CONTEXT = "(KhÃ´ng tÃ¬m tháº¥y Äoáº¡n tÃ i liá»u nÃ o liÃªn quan trong cÆ¡ sá» tri thá»©c.)"


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

    def answer(self, question: str, top_k: int = 3, metadata_filter: dict | None = None) -> str:
        # 1) Truy xuáº¥t (lá»c metadata trÆ°á»c khi xáº¿p háº¡ng náº¿u cÃ³ yÃªu cáº§u â cáº§n cho K4)
        if metadata_filter:
            results = self.store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = self.store.search(question, top_k=top_k)

        # 2) Dá»±ng ngá»¯ cáº£nh cÃ³ ÄÃ¡nh sá» + nguá»n Äá» cÃ¢u tráº£ lá»i truy váº¿t ÄÆ°á»£c
        if results:
            blocks = []
            for index, result in enumerate(results, start=1):
                metadata = result.get("metadata") or {}
                source = metadata.get("source_url") or metadata.get("doc_id") or result.get("id", "unknown")
                blocks.append(
                    f"[{index}] (nguá»n: {source} | score={result.get('score', 0.0):.3f})\n{result.get('content', '')}"
                )
            context = "\n\n".join(blocks)
        else:
            context = NO_CONTEXT

        prompt = PROMPT_TEMPLATE.format(context=context, question=question)

        # 3) Sinh cÃ¢u tráº£ lá»i
        answer = self.llm_fn(prompt)
        return answer if isinstance(answer, str) else str(answer)
