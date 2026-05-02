import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

def load_and_split(file_path: str) -> List[Document]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {ext}")

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)

    documents = loader.load()
    base_name = os.path.basename(file_path)
    for doc in documents:
        doc.metadata["source"] = base_name

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )
    split_docs = text_splitter.split_documents(documents)
    # 为每个块生成唯一 ID（用于后续删除等）
    for idx, doc in enumerate(split_docs):
        doc.metadata["chunk_id"] = f"{base_name}_{idx}"
    return split_docs


def split_text(text: str, source_name: str) -> List[Document]:
    """
    将纯文本内容按已有分块策略分割为多个 Document
    source_name 会写入每个块的 metadata 中
    """
    from langchain.schema import Document as LangDocument

    # 手动创建一个 Document 对象，包含全部文本
    full_doc = LangDocument(page_content=text, metadata={"source": source_name})

    # 使用与文件加载相同的分割器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )
    split_docs = text_splitter.split_documents([full_doc])
    # 为每个块补充 chunk_id
    for idx, doc in enumerate(split_docs):
        doc.metadata["chunk_id"] = f"{source_name}_{idx}"
    return split_docs