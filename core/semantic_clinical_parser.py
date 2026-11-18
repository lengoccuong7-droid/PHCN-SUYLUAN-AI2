"""Offline Vietnamese clinical narrative parser for PHCN AI 4.1.

Explainable, deterministic NLP utilities. This module extracts reported facts and
relations; it does not diagnose, infer causality as fact, or replace clinician review.
"""
from __future__ import annotations
import re
import unicodedata
from typing import Any, Dict, List, Tuple


def normalize(text: Any) -> str:
    s = str(text or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("đ", "d")
    s = re.sub(r"\s+", " ", s)
    return s


# Broad vocabularies are intentionally descriptive, not diagnostic.
SYMPTOMS = {
    "đau": ["dau", "nhuc", "dau nhuc", "dau am i", "dau choi", "dau buot"],
    "tê/dị cảm": ["te", "te ran", "te bi", "cham chich", "kien bo", "di cam", "mat cam giac"],
    "yếu/mất lực": ["yeu", "mat luc", "hut luc", "khong co luc", "de roi do"],
    "sưng": ["sung", "phu ne", "phu"],
    "nóng/đỏ": ["nong do", "do nong", "sung nong do"],
    "cứng/hạn chế vận động": ["cung khop", "cung co", "han che van dong", "kho gap", "kho duoi", "khong gap het"],
    "co thắt/chuột rút": ["co that", "chuot rut", "vop bo", "co rut"],
    "mất vững": ["mat vung", "long goi", "khop lung lay", "khong vung"],
    "tiếng kêu/cảm giác cơ học": ["luc cuc", "click", "ket khop", "mac khop", "ket"],
    "sốt": ["sot", "ret run"],
    "mệt mỏi": ["met moi", "suy nhuoc", "met"],
}

BODY_SITES = [
    "cổ", "gáy", "vai", "bả vai", "cánh tay", "khuỷu", "cẳng tay", "cổ tay", "bàn tay", "ngón tay",
    "ngực", "lưng", "thắt lưng", "hông", "mông", "háng", "đùi", "gối", "khoeo", "cẳng chân",
    "bắp chân", "cổ chân", "gót chân", "bàn chân", "ngón chân", "bụng", "vùng chậu",
]

TIME_PATTERNS = [
    ("khởi phát đột ngột/đợt cấp", ["dot ngot", "bat ngo", "bung phat", "dang lam thi", "tu nhien xuat hien", "5 ngay"]),
    ("khởi phát từ từ", ["tu tu", "dan dan", "am i", "khong ro luc bat dau"]),
    ("sau chấn thương/sự kiện", ["sau khi nga", "sau chan thuong", "sau va dap", "sau tai nan", "sau khi nang vat"]),
    ("kéo dài/tái diễn", ["keo dai", "tai phat", "lap di lap lai", "nhieu thang", "nhieu nam", "man tinh", "3 nam"]),
    ("đang cải thiện", ["giam dan", "do dan", "cai thien", "tot dan"]),
    ("đang nặng lên", ["tang dan", "nang dan", "xau dan", "lan rong hon"]),
]

NEGATORS = ["khong", "khong co", "khong bi", "khong thay", "khong ghi nhan", "phu nhan", "chua tung"]
CONTRAST = ["nhung", "tuy nhien", "song", "trai lai", "mac du"]
CAUSE_MARKERS = ["vi", "do", "boi vi", "sau khi", "ke tu khi", "sau dot", "sau lan"]
AGGRAVATORS = ["tang khi", "dau hon khi", "nang hon khi", "khi gap", "khi cui", "cui gap", "khi duoi", "khi xoay", "khi di", "khi dung", "khi ngoi", "khi nang", "khi chay", "khi len cau thang", "khi ho", "khi hat hoi", "ho hoac hat hoi"]
RELIEVERS = ["giam khi", "do khi", "de chiu hon khi", "het khi", "nhe hon khi", "nghi ngoi", "nam ngua", "khi nam", "ke goi", "chom lanh", "chom am"]


def _find_terms(text: str, vocab: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    found = []
    for label, terms in vocab.items():
        for term in terms:
            for m in re.finditer(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text):
                found.append({"label": label, "term": term, "start": m.start(), "end": m.end()})
    return sorted(found, key=lambda x: (x["start"], -(x["end"] - x["start"])))


def _clause_before(text: str, start: int) -> str:
    left = text[:start]
    # Commas are not always clause boundaries in Vietnamese lists; preserve short scope.
    return re.split(r"[.!?;\n]|\b(?:nhung|tuy nhien|song|trai lai|hien tai|luc nay|bay gio|sau do|truoc do)\b", left)[-1][-90:]


def _negated(text: str, start: int) -> bool:
    prefix = _clause_before(text, start)
    matches = list(re.finditer(r"\b(?:khong co|khong bi|khong thay|khong ghi nhan|khong|phu nhan|chua tung)\b", prefix))
    if not matches:
        return False
    tail = prefix[matches[-1].end():]
    return len(tail) <= 55 and not any(re.search(r"\b" + re.escape(c) + r"\b", tail) for c in CONTRAST)


def _side(text: str) -> str:
    left = bool(re.search(r"\b(trai|ben trai|tay trai|chan trai)\b", text))
    right = bool(re.search(r"\b(phai|ben phai|tay phai|chan phai)\b", text))
    if left and right:
        return "hai bên hoặc có dữ kiện trái-phải cần xác minh"
    if left:
        return "trái"
    if right:
        return "phải"
    if re.search(r"\b(hai ben|ca hai ben|2 ben|doi ben)\b", text):
        return "hai bên"
    return "chưa xác định"


def _extract_locations(text: str) -> List[str]:
    n = normalize(text)
    # Prefer longer anatomical phrases and suppress overlapping sub-parts.
    candidates = []
    for site in BODY_SITES:
        term = normalize(site)
        for match in re.finditer(r"(?<!\w)" + re.escape(term) + r"(?!\w)", n):
            # Vietnamese diacritic normalization makes 'vai' and 'vài' identical;
            # accept shoulder only when an anatomical context is nearby.
            context = n[max(0, match.start()-24):min(len(n), match.end()+24)]
            if term == "vai":
                if not re.search(r"(khop|dau|vung|ben|co)\s+vai|vai\s+(trai|phai|ben)", context):
                    continue
            # Disambiguate "đau bùng phát" from anatomical "đau bụng".
            if term == "bung" and re.search(r"bung\s+phat\b", context):
                continue
            # 'co' (muscle contraction) must not be read as anatomical 'cổ'.
            if term == "co" and not re.search(r"(vung|cot song|gay|dau|ben)\s+co\b|co\s+(vai|gai|chan|tay)", context):
                continue
            candidates.append((match.start(), match.end(), site))
    candidates.sort(key=lambda x: (x[0], -(x[1]-x[0])))
    chosen = []
    for start, end, site in candidates:
        if any(not (end <= a or start >= b) for a, b, _ in chosen):
            continue
        chosen.append((start, end, site))
    return list(dict.fromkeys(site for _, _, site in sorted(chosen)))


def _split_clauses(text: str) -> List[str]:
    chunks = re.split(r"[.!?;\n]+|,\s*(?=(?:sau|nhung|tuy nhien|dong thoi|kem theo|roi|sau do)\b)", text)
    return [x.strip(" ,-") for x in chunks if x.strip(" ,-")]


def parse_narrative(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse free narrative plus structured fields into transparent evidence."""
    keys = ("free_text", "supplemental_text", "reason", "history", "site", "onset", "character", "radiation", "associations", "course", "inspection", "palpation", "rom_mmt")
    raw_parts = [(k, str(data.get(k, "") or "").strip()) for k in keys if str(data.get(k, "") or "").strip()]
    raw = "\n".join(v for _, v in raw_parts)
    n = normalize(raw)
    clauses = _split_clauses(raw)
    normalized_clauses = [normalize(c) for c in clauses]

    symptom_mentions = _find_terms(n, SYMPTOMS)
    symptoms = []
    for item in symptom_mentions:
        state = "phủ định" if _negated(n, item["start"]) else "được ghi nhận"
        clause_context = n[max(0, item["start"]-45):min(len(n), item["end"]+45)]
        site_context = n[item["end"]:min(len(n), item["end"]+32)]
        symptoms.append({"symptom": item["label"], "matched_text": item["term"], "state": state, "context": clause_context, "site_context": site_context})
    # Deduplicate while preserving both present and denied states.
    unique_symptoms = []
    seen = set()
    for item in symptoms:
        key = (item["symptom"], item["state"])
        if key not in seen:
            seen.add(key); unique_symptoms.append(item)

    # Anatomical locations are taken from symptom/history fields, not from comparison
    # notes such as the healthy side, kneepit support, or unrelated exam wording.
    location_text = "\n".join(v for k, v in raw_parts if k in ("free_text", "supplemental_text", "reason", "history", "site", "radiation", "associations"))
    locations = _extract_locations(normalize(location_text))
    side_text = "\n".join(v for k, v in raw_parts if k not in ("rom_mmt", "inspection"))
    side_n = normalize(side_text)
    # A contralateral comparison in objective examination is not a second symptomatic side.
    side_n = re.sub(r"ben phai\s*(?:dat\s*)?[0-5]\s*/\s*5", "", side_n)
    side_n = re.sub(r"ben phai\s*\d\s*\+", "", side_n)
    side_n = re.sub(r"so voi ben phai", "", side_n)
    side = _side(side_n)
    timeline = []
    for label, terms in TIME_PATTERNS:
        if any(normalize(term) in n for term in terms):
            timeline.append(label)
    # Explicit durations are reported as text, not converted into assumed onset categories.
    durations = list(dict.fromkeys(re.findall(r"\b\d+\s*(?:ngày|tuần|tháng|năm|giờ|phút)\b", raw, flags=re.IGNORECASE)))

    aggravating = []
    relieving = []
    if re.search(r"(tang|dau hon|nang hon)[^.!?;\n]{0,50}\b(khi )?ngoi\b", n): aggravating.append("ngồi lâu")
    if re.search(r"(tang|dau hon|nang hon)[^.!?;\n]{0,50}\b(cui|gap nguoi)\b", n): aggravating.append("cúi/gập người")
    if re.search(r"(tang|dau hon|nang hon)[^.!?;\n]{0,50}\bho\b", n): aggravating.append("ho")
    if re.search(r"(tang|dau hon|nang hon)[^.!?;\n]{0,50}\bhat hoi\b", n): aggravating.append("hắt hơi")
    if re.search(r"(giam|do|nhe hon)[^.!?;\n]{0,70}\bnam ngua\b", n): relieving.append("nằm ngửa")
    if re.search(r"(giam|do|nhe hon)[^.!?;\n]{0,70}\bke goi\b", n): relieving.append("kê gối")
    # "Tăng khi nằm" and "giảm khi nằm ngửa" must not collapse into the same cue.
    if re.search(r"(tang|dau hon|nang hon)\s+(?:ro|nhieu)?\s*khi nam\b", n):
        aggravating.append("tăng khi nằm")
    if re.search(r"(giam|do|nhe hon)\s+[^.]{0,45}\bkhi nam\b", n):
        relieving.append("giảm khi nằm")
    relations = []
    for clause in normalized_clauses:
        if any(re.search(r"(?<!\w)" + re.escape(normalize(x)) + r"(?!\w)", clause) for x in CAUSE_MARKERS):
            relations.append({"type": "trình tự/quan hệ được người bệnh mô tả", "text": clause, "interpretation": "Ghi nhận sự kiện xảy ra trước-sau hoặc yếu tố người bệnh cho là liên quan; chưa chứng minh quan hệ nhân quả."})
        if any(re.search(r"(?<!\w)" + re.escape(normalize(x)) + r"(?!\w)", clause) for x in AGGRAVATORS):
            relations.append({"type": "yếu tố làm tăng triệu chứng", "text": clause, "interpretation": "Mối liên hệ với hoạt động/tư thế cần được kiểm tra khả năng tái hiện triệu chứng."})
        if any(re.search(r"(?<!\w)" + re.escape(normalize(x)) + r"(?!\w)", clause) for x in RELIEVERS):
            relations.append({"type": "yếu tố làm giảm triệu chứng", "text": clause, "interpretation": "Mối liên hệ giảm triệu chứng cần được xác minh trong bệnh sử và theo dõi."})

    # Extract explicit cause/effect phrasing as a *reported* relationship only.
    causal_chains = []
    for clause in normalized_clauses:
        patterns = [
            (r"(?P<effect>[^,]{2,90}?)\s+(?:sau khi|sau lan|ke tu khi)\s+(?P<cause>[^,]{2,90})", "trình tự thời gian được mô tả"),
            (r"(?:do|boi vi|vi)\s+(?P<cause>[^,]{2,90}?)\s+(?:nen|ma)\s+(?P<effect>[^,]{2,90})", "nguyên nhân do người kể quy kết"),
            (r"khi\s+(?P<cause>[^,]{2,70}?)\s+(?:thi|la)\s+(?P<effect>[^,]{2,90})", "mối liên hệ điều kiện được mô tả"),
        ]
        for pattern, relation_type in patterns:
            match = re.search(pattern, clause)
            if match:
                causal_chains.append({
                    "relation_type": relation_type,
                    "reported_trigger_or_context": match.group("cause").strip(),
                    "reported_outcome": match.group("effect").strip(),
                    "interpretation": "Chỉ là quan hệ do người bệnh/người ghi bệnh sử thuật lại, chưa chứng minh quan hệ nhân quả; cần xác minh tính thời gian, khả năng tái hiện và các nguyên nhân thay thế.",
                })
                break

    # Conservative contradiction checks: present and explicitly denied same symptom.
    contradictions = []
    for label in SYMPTOMS:
        # Pain in different contexts (e.g. activity pain but no pain at rest)
        # is not a contradiction; the current parser cannot reliably time-scope it.
        if label == "đau":
            continue
        mentions = [x for x in symptoms if x["symptom"] == label]
        positive_contexts = [x.get("site_context", "") for x in mentions if x["state"] == "được ghi nhận"]
        negative_contexts = [x.get("site_context", "") for x in mentions if x["state"] == "phủ định"]
        if positive_contexts and negative_contexts:
            # Different anatomical contexts are not automatically contradictory
            # (e.g. tingling in the leg but no saddle-area numbness).
            site_tokens = ("chan", "tay", "ban chan", "ban tay", "yen ngua", "lung", "mong", "dui")
            pos_sites = {site for ctx in positive_contexts for site in site_tokens if site in ctx}
            neg_sites = {site for ctx in negative_contexts for site in site_tokens if site in ctx}
            if pos_sites and neg_sites and pos_sites.isdisjoint(neg_sites):
                continue
            contradictions.append(f"Triệu chứng '{label}' vừa được ghi nhận vừa bị phủ định; cần xác minh thời điểm hoặc bối cảnh.")
    if side == "hai bên hoặc có dữ kiện trái-phải cần xác minh":
        contradictions.append("Bệnh sử có cả thông tin bên trái và bên phải; cần làm rõ triệu chứng một bên, hai bên hay thay đổi theo thời gian.")

    red_terms = {
        "Rối loạn cơ tròn/bí tiểu mới": ["bi tieu moi xuat hien", "tieu khong tu chu", "mat kiem soat dai tieu tien"],
        "Tê vùng yên ngựa": ["te vung yen ngua", "te vung hoi am"],
        "Yếu tiến triển/hai chân": ["yeu tien trien", "yeu tang dan", "yeu hai chan"],
        "Sốt/rét run": ["sot", "ret run"],
        "Tiền sử ung thư/sụt cân không chủ ý": ["tien su ung thu", "ung thu", "sut can khong chu y"],
        "Chấn thương đáng kể/không chịu lực": ["chan thuong manh", "nga cao", "khong chiu luc duoc", "khong the chiu luc"],
    }
    safety_cues = []
    for label, terms in red_terms.items():
        for term in terms:
            for match in re.finditer(r"(?<!\w)" + re.escape(term) + r"(?!\w)", n):
                if not _negated(n, match.start()):
                    safety_cues.append(label); break
            if label in safety_cues: break

    # Deduplicate repeated source fields/overlapping narrative sections.
    relations = list({(x["type"], x["text"]): x for x in relations}.values())
    causal_chains = list({(x["relation_type"], x["reported_trigger_or_context"], x["reported_outcome"]): x for x in causal_chains}.values())
    aggravating = list(dict.fromkeys(aggravating))
    relieving = list(dict.fromkeys(relieving))
    if "nằm ngửa" in relieving:
        relieving = [x for x in relieving if x not in ("giảm khi nằm",)]
    # Unknown wording is not treated as a negative result.
    unparsed = not bool(unique_symptoms or locations or timeline or relations or safety_cues)
    return {
        "engine": "offline_vietnamese_narrative_parser_1.0",
        "input_sources": [k for k, _ in raw_parts],
        "narrative_length": len(raw),
        "clauses": clauses,
        "symptoms": unique_symptoms,
        "anatomical_locations": locations,
        "laterality": side,
        "timeline_patterns": timeline,
        "explicit_durations": durations,
        "aggravating_factors": aggravating,
        "relieving_factors": relieving,
        "reported_relations": relations,
        "causal_chains": causal_chains,
        "contradictions": list(dict.fromkeys(contradictions)),
        "safety_cues": list(dict.fromkeys(safety_cues)),
        "unparsed_or_sparse": unparsed,
        "limitations": [
            "Bộ phân tích hoạt động offline dựa trên quy tắc ngôn ngữ và từ vựng; cách diễn đạt hoàn toàn mới hoặc thuật ngữ hiếm có thể chưa được nhận diện.",
            "Quan hệ trước-sau hoặc yếu tố làm tăng/giảm không tự chứng minh nguyên nhân bệnh lý.",
            "Không suy diễn triệu chứng không được nhắc đến thành triệu chứng âm tính.",
        ],
    }
