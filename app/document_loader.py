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
        raise ValueError(f"不支持的文件类型: {ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}")

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)

    documents = loader.load()

    # 提取纯净文件名（不含路径）
    base_name = os.path.basename(file_path)

    # 强制覆盖所有文档的 source 为文件名
    for doc in documents:
        doc.metadata["source"] = base_name
        # 注意：如果有 page 信息保留，没有则忽略

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )
    split_docs = text_splitter.split_documents(documents)

    # 分割后的文档会自动继承 metadata，确保 source 一致
    return split_docs