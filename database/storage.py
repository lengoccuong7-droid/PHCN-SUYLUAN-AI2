"""Lưu hồ sơ và lần khám cục bộ bằng SQLite. Không lưu ảnh tải lên."""
import sqlite3
import json
import uuid
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path(os.environ.get(
    "PHCN_DB_PATH", str(Path(__file__).resolve().parents[1] / "data" / "phcn_ai.db")
)).expanduser().resolve()


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            birth_year INTEGER,
            job TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            region TEXT NOT NULL,
            input_json TEXT NOT NULL,
            summary_text TEXT,
            analysis_json TEXT,
            report_text TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(id))""")
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_visits_patient "
            "ON visits(patient_id, created_at DESC)"
        )
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
            CREATE TABLE IF NOT EXISTS feedback_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id INTEGER,
                hypothesis_key TEXT NOT NULL,
                doctor_agreement TEXT NOT NULL,
                doctor_note TEXT,
                created_at TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS learned_synonyms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_term TEXT NOT NULL,
                synonym_term TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                source TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(canonical_term, synonym_term)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS learned_phrases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phrase TEXT NOT NULL UNIQUE,
                feature_code TEXT,
                count INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS treatment_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                source_visit_id INTEGER,
                plan_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(patient_id) REFERENCES patients(id),
                FOREIGN KEY(source_visit_id) REFERENCES visits(id)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS offline_imports (
                record_id TEXT PRIMARY KEY,
                visit_id INTEGER NOT NULL,
                imported_at TEXT NOT NULL,
                FOREIGN KEY(visit_id) REFERENCES visits(id)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS analysis_rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id INTEGER NOT NULL,
                round_no INTEGER NOT NULL,
                input_json TEXT NOT NULL,
                analysis_json TEXT NOT NULL,
                report_text TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(visit_id, round_no),
                FOREIGN KEY(visit_id) REFERENCES visits(id) ON DELETE CASCADE
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS clinical_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id INTEGER NOT NULL,
                round_no INTEGER NOT NULL,
                decision TEXT NOT NULL,
                primary_hypothesis TEXT,
                doctor_note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(visit_id) REFERENCES visits(id) ON DELETE CASCADE
            )
        """)


def save_visit(patient, region, payload, summary_text, analysis, report, source_record_id=None):
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as con:
        if source_record_id:
            imported = con.execute(
                "SELECT visit_id FROM offline_imports WHERE record_id=?",
                (str(source_record_id),),
            ).fetchone()
            if imported:
                return int(imported["visit_id"])
        phone = str(patient.get("phone") or "").strip()
        patient_token = str(patient.get("patient_token") or "").strip()
        patient_key = phone or patient_token or ("PHCN-" + uuid.uuid4().hex)
        row = con.execute(
            "SELECT id FROM patients WHERE phone=?", (patient_key,)
        ).fetchone()
        if row:
            pid = row["id"]
            con.execute(
                "UPDATE patients SET name=?, birth_year=?, job=?, updated_at=? WHERE id=?",
                (patient.get("name", ""), patient.get("age"),
                 patient.get("job", ""), now, pid),
            )
        else:
            cur = con.execute(
                "INSERT INTO patients(name,phone,birth_year,job,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?)",
                (patient.get("name", ""), patient_key, patient.get("age"),
                 patient.get("job", ""), now, now),
            )
            pid = cur.lastrowid
        cur = con.execute(
            "INSERT INTO visits(patient_id,region,input_json,summary_text,"
            "analysis_json,report_text,created_at) VALUES(?,?,?,?,?,?,?)",
            (pid, region, json.dumps(payload, ensure_ascii=False), summary_text,
             json.dumps(analysis, ensure_ascii=False), report, now),
        )
        visit_id = int(cur.lastrowid)
        if source_record_id:
            con.execute(
                "INSERT INTO offline_imports(record_id, visit_id, imported_at) VALUES(?,?,?)",
                (str(source_record_id), visit_id, now),
            )
        return visit_id


