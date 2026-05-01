from pydantic import BaseModel
from typing import List, Optional

class AskRequest(BaseModel):
    question: str
    documents: Optional[List[str]] = None   # 用户限定的文档名列表
    session_id: Optional[str] = None        # 多轮对话标识

class SourceInfo(BaseModel):
    content: str
    source: str
    page: Optional[int] = None
    score: float = 0.0                      # 相似度分数，用于调试/显示

class AskResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    confidence: str = ""                    # 置信度说明文本

class UploadResponse(BaseModel):
    message: str
    file_count: int
    chunk_count: int