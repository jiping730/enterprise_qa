from typing import List, Tuple
import logging
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from app.config import ZHIPU_API_KEY, LLM_MODEL, LLM_API_BASE, TOP_K
from app.vector_store import get_retriever
from app.models import SourceInfo

logger = logging.getLogger(__name__)

def _build_llm():
    return ChatOpenAI(
        model=LLM_MODEL,
        openai_api_key=ZHIPU_API_KEY,
        openai_api_base=LLM_API_BASE,
        temperature=0.1,
    )

def answer_question(question: str) -> Tuple[str, List[SourceInfo]]:
    """问答主逻辑：检索 -> 生成 -> 提取来源"""
    retriever = get_retriever()
    if not retriever:
        return "知识库中没有文档，请先上传文件。", []

    # 1. 检索
    docs: List[Document] = retriever.invoke(question)
    if not docs:
        return "未找到与问题相关的文档片段。", []

    # 2. 构建提示词，附上来源标记
    context_parts = []
    for idx, doc in enumerate(docs):
        source = doc.metadata.get("source", "未知文档")
        page = doc.metadata.get("page")
        page_str = f", 第{page+1}页" if page is not None else ""
        context_parts.append(f"[参考{idx+1} 来源: {source}{page_str}]\n{doc.page_content}")
    context = "\n\n".join(context_parts)

    prompt = f"""你是一个严谨的企业文档问答助手。请仅根据以下参考资料回答用户问题，禁止编造。
如果资料中没有答案，请明确回答“根据现有资料无法回答”。

参考资料：
{context}

用户问题：{question}
回答："""

    # 3. 调用大模型
    llm = _build_llm()
    try:
        response = llm.invoke(prompt)
        answer = response.content.strip()
    except Exception as e:
        logger.error(f"LLM调用失败: {e}")
        answer = "生成答案时出错，请检查 API Key 或网络连接。"

    # 4. 构建来源信息
    sources = []
    for doc in docs:
        sources.append(SourceInfo(
            content=doc.page_content[:200],  # 截取前200字符
            source=doc.metadata.get("source", "未知"),
            page=doc.metadata.get("page") + 1 if doc.metadata.get("page") is not None else None
        ))

    return answer, sources