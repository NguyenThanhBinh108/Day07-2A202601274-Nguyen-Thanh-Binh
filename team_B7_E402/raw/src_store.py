from __future__ import annotations

import os
import warnings
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


def _chroma_safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Ãp metadata vá» kiá»u vÃ´ hÆ°á»ng mÃ  ChromaDB cháº¥p nháº­n (str/int/float/bool).

    `ingest.py` dÃ¹ng pyyaml náº¿u cÃ³, nÃªn `retrieved_at: 2026-08-02` ra `datetime.date`.
    Chroma tá»« chá»i nguyÃªn cáº£ lÃ´ khi gáº·p kiá»u khÃ´ng vÃ´ hÆ°á»ng â khÃ´ng Ã©p kiá»u thÃ¬ toÃ n
    bá» tÃ i liá»u sáº½ khÃ´ng vÃ o ÄÆ°á»£c Chroma. Báº£n gá»c váº«n giá»¯ nguyÃªn trong `self._store`
    nÃªn viá»c lá»c/tÃ¬m kiáº¿m khÃ´ng bá» áº£nh hÆ°á»ng bá»i phÃ©p Ã©p nÃ y.
    """
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        safe[str(key)] = value if isinstance(value, (str, int, float, bool)) else str(value)
    return safe


def _matches(stored_value: Any, wanted: Any) -> bool:
    """So khá»p má»t cáº·p metadata.

    Máº·c Äá»nh lÃ  so báº±ng (==) ÄÃºng nhÆ° Äáº·c táº£. ThÃªm 2 ná»i lá»ng cÃ³ chá»§ ÄÃ­ch:
      - `wanted` lÃ  list/tuple/set  -> khá»p náº¿u thuá»c táº­p ÄÃ³, vÃ­ dá»¥
        {"customer_role": ["seller", "both"]} Äá» khÃ´ng bá» sÃ³t tÃ i liá»u dÃ¹ng chung.
      - so báº±ng chuá»i khi kiá»u khÃ¡c nhau -> `ingest.py` dÃ¹ng pyyaml náº¿u cÃ³, nÃªn
        `retrieved_at: 2026-08-02` ra `datetime.date` khi cÃ³ pyyaml vÃ  `str` khi khÃ´ng.
        Náº¿u chá» dÃ¹ng `==` thÃ¬ lá»c theo ngÃ y sáº½ Ã¢m tháº§m tráº£ vá» rá»ng tuá»³ mÃ´i trÆ°á»ng.
    """
    if isinstance(wanted, (list, tuple, set)):
        return any(_matches(stored_value, option) for option in wanted)
    if stored_value == wanted:
        return True
    return stored_value is not None and str(stored_value) == str(wanted)


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

            persist_dir = os.getenv("CHROMA_PERSIST_DIR", "").strip()
            if persist_dir:
                client = chromadb.PersistentClient(path=persist_dir)
            else:
                # Ephemeral = cháº¡y hoÃ n toÃ n trong RAM: má»i store má»i báº¯t Äáº§u rá»ng,
                # nÃªn get_collection_size() cá»§a store vá»«a táº¡o luÃ´n = 0 (táº¥t Äá»nh cho test).
                client = chromadb.EphemeralClient()

            try:
                client.delete_collection(name=collection_name)
            except Exception:
                pass  # collection chÆ°a tá»n táº¡i -> khÃ´ng cÃ³ gÃ¬ Äá» xoÃ¡

            self._client = client
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Chuáº©n hoÃ¡ má»t Document thÃ nh báº£n ghi lÆ°u trá»¯ (ÄÃ£ nhÃºng sáºµn embedding)."""
        metadata = dict(doc.metadata or {})
        # doc_id lÃ  khoÃ¡ Äá» lá»c & xoÃ¡ theo tÃ i liá»u gá»c; náº¿u ingest chÆ°a gáº¯n thÃ¬ láº¥y tá»« id.
        metadata.setdefault("doc_id", doc.id)

        record = {
            "id": doc.id,
            # id ná»i bá» luÃ´n duy nháº¥t -> thÃªm cÃ¹ng má»t doc.id nhiá»u láº§n váº«n Äáº¿m ÄÃºng.
            "storage_id": f"{doc.id}#{self._next_index}",
            "content": doc.content,
            "embedding": self._embedding_fn(doc.content),
            "metadata": metadata,
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """TÃ¬m kiáº¿m tÆ°Æ¡ng tá»± trong bá» nhá» trÃªn ÄÃºng táº­p báº£n ghi ÄÆ°á»£c truyá»n vÃ o."""
        if not records or top_k is None or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        scored = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                # Embedding cá»§a lab ÄÃ£ ÄÆ°á»£c chuáº©n hoÃ¡ L2 -> dot product == cosine similarity.
                "score": float(_dot(query_embedding, record["embedding"])),
            }
            for record in records
        ]
        scored.sort(key=lambda result: result["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]
        self._store.extend(records)

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[record["storage_id"] for record in records],
                    documents=[record["content"] for record in records],
                    embeddings=[record["embedding"] for record in records],
                    metadatas=[_chroma_safe_metadata(record["metadata"]) for record in records],
                )
            except Exception as error:
                # Chroma lá»i (schema metadata, version...) -> quay vá» in-memory, khÃ´ng máº¥t dá»¯ liá»u.
                # Cáº£nh bÃ¡o tÆ°á»ng minh thay vÃ¬ im láº·ng, Äá» ngÆ°á»i dÃ¹ng biáº¿t store Äang cháº¡y cháº¿ Äá» nÃ o.
                warnings.warn(f"ChromaDB add tháº¥t báº¡i ({error}); chuyá»n sang store in-memory.", stacklevel=2)
                self._use_chroma = False
                self._collection = None

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            try:
                return int(self._collection.count())
            except Exception:
                pass
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            candidates = self._store
        else:
            candidates = [
                record
                for record in self._store
                if all(_matches(record["metadata"].get(key), value) for key, value in metadata_filter.items())
            ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        size_before = len(self._store)
        self._store = [record for record in self._store if record["metadata"].get("doc_id") != doc_id]
        removed = size_before - len(self._store)

        if removed and self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(where={"doc_id": doc_id})
            except Exception:
                self._use_chroma = False
                self._collection = None

        return removed > 0
