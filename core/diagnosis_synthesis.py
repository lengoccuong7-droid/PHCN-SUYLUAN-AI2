"""PHCN AI 4.5 – tổng hợp chẩn đoán sơ bộ có giải thích.

This layer ranks existing rule-engine hypotheses; it does not create a diagnosis
from absent evidence and never interprets heuristic scores as disease probability.
"""
from __future__ import annotations
from typing import Any, Dict, List


def _unique(items: List[str]) -> List[str]:
    return list(dict.fromkeys(str(x) for x in items if str(x).strip()))


def _group_evidence(items: List[str]) -> List[str]:
    """Avoid presenting closely related nerve-tension tests as independent evidence."""
    out: List[str] = []
    nerve_terms = ("Lasègue", "Lasegue", "nâng chân thẳng", "SLR", "Bragard")
    nerve_hits = [x for x in items if any(t.lower() in x.lower() for t in nerve_terms)]
    out.extend(x for x in items if x not in nerve_hits)
    if nerve_hits:
        out.append(
            "Cụm nghiệm pháp căng thần kinh có kết quả dương tính: "
            + "; ".join(_unique(nerve_hits))
            + ". Các nghiệm pháp có liên quan về cơ chế, không xem là bằng chứng độc lập hoàn toàn."
        )
    return _unique(out)


def synthesize_diagnosis(result: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    hypotheses = [h for h in result.get("detailed_hypotheses", []) if h.get("do_tin_cay", 0) >= 0.30]
    hypotheses.sort(key=lambda h: h.get("do_tin_cay", 0), reverse=True)
    narrative = result.get("narrative_analysis", {}) or {}
    general = result.get("general_reasoning", {}) or {}
    contradictions = _unique(
        list(narrative.get("contradictions", []))
        + list(general.get("contradictions", []))
    )
    gaps = _unique(list(result.get("unresolved", [])) + list(result.get("missing", [])))
    red_flags = _unique(list(result.get("red_flags", [])))

    if not hypotheses:
        return {
            "status": "insufficient_data",
            "primary": None,
            "differentials": [],
            "supporting": _group_evidence(result.get("supporting", [])),
            "opposing": contradictions,
            "gaps": gaps,
            "red_flags": red_flags,
            "summary": "Chưa có giả thuyết chuyên biệt đạt ngưỡng dữ kiện tối thiểu. Cần bổ sung bệnh sử và khám trước khi tổng hợp chẩn đoán sơ bộ.",
            "laterality": narrative.get("laterality", "chưa xác định"),
            "limitations": ["Điểm thuật toán chỉ dùng xếp thứ tự giả thuyết, không phải xác suất mắc bệnh."],
        }

    primary = hypotheses[0]
    primary_support = _group_evidence(primary.get("dac_trung_ung_ho", []))
    primary_opposing = _unique(primary.get("dac_trung_chong_lai", []) + contradictions)
    differentials = []
    for h in hypotheses[1:4]:
        differentials.append({
            "label": h.get("label", "Giả thuyết chưa đặt tên"),
            "supporting": _group_evidence(h.get("dac_trung_ung_ho", [])),
            "opposing": _unique(h.get("dac_trung_chong_lai", [])),
            "score": h.get("do_tin_cay", 0),
            "caution": h.get("luu_y", ""),
        })

    laterality = narrative.get("laterality", "chưa xác định")
    if "hai bên hoặc" in laterality:
        laterality_note = "Có dấu hiệu trái/phải trong các trường được phân tích; cần phân biệt bên triệu chứng với bên đối chiếu khi khám."
    elif laterality in ("trái", "phải", "hai bên"):
        laterality_note = f"Dữ kiện văn bản ghi nhận bên {laterality}; cần đối chiếu bản đồ triệu chứng và khám hai bên."
    else:
        laterality_note = "Chưa xác định bên ưu thế."

    caution = primary.get("luu_y", "")
    missing_signs = primary.get("dac_trung_con_thieu", [])
    if red_flags:
        summary = "Có dữ kiện cảnh báo an toàn; ưu tiên đánh giá y khoa trực tiếp. Không dùng kết quả này để lập kế hoạch PHCN thường quy trước khi làm rõ nguy cơ."
        status = "safety_review_required"
    elif primary.get("do_tin_cay", 0) >= 0.75 and primary.get("co_dau_hieu_vang", False):
        summary = "Giả thuyết ưu tiên có mức hỗ trợ thuật toán cao trong phạm vi bộ quy tắc; vẫn cần xác minh bằng khám trực tiếp và loại trừ chẩn đoán phân biệt."
        status = "provisional_supported"
    else:
        summary = "Có hướng chẩn đoán sơ bộ ưu tiên nhưng dữ kiện còn thiếu hoặc chưa đạt tiêu chí xác nhận; cần khám bổ sung và đối chiếu chẩn đoán phân biệt."
        status = "provisional_needs_verification"

    return {
        "status": status,
        "primary": {
            "label": primary.get("label"),
            "algorithmic_score": primary.get("do_tin_cay", 0),
            "supporting": primary_support,
            "opposing": primary_opposing,
            "missing_expected": list(missing_signs),
            "caution": caution,
        },
        "differentials": differentials,
        "supporting": primary_support,
        "opposing": primary_opposing,
        "gaps": gaps,
        "red_flags": red_flags,
        "laterality": laterality,
        "laterality_note": laterality_note,
        "summary": summary,
        "limitations": [
            "Điểm định hướng là điểm thuật toán, không phải xác suất mắc bệnh.",
            "Không có dữ kiện không đồng nghĩa dấu hiệu âm tính.",
            "Nghiệm pháp căng thần kinh có liên quan về cơ chế, không được cộng như bằng chứng độc lập hoàn toàn.",
            "Không suy ra tầng đĩa đệm, rễ thần kinh hoặc tổn thương cấu trúc nếu chưa có dữ kiện định khu phù hợp.",
        ],
    }
