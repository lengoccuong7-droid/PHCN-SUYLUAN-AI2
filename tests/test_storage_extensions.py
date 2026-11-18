from database import storage


def test_patient_token_links_visits_without_phone_and_plan_is_saved(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "phcn.sqlite")
    storage.init_db()
    patient = {
        "name": "Synthetic Case",
        "phone": "",
        "age": 1990,
        "job": "",
        "patient_token": "PHCN-TEST-001",
    }
    first = storage.save_visit(patient, "Khớp gối", {"nrs": 4}, "visit 1", {}, "")
    second = storage.save_visit(patient, "Khớp gối", {"nrs": 3}, "visit 2", {}, "")
    first_detail = storage.get_visit_detail(first)
    second_detail = storage.get_visit_detail(second)
    assert first_detail["patient_id"] == second_detail["patient_id"]
    plan_id = storage.save_treatment_plan(
        first_detail["patient_id"], first, {"goals": "Synthetic goal"}
    )
    plans = storage.list_treatment_plans(first_detail["patient_id"])
    assert plans and plans[0]["id"] == plan_id
    assert storage.get_treatment_plan(plan_id)["plan"]["goals"] == "Synthetic goal"
