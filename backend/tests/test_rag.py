"""RAG retrieval test. Requires sentence-transformers + chromadb (AI stack)."""
from __future__ import annotations

import pytest

pytest.importorskip("chromadb")
pytest.importorskip("sentence_transformers")


def test_rag_novapods_bluetooth():
    from app.rag import get_rag

    rag = get_rag()
    rag.reindex(force=True)
    chunks = rag.search("NovaPods Pro keep disconnecting bluetooth", top_k=4)
    assert chunks
    joined = " ".join(c.text.lower() for c in chunks)
    assert "pairing button" in joined or "disconnect" in joined
    assert any("novapods-pro" in c.source for c in chunks)


def test_rag_return_policy():
    from app.rag import get_rag

    chunks = get_rag().search("how many days do I have to return an item", top_k=3)
    assert any(c.source == "returns.md" for c in chunks)
