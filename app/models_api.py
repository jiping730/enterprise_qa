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


class EvaluationItem(BaseModel):
    question: str
    expected: str


class EvaluationDetail(BaseModel):
    question: str
    expected: str
    answer: str
    match_type: str


class EvaluationSummary(BaseModel):
    total: int
    exact_match: int
    exact_match_rate: float
    partial_match: int
    partial_match_rate: float
    rejected: int
    rejected_rate: float
    error: int
    error_rate: float


class EvaluationReport(BaseModel):
    summary: EvaluationSummary
    details: List[EvaluationDetail]