from core.clinical_engine import analyze_case, render_report
from core.semantic_clinical_parser import parse_narrative
from database import storage


def test_supplemental_text_is_included_in_narrative_parser():
    parsed = parse_narrative({
        "region": "Cột sống thắt lưng",
        "free_text": "Đau thắt lưng bên trái.",
        "supplemental_text": "Hiện tại không tê chân trái; người bệnh cảm thấy yếu chân trái.",
    })
    assert "supplemental_text" in parsed["input_sources"]
    assert any(x["symptom"] == "tê/dị cảm" and x["state"] == "phủ định" for x in parsed["symptoms"])
    assert any(x["symptom"] == "yếu/mất lực" for x in parsed["symptoms"])


def test_supplemental_text_participates_in_analysis_and_report():
    base = {"region": "Cột sống thắt lưng", "reason": "Đau thắt lưng",
            "free_text": "Đau thắt lưng bên trái 2 tuần.", "tests": {}}
    enriched = dict(base, supplemental_text="Không tê chân; người bệnh cảm thấy yếu chân trái.")
    result = analyze_case(enriched)
    assert "supplemental_text" in result["narrative_analysis"]["input_sources"]
    result["analysis_round"] = 2
    result["supplemental_text"] = enriched["supplemental_text"]
    report = render_report(result)
    assert "Vòng phân tích: 2" in report
    assert "Không tê chân" in report


def test_analysis_rounds_and_doctor_reviews_persist(tmp_path, monkeypatch):
    db = tmp_path / "test_phcn.sqlite"
    monkeypatch.setattr(storage, "DB_PATH", db)
    storage.init_db()
    visit_id = storage.save_visit(
        {"name": "Test Patient", "phone": "", "age": 2000, "job": ""},
        "Cột sống thắt lưng", {"free_text": "đau"}, "summary", {}, "report"
    )
    count = storage.save_analysis_rounds(visit_id, [{
        "round": 1, "payload": {"free_text": "đau"}, "analysis": {"round": 1}, "report": "r1"
    }, {
        "round": 2, "payload": {"supplemental_text": "không tê"}, "analysis": {"round": 2}, "report": "r2"
    }])
    assert count == 2
    assert len(storage.list_analysis_rounds(visit_id)) == 2
    review_id = storage.save_clinical_review(visit_id, 2, "Chấp nhận có điều chỉnh", "Giả thuyết A", "Ghi chú")
    assert review_id > 0
    assert len(storage.list_clinical_reviews(visit_id)) == 1