def list_visits(limit=100):
    with connect() as con:
        return con.execute(
            """SELECT v.id, p.id AS patient_id, p.name, p.birth_year,
            CASE WHEN p.phone LIKE 'PHCN-%' THEN '' ELSE p.phone END AS phone,
            v.region, v.created_at
            FROM visits v JOIN patients p ON p.id=v.patient_id
            ORDER BY v.created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()


def get_visit_detail(visit_id):
    with connect() as con:
        row = con.execute(
            """SELECT v.*, p.name, p.phone, p.birth_year, p.job
            FROM visits v JOIN patients p ON p.id=v.patient_id WHERE v.id=?""",
            (int(visit_id),),
        ).fetchone()
        if not row:
            return None
        item = dict(row)
        for key in ("input_json", "analysis_json"):
            try:
                item[key.replace("_json", "")] = json.loads(item[key] or "{}")
            except (TypeError, ValueError):
                item[key.replace("_json", "")] = {}
        return item


def list_patient_visits(phone, limit=100):
    with connect() as con:
        return con.execute(
            """SELECT v.id, v.region, v.created_at, v.summary_text,
            v.analysis_json, p.name, p.phone
            FROM visits v JOIN patients p ON p.id=v.patient_id
            WHERE p.phone=? ORDER BY v.created_at ASC LIMIT ?""",
            (str(phone).strip(), int(limit)),
        ).fetchall()


def list_patient_visits_by_id(patient_id, limit=100):
    with connect() as con:
        return con.execute(
            """SELECT v.id, v.region, v.created_at, v.summary_text,
            v.analysis_json, p.name, p.phone, p.birth_year
            FROM visits v JOIN patients p ON p.id=v.patient_id
            WHERE p.id=? ORDER BY v.created_at ASC LIMIT ?""",
            (int(patient_id), int(limit)),
        ).fetchall()

def save_treatment_plan(patient_id, source_visit_id, plan):
    """Save a versioned draft plan linked to an existing patient and source visit."""
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as con:
        exists = con.execute("SELECT id FROM patients WHERE id=?", (int(patient_id),)).fetchone()
        if not exists:
            raise ValueError("Không tìm thấy hồ sơ bệnh nhân.")
        if source_visit_id is not None:
            source = con.execute(
                "SELECT id, patient_id FROM visits WHERE id=?", (int(source_visit_id),)
            ).fetchone()
            if not source or int(source["patient_id"]) != int(patient_id):
                raise ValueError("Lần khám nguồn không thuộc hồ sơ bệnh nhân đã chọn.")
        cur = con.execute(
            "INSERT INTO treatment_plans(patient_id, source_visit_id, plan_json, status, created_at, updated_at) "
            "VALUES(?,?,?,?,?,?)",
            (int(patient_id), int(source_visit_id) if source_visit_id is not None else None,
             json.dumps(plan, ensure_ascii=False), "draft", now, now),
        )
        return int(cur.lastrowid)


def list_treatment_plans(patient_id, limit=100):
    with connect() as con:
        return con.execute(
            "SELECT * FROM treatment_plans WHERE patient_id=? ORDER BY created_at DESC LIMIT ?",
            (int(patient_id), int(limit)),
        ).fetchall()


def get_treatment_plan(plan_id):
    with connect() as con:
        row = con.execute("SELECT * FROM treatment_plans WHERE id=?", (int(plan_id),)).fetchone()
        if not row:
            return None
        result = dict(row)
        try:
            result["plan"] = json.loads(result.pop("plan_json") or "{}")
        except (TypeError, ValueError):
            result["plan"] = {}
        return result


def save_analysis_rounds(visit_id, rounds):
    """Persist all analysis iterations associated with a saved visit."""
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as con:
        for item in rounds or []:
            round_no = int(item.get("round", 1))
            con.execute(
                """INSERT INTO analysis_rounds(visit_id,round_no,input_json,analysis_json,report_text,created_at)
                   VALUES(?,?,?,?,?,?)
                   ON CONFLICT(visit_id,round_no) DO UPDATE SET
                   input_json=excluded.input_json, analysis_json=excluded.analysis_json,
                   report_text=excluded.report_text, created_at=excluded.created_at""",
                (int(visit_id), round_no,
                 json.dumps(item.get("payload", {}), ensure_ascii=False),
                 json.dumps(item.get("analysis", {}), ensure_ascii=False),
                 str(item.get("report", "")), now),
            )
    return len(rounds or [])


def list_analysis_rounds(visit_id):
    with connect() as con:
        rows = con.execute(
            "SELECT * FROM analysis_rounds WHERE visit_id=? ORDER BY round_no ASC",
            (int(visit_id),),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        for key in ("input_json", "analysis_json"):
            try:
                item[key.replace("_json", "")] = json.loads(item[key] or "{}")
            except (TypeError, ValueError):
                item[key.replace("_json", "")] = {}
        result.append(item)
    return result


def save_clinical_review(visit_id, round_no, decision, primary_hypothesis="", doctor_note=""):
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as con:
        cur = con.execute(
            "INSERT INTO clinical_reviews(visit_id,round_no,decision,primary_hypothesis,doctor_note,created_at) VALUES(?,?,?,?,?,?)",
            (int(visit_id), int(round_no), str(decision), str(primary_hypothesis or ""), str(doctor_note or ""), now),
        )
        return int(cur.lastrowid)


def list_clinical_reviews(visit_id):
    with connect() as con:
        return con.execute(
            "SELECT * FROM clinical_reviews WHERE visit_id=? ORDER BY created_at ASC",
            (int(visit_id),),
        ).fetchall()
