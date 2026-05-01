import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from typing import List, Optional, Tuple
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from app.config import EMBEDDING_MODEL, INDEX_DIR

_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
    return _embeddings

def _get_kb_index_dir(kb_id: int) -> str:
    return os.path.join(INDEX_DIR, f"kb_{kb_id}")

def load_vector_store(kb_id: int) -> Optional[FAISS]:
    index_dir = _get_kb_index_dir(kb_id)
    if os.path.exists(index_dir) and os.path.exists(os.path.join(index_dir, "index.faiss")):
        return FAISS.load_local(index_dir, get_embeddings(), allow_dangerous_deserialization=True)
    return None

def save_vector_store(kb_id: int, store: FAISS):
    index_dir = _get_kb_index_dir(kb_id)
    os.makedirs(index_dir, exist_ok=True)
    store.save_local(index_dir)

def add_documents_to_kb(kb_id: int, docs: List[Document]):
    store = load_vector_store(kb_id)
    if store:
        store.add_documents(docs)
    else:
        store = FAISS.from_documents(docs, get_embeddings())
    save_vector_store(kb_id, store)

def delete_document_from_kb(kb_id: int, filename: str):
    """删除某文档在索引中的所有向量"""
    store = load_vector_store(kb_id)
    if not store:
        return
    ids_to_delete = []
    for doc_id, doc in store.docstore._dict.items():
        if doc.metadata.get("source") == filename:
            ids_to_delete.append(doc_id)
    if ids_to_delete:
        store.delete(ids_to_delete)
        save_vector_store(kb_id, store)

def search_with_score_in_kb(
    kb_id: int,
    query: str,
    k: int = 4,
    filter_source: List[str] = None
) -> List[Tuple[Document, float]]:
    """
    在指定知识库中检索，返回 (Document, score) 列表。
    score 为 FAISS 返回的 L2 距离（越小越相关），可与之前逻辑保持一致。
    """
    store = load_vector_store(kb_id)
    if not store:
        return []
    if filter_source:
        # 多取一些结果再过滤
        fetch_k = k * 3
        docs_with_scores = store.similarity_search_with_score(query, k=fetch_k)
        filtered = []
        for doc, score in docs_with_scores:
            if doc.metadata.get("source") in filter_source:
                filtered.append((doc, score))
            if len(filtered) >= k:
                break
        return filtered
    else:
        return store.similarity_search_with_score(query, k=k)