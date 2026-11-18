"""Local semantic-feedback statistics. Suggestions are not auto-applied."""
from __future__ import annotations
from database.storage import connect

def get_learning_stats():
    with connect() as con:
        synonyms = con.execute("SELECT COUNT(*) FROM learned_synonyms").fetchone()[0]
        phrases = con.execute("SELECT COUNT(*) FROM learned_phrases").fetchone()[0]
        common = con.execute(
            "SELECT phrase, feature_code, count FROM learned_phrases ORDER BY count DESC, updated_at DESC LIMIT 10"
        ).fetchall()
    return {
        "so_tu_dong_nghia": int(synonyms),
        "so_cum_tu": int(phrases),
        "cum_tu_pho_bien": [dict(x) for x in common],
    }
