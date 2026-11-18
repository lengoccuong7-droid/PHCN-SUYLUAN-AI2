"""PHCN AI 4.5 - Bộ máy suy luận lâm sàng nhiều vòng."""
from __future__ import annotations
import re
import unicodedata
from typing import Dict, List, Any
from core.inference_engine import infer as _infer
from core.general_reasoning_engine import reason_case as _reason_case
from core.semantic_clinical_parser import parse_narrative
from core.diagnosis_synthesis import synthesize_diagnosis


def norm(s: Any) -> str:
    s = str(s or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    return re.sub(r"\s+", " ", s)


def has(text: str, *terms: str) -> bool:
    t = norm(text)
    return any(norm(x) in t for x in terms)


def affirmed(text: str, *terms: str) -> bool:
    t = norm(text)
    for term in terms:
        term_n = norm(term)
        start = 0
        while True:
            idx = t.find(term_n, start)
            if idx < 0:
                break
            prefix = t[max(0, idx - 24):idx]
            if not re.search(
                r"\b(khong|khong co|khong nghe|khong lom|phu nhan|khong ghi nhan|khong thay)\s*$",
                prefix,
            ):
                return True
            start = idx + len(term_n)
    return False


def _test_state(results: Dict[str, str]) -> Dict[str, List[str]]:
    positive, negative, unperformed = [], [], []
    for name, value in (results or {}).items():
        value_n = norm(value)
        if "chua lam" in value_n or "chua thuc hien" in value_n:
            unperformed.append(name)
        elif "duong tinh" in value_n:
            positive.append(name)
        elif "am tinh" in value_n:
            negative.append(name)
        else:
            unperformed.append(name)
    return {
        "positive": positive,
        "negative": negative,
        "unperformed": unperformed,
        "unknown": unperformed,
    }


def analyze_case(data: Dict[str, Any]) -> Dict[str, Any]:
    result = _infer(data)
    # PHCN AI 4.1: parse arbitrary free-text narrative into transparent evidence.
    narrative_analysis = parse_narrative(data)
    result["narrative_analysis"] = narrative_analysis
    # Cross-check key extracted facts against the original structured input.
    feature_set = set(result.get("features_extracted", []))
    tests = data.get("tests") or {}
    test_state = _test_state(tests)
    audit_issues = []
    if set(test_state["positive"]) & set(test_state["negative"]):
        audit_issues.append("Một nghiệm pháp đang có đồng thời trạng thái dương tính và âm tính.")
    if any("lasegue" in norm(k) or "lasègue" in norm(k) for k in tests) and test_state["positive"] and not any("lasegue" in norm(k) or "lasègue" in norm(k) for k in test_state["positive"]):
        audit_issues.append("Cần kiểm tra lại chuẩn hóa trạng thái nghiệm pháp Lasègue.")
    if "ehl" in norm(data.get("rom_mmt", "")) and re.search(r"4\s*/\s*5", str(data.get("rom_mmt", ""))) and "ehl_weakness" not in feature_set:
        audit_issues.append("Có ghi EHL 4/5 nhưng bộ trích xuất chưa tạo đặc trưng giảm sức cơ EHL.")
    if re.search(r"phan xa gan got[^.;\n]{0,80}(?:1\s*\+|giam)", norm(data.get("rom_mmt", ""))) and "reduced_ankle_reflex" not in feature_set:
        audit_issues.append("Có ghi phản xạ gân gót giảm nhưng bộ trích xuất chưa nhận diện được.")
    result["data_quality_audit"] = {
        "status": "Cần rà soát" if audit_issues else "Không phát hiện lỗi nhất quán tự động trong các trường đã kiểm tra",
        "issues": list(dict.fromkeys(audit_issues)),
        "positive_tests": test_state["positive"],
        "negative_tests": test_state["negative"],
        "unperformed_tests": test_state["unperformed"],
        "note": "Đối soát tự động chỉ kiểm tra một số lỗi cấu trúc có thể nhận diện; không bảo đảm bệnh án đầy đủ hoặc chính xác.",
    }
    result["diagnosis_synthesis"] = synthesize_diagnosis(result, data)
    # PHCN AI 3.0-dev2 general reasoning is integrated as a complementary layer.
    # It does not overwrite region-specific Deepseek findings.
    general = _reason_case(data, {
        "hypotheses": result.get("hypotheses", []),
        "red_flags": result.get("red_flags", []),
    })
    result["general_reasoning"] = general
    bridge_opposing = list(general.get("contradictions", []))
    bridge_opposing.extend(narrative_analysis.get("contradictions", []))
    bridge_unresolved = list(general.get("information_gaps", []))
    # Normalize common test aliases across the two source engines.
    test_items = data.get("tests") or {}
    for test_name, raw_state in test_items.items():
        test_n = norm(test_name).replace("-", " ").replace("–", " ")
        state_n = norm(raw_state)
        if ("straight leg raise" in test_n or test_n == "slr") and "am tinh" in state_n and "chua" not in state_n:
            bridge_opposing.append("SLR âm tính: làm giảm hỗ trợ cho một số kiểu kích thích thần kinh khi nâng chân thẳng, nhưng không loại trừ bệnh lý rễ hoặc đau mông sâu.")
        if ("single leg heel raise" in test_n or "nhon got mot chan" in test_n) and ("chua" in state_n or not state_n):
            bridge_unresolved.append("Cần đánh giá nhón gót một chân để ghi nhận khả năng chịu tải và sức bền cơ gấp gan chân.")
    # Record explicit side-to-side knee ROM limitation as an observed finding only.
    rom_text = str(data.get("rom_mmt", "") or "")
    if data.get("region") == "Khớp gối" and rom_text.strip():
        rom_n = norm(rom_text)
        has_rom_measure = bool(re.search(r"\brom\b|do|degree|goc", rom_n))
        has_limitation = any(x in rom_n for x in ["han che", "gioi han", "95 do", "90 do", "rom trai 0"])
        has_reduced_arc = bool(re.search(r"0\s*[–—-]\s*(?:9[0-9]|100)\s*(?:do|°)", rom_text.lower()))
        if has_rom_measure and (has_limitation or has_reduced_arc):
            result["supporting"] = list(dict.fromkeys(result.get("supporting", []) + ["ROM gối hạn chế được ghi nhận; cần đối chiếu bên lành, đau và điều kiện đo."]))
        if re.search(r"\b[0-5]\s*/\s*5\b", rom_text, flags=re.IGNORECASE) or "suc co" in rom_n:
            result["supporting"] = list(dict.fromkeys(result.get("supporting", []) + ["Đã ghi nhận sức cơ; cần đối chiếu nhóm cơ, bên đo và điều kiện gây đau."]))
    if data.get("region") == "Thần kinh & Khác" and any(
        "fair" in norm(k) and "duong tinh" in norm(v) for k, v in test_items.items()
    ):
        bridge_unresolved.append("Cần khám thần kinh theo rễ L5/S1 để phân biệt đau mông sâu với bệnh lý rễ thần kinh.")
    result["opposing"] = list(dict.fromkeys(
        result.get("opposing", []) + bridge_opposing
    ))
    result["unresolved"] = list(dict.fromkeys(
        result.get("unresolved", []) + bridge_unresolved
    ))
    result["red_flags"] = list(dict.fromkeys(
        result.get("red_flags", []) + general.get("warnings", []) + narrative_analysis.get("safety_cues", [])
    ))
    if general.get("warnings"):
        result["confidence"] = general.get("certainty", result.get("confidence", ""))
    result["diagnosis_synthesis"] = synthesize_diagnosis(result, data)
    return result


def render_report(result: Dict[str, Any]) -> str:
    def bullets(items):
        return "\n".join("- " + str(x) for x in items) if items else "- Chưa có dữ liệu đủ để nhận định."

    lines = [
        "PHCN AI 4.5 – BÁO CÁO HỖ TRỢ SUY LUẬN LÂM SÀNG NHIỀU VÒNG",
        "Nền tảng NLP và suy luận offline nhiều vòng; phiên bản 4.5 tăng cường kiểm tra tính nhất quán dữ liệu lâm sàng.",
        "Vùng khám: " + str(result.get("region", "")),
        "Diễn tiến: " + str(result.get("temporal_state_vi", "chưa rõ")),
        "Vòng phân tích: " + str(result.get("analysis_round", 1)),
        "",
        "I. GIẢ THUYẾT VÀ ĐỊNH HƯỚNG CẦN KIỂM CHỨNG",
    ]
    detailed = result.get("detailed_hypotheses", [])
    if detailed:
        for h in detailed:
            if h["do_tin_cay"] < 0.30:
                continue
            lines.append("")
            lines.append("### " + h["label"])
            lines.append(
                "Điểm định hướng thuật toán (không phải xác suất mắc bệnh): "
                + f"{h['do_tin_cay'] * 100:.0f}/100"
                + " (" + h["muc_tin_cay"] + ")"
                + " | Điểm thô: " + str(h["diem_tho"])
            )
            if h["dac_trung_ung_ho"]:
                lines.append("**Dữ kiện ủng hộ:**")
                for s in h["dac_trung_ung_ho"]:
                    lines.append("  - " + s)
            if h["dac_trung_chong_lai"]:
                lines.append("**Dữ kiện chống lại:**")
                for o in h["dac_trung_chong_lai"]:
                    lines.append("  - " + o)
            if h["dac_trung_con_thieu"]:
                lines.append(
                    "**Dấu hiệu kỳ vọng chưa có (" + str(len(h["dac_trung_con_thieu"])) + "):**"
                )
                for m in h["dac_trung_con_thieu"][:5]:
                    lines.append("  - " + m)
            if not h["co_dau_hieu_vang"] and h["dau_hieu_vang_can_co"]:
                lines.append("Lưu ý: thiếu dấu hiệu vàng — không thể kết luận chắc chắn.")
            lines.append("*Ghi chú chuyên môn:* " + h["luu_y"])
    else:
        lines.append("- Chưa có giả thuyết nào đủ dữ kiện.")

    synthesis = result.get("diagnosis_synthesis", {})
    if synthesis:
        lines.extend(["", "I-A. TỔNG HỢP CHẨN ĐOÁN SƠ BỘ"])
        primary = synthesis.get("primary")
        if primary:
            lines.append("- Chẩn đoán/hội chứng ưu tiên cần kiểm chứng: " + str(primary.get("label", "")))
            lines.append("- Điểm định hướng thuật toán: " + str(round(float(primary.get("algorithmic_score", 0)) * 100)) + "/100 (không phải xác suất mắc bệnh).")
            lines.append("- Bên triệu chứng: " + str(synthesis.get("laterality_note", "Chưa xác định.")))
            lines.append("- Bằng chứng tổng hợp ủng hộ:")
            lines.extend("  - " + x for x in (primary.get("supporting") or ["Chưa ghi nhận đủ."]))
            lines.append("- Bằng chứng chống lại/mâu thuẫn:")
            lines.extend("  - " + x for x in (primary.get("opposing") or ["Chưa ghi nhận rõ; không đồng nghĩa đã loại trừ."]))
            lines.append("- Dấu hiệu kỳ vọng chưa có thông tin:")
            lines.extend("  - " + x for x in (primary.get("missing_expected") or ["Chưa xác định thêm."]))
            if primary.get("caution"):
                lines.append("- Lưu ý: " + str(primary["caution"]))
        else:
            lines.append("- " + str(synthesis.get("summary", "Chưa đủ dữ liệu để tổng hợp.")))
        if synthesis.get("differentials"):
            lines.append("- Chẩn đoán phân biệt cần xem xét:")
            for item in synthesis["differentials"]:
                lines.append("  - " + str(item["label"]) + ": " + ("; ".join(item.get("supporting", [])) or "chưa có bằng chứng đặc hiệu"))
        lines.append("- Kết luận tổng hợp: " + str(synthesis.get("summary", "")))
        lines.append("- Giới hạn:")
        lines.extend("  - " + x for x in synthesis.get("limitations", []))

    narrative = result.get("narrative_analysis", {})
    if narrative:
        lines.extend(["", "II. PHÂN TÍCH BỆNH SỬ TỰ DO – NLP OFFLINE"])
        lines.append("- Nguồn văn bản: " + (", ".join(narrative.get("input_sources", [])) or "Chưa có"))
        lines.append("- Vị trí giải phẫu nhận diện: " + (", ".join(narrative.get("anatomical_locations", [])) or "Chưa nhận diện rõ"))
        lines.append("- Bên: " + str(narrative.get("laterality", "chưa xác định")))
        lines.append("- Kiểu diễn tiến nhận diện từ bệnh sử: " + (", ".join(narrative.get("timeline_patterns", [])) or "Chưa đủ dữ kiện"))
        lines.append("- Thời lượng được ghi: " + (", ".join(narrative.get("explicit_durations", [])) or "Chưa ghi rõ"))
        lines.append("- Yếu tố tăng triệu chứng: " + (", ".join(narrative.get("aggravating_factors", [])) or "Chưa nhận diện"))
        lines.append("- Yếu tố giảm triệu chứng: " + (", ".join(narrative.get("relieving_factors", [])) or "Chưa nhận diện"))
        if narrative.get("symptoms"):
            lines.append("- Triệu chứng và trạng thái:")
            for item in narrative["symptoms"]:
                lines.append("  - " + item["symptom"] + ": " + item["state"])
        if narrative.get("causal_chains"):
            lines.append("- Chuỗi sự kiện/quan hệ được thuật lại (chưa chứng minh nhân quả):")
            for chain in narrative["causal_chains"]:
                lines.append("  - Bối cảnh/yếu tố: " + chain["reported_trigger_or_context"] + " → Kết quả được thuật lại: " + chain["reported_outcome"])
                lines.append("    " + chain["interpretation"])
        if narrative.get("reported_relations"):
            lines.append("- Quan hệ được mô tả:")
            for rel in narrative["reported_relations"]:
                lines.append("  - " + rel["type"] + ": " + rel["text"] + " (" + rel["interpretation"] + ")")
        if narrative.get("contradictions"):
            lines.append("- Mâu thuẫn cần xác minh:")
            lines.extend("  - " + x for x in narrative["contradictions"])
        lines.append("- Giới hạn: đây là trích xuất ngôn ngữ theo quy tắc offline, không phải hiểu ngôn ngữ tự do hoàn hảo.")

    if result.get("syndromes"):
        lines.append("")
        lines.append("III. HỘI CHỨNG ĐƯỢC KÍCH HOẠT")
        for syn in result["syndromes"]:
            # Keep compatibility with the actual logic_reasoner schema.
            is_red = bool(syn.get("red_flag", syn.get("co_nguy_hiem", False)))
            name = syn.get("name", syn.get("ten", "Hội chứng chưa đặt tên"))
            conclusion = syn.get("conclusion", syn.get("ket_luan", "Cần đánh giá thêm."))
            matched = syn.get("required_matched", syn.get("dac_trung_khop", []))
            optional = syn.get("optional_matched", [])
            prefix = "CẢNH BÁO: " if is_red else ""
            lines.append(f"- {prefix}{name}: {conclusion}")
            lines.append(f"  Đặc trưng khớp: {', '.join(matched + optional)}")

    if result.get("cross_inferences"):
        lines.append("")
        lines.append("IV. SUY LUẬN BẮC CẦU")
        for inf in result["cross_inferences"]:
            lines.append(f"- {inf}")

    if result.get("conditionals"):
        lines.append("")
        lines.append("V. MỆNH ĐỀ ĐIỀU KIỆN ĐÃ NHẬN DIỆN")
        for cond in result["conditionals"]:
            lines.append(f"- Nếu {cond['condition']} thì {cond['consequence']}")

    lines.append("")
    audit = result.get("data_quality_audit", {})
    if audit:
        lines.extend(["", "VI-A. ĐỐI SOÁT TÍNH NHẤT QUÁN DỮ LIỆU"])
        lines.append("- Trạng thái: " + str(audit.get("status", "Chưa chạy")))
        if audit.get("issues"):
            lines.extend("  - " + str(x) for x in audit["issues"])
        else:
            lines.append("- Không phát hiện lỗi cấu trúc trong các mục tự động đối soát.")
        lines.append("- " + str(audit.get("note", "")))

    lines.append("VI. ĐẶC TRƯNG ĐÃ TRÍCH XUẤT")
    feats = result.get("features_extracted", [])
    lines.append("- Tổng số: " + str(len(feats)))
    for f in feats[:25]:
        lines.append("  - " + f)
    if len(feats) > 25:
        lines.append("  ... và " + str(len(feats) - 25) + " đặc trưng khác")

    cross = result.get("cross_region_findings", [])
    if cross:
        lines.append("")
        lines.append("VII. SUY LUẬN LIÊN VÙNG")
        lines.append(bullets(cross))

    general = result.get("general_reasoning", {})
    if general:
        lines.extend([
            "",
            "VIII. SUY LUẬN TỔNG QUÁT KẾ THỪA PHCN AI 3.0-dev2",
            "- Mức chắc chắn: " + str(general.get("certainty", "Chưa xác định")),
        ])
        for item in general.get("mechanism_hypotheses", []):
            lines.append("- Nhóm cơ chế: " + str(item.get("label", "")) + " — " + str(item.get("rationale", "")))
        for item in general.get("clinical_patterns", []):
            lines.append("- Kiểu hình: " + str(item.get("label", "")) + " — " + str(item.get("interpretation", "")))
        lines.extend(["- Thông tin cần bổ sung:"] + ["  - " + str(x) for x in general.get("information_gaps", [])])

    lines.extend([
        "",
        "IX. DỮ KIỆN ỦNG HỘ TỔNG HỢP",
        bullets(result.get("supporting", [])),
        "",
        "X. DỮ KIỆN CHỐNG LẠI HOẶC MÂU THUẪN",
        bullets(result.get("opposing", [])),
        "",
        "XI. DỮ LIỆU CHƯA RÕ HOẶC CẦN BỔ SUNG",
        bullets(result.get("unresolved", [])),
        "",
        "XII. DỮ LIỆU CÒN THIẾU",
        bullets(result.get("missing", [])),
        "",
        "XIII. CẢNH BÁO AN TOÀN",
        bullets(result.get("red_flags", []) + result.get("safety", [])),
        "",
        "XIV. MỨC ĐỘ TIN CẬY",
        "- " + str(result.get("confidence", "")),
        "",
        "XV. KẾT LUẬN SỬ DỤNG",
        "- Đây là hỗ trợ tổng hợp dữ liệu, không phải chẩn đoán xác định. "
        "Bác sĩ cần đối chiếu khám trực tiếp, bệnh sử đầy đủ, cận lâm sàng khi có chỉ định "
        "và hướng dẫn chuyên môn hiện hành.",
    ])
    supplemental = str(result.get("supplemental_text", "") or "").strip()
    if supplemental:
        lines.extend(["", "VIII. THÔNG TIN BỔ SUNG DO BÁC SĨ NHẬP", supplemental])
    lines.extend([
        "",
        "QUYỀN QUYẾT ĐỊNH CHUYÊN MÔN: Báo cáo chỉ hỗ trợ suy luận. Bác sĩ trực tiếp khám chịu trách nhiệm đánh giá, chấp nhận, điều chỉnh hoặc bác bỏ định hướng.",
    ])
    return "\n".join(lines)