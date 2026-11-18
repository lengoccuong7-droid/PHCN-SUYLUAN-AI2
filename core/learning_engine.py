"""Học trọng số từ phản hồi của bác sĩ."""
from __future__ import annotations
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple
from core.reasoning_rules import RULES

DB_PATH = Path(os.environ.get(
    "PHCN_DB_PATH", str(Path(__file__).resolve().parents[1] / "data" / "phcn_ai.db")
)).expanduser().resolve()

LEARNING_RATE = 0.05
MIN_WEIGHT = 0.01
MAX_WEIGHT = 0.80


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_learning_table():
    with _connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS learned_weights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hypothesis_key TEXT NOT NULL,
                feature_code TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                weight REAL NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(hypothesis_key, feature_code, rule_type)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS learning_proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hypothesis_key TEXT NOT NULL,
                feature_code TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                old_weight REAL NOT NULL,
                proposed_weight REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                reviewed_at TEXT,
                UNIQUE(hypothesis_key, feature_code, rule_type, status)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS feedback_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id INTEGER,
                hypothesis_key TEXT NOT NULL,
                doctor_agreement TEXT NOT NULL,
                doctor_note TEXT,
                created_at TEXT NOT NULL
            )
        """)


def load_learned_weights() -> Dict[Tuple[str, str, str], float]:
    init_learning_table()
    with _connect() as con:
        rows = con.execute("SELECT * FROM learned_weights").fetchall()
    result = {}
    for r in rows:
        result[(r["hypothesis_key"], r["feature_code"], r["rule_type"])] = r["weight"]
    return result


def apply_learned_weights() -> None:
    learned = load_learned_weights()
    if not learned:
        return
    for hyp_key, rule in RULES.items():
        for rule_type in ("positive_rules", "negative_rules"):
            new_rules = []
            for feat, weight, label in rule.get(rule_type, []):
                key = (hyp_key, feat, rule_type)
                if key in learned:
                    weight = learned[key]
                new_rules.append((feat, weight, label))
            if new_rules:
                rule[rule_type] = new_rules


def record_feedback(visit_id: int | None, hypothesis_key: str,
                    doctor_agreement: str, doctor_note: str = "") -> None:
    init_learning_table()
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as con:
        con.execute(
            "INSERT INTO feedback_log(visit_id, hypothesis_key, doctor_agreement, "
            "doctor_note, created_at) VALUES(?,?,?,?,?)",
            (visit_id, hypothesis_key, doctor_agreement, doctor_note, now),
        )


def learn_from_feedback(hypothesis_key: str, doctor_agreement: str,
                        triggered_features: List[str],
                        rule_type: str = "positive_rules") -> Dict[str, Any]:
    """Create review proposals only; never change active rules automatically."""
    init_learning_table()
    if doctor_agreement == "khong_ro":
        return {"changed": False, "proposal_created": 0,
                "reason": "Bác sĩ chưa rõ; không tạo đề xuất điều chỉnh."}
    rule = RULES.get(hypothesis_key)
    if not rule:
        return {"changed": False, "proposal_created": 0,
                "reason": f"Không tìm thấy giả thuyết {hypothesis_key}."}
    delta = LEARNING_RATE if doctor_agreement == "dong_y" else -LEARNING_RATE
    proposals = []
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as con:
        for feat, weight, _label in rule.get(rule_type, []):
            if feat not in triggered_features:
                continue
            new_weight = max(MIN_WEIGHT, min(MAX_WEIGHT, weight + delta))
            if abs(new_weight - weight) < 1e-6:
                continue
            cur = con.execute("""
                INSERT INTO learning_proposals(
                    hypothesis_key, feature_code, rule_type, old_weight,
                    proposed_weight, status, created_at
                ) VALUES(?,?,?,?,?,'pending',?)
                ON CONFLICT(hypothesis_key, feature_code, rule_type, status)
                DO UPDATE SET old_weight=excluded.old_weight,
                              proposed_weight=excluded.proposed_weight,
                              created_at=excluded.created_at
            """, (hypothesis_key, feat, rule_type, weight, new_weight, now))
            proposals.append({"feature": feat, "old_weight": round(weight, 3),
                              "proposed_weight": round(new_weight, 3)})
    return {"changed": False, "proposal_created": len(proposals),
            "hypothesis": hypothesis_key, "agreement": doctor_agreement,
            "proposals": proposals,
            "reason": "Đã ghi đề xuất để người có chuyên môn duyệt; trọng số đang sử dụng chưa thay đổi."}


def list_learning_proposals(status: str = "pending"):
    init_learning_table()
    with _connect() as con:
        return con.execute(
            "SELECT * FROM learning_proposals WHERE status=? ORDER BY created_at DESC",
            (status,),
        ).fetchall()


def review_learning_proposal(proposal_id: int, approve: bool) -> bool:
    init_learning_table()
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as con:
        row = con.execute(
            "SELECT * FROM learning_proposals WHERE id=? AND status='pending'",
            (int(proposal_id),),
        ).fetchone()
        if not row:
            return False
        if approve:
            con.execute("""
                INSERT INTO learned_weights(hypothesis_key, feature_code, rule_type, weight, updated_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(hypothesis_key, feature_code, rule_type)
                DO UPDATE SET weight=excluded.weight, updated_at=excluded.updated_at
            """, (row["hypothesis_key"], row["feature_code"], row["rule_type"],
                  row["proposed_weight"], now))
        con.execute(
            "UPDATE learning_proposals SET status=?, reviewed_at=? WHERE id=?",
            ("approved" if approve else "rejected", now, int(proposal_id)),
        )
    return True


def get_learning_statistics() -> Dict[str, Any]:
    init_learning_table()
    with _connect() as con:
        n_weights = con.execute("SELECT COUNT(*) FROM learned_weights").fetchone()[0]
        n_feedback = con.execute("SELECT COUNT(*) FROM feedback_log").fetchone()[0]
        recent = con.execute(
            "SELECT * FROM feedback_log ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
    return {
        "so_trong_so_da_hoc": n_weights,
        "so_phan_hoi": n_feedback,
        "phan_hoi_gan_nhat": [dict(r) for r in recent],
    }