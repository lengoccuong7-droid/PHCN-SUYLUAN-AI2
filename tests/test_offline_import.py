from database import storage


def test_offline_record_import_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "offline.sqlite")
    storage.init_db()
    args = (
        {"name": "PHCN-OFF-01", "phone": "", "age": None, "job": "", "patient_token": "PHCN-OFF-01"},
        "Khớp gối", {"region": "Khớp gối"}, "offline", {}, "report"
    )
    first = storage.save_visit(*args, source_record_id="offline-record-001")
    second = storage.save_visit(*args, source_record_id="offline-record-001")
    assert first == second
    assert len(storage.list_visits(10)) == 1
