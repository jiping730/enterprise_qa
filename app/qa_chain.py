import logging
from typing import List, Tuple, Dict
from langchain.schema import Document, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.config import ZHIPU_API_KEY, LLM_MODEL, LLM_API_BASE, TOP_K
from app.vector_store import search_with_score_in_kb
from app.models_api import SourceInfo
from app.models_db import QueryLog, User
from app.database import get_db

logger = logging.getLogger(__name__)

# 内存中的多轮对话历史（仍保留，服务重启丢失）
session_histories: Dict[str, List] = {}

def _build_llm():
    return ChatOpenAI(
        model=LLM_MODEL,
        openai_api_key=ZHIPU_API_KEY,
        openai_api_base=LLM_API_BASE,
        temperature=0.1,
    )

def _get_confidence(docs_with_score: List[Tuple[Document, float]]) -> str:
    if not docs_with_score:
        return "知识库中没有匹配的文档片段。"
    min_distance = docs_with_score[0][1]
    similarity = 1.0 / (1.0 + min_distance)
    if similarity > 0.75:
        return "✅ 在文档中找到了高度相关内容，答案可信。"
    elif similarity > 0.5:
        return "⚠️ 文档中有部分相关内容，答案可能不够完整。"
    elif similarity > 0.3:
        return "❓ 文档中未找到直接相关内容，以下回答基于模型推断，请谨慎参考。"
    else:
        return "❌ 文档中几乎没有相关信息，回答可能不可靠。"

def answer_question(
        kb_id: int,
        question: str,
        user: User,
        filter_docs: List[str] = None,
        session_id: str = None
) -> Tuple[str, List[SourceInfo], str]:
    # 1. 检索（在指定知识库内）
    raw_docs_with_score = search_with_score_in_kb(
        kb_id,
        question,
        k=TOP_K,
        filter_source=filter_docs if filter_docs else None
    )

    if not raw_docs_with_score:
        # 检查知识库是否为空
        from app.vector_store import load_vector_store
        store = load_vector_store(kb_id)
        if store is None or store.index.ntotal == 0:
            confidence = "知识库中没有文档，请先上传文件。"
        else:
            if filter_docs:
                confidence = f"在您选择的文档（{', '.join(filter_docs)}）中未找到相关内容，请尝试扩大检索范围。"
            else:
                confidence = "知识库中未找到匹配的文档片段。"
        return "请先上传相关文档，或尝试更换问题。", [], confidence

    # 2. 置信度
    confidence = _get_confidence(raw_docs_with_score)
    docs = [doc for doc, _ in raw_docs_with_score]

    # 3. 构建消息（含历史）
    messages = [
        SystemMessage(content="你是一个严谨的企业文档问答助手。请仅根据提供的参考资料回答，不要编造。")
    ]
    if session_id and session_id in session_histories:
        messages.extend(session_histories[session_id])

    context_parts = []
    for idx, doc in enumerate(docs):
        source = doc.metadata.get("source", "未知文档")
        page = doc.metadata.get("page")
        page_str = f"第{page+1}页" if page is not None else ""
        context_parts.append(f"[参考{idx+1} 来源: {source} {page_str}]\n{doc.page_content}")
    context = "\n\n".join(context_parts)

    messages.append(HumanMessage(content=f"参考资料：\n{context}\n\n用户问题：{question}"))

    # 4. 调用 LLM
    llm = _build_llm()
    try:
        response = llm.invoke(messages)
        answer = response.content.strip()
    except Exception as e:
        logger.error(f"LLM调用失败: {e}")
        answer = "生成答案时出错，请检查 API Key 或网络。"

    # 5. 记录查询日志到 MySQL
    db = next(get_db())
    log = QueryLog(
        user_id=user.id,
        kb_id=kb_id,
        question=question,
        answer_snippet=answer[:200]
    )
    db.add(log)
    db.commit()

    # 6. 更新会话历史
    if session_id:
        if session_id not in session_histories:
            session_histories[session_id] = []
        session_histories[session_id].append(HumanMessage(content=question))
        session_histories[session_id].append(AIMessage(content=answer))
        session_histories[session_id] = session_histories[session_id][-40:]

    # 7. 构建来源信息
    sources = []
    for doc, score in raw_docs_with_score:
        sources.append(SourceInfo(
            content=doc.page_content[:200],
            source=doc.metadata.get("source", "未知"),
            page=doc.metadata.get("page") + 1 if doc.metadata.get("page") is not None else None,
            score=round(score, 4)
        ))

    return answer, sources, confidence