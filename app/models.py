from pydantic import BaseModel
from typing import List, Optional

class AskRequest(BaseModel):
    question: str

class SourceInfo(BaseModel):
    content: str          # 文档片段原文（前200字）
    source: str           # 文档文件名
    page: Optional[int] = None   # 页码（PDF），从1开始

class AskResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]

class UploadResponse(BaseModel):
    message: str
    file_count: int
    chunk_count: int