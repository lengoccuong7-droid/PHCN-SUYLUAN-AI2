"""Suy luận giả thuyết từ đặc trưng với trọng số, thời gian, liên vùng."""
from __future__ import annotations
import math
from typing import Dict, Any, List
from core.feature_extractor import extract_features
from core.reasoning_rules import RULES
from core.learning_engine import apply_learned_weights
from core.logic_reasoner import analyze_logic


def _sigmoid(x: float, scale: float = 2.5) -> float:
    try:
        return 1 / (1 + math.exp(-x * scale))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def _muc_tin_cay(do_tin_cay: float, co_dau_hieu_vang: bool) -> str:
    if do_tin_cay >= 0.75 and co_dau_hieu_vang:
        return "Cao"
    if do_tin_cay >= 0.55:
        return "Trung bình"
    if do_tin_cay >= 0.30:
        return "Thấp"
    return "Rất thấp"


def _ten_dien_tien(temporal: str) -> str:
    return {
        "acute": "cấp tính",
        "subacute": "bán cấp",
        "chronic": "mạn tính",
        "unknown": "chưa rõ",
        "acute_on_chronic": "đợt cấp trên nền mạn tính",
    }.get(temporal, "chưa rõ")


def infer(data: Dict[str, Any]) -> Dict[str, Any]:
    apply_learned_weights()
    region = data.get("region", "Chưa xác định")
    feats = extract_features(data, region)
    codes = feats["codes"]
    negated = feats["negated_features"]
    temporal = feats["temporal"]

    full_text = " ".join(str(v) for v in data.values() if isinstance(v, str))
    logic = analyze_logic(full_text, codes)

    detailed: List[Dict[str, Any]] = []
    cross_region_findings: List[str] = []

    for hyp_key, rule in RULES.items():
        if rule["region"] != region:
            continue
        score = 0.0
        supporting, opposing, missing = [], [], []
        triggered_features: List[str] = []
        # Lasègue, SLR and Bragard are related nerve-tension maneuvers.
        # Keep every observed result visible, but cap their combined score so
        # correlated tests are not treated as three independent evidence items.
        nerve_tension_features = {
            "test_lasegue_test_pos", "test_slr_test_pos", "test_bragard_test_pos",
            "test_crossed_lasegue_test_pos"
        }
        nerve_tension_weights: List[float] = []
        for feat, weight, label in rule.get("positive_rules", []):
            if feat in codes:
                if feat in nerve_tension_features:
                    nerve_tension_weights.append(weight)
                else:
                    score += weight
                supporting.append(label)
                triggered_features.append(feat)
            elif feat in negated:
                score -= weight * 0.5
                opposing.append("Phủ định rõ ràng: " + label.lower())
            else:
                missing.append(label)
        if nerve_tension_weights:
            score += max(nerve_tension_weights)
        for feat, weight, label in rule.get("negative_rules", []):
            if feat in codes:
                score += weight
                opposing.append(label)
        if "temporal_modifier" in rule and temporal in rule["temporal_modifier"]:
            adj = rule["temporal_modifier"][temporal]
            score += adj
            supporting.append(
                f"Diễn tiến {_ten_dien_tien(temporal)} (điều chỉnh {adj:+.2f})"
            )
        for src_region, feat, weight in rule.get("cross_region_triggers", []):
            if feat in codes and region != src_region:
                score += weight
                cross_region_findings.append(
                    f"{rule['label']}: cộng {weight} từ đặc trưng '{feat}' (vùng {src_region})"
                )
        # A zero raw score is not evidence. Do not let sigmoid(0)=0.50
        # create a hypothesis when no supporting feature was observed.
        has_positive_evidence = bool(supporting or triggered_features)
        has_cross_evidence = any(
            feat in codes and region != src_region
            for src_region, feat, _weight in rule.get("cross_region_triggers", [])
        )
        if not has_positive_evidence and not has_cross_evidence:
            do_tin_cay = 0.0
        elif score <= 0 and not has_positive_evidence:
            do_tin_cay = 0.05
        else:
            do_tin_cay = _sigmoid(score)
        co_dau_hieu_vang = all(f in codes for f in rule.get("required_features", []))
        if rule.get("required_features") and not co_dau_hieu_vang:
            do_tin_cay = min(do_tin_cay, 0.55)
        co_dau_hieu_nguy_hiem = [
            f for f in rule.get("critical_red_flags", []) if f in codes
        ]
        detailed.append({
            "key": hyp_key,
            "label": rule["label"],
            "do_tin_cay": round(do_tin_cay, 2),
            "muc_tin_cay": _muc_tin_cay(do_tin_cay, co_dau_hieu_vang),
            "diem_tho": round(score, 2),
            "dac_trung_ung_ho": supporting,
            "dac_trung_chong_lai": opposing,
            "dac_trung_con_thieu": missing,
            "co_dau_hieu_vang": co_dau_hieu_vang,
            "dau_hieu_vang_can_co": rule.get("required_features", []),
            "co_dau_hieu_nguy_hiem": co_dau_hieu_nguy_hiem,
            "luu_y": rule["caution"],
            "triggered_features": triggered_features,
        })
    detailed.sort(key=lambda x: x["do_tin_cay"], reverse=True)

    hypotheses_str, all_supporting, all_opposing, all_unresolved, all_red_flags = [], [], [], [], []
    for h in detailed:
        if h["do_tin_cay"] >= 0.30:
            ten = h["label"]
            if not h["co_dau_hieu_vang"] and h["dau_hieu_vang_can_co"]:
                ten += " (thiếu dấu hiệu vàng — cần xác minh)"
            hypotheses_str.append(ten)
        all_supporting.extend(h["dac_trung_ung_ho"])
        all_opposing.extend(h["dac_trung_chong_lai"])
        all_red_flags.extend(h["co_dau_hieu_nguy_hiem"])
        if h["do_tin_cay"] >= 0.30:
            for m in h["dac_trung_con_thieu"][:3]:
                all_unresolved.append(f"{h['label']}: {m}")

    top = detailed[0] if detailed else None
    if all_red_flags or logic["has_red_flag_syndrome"]:
        confidence_str = "Không đưa ra kết luận phục hồi chức năng trước khi đánh giá nguy cơ hoặc cờ đỏ."
    elif top and top["do_tin_cay"] >= 0.75:
        confidence_str = "Mức định hướng: cao; cần xác minh bằng khám trực tiếp."
    elif top and top["do_tin_cay"] >= 0.55:
        confidence_str = "Mức định hướng: trung bình; cần xác minh bằng khám trực tiếp và dữ liệu còn thiếu."
    else:
        confidence_str = "Mức định hướng: thấp; dữ liệu hiện tại chưa đủ để kết luận."

    safety = []
    if all_red_flags or logic["has_red_flag_syndrome"]:
        safety.append(
            "Có dấu hiệu cảnh báo: " + "; ".join(all_red_flags)
            + ". Ưu tiên đánh giá y khoa trực tiếp."
        )
    else:
        safety.append(
            "Chưa ghi nhận cờ đỏ trong các mục hiện có; điều này KHÔNG loại trừ bệnh lý nghiêm trọng."
        )
    safety.append("Không dùng kết quả một nghiệm pháp đơn lẻ để xác nhận hoặc loại trừ chẩn đoán.")
    if "leg_weakness" in codes or "ehl_weakness" in codes:
        safety.append("Có ghi nhận giảm sức cơ chi dưới trong dữ liệu khám; cần xác minh lại MMT theo nhóm cơ, bên và khả năng lặp lại. Nếu là yếu cơ mới xuất hiện hoặc đang tăng, cần đánh giá y khoa trực tiếp sớm; nếu tiến triển nhanh hoặc kèm rối loạn cơ tròn/tê yên ngựa, chuyển cấp cứu.")

    required_fields = [
        ("Lý do khám", "reason"),
        ("Vị trí triệu chứng", "site"),
        ("Diễn tiến", "course"),
        ("Khám thực thể", "inspection"),
        ("Tầm vận động và sức cơ", "rom_mmt"),
    ]
    missing_basic = [
        label for label, key in required_fields
        if not str(data.get(key, "") or "").strip()
    ]
    if not data.get("tests"):
        missing_basic.append("Kết quả nghiệm pháp")

    return {
        "region": region,
        "hypotheses": list(dict.fromkeys(hypotheses_str)),
        "supporting": list(dict.fromkeys(all_supporting)),
        "opposing": list(dict.fromkeys(all_opposing)),
        "unresolved": list(dict.fromkeys(all_unresolved)),
        "missing": missing_basic,
        "red_flags": list(dict.fromkeys(all_red_flags)),
        "confidence": confidence_str,
        "safety": safety,
        "positive_tests": feats["positive_tests"],
        "negative_tests": feats["negative_tests"],
        "unperformed_tests": feats["unperformed_tests"],
        "unknown_tests": feats["unperformed_tests"],
        "summary": str(data.get("reason", "") or "Chưa ghi nhận lý do khám"),
        "detailed_hypotheses": detailed,
        "features_extracted": sorted(codes),
        "temporal_state": temporal,
        "temporal_state_vi": _ten_dien_tien(temporal),
        "cross_region_findings": cross_region_findings,
        "section_matches": feats.get("section_matches", {}),
        "syndromes": logic["syndromes"],
        "cross_inferences": logic["cross_inferences"],
        "conditionals": logic["conditionals"],
        "has_red_flag_syndrome": logic["has_red_flag_syndrome"],
    }