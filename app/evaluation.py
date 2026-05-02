import json
import re
from typing import List, Dict, Any
from app.qa_chain import answer_question
from app.models_db import User

def _normalize(text: str) -> str:
    """保留中文、英文、数字，去除其他所有字符（标点、空格等），转小写"""
    # \u4e00-\u9fff 是中文字符范围，\w 在 Python 中默认仅 ASCII 字母数字
    # 我们显式保留中文、字母、数字，去除其余符号
    text = re.sub(r'[^\w\u4e00-\u9fff]', '', text.lower().strip())
    text = text.replace('_', '')
    return text

def _char_coverage(expected_norm: str, answer_norm: str) -> float:
    """计算预期答案中的字符在答案中出现的覆盖率"""
    if not expected_norm:
        return 1.0
    expected_chars = set(expected_norm)
    answer_chars = set(answer_norm)
    covered = expected_chars.intersection(answer_chars)
    return len(covered) / len(expected_chars)

def _is_exact_match(answer: str, expected: str) -> bool:
    ans_norm = _normalize(answer)
    exp_norm = _normalize(expected)
    coverage = _char_coverage(exp_norm, ans_norm)
    return coverage >= 0.8   # 80% 字符覆盖

def _is_partial_match(answer: str, expected: str) -> bool:
    ans_norm = _normalize(answer)
    exp_norm = _normalize(expected)
    coverage = _char_coverage(exp_norm, ans_norm)
    return 0.5 <= coverage < 0.8

def evaluate_kb(
    kb_id: int,
    user: User,
    test_data: List[Dict[str, str]]
) -> Dict[str, Any]:
    results = []
    stats = {"total": 0, "exact_match": 0, "partial_match": 0, "rejected": 0, "error": 0}

    for item in test_data:
        question = item.get("question", "").strip()
        expected = item.get("expected", "").strip()
        if not question or not expected:
            continue

        answer, sources, confidence = answer_question(
            kb_id=kb_id,
            question=question,
            user=user,
            filter_docs=None,
            session_id=None
        )

        if not answer or "请先上传相关文档" in answer or "知识库中没有找到" in answer:
            match_type = "rejected"
            stats["rejected"] += 1
        elif _is_exact_match(answer, expected):
            match_type = "exact_match"
            stats["exact_match"] += 1
        elif _is_partial_match(answer, expected):
            match_type = "partial_match"
            stats["partial_match"] += 1
        else:
            match_type = "error"
            stats["error"] += 1

        stats["total"] += 1
        results.append({
            "question": question,
            "expected": expected,
            "answer": answer[:500],
            "match_type": match_type
        })

    total = stats["total"]
    report = {
        "summary": {
            "total": total,
            "exact_match": stats["exact_match"],
            "exact_match_rate": round(stats["exact_match"] / total, 4) if total > 0 else 0,
            "partial_match": stats["partial_match"],
            "partial_match_rate": round(stats["partial_match"] / total, 4) if total > 0 else 0,
            "rejected": stats["rejected"],
            "rejected_rate": round(stats["rejected"] / total, 4) if total > 0 else 0,
            "error": stats["error"],
            "error_rate": round(stats["error"] / total, 4) if total > 0 else 0,
        },
        "details": results
    }
    return report