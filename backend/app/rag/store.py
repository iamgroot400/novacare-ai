"""RAG over the /knowledge Markdown files using ChromaDB + local embeddings.

- Markdown is split on headings into sections.
- Embeddings are local: sentence-transformers/all-MiniLM-L6-v2 when available,
  otherwise Chroma's bundled ONNX all-MiniLM-L6-v2 (same model, no torch, no paid API).
- Each file's SHA-256 is stored so unchanged files are not re-embedded.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.config import settings

log = logging.getLogger("novacare.rag")

KNOWLEDGE_DIR = Path(
    os.getenv("KNOWLEDGE_DIR", Path(__file__).resolve().parents[3] / "knowledge")
)
DATA_DIR = Path(os.getenv("RAG_PERSIST_DIR", KNOWLEDGE_DIR.parent / "data" / "chroma"))
COLLECTION_NAME = "novacare_knowledge"
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


@dataclass
class RetrievedChunk:
    text: str
    source: str
    document_type: str
    section: str
    product_id: str | None
    score: float


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    m = _FRONTMATTER_RE.match(raw)
    meta: dict = {}
    body = raw
    if m:
        body = raw[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
    return meta, body


def _chunk_markdown(body: str) -> list[tuple[str, str]]:
    lines = body.splitlines()
    chunks: list[tuple[str, str]] = []
    current_title = "Overview"
    buf: list[str] = []

    def flush() -> None:
        text = "\n".join(buf).strip()
        if text:
            chunks.append((current_title, text))

    for line in lines:
        if re.match(r"^#{1,3}\s+", line):
            flush()
            buf = [line]
            current_title = re.sub(r"^#{1,3}\s+", "", line).strip()
        else:
            buf.append(line)
    flush()

    merged: list[tuple[str, str]] = []
    for title, text in chunks:
        if merged and len(text) < 160:
            pt, ptext = merged[-1]
            merged[-1] = (pt, ptext + "\n\n" + text)
        else:
            merged.append((title, text))
    return merged


def _embedding_function():
    from chromadb.utils import embedding_functions

    model_name = settings.embedding_model
    try:
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
        log.info("RAG embeddings: sentence-transformers %s", model_name)
        return ef
    except Exception as exc:  # noqa: BLE001
        log.warning("sentence-transformers unavailable (%s); using Chroma default ONNX MiniLM", exc)
        return embedding_functions.DefaultEmbeddingFunction()


class RAGStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._client = None
        self._collection = None
        self._ready = False

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        import chromadb

        host = settings.chroma_host
        if host and host not in {"", "local", "none", "localhost-disabled"}:
            try:
                self._client = chromadb.HttpClient(host=host, port=settings.chroma_port)
                self._client.heartbeat()
            except Exception as exc:  # noqa: BLE001
                log.warning("Chroma HttpClient(%s:%s) failed (%s); using local persistent client",
                            host, settings.chroma_port, exc)
                self._client = None
        if self._client is None:
            os.makedirs(DATA_DIR, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(DATA_DIR))

        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            embedding_function=_embedding_function(),
        )
        return self._collection

    def reindex(self, force: bool = False) -> dict:
        with self._lock:
            collection = self._get_collection()
            files = sorted(KNOWLEDGE_DIR.glob("*.md"))
            indexed, skipped = 0, 0

            existing_hashes: dict[str, str] = {}
            try:
                got = collection.get(include=["metadatas"])
                for md in got.get("metadatas", []) or []:
                    if md and md.get("source") and md.get("file_hash"):
                        existing_hashes[md["source"]] = md["file_hash"]
            except Exception:  # noqa: BLE001
                pass

            for path in files:
                raw = path.read_text(encoding="utf-8")
                file_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
                source = path.name
                if not force and existing_hashes.get(source) == file_hash:
                    skipped += 1
                    continue

                try:
                    collection.delete(where={"source": source})
                except Exception:  # noqa: BLE001
                    pass

                meta, body = _parse_frontmatter(raw)
                doc_type = meta.get("document_type", "general")
                product_id = meta.get("product_id")
                sections = _chunk_markdown(body)
                ids, docs, metadatas = [], [], []
                for i, (title, text) in enumerate(sections):
                    ids.append(f"{source}::{i}")
                    docs.append(text)
                    m = {
                        "source": source,
                        "document_type": doc_type,
                        "section": title,
                        "file_hash": file_hash,
                    }
                    if product_id:
                        m["product_id"] = product_id
                    metadatas.append(m)
                if docs:
                    collection.add(ids=ids, documents=docs, metadatas=metadatas)
                    indexed += 1

            self._ready = True
            return {"files": len(files), "indexed": indexed, "skipped": skipped,
                    "chunks": collection.count()}

    def ensure_ready(self) -> None:
        if not self._ready:
            self.reindex(force=False)

    def search(self, query: str, top_k: int = 4, product_id: str | None = None) -> list[RetrievedChunk]:
        self.ensure_ready()
        collection = self._get_collection()
        where = {"product_id": product_id} if product_id else None
        res = collection.query(
            query_texts=[query],
            n_results=max(1, min(top_k, 8)),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        out: list[RetrievedChunk] = []
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        for text, md, dist in zip(docs, metas, dists):
            md = md or {}
            out.append(RetrievedChunk(
                text=text,
                source=md.get("source", "unknown"),
                document_type=md.get("document_type", "general"),
                section=md.get("section", ""),
                product_id=md.get("product_id"),
                score=round(1.0 - float(dist), 4),
            ))
        return out


@lru_cache
def get_rag() -> RAGStore:
    return RAGStore()
