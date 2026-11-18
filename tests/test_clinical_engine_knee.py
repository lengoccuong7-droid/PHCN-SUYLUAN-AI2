from core.clinical_engine import analyze_case, _test_state


def base_case():
    return {
        "region": "Khớp gối", "reason": "Đau gối trái sau chấn thương khi chơi bóng đá",
        "history": "Xoay vặn gối trên chân trụ cố định, nghe tiếng rắc nhẹ. Sưng sau 4 giờ. Cảm giác lỏng khớp khi xuống dốc.",
        "site": "Đau khe khớp trong và mặt trước dưới xương bánh chè",
        "onset": "Xoay vặn khi chuyển hướng", "character": "Đau nhói khi xoay và chịu lực",
        "radiation": "Không lan", "associations": "Sưng vừa, bập bềnh xương bánh chè (+)",
        "course": "Đau tăng khi gấp sâu, ngồi xổm và leo cầu thang",
        "nrs": 7, "inspection": "Sưng vừa, mất hõm tự nhiên",
        "palpation": "Ấn đau khe khớp trong và điểm bám MCL",
        "rom_mmt": "ROM trái 0–95°, phải 0–135°. MMT tứ đầu và hamstring 4/5.",
        "tests": {
            "Lachman Test": "Dương tính (+)",
            "McMurray Test": "Chưa thực hiện",
            "Anterior Drawer Test": "Dương tính (+)",
            "Appley Compression Test": "Chưa thực hiện",
        },
        "red_flags": {},
    }


def test_knee_case_integrates_acl_meniscus_and_mcl_clues():
    result = analyze_case(base_case())
    joined = " ".join(result["hypotheses"])
    assert "ACL" in joined
    assert any("sụn chêm" in item for item in result["hypotheses"])
    assert any("MCL" in item for item in result["hypotheses"])
    assert "Lachman Test" in result["positive_tests"]
    assert "Anterior Drawer Test" in result["positive_tests"]
    assert "McMurray Test" in result["unperformed_tests"]
    assert not any("McMurray được ghi dương tính" in item for item in result["supporting"])
    assert any("ROM gối hạn chế" in item for item in result["supporting"])
    assert any("sức cơ" in item.lower() for item in result["supporting"])


def test_combined_test_state_is_not_misread_as_negative():
    result = _test_state({"McMurray": "Chưa làm / Âm tính"})
    assert result["negative"] == []
    assert result["unperformed"] == ["McMurray"]


def test_negative_lachman_is_reported_as_opposing_not_absolute_exclusion():
    case = base_case()
    case["tests"]["Lachman Test"] = "Âm tính (-)"
    result = analyze_case(case)
    assert any("Lachman được ghi âm tính" in item for item in result["opposing"])
    assert not any("đứt ACL" in item.lower() for item in result["hypotheses"])


def test_empty_knee_case_does_not_invent_positive_findings():
    result = analyze_case({"region": "Khớp gối", "tests": {}})
    assert result["positive_tests"] == []
    assert result["supporting"] == []
    assert result["confidence"].startswith("Mức định hướng: thấp")


def test_no_evidence_does_not_generate_midpoint_hypotheses():
    result = analyze_case({"region": "Khớp gối", "tests": {}})
    assert result["hypotheses"] == []
    assert all(item["do_tin_cay"] == 0.0 for item in result["detailed_hypotheses"])
