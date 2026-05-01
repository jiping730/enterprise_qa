from pydantic import BaseModel
from typing import List, Optional

class AskRequest(BaseModel):
    question: str
    documents: Optional[List[str]] = None   # 限定文档过滤
    session_id: Optional[str] = None        # 多轮对话标识

class SourceInfo(BaseModel):
    content: str
    source: str
    page: Optional[int] = None
    score: float = 0.0

class AskResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    confidence: str = ""

class UploadResponse(BaseModel):
    message: str
    file_count: int = 0
    chunk_count: int = 0