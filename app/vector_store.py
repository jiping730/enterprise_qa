import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import logging
from typing import List, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from app.config import EMBEDDING_MODEL, INDEX_DIR
# ... 其余不变

logger = logging.getLogger(__name__)

# 全局嵌入模型（单例）
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

def load_vector_store() -> Optional[FAISS]:
    """加载本地索引，不存在或损坏返回 None"""
    if os.path.exists(INDEX_DIR) and os.path.exists(os.path.join(INDEX_DIR, "index.faiss")):
        try:
            return FAISS.load_local(INDEX_DIR, get_embeddings(), allow_dangerous_deserialization=True)
        except Exception as e:
            logger.warning(f"加载索引失败: {e}，将重建新索引")
            return None
    return None

def save_vector_store(store: FAISS):
    os.makedirs(INDEX_DIR, exist_ok=True)
    store.save_local(INDEX_DIR)

def add_documents(docs: List[Document]):
    """增量添加文档到向量库"""
    store = load_vector_store()
    if store:
        store.add_documents(docs)
    else:
        store = FAISS.from_documents(docs, get_embeddings())
    save_vector_store(store)

def reset_knowledge_base():
    """清空知识库（删除索引目录）"""
    import shutil
    if os.path.exists(INDEX_DIR):
        shutil.rmtree(INDEX_DIR)
        logger.info("知识库已重置")

def get_retriever():
    """返回检索器，库为空返回 None"""
    store = load_vector_store()
    if store:
        return store.as_retriever(search_kwargs={"k": 4})
    return None