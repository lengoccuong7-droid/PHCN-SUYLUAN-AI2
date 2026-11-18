"""Regression case: unilateral lumbar radicular presentation on chronic background."""
from core.clinical_engine import analyze_case, render_report


def sample_case():
    return {
        "region": "Cột sống thắt lưng",
        "reason": "Đau thắt lưng trái lan xuống chân trái sau khi bê vật nặng",
        "history": "Tài xế lái xe đường dài 12 năm. Đau thắt lưng mạn tính 3 năm. Không chấn thương trực tiếp vùng lưng; không bệnh lý ác tính hay lao.",
        "free_text": "",
        "site": "Đau vùng cột sống thắt lưng thấp L4-L5, L5-S1 lệch trái.",
        "onset": "Đau bùng phát dữ dội cách đây 5 ngày ngay sau khi cúi người bê thùng hàng nặng khoảng 25kg từ cốp xe xuống.",
        "character": "Đau nhói buốt như điện giật dọc đường đi dây thần kinh, kèm căng tức, co rút cơ vùng thắt lưng.",
        "radiation": "Đau lan từ thắt lưng trái xuống mông trái, mặt sau ngoài đùi trái, mặt ngoài cẳng chân trái, mu bàn chân và ngón cái chân trái.",
        "associations": "Tê bì, kiến bò vùng cẳng chân và mu bàn chân trái; hơi yếu khi nhấc mũi bàn chân trái. Không sốt, không sụt cân bất thường, đại tiểu tiện tự chủ.",
        "course": "Đau tăng khi ngồi lái xe, cúi gập người, ho hoặc hắt hơi; giảm khi nằm ngửa và kê gối dưới khoeo chân. NRS 8/10.",
        "inspection": "Dáng đi khập khiễng né đau, thân hơi nghiêng phải; mất ưỡn thắt lưng; không sưng nề.",
        "palpation": "Co cứng cơ cạnh sống; ấn đau L4-L5, L5-S1 trái; đau điểm Valleix mông và mặt sau đùi trái.",
        "rom_mmt": "ROM gập 35°, duỗi 10°, Schober 10/12 cm. Cơ duỗi ngón cái dài (EHL - rễ L5) chân trái 4/5 so với bên phải 5/5. Phản xạ gân gót S1 trái 1+ so với phải 2+.",
        "tests": {
            "Lasègue Test": "Dương tính ở 40°",
            "Lasègue chéo": "Dương tính",
            "Bragard Test": "Dương tính",
            "SLR Test": "Dương tính",
        },
        "red_flags": {
            "Rối loạn cơ tròn hoặc nghi hội chứng đuôi ngựa": False,
            "Tiền sử ung thư hoặc sụt cân nhanh": False,
            "Sốt cao hoặc sưng nóng đỏ đau cấp tính": False,
        },
    }


def test_lumbar_case_recognizes_acute_flare_on_chronic_background_and_left_side():
    result = analyze_case(sample_case())
    assert result["temporal_state"] == "acute_on_chronic"
    assert result["narrative_analysis"]["laterality"] == "trái"
    assert not any("trái" in x and "phải" in x for x in result["narrative_analysis"]["contradictions"])


def test_lumbar_case_recognizes_positive_tests_and_neurological_findings():
    result = analyze_case(sample_case())
    features = set(result["features_extracted"])
    assert "test_lasegue_test_pos" in features
    assert "test_crossed_lasegue_test_pos" in features
    assert "test_bragard_test_pos" in features
    assert "test_slr_test_pos" in features
    assert "ehl_weakness" in features
    assert "reduced_ankle_reflex" in features
    assert "mechanism_fall" not in features
    assert "mechanism_lifting_load" in features


def test_lumbar_radicular_hypothesis_ranks_above_nonspecific_mechanical_pain():
    result = analyze_case(sample_case())
    ordered = [x["key"] for x in result["detailed_hypotheses"] if x["do_tin_cay"] >= 0.30]
    assert ordered[0] == "lumbar_radiculopathy"
    assert not any("đuôi ngựa" in x["label"].lower() for x in result["detailed_hypotheses"] if x["do_tin_cay"] >= 0.30)


def test_report_renders_syndromes_without_schema_error():
    result = analyze_case(sample_case())
    report = render_report(result)
    assert "đợt cấp trên nền mạn tính" in report
    assert "Hội chứng đau kiểu rễ thần kinh chi dưới" in report


def test_lumbar_case_data_audit_catches_no_false_side_or_missed_neuro_fact():
    result = analyze_case(sample_case())
    assert result["data_quality_audit"]["issues"] == []
    assert result["data_quality_audit"]["positive_tests"] == [
        "Lasègue Test", "Lasègue chéo", "Bragard Test", "SLR Test"
    ]


def test_lumbar_case_only_reports_sensory_dermatome_mapping_as_a_missing_neuro_detail():
    result = analyze_case(sample_case())
    gaps = result["general_reasoning"]["information_gaps"]
    assert any("bản đồ cảm giác" in x.lower() for x in gaps)
    assert not any("khám sức cơ, phản xạ" in x.lower() for x in gaps)
