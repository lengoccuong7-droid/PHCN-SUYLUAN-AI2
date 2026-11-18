"""Suy luận logic đơn giản từ văn bản."""
from __future__ import annotations
import re
from typing import Any, Dict, List, Set
from core.feature_extractor import norm


CONDITIONAL_PATTERNS = [
    r"neu\s+(.+?)\s+thi\s+(.+)",
    r"khi\s+(.+?)\s+thi\s+(.+)",
    r"moi khi\s+(.+?)\s+thi\s+(.+)",
    r"luc\s+(.+?)\s+thi\s+(.+)",
]


SYNDROME_RULES = [
    {
        "name": "Hội chứng nhiễm trùng",
        "required_features": ["fever"],
        "optional_features": ["weight_loss"],
        "conclusion": "Có thể có nhiễm trùng; cần đánh giá y khoa.",
        "red_flag": True,
    },
    {
        "name": "Hội chứng đau kiểu rễ thần kinh chi dưới",
        "required_features": ["radicular_leg"],
        "optional_features": ["leg_weakness", "sensory_symptoms", "test_lasegue_test_pos", "test_bragard_test_pos"],
        "conclusion": "Có kiểu hình đau/rối loạn cảm giác lan theo chi dưới; cần khám thần kinh để xác định có thiếu hụt rễ hay không.",
        "red_flag": False,
    },
    {
        "name": "Hội chứng đuôi ngựa",
        "required_features": ["saddle_anesthesia", "bowel_bladder"],
        "optional_features": ["leg_weakness"],
        "conclusion": "NGHI NGỜ HỘI CHỨNG ĐUÔI NGỰA — CẤP CỨU.",
        "red_flag": True,
    },
    {
        "name": "Hội chứng viêm khớp cấp",
        "required_features": ["effusion", "night_pain"],
        "optional_features": ["fever"],
        "conclusion": "Có thể có viêm khớp cấp; cần đánh giá.",
        "red_flag": False,
    },
    {
        "name": "Hội chứng tổn thương dây chằng gối",
        "required_features": ["instability", "swelling_early"],
        "optional_features": ["pop_sound", "mechanism_pivot"],
        "conclusion": "Có thể có tổn thương dây chằng; cần khám chuyên khoa.",
        "red_flag": False,
    },
]


def extract_conditionals(text: str) -> List[Dict[str, str]]:
    t = norm(text)
    results = []
    for pattern in CONDITIONAL_PATTERNS:
        for match in re.finditer(pattern, t):
            results.append({
                "condition": match.group(1).strip(),
                "consequence": match.group(2).strip(),
            })
    return results


def check_syndromes(active_features: Set[str]) -> List[Dict[str, Any]]:
    results = []
    for rule in SYNDROME_RULES:
        required = set(rule["required_features"])
        if required.issubset(active_features):
            optional_matched = [
                f for f in rule["optional_features"] if f in active_features
            ]
            results.append({
                "name": rule["name"],
                "conclusion": rule["conclusion"],
                "red_flag": rule["red_flag"],
                "required_matched": list(required),
                "optional_matched": optional_matched,
            })
    return results


def cross_reason(active_features: Set[str]) -> List[str]:
    inferences = []
    if "swelling_early" in active_features and "instability" in active_features:
        inferences.append(
            "Sưng sớm + mất vững gợi ý tổn thương cấu trúc nội khớp (dây chằng hoặc sụn chêm)."
        )
    if "night_pain" in active_features and "morning_stiffness" in active_features:
        inferences.append(
            "Đau đêm + cứng buổi sáng gợi ý viêm hoặc thoái hóa."
        )
    if "radicular_leg" in active_features and "sitting_aggravation" in active_features:
        inferences.append(
            "Đau lan chân + tăng khi ngồi gợi ý chèn ép rễ hoặc đau mông sâu."
        )
    if "locking" in active_features and "joint_line_tenderness_medial" in active_features:
        inferences.append(
            "Khóa khớp + đau khe khớp trong gợi ý tổn thương sụn chêm trong."
        )
    return inferences


def analyze_logic(text: str, active_features: Set[str]) -> Dict[str, Any]:
    conditionals = extract_conditionals(text)
    syndromes = check_syndromes(active_features)
    cross = cross_reason(active_features)
    has_red = any(s["red_flag"] for s in syndromes)
    return {
        "conditionals": conditionals,
        "syndromes": syndromes,
        "cross_inferences": cross,
        "has_red_flag_syndrome": has_red,
    }