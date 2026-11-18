"""Phân tích cú pháp đơn giản cho tiếng Việt y khoa.

Xử lý:
- Tách mệnh đề chủ-vị
- Phủ định lồng
- Mức độ
- So sánh
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple
from core.feature_extractor import norm


CLAUSE_CONNECTORS = [
    "nhung", "tuy nhien", "ngoai tru", "tru", "mac du", "du",
    "va", "voi", "cung", "roi", "sau do", "truoc do",
]

NEGATION_WORDS = [
    "khong", "chua", "chua tung", "khong he", "khong bao gio",
    "phu nhan", "khong co", "khong bi", "khong xuat hien",
]

DEGREE_WORDS = {
    "nhe": 0.5, "it": 0.5, "hoi": 0.6, "vua": 0.7, "kha": 0.8,
    "nhieu": 0.9, "rat": 1.0, "cuc": 1.0, "du doi": 0.7,
    "manh": 0.9, "du": 0.8,
}

COMPARISON_WORDS = ["hon", "kem", "bang", "nhu", "tuong tu", "it hon", "nhieu hon"]


def split_into_clauses(text: str) -> List[str]:
    t = norm(text)
    parts = re.split(r"[,;.!?]", t)
    clauses: List[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        for conn in CLAUSE_CONNECTORS:
            if f" {conn} " in f" {p} ":
                sub = re.split(rf"\s+{conn}\s+", p)
                clauses.extend(s.strip() for s in sub if s.strip())
                break
        else:
            clauses.append(p)
    return clauses


def analyze_negation_in_clause(clause: str) -> Dict[str, Any]:
    clause_n = norm(clause)
    negations_found = []
    for neg in NEGATION_WORDS:
        if re.search(rf"\b{re.escape(neg)}\b", clause_n):
            negations_found.append(neg)
    double_neg_patterns = [
        r"khong\s+phai\s+khong",
        r"khong\s+the\s+khong",
        r"chang\s+le\s+khong",
        r"khong\s+ai\s+khong",
    ]
    is_double = any(re.search(p, clause_n) for p in double_neg_patterns)
    return {
        "has_negation": len(negations_found) > 0,
        "negation_count": len(negations_found),
        "is_double_negation": is_double,
        "negated_terms": negations_found,
    }


def extract_degree(clause: str) -> Tuple[float, str]:
    clause_n = norm(clause)
    for word, score in sorted(DEGREE_WORDS.items(), key=lambda x: -x[1]):
        if re.search(rf"\b{re.escape(word)}\b", clause_n):
            return score, word
    return 0.7, ""


def extract_comparison(clause: str) -> Dict[str, Any]:
    clause_n = norm(clause)
    for word in COMPARISON_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", clause_n):
            if word in ("hon", "nhieu hon"):
                return {"has_comparison": True, "comparison_type": "hon", "comparison_word": word}
            if word in ("kem", "it hon"):
                return {"has_comparison": True, "comparison_type": "kem", "comparison_word": word}
            return {"has_comparison": True, "comparison_type": "bang", "comparison_word": word}
    return {"has_comparison": False, "comparison_type": None, "comparison_word": ""}


def analyze_syntax(text: str) -> Dict[str, Any]:
    clauses = split_into_clauses(text)
    analyzed_clauses = []
    overall_neg = False
    degrees = []
    has_comp = False
    for clause in clauses:
        neg = analyze_negation_in_clause(clause)
        deg_score, deg_word = extract_degree(clause)
        comp = extract_comparison(clause)
        effective_negation = neg["has_negation"] and not neg["is_double_negation"]
        analyzed_clauses.append({
            "text": clause,
            "negation": neg,
            "effective_negation": effective_negation,
            "degree_score": deg_score,
            "degree_word": deg_word,
            "comparison": comp,
        })
        if effective_negation:
            overall_neg = True
        degrees.append(deg_score)
        if comp["has_comparison"]:
            has_comp = True
    return {
        "clauses": analyzed_clauses,
        "overall_negation": overall_neg,
        "overall_degree": sum(degrees) / len(degrees) if degrees else 0.7,
        "has_comparison": has_comp,
    }