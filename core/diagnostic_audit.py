"""PHCN AI 2.6 - Đối soát chẩn đoán hai chiều."""
from __future__ import annotations
from typing import Any, Dict, List
from core.clinical_engine import analyze_case


def run_bidirectional_audit(
    data: Dict[str, Any],
    base_analysis: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    result = base_analysis or analyze_case(data)
    region = result.get("region", "Chưa xác định")
    detailed = result.get("detailed_hypotheses", [])
    chieu_thuan = [
        h for h in detailed
        if h["dac_trung_ung_ho"] and h["do_tin_cay"] >= 0.30
    ]
    chieu_nguoc = detailed
    mau_thuan: List[str] = []
    raw = result.get("features_extracted", [])
    chua_thuc_hien = result.get("unperformed_tests", [])
    if chua_thuc_hien:
        mau_thuan.append(
            "Các nghiệm pháp chưa thực hiện được giữ ở trạng thái CHƯA CÓ KẾT QUẢ, "
            "không dùng để loại trừ: " + ", ".join(chua_thuc_hien)
        )
    if "radicular_leg" in raw and "no_radiation" in raw:
        mau_thuan.append(
            "Bệnh sử mô tả lan hoặc tê nhưng trường Hướng lan lại ghi không lan hoặc không tê."
        )
    general = result.get("general_reasoning", {}) or {}
    mau_thuan.extend(general.get("contradictions", []))
    red_flags = list(dict.fromkeys(
        result.get("red_flags", []) + general.get("warnings", [])
    ))
    if red_flags:
        ket_luan = "ƯU TIÊN AN TOÀN – chưa đưa ra định hướng phục hồi chức năng thường quy"
    elif mau_thuan:
        ket_luan = "CẦN XÁC MINH – dữ liệu chưa nhất quán hoặc trạng thái nghiệm pháp chưa rõ"
    elif chieu_thuan:
        ket_luan = "CÓ GIẢ THUYẾT ĐỂ ĐỐI CHIẾU – chưa phải chẩn đoán xác định"
    else:
        ket_luan = "CHƯA ĐỦ DỮ LIỆU – chưa hình thành kiểu hình đủ tương hợp"
    return {
        "region": region,
        "overall": ket_luan,
        "forward": chieu_thuan,
        "reverse": chieu_nguoc,
        "contradictions": mau_thuan,
        "unknown_tests": result.get("unperformed_tests", []),
        "red_flags": red_flags,
        "base_hypotheses": result.get("hypotheses", []),
        "syndromes": result.get("syndromes", []),
        "cross_inferences": result.get("cross_inferences", []),
        "limitations": [
            "Đây là đối soát quy tắc có trọng số, không phải mô hình đã được thẩm định trên quần thể bệnh nhân.",
            "Không tính xác suất hậu nghiệm, tỷ số khả năng, độ nhạy hoặc độ đặc hiệu khi chưa có nguồn dữ liệu phù hợp.",
            "Không tìm thấy một dấu hiệu trong ghi chép không có nghĩa là dấu hiệu đó âm tính.",
            "Cần bác sĩ xác minh trực tiếp bệnh sử, kỹ thuật nghiệm pháp, khám thần kinh và chức năng, cận lâm sàng khi có chỉ định.",
        ],
    }


def render_audit_report(result: Dict[str, Any]) -> str:
    def bullets(items):
        return "\n".join("- " + str(x) for x in items) if items else "- Chưa có dữ liệu ghi nhận."

    lines = [
        "PHCN AI 4.1 – ĐỐI SOÁT CHẨN ĐOÁN HAI CHIỀU TỰ ĐỘNG",
        "Vùng khám: " + str(result["region"]),
        "Kết quả kiểm soát: " + str(result["overall"]),
        "",
        "I. CHIỀU THUẬN – GIẢ THUYẾT CÓ DỮ KIỆN GỢI Ý",
    ]
    if result["forward"]:
        for item in result["forward"]:
            lines.append("")
            lines.append(
                "- " + item["label"]
                + " (Điểm định hướng heuristic: " + f"{item['do_tin_cay'] * 100:.0f}/100"
                + " – " + item["muc_tin_cay"] + ")"
            )
            lines.append(
                "  Dữ kiện gợi ý: "
                + ("; ".join(item["dac_trung_ung_ho"]) or "Chưa ghi nhận")
            )
            lines.append(
                "  Điểm chưa tương hợp: "
                + ("; ".join(item["dac_trung_chong_lai"]) or "Chưa ghi nhận rõ")
            )
            lines.append(
                "  Dấu hiệu kỳ vọng chưa có: "
                + ("; ".join(item["dac_trung_con_thieu"][:5]) or "Không còn mục chưa xác minh")
            )
    else:
        lines.append("- Chưa có giả thuyết nào có dữ kiện gợi ý đủ để đưa lên chiều thuận.")

    lines.append("")
    lines.append("II. CHIỀU NGƯỢC – KIỂM TRA LẠI TỪNG GIẢ THUYẾT")
    for item in result["reverse"]:
        lines.append("")
        lines.append(
            "- " + item["label"] + ": "
            + f"{item['do_tin_cay'] * 100:.0f}/100"
            + " (" + item["muc_tin_cay"] + ")"
        )
        lines.append(
            "  Ủng hộ: "
            + ("; ".join(item["dac_trung_ung_ho"]) or "Chưa thấy dữ kiện trong ghi chép")
        )
        lines.append(
            "  Chống lại: "
            + ("; ".join(item["dac_trung_chong_lai"]) or "Chưa ghi nhận dữ kiện chống lại rõ ràng")
        )
        lines.append(
            "  Dấu hiệu kỳ vọng chưa có: "
            + ("; ".join(item["dac_trung_con_thieu"][:5]) or "Không còn mục chưa xác minh")
        )
        lines.append("  Ghi chú chuyên môn: " + item["luu_y"])

    if result.get("syndromes"):
        lines.append("")
        lines.append("III. HỘI CHỨNG PHÁT HIỆN")
        for syn in result["syndromes"]:
            prefix = "CẢNH BÁO: " if syn["co_nguy_hiem"] else ""
            lines.append(f"- {prefix}{syn['ten']}: {syn['ket_luan']}")

    if result.get("cross_inferences"):
        lines.append("")
        lines.append("IV. SUY LUẬN BẮC CẦU")
        for inf in result["cross_inferences"]:
            lines.append(f"- {inf}")

    lines.extend([
        "",
        "V. MÂU THUẪN VÀ GIỚI HẠN DỮ LIỆU",
        bullets(result["contradictions"]),
        "",
        "VI. GIỚI HẠN VÀ AN TOÀN",
        bullets(result["limitations"]),
        "",
        "Lưu ý: Điểm định hướng là heuristic chưa hiệu chuẩn, không phải xác suất mắc bệnh, độ nhạy hoặc độ đặc hiệu.",
        "Kết luận: Báo cáo chỉ hỗ trợ đối chiếu lâm sàng, không xác lập chẩn đoán và không thay thế khám trực tiếp.",
    ])
    return "\n".join(lines)