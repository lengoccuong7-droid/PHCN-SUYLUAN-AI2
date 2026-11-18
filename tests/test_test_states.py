from core.clinical_engine import _test_state


def test_test_states_keep_negative_separate_from_not_performed():
    result = _test_state({
        "Test A": "Dương tính (+)",
        "Test B": "Âm tính (-)",
        "Test C": "Chưa thực hiện",
        "Test D": "Chưa làm / Âm tính (-)",
    })
    assert result["positive"] == ["Test A"]
    assert result["negative"] == ["Test B"]
    assert result["unperformed"] == ["Test C", "Test D"]
