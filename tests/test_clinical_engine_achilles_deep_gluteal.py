from core.clinical_engine import analyze_case


def test_achilles_tendinopathy_pattern_is_recognized():
    case = {
        "region": "Cổ chân – bàn chân",
        "reason": "Đau gân gót trái khi chạy và nhón gót",
        "history": "Đau thân gân Achilles trái 3 tuần; đau khi nhón gót, chạy, leo cầu thang; cứng đau bước đầu buổi sáng và sau ngồi lâu.",
        "site": "Thân gân Achilles trái cách điểm bám 3-4 cm",
        "onset": "Tăng đột ngột cự ly chạy và chạy dốc",
        "character": "Đau khi chịu tải",
        "radiation": "Không lan",
        "associations": "Không tê",
        "course": "Đỡ sau khởi động hoặc nghỉ",
        "inspection": "Dày gân hình thoi đoạn giữa, không đỏ/bầm",
        "palpation": "Gân ấm nhẹ",
        "rom_mmt": "DF 10 độ gối duỗi; PF 40 độ; tam đầu cẳng chân 4/5 do đau",
        "tests": {
            "Thompson Test": "Âm tính (-)",
            "Royal London Hospital Test": "Dương tính (+)",
            "Painful Arc Sign": "Dương tính (+)",
            "Single-Leg Heel Raise": "Chưa thực hiện",
        },
        "red_flags": {},
    }
    result = analyze_case(case)
    assert any("Achilles tendinopathy" in h for h in result["hypotheses"])
    assert any("gân Achilles" in s for s in result["supporting"])
    assert any("Thompson âm tính" in s for s in result["opposing"])
    assert any("nhón gót một chân" in u for u in result["unresolved"])
    assert not any("tổn thương gân cấp" in c for c in result["safety"])


def test_deep_gluteal_pattern_is_recognized_without_confirming_piriformis():
    case = {
        "region": "Thần kinh & Khác",
        "reason": "Đau sâu giữa mông phải khi ngồi lâu",
        "history": "Đau mông phải 1 tháng; tăng khi ngồi lâu trên ghế cứng hoặc lái xe; lan mặt sau đùi đến khoeo, đôi khi mặt sau bắp chân; tê châm chích khi ngồi lâu.",
        "site": "Đau sâu vùng mông phải",
        "onset": "Xuất hiện sau đợt ngồi lâu",
        "character": "Âm ỉ, nhói, nóng rát",
        "radiation": "Lan mặt sau đùi đến khoeo",
        "associations": "Tê châm chích mặt sau đùi",
        "course": "Giảm khi đi lại hoặc nằm nghiêng",
        "inspection": "Dáng đi bình thường",
        "palpation": "Ấn sâu vùng giữa PSIS và mấu chuyển lớn tái hiện triệu chứng",
        "rom_mmt": "Xoay trong háng phải hạn chế và đau",
        "tests": {
            "FAIR Test": "Dương tính (+)",
            "Pace Test": "Dương tính (+)",
            "Freiberg Test": "Dương tính (+)",
            "Straight Leg Raise (SLR)": "Âm tính (-)",
        },
        "red_flags": {},
    }
    result = analyze_case(case)
    assert any("deep gluteal pain syndrome" in h for h in result["hypotheses"])
    assert any("FAIR" in s for s in result["supporting"])
    assert any("SLR âm tính" in s for s in result["opposing"])
    assert any("L5/S1" in u for u in result["unresolved"])
    assert not any("đánh giá y khoa trực tiếp" in c for c in result["safety"])
