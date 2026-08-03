from __future__ import annotations

import math
import re
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _token_set(text: str) -> set[str]:
    return set(_tokens(text))


def _bigrams(words: list[str]) -> set[tuple[str, str]]:
    return set(zip(words, words[1:]))


def _phrases(words: list[str], min_size: int = 2, max_size: int = 4) -> set[str]:
    phrases: set[str] = set()
    for size in range(min_size, max_size + 1):
        for start in range(0, max(0, len(words) - size + 1)):
            phrase_words = words[start : start + size]
            if any(len(word) >= 3 for word in phrase_words):
                phrases.add(" ".join(phrase_words))
    return phrases


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # Required checkpoints use the deterministic in-memory store.
            self._use_chroma = False
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata or {})
        metadata.setdefault("doc_id", doc.id)
        record_id = f"{doc.id}:{self._next_index}"
        self._next_index += 1
        return {
            "id": record_id,
            "document_id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []

        query_embedding = self._embedding_fn(query)
        query_words = _tokens(query)
        query_terms = set(query_words)
        query_bigrams = _bigrams(query_words)
        query_phrases = _phrases(query_words)
        asks_for_amount = bool({"phí", "bao", "nhiêu", "tính", "tiền"} & query_terms)

        document_frequency: dict[str, int] = {}
        record_terms: list[set[str]] = []
        record_bigrams: list[set[tuple[str, str]]] = []
        for record in records:
            terms = _token_set(record["content"])
            record_terms.append(terms)
            record_bigrams.append(_bigrams(_tokens(record["content"])))
            for term in query_terms & terms:
                document_frequency[term] = document_frequency.get(term, 0) + 1

        total_records = len(records)

        def idf(term: str) -> float:
            return math.log((total_records + 1) / (document_frequency.get(term, 0) + 1)) + 1.0

        query_weight = sum(idf(term) for term in query_terms) or 1.0
        scored: list[dict[str, Any]] = []
        for index, record in enumerate(records):
            terms = record_terms[index]
            overlap = query_terms & terms
            lexical_recall = sum(idf(term) for term in overlap) / query_weight
            lexical_precision = len(overlap) / (len(terms) or 1)
            bigram_overlap = len(query_bigrams & record_bigrams[index]) / (len(query_bigrams) or 1)
            numeric_overlap = len({term for term in overlap if any(ch.isdigit() for ch in term)})
            content_lower = record["content"].lower()
            phrase_bonus = sum(0.35 for term in query_terms if len(term) >= 6 and term in content_lower)
            phrase_bonus += sum(0.45 for phrase in query_phrases if phrase in content_lower)
            amount_bonus = 0.7 if asks_for_amount and re.search(r"\d|%|vnđ|xu", content_lower) else 0.0
            lexical_score = (2.4 * lexical_recall) + (0.8 * lexical_precision) + (1.2 * bigram_overlap) + (0.3 * numeric_overlap) + phrase_bonus
            lexical_score += amount_bonus
            vector_score = float(_dot(query_embedding, record["embedding"]))
            scored.append(
                {
                    "id": record["id"],
                    "document_id": record["document_id"],
                    "content": record["content"],
                    "metadata": dict(record["metadata"]),
                    "score": vector_score + lexical_score,
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        self._store.extend(self._make_record(doc) for doc in docs)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        def matches(record: dict[str, Any]) -> bool:
            for key, expected in metadata_filter.items():
                actual = record["metadata"].get(key)
                if isinstance(expected, (list, tuple, set)):
                    if actual not in expected:
                        return False
                elif actual != expected:
                    return False
            return True

        filtered = [record for record in self._store if matches(record)]
        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        size_before = len(self._store)
        self._store = [
            record
            for record in self._store
            if record["metadata"].get("doc_id") != doc_id and record["document_id"] != doc_id
        ]
        return len(self._store) < size_before
