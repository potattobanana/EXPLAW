"""
RAG vector store: wraps chromadb for indexing and searching statute
text and firm document clauses. Two collections - "statutes" and
"firm_documents" - keyed by chunk id; metadata carries the ids the
agent tools need to build a citation (statute_id/section, or
document_id).
"""

from app.config import settings

_client = None


def _get_client():
    global _client
    if _client is None:
        import chromadb

        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def _get_collection(name: str):
    return _get_client().get_or_create_collection(name)


def upsert(collection: str, chunk_id: str, text: str, metadata: dict) -> None:
    """Embeds `text` and stores it under `chunk_id` with `metadata`
    (e.g. {statute_id, section, citation} or {document_id})."""
    _get_collection(collection).upsert(ids=[chunk_id], documents=[text], metadatas=[metadata])


def delete(collection: str, where: dict) -> None:
    """Removes every chunk matching `where` (e.g. {"statute_id": "..."})
    - used to reset a demo act's indexed sections between rehearsals."""
    _get_collection(collection).delete(where=where)


def search(collection: str, query: str, k: int = 5, where: dict | None = None) -> list[dict]:
    """Returns the top-k chunks as [{chunk_id, text, metadata}, ...],
    optionally filtered by `where` (e.g. {"statute_id": "..."})."""
    result = _get_collection(collection).query(query_texts=[query], n_results=k, where=where)
    ids = result["ids"][0]
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    return [
        {"chunk_id": chunk_id, "text": text, **metadata}
        for chunk_id, text, metadata in zip(ids, documents, metadatas)
    ]
