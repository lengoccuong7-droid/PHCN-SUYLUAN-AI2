from core.clinical_engine import analyze_case, render_report
from core.semantic_clinical_parser import parse_narrative


def test_synthesis_creates_provisional_diagnosis_from_hypotheses():
    data = {
        "region": "Cột sống thắt lưng",
        "reason": "Đau thắt lưng lan chân trái",
        "free_text": "Đau thắt lưng lan xuống mặt sau đùi trái, tê chân trái, tăng khi ngồi và cúi gập.",
        "history": "Đau lan xuống chân trái, tê chân trái.",
        "site": "Thắt lưng trái, mông trái, mặt sau đùi trái",
        "onset": "Sau khi nâng vật nặng",
        "character": "Đau nhói như điện giật",
        "radiation": "Lan xuống mặt sau đùi trái",
        "associations": "Không bí tiểu, không tê vùng yên ngựa",
        "course": "5 ngày",
        "inspection": "",
        "palpation": "",
        "rom_mmt": "",
        "tests": {
            "Lasègue": "Dương tính",
            "SLR": "Dương tính",
            "Bragard": "Dương tính",
        },
    }
    result = analyze_case(data)
    synthesis = result["diagnosis_synthesis"]
    assert synthesis["primary"] is not None
    assert "rễ thần kinh" in synthesis["primary"]["label"].lower()
    assert synthesis["differentials"]
    assert not any("tê/dị cảm" in x for x in result["narrative_analysis"]["contradictions"])
    assert any("Cụm nghiệm pháp căng thần kinh" in x for x in synthesis["primary"]["supporting"])
    report = render_report(result)
    assert "TỔNG HỢP CHẨN ĐOÁN SƠ BỘ" in report
    assert "Chẩn đoán phân biệt" in report


def test_bung_phat_is_not_abdominal_location():
    parsed = parse_narrative({"free_text": "Đau bùng phát dữ dội cách đây 5 ngày."})
    assert "bụng" not in parsed["anatomical_locations"]


def test_unknown_case_does_not_force_diagnosis():
    result = analyze_case({"region": "Cột sống thắt lưng", "free_text": "Đau lưng."})
    assert result["diagnosis_synthesis"]["primary"] is None
    assert result["diagnosis_synthesis"]["status"] == "insufficient_data"


def test_same_site_symptom_present_and_denied_is_flagged():
    parsed = parse_narrative({"free_text": "Lúc đầu tê chân trái, hiện tại không tê chân trái."})
    assert any("tê/dị cảm" in item for item in parsed["contradictions"])


def test_tingling_leg_and_denied_saddle_numbness_are_not_false_conflict():
    parsed = parse_narrative({"free_text": "Tê chân trái, không tê vùng yên ngựa."})
    assert not any("tê/dị cảm" in item for item in parsed["contradictions"])
