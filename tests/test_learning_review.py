from core import learning_engine as le


def test_feedback_creates_proposal_not_active_weight(tmp_path, monkeypatch):
    monkeypatch.setattr(le, "DB_PATH", tmp_path / "learning.sqlite")
    result = le.learn_from_feedback(
        "knee_acl", "dong_y", ["mechanism_pivot"], "positive_rules"
    )
    assert result["changed"] is False
    assert result["proposal_created"] == 1
    assert le.load_learned_weights() == {}
    proposals = le.list_learning_proposals("pending")
    assert len(proposals) == 1
    assert le.review_learning_proposal(proposals[0]["id"], True) is True
    learned = le.load_learned_weights()
    assert ("knee_acl", "mechanism_pivot", "positive_rules") in learned
    assert le.list_learning_proposals("pending") == []
