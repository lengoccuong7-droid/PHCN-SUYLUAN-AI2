import json
from pathlib import Path


def test_catalog_has_63_exercises_and_315_detailed_variants():
    base = Path(__file__).resolve().parents[1]
    catalog = json.loads((base / "knowledge/rehabilitation/exercise_catalog.json").read_text(encoding="utf-8"))
    assert len(catalog["groups"]) == 9
    exercises = [e for g in catalog["groups"] for e in g["exercises"]]
    assert len(exercises) == 63
    variants = [v for e in exercises for v in e["variants"]]
    assert len(variants) == 315
    assert len({v["variant_id"] for v in variants}) == 315
    required = ("name", "method", "equipment", "purpose", "setup", "technique", "dose",
                "progression", "regression", "common_errors", "safety", "stop_criteria", "supervision")
    for variant in variants:
        for field in required:
            assert isinstance(variant[field], str) and variant[field].strip()
