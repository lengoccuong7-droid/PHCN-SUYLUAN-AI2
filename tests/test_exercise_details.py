import json
from pathlib import Path


def test_exercise_details_cover_all_library_items():
    base = Path(__file__).resolve().parents[1]
    library = json.loads((base / "knowledge/rehabilitation/exercise_library.json").read_text(encoding="utf-8"))
    details = json.loads((base / "knowledge/rehabilitation/exercise_details.json").read_text(encoding="utf-8"))
    assert list(library) == list(details)
    for group, exercises in library.items():
        assert len(exercises) == len(details[group]) == 7
        for guide in details[group]:
            for field in ("purpose", "position", "technique", "common_errors", "dose", "safety"):
                assert guide[field].strip()
