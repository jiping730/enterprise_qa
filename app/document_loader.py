import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

# 支持的文件类型
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

def load_and_split(file_path: str) -> List[Document]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}")

    # 根据扩展选择加载器
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)

    documents = loader.load()

    # 确保元数据中包含 source（文件名）
    base_name = os.path.basename(file_path)
    for doc in documents:
        if "source" not in doc.metadata:
            doc.metadata["source"] = base_name
        # 如果是PDF，page 字段从0开始，保持原样

    # 中文友好的递归分割
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )
    return text_splitter.split_documents(documents)