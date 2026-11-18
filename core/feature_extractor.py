"""Trích xuất đặc trưng lâm sàng có cấu trúc từ văn bản thô."""
from __future__ import annotations
import re
import unicodedata
from typing import Any, Dict, Set, List, Tuple


def norm(s: Any) -> str:
    s = str(s or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    return re.sub(r"\s+", " ", s)


SYNONYM_GROUPS: List[List[str]] = [
    ["dau nhoi", "dau choi", "dau buot", "dau sac", "dau nhu dao dam"],
    ["dau am i", "dau mo ho", "dau lan lan", "dau nhe"],
    ["dau du doi", "dau nhuc", "dau moi"],
    ["sung", "phu", "sung ne", "sung vung", "day len"],
    ["long khop", "long leo", "mat vung", "giving way", "khuy goi",
     "cam giac long", "goi long", "truot khop"],
    ["khoa khop", "ket khop", "mac khop", "khong duoi duoc",
     "khong gap duoc", "bi ket"],
    ["tieng pop", "tieng rac", "tieng bat", "tieng tac", "nghe tieng",
     "tieng no", "tieng lao xao"],
    ["te", "cham chich", "kien bo", "nong rat", "di cam", "te bi", "te ran"],
    ["yeu", "mat luc", "suc co giam", "khong co luc", "yeu co"],
    ["cung", "cung khop", "kho van dong", "han che van dong", "cung nhac"],
    ["dau khi chiu luc", "dau khi di lai", "dau khi dung",
     "dau khi len cau thang", "dau khi chay", "dau khi nho got",
     "dau tang khi van dong", "dau khi tai"],
    ["dau ve dem", "dau ban dem", "thuc giac vi dau", "dau khi ngu", "dau dem"],
    ["cung buoi sang", "cung khop buoi sang", "buoc dau buoi sang",
     "sau khi ngoi lau", "sau nghi", "cung sau ngoi", "dau buoi sang"],
]


def _build_synonym_index() -> Dict[str, List[str]]:
    idx: Dict[str, List[str]] = {}
    for group in SYNONYM_GROUPS:
        for term in group:
            idx.setdefault(norm(term), []).extend(group)
    return idx


_SYNONYM_INDEX = _build_synonym_index()


def _expand_synonyms(text: str) -> str:
    t = norm(text)
    extras: List[str] = []
    for term, group in _SYNONYM_INDEX.items():
        if term in t:
            for syn in group:
                if norm(syn) not in t:
                    extras.append(norm(syn))
    if extras:
        return t + " " + " ".join(sorted(set(extras)))
    return t


FEATURES: Dict[str, Dict[str, Any]] = {
    "mechanism_pivot": {
        "terms": ["xoay van", "xoay tru", "chuyen huong", "doi huong", "pivot",
                  "xoay nguoi", "xoay minh", "xoay nhanh"],
        "regions": ["Khớp gối", "Khớp háng"],
        "section_priority": ["onset", "history"],
    },
    "mechanism_direct": {
        "terms": ["va dap truc tiep", "nga dap", "chan thuong truc tiep", "va vao", "dap manh"],
        "regions": ["*"],
        "section_priority": ["onset", "history"],
    },
    "mechanism_hyperextension": {
        "terms": ["goi uon", "duoi qua muc", "hyperextension", "uon nguoc", "goi gap sau"],
        "regions": ["Khớp gối"],
        "section_priority": ["onset"],
    },
    "mechanism_valgus": {
        "terms": ["chan thuong valgus", "luc valgus vao goi", "luc day vao trong", "dap mat trong goi", "chanh vao trong do luc ngoai"],
        "regions": ["Khớp gối"],
        "section_priority": ["onset"],
    },
    "mechanism_varus": {
        "terms": ["varus", "luc varus", "chanh ra ngoai", "luc day ra ngoai"],
        "regions": ["Khớp gối"],
        "section_priority": ["onset"],
    },
    "mechanism_lateral_ankle": {
        "terms": ["lat trong ban chan", "lat co chan", "xoan co chan",
                  "bong gan co chan", "lan trong"],
        "regions": ["Cổ chân – bàn chân"],
        "section_priority": ["onset", "history"],
    },
    "mechanism_twist_load": {
        "terms": ["xoay khi chiu luc", "xoay van chiu luc", "ngoi xo gom",
                  "xoay tren chan tru", "xoay co tai"],
        "regions": ["Khớp gối"],
        "section_priority": ["onset", "history"],
    },
    "mechanism_fall": {
        "terms": ["te nga", "nga", "truot chan", "vap", "nga guc"],
        "regions": ["*"],
        "section_priority": ["onset", "history"],
    },
    "mechanism_lifting_load": {
        "terms": ["nang vat nang", "be vat nang", "be thung hang", "nang thung hang", "cui nguoi nang", "cui be vat", "nang vat tu san", "nang do vat"],
        "regions": ["Cột sống thắt lưng"],
        "section_priority": ["onset", "history", "free_text"],
    },
    "cough_sneeze_aggravation": {
        "terms": ["ho", "hat hoi", "ho hoac hat hoi", "tang khi ho", "tang khi hat hoi"],
        "regions": ["Cột sống thắt lưng"],
        "section_priority": ["course", "associations", "history", "free_text"],
    },
    "swelling_early": {
        "terms": ["sung sau 4 gio", "sung trong vai gio", "sung nhanh sau chan thuong",
                  "tran dich sau chan thuong", "sung xuat hien sau", "sung sau 2 gio",
                  "sung sau 3 gio", "sung sau 1 2 gio", "sung ngay sau chan thuong"],
        "regions": ["Khớp gối", "Cổ chân – bàn chân"],
        "section_priority": ["history", "course"],
    },
    "swelling_late": {
        "terms": ["sung sau 24 gio", "sung tu tu", "sung muon", "sung sau 1 ngay"],
        "regions": ["Khớp gối"],
        "section_priority": ["history", "course"],
    },
    "instability": {
        "terms": ["long khop", "long leo", "mat vung", "giving way", "khuy goi",
                  "cam giac long", "goi long", "truot khop"],
        "regions": ["Khớp gối", "Khớp háng", "Cổ chân – bàn chân"],
        "section_priority": ["history", "associations"],
    },
    "locking": {
        "terms": ["khoa khop", "ket khop", "mac khop", "khong duoi duoc",
                  "khong gap duoc", "bi ket"],
        "regions": ["Khớp gối"],
        "section_priority": ["history", "associations"],
    },
    "pop_sound": {
        "terms": ["tieng pop", "tieng rac", "tieng bat", "tieng tac",
                  "nghe tieng", "tieng no", "tieng lao xao"],
        "regions": ["Khớp gối", "Cổ chân – bàn chân"],
        "section_priority": ["onset", "history"],
    },
    "deep_flexion_pain": {
        "terms": ["dau khi gap sau", "dau gap goi sau", "dau khi ngoi chom ho",
                  "dau khi ngoi xo chom", "dau khi ngoi sau", "dau khi quy goi",
                  "dau khi gap sau sau"],
        "regions": ["Khớp gối"],
        "section_priority": ["course", "history"],
    },
    "night_pain": {
        "terms": ["dau ve dem", "dau ban dem", "thuc giac vi dau",
                  "dau khi ngu", "dau dem"],
        "regions": ["*"],
        "section_priority": ["history", "course"],
    },
    "morning_stiffness": {
        "terms": ["cung buoi sang", "cung khop buoi sang", "buoc dau buoi sang",
                  "sau khi ngoi lau", "sau nghi", "cung sau ngoi", "dau buoi sang"],
        "regions": ["Khớp gối", "Cổ chân – bàn chân", "Cột sống thắt lưng", "Khớp háng"],
        "section_priority": ["history", "course"],
    },
    "loading_pain": {
        "terms": ["dau khi chiu luc", "dau khi di lai", "dau khi dung",
                  "dau khi len cau thang", "dau khi chay", "dau khi nho got",
                  "dau tang khi van dong", "dau khi tai", "dau khi di bo"],
        "regions": ["*"],
        "section_priority": ["history", "course"],
    },
    "relief_with_rest": {
        "terms": ["giam khi nghi", "do khi nghi", "do sau khoi dong", "giam khi ngoi"],
        "regions": ["*"],
        "section_priority": ["course"],
    },
    "joint_line_tenderness_medial": {
        "terms": ["dau khe khop trong", "dau mat trong khe khop", "dau khe khop phia trong"],
        "regions": ["Khớp gối"],
        "section_priority": ["palpation"],
    },
    "joint_line_tenderness_lateral": {
        "terms": ["dau khe khop ngoai", "dau mat ngoai khe khop"],
        "regions": ["Khớp gối"],
        "section_priority": ["palpation"],
    },
    "mcl_tenderness": {
        "terms": ["dau diem bam mcl", "dau day chang ben trong", "an dau mcl",
                  "dau day chang ben trong goi", "dau mat trong goi"],
        "regions": ["Khớp gối"],
        "section_priority": ["palpation"],
    },
    "lcl_tenderness": {
        "terms": ["dau day chang ben ngoai", "an dau lcl", "dau diem bam lcl", "dau doc day chang ben ngoai"],
        "regions": ["Khớp gối"],
        "section_priority": ["palpation"],
    },
    "effusion": {
        "terms": ["tran dich", "bap benh xuong ban che", "dau hieu bulging",
                  "sung khop", "bap benh", "dau hieu tran dich", "dau hieu song"],
        "regions": ["Khớp gối"],
        "section_priority": ["inspection", "palpation"],
    },
    "achilles_thickening": {
        "terms": ["day len", "day gan", "sung gan", "hinh thoi",
                  "dau khi an doc gan", "gan achilles day", "gan got day"],
        "regions": ["Cổ chân – bàn chân"],
        "section_priority": ["inspection", "palpation"],
    },
    "achilles_site_mid": {
        "terms": ["than gan got", "than gan achilles", "cach diem bam 3",
                  "cach diem bam 4", "doan giua gan", "than gan cach"],
        "regions": ["Cổ chân – bàn chân"],
        "section_priority": ["site", "palpation"],
    },
    "achilles_site_insertion": {
        "terms": ["diem bam gan got", "bam xuong got", "sau got", "diem bam xuong"],
        "regions": ["Cổ chân – bàn chân"],
        "section_priority": ["site", "palpation"],
    },
    "plantar_heel_pain": {
        "terms": ["dau got chan", "dau long ban chan", "dau buoc chan dau tien",
                  "dau buoi sang khi moi di", "dau gan chan"],
        "regions": ["Cổ chân – bàn chân"],
        "section_priority": ["site", "history"],
    },
    "groin_pain": {
        "terms": ["dau ben", "dau vung ben", "dau khop hang",
                  "dau mat truoc khop hang", "dau hang", "dau sau trong ben"],
        "regions": ["Khớp háng", "Cột sống thắt lưng"],
        "section_priority": ["site"],
    },
    "lateral_hip_pain": {
        "terms": ["dau mat ngoai khop hang", "dau mat ngoai dui",
                  "dau vung mau chuyen", "dau hong ngoai"],
        "regions": ["Khớp háng"],
        "section_priority": ["site"],
    },
    "deep_gluteal_pain": {
        "terms": ["dau mong", "vung mong", "mong phai", "mong trai",
                  "dau sau mong", "dau sau trong mong"],
        "regions": ["Thần kinh & Khác"],
        "section_priority": ["site"],
    },
    "sitting_aggravation": {
        "terms": ["ngoi lau", "ngoi 30 phut", "ghe cung", "lai xe",
                  "ngoi nhieu", "ngoi"],
        "regions": ["Thần kinh & Khác", "Cột sống thắt lưng"],
        "section_priority": ["history", "course"],
    },
    "posterior_thigh_radiation": {
        "terms": ["mat sau dui", "xuong khoeo", "mat sau bap chan", "lan mat sau dui"],
        "regions": ["Thần kinh & Khác", "Cột sống thắt lưng"],
        "section_priority": ["radiation"],
    },
    "sensory_symptoms": {
        "terms": ["te", "cham chich", "kien bo", "di cam", "te bi", "te ran", "mat cam giac"],
        "regions": ["*"],
        "section_priority": ["associations", "history"],
    },
    "radicular_leg": {
        "terms": ["lan xuong chan", "lan xuong ban chan", "lan xuong ngon chan",
                  "lan toi mu ban chan", "lan den ngon cai", "lan toi ngon cai",
                  "te mu ban chan", "te vung mu ban chan", "kien bo chan", "lan xuong dui",
                  "dau doc mat sau dui va mat ngoai cang chan"],
        "regions": ["Cột sống thắt lưng"],
        "section_priority": ["radiation", "history"],
    },
    "radicular_arm": {
        "terms": ["lan xuong tay", "lan xuong ngon tay", "te ngon tay",
                  "te ban tay", "lan xuong canh tay", "te tay"],
        "regions": ["Cột sống cổ"],
        "section_priority": ["radiation", "history"],
    },
    "arm_weakness": {
        "terms": ["yeu tay", "mat luc tay", "suc co tay giam", "yeu canh tay"],
        "regions": ["Cột sống cổ", "Khớp vai"],
        "section_priority": ["history", "rom_mmt"],
    },
    "leg_weakness": {
        "terms": ["yeu chan", "mat luc chan", "suc co chan giam", "yeu dui", "yeu goi", "ehl trai 4/5", "duoi ngon cai 4/5", "yeu khi nhac mui ban chan", "giam suc co duoi ngon cai"],
        "regions": ["Cột sống thắt lưng"],
        "section_priority": ["history", "associations", "rom_mmt", "free_text"],
    },
    "ehl_weakness": {
        "terms": ["ehl trai 4/5", "ehl 4/5", "co duoi ngon cai dai 4/5", "duoi ngon cai 4/5", "yeu co duoi ngon cai", "extensor hallucis longus 4/5"],
        "regions": ["Cột sống thắt lưng"],
        "section_priority": ["rom_mmt", "associations", "free_text"],
    },
    "reduced_ankle_reflex": {
        "terms": ["phan xa gan got trai giam", "phan xa gan got trai 1+", "gan got trai 1+", "phan xa achilles trai giam", "phan xa gan got ben trai giam"],
        "regions": ["Cột sống thắt lưng"],
        "section_priority": ["rom_mmt", "free_text"],
    },
    "babinski": {
        "terms": ["babinski", "duoi dau ngon chan", "dau hieu babinski"],
        "regions": ["Thần kinh & Khác", "Cột sống cổ"],
        "section_priority": ["rom_mmt"],
    },
    "hyperreflexia": {
        "terms": ["tang phan xa", "phan xa manh", "phan xa tang"],
        "regions": ["Thần kinh & Khác", "Cột sống cổ"],
        "section_priority": ["rom_mmt"],
    },
    "clonus": {
        "terms": ["clonus", "rung giat", "rung co"],
        "regions": ["Thần kinh & Khác", "Cột sống cổ"],
        "section_priority": ["rom_mmt"],
    },
    "lhermitte": {
        "terms": ["lhermitte", "dien giat doc song", "cam giac dien giat"],
        "regions": ["Cột sống cổ"],
        "section_priority": ["history"],
    },
    "saddle_anesthesia": {
        "terms": ["te vung yen ngua", "te vung hoi am", "te vung quanh hau mon"],
        "regions": ["Cột sống thắt lưng"],
        "section_priority": ["associations"],
    },
    "bowel_bladder": {
        "terms": ["bi tieu", "tieu khong tu chu", "dai tien khong tu chu",
                  "mat kiem soat dai tieu tien", "khong kiem soat tieu"],
        "regions": ["Cột sống thắt lưng"],
        "section_priority": ["associations"],
    },
    "gait_disturbance": {
        "terms": ["di loang choang", "mat thang bang", "roi loan dang di",
                  "di khong vung", "di choang"],
        "regions": ["Thần kinh & Khác", "Cột sống cổ"],
        "section_priority": ["history", "inspection"],
    },
    "hand_dexterity_loss": {
        "terms": ["vuong ve ban tay", "roi loan van dong tinh", "kho cam", "kho viet"],
        "regions": ["Cột sống cổ"],
        "section_priority": ["history"],
    },
    "fever": {
        "terms": ["sot", "ret run", "nhiem trung", "sot cao"],
        "regions": ["*"],
        "section_priority": ["history"],
    },
    "weight_loss": {
        "terms": ["sut can", "sut can khong chu y", "ung thu", "giam can"],
        "regions": ["*"],
        "section_priority": ["history"],
    },
    "trauma_significant": {
        "terms": ["chan thuong manh", "nga cao", "khong chiu luc duoc",
                  "khong the chiu luc", "chan thuong nang"],
        "regions": ["*"],
        "section_priority": ["onset", "history"],
    },
    "no_trauma": {
        "terms": ["khong chan thuong", "khong co chan thuong", "khong nga"],
        "regions": ["*"],
        "section_priority": ["history"],
    },

    # Region-specific evidence added in 4.5. These are observed findings, not diagnoses.
    "shoulder_arom_prom_restriction": {
        "terms": ["arom va prom deu han che", "arom va prom đều han che", "ca chu dong va thu dong deu han che", "han che ca chu dong va thu dong", "chu dong va thu dong deu han che"],
        "regions": ["Khớp vai"], "section_priority": ["rom_mmt", "free_text", "history"],
    },
    "shoulder_multiplanar_restriction": {
        "terms": ["han che da huong", "han che gap dang xoay", "han che gap, dang va xoay", "han che nhieu huong"],
        "regions": ["Khớp vai"], "section_priority": ["rom_mmt", "free_text"],
    },
    "shoulder_external_rotation_marked_loss": {
        "terms": ["xoay ngoai 15 do", "xoay ngoai 10 do", "xoay ngoai giam ro", "han che xoay ngoai ro"],
        "regions": ["Khớp vai"], "section_priority": ["rom_mmt", "free_text"],
    },
    "diabetes_history": {
        "terms": ["dai thao duong", "tieu duong type 2", "diabetes mellitus"],
        "regions": ["Khớp vai", "*"], "section_priority": ["history", "free_text"],
    },
    "itb_focal_site": {
        "terms": ["2 cm phia tren loi cau ngoai xuong dui", "2 cm tren loi cau ngoai", "loi cau ngoai xuong dui", "diem bam dai chang chau chau"],
        "regions": ["Khớp gối"], "section_priority": ["site", "palpation", "free_text"],
    },
    "itb_downhill_load": {
        "terms": ["chay xuong doc", "chay trail xuong doc", "xuong doc", "downhill running"],
        "regions": ["Khớp gối"], "section_priority": ["history", "onset", "associations", "course"],
    },
    "itb_flexion_angle_pain": {
        "terms": ["30 do gap goi", "30° gap goi", "goc gap 30 do", "khoang 30 do gap goi"],
        "regions": ["Khớp gối"], "section_priority": ["palpation", "rom_mmt", "free_text"],
    },
    "itb_overuse_running": {
        "terms": ["chay 40-50 km", "chay trail", "tang tai chay", "chay bo nhieu", "chay duong dai"],
        "regions": ["Khớp gối"], "section_priority": ["history", "onset", "free_text"],
    },
}


TEMPORAL_PATTERNS = {
    "acute": r"(dot ngot|cap tinh|sau chan thuong|moi xuat hien|vai gio|sau 4 gio|sau 2 gio|sau 1 2 gio)",
    "subacute": r"(vai ngay|1 tuan|2 tuan|3 tuan|4 tuan|mot tuan|hai tuan|\b\d+\s*tuan\b)",
    "chronic": r"(vai thang|nhieu thang|vai nam|man tinh|keo dai|tren 3 thang|\b[4-9]\s*thang\b|\b\d{2,}\s*thang\b)",
}


def _get_text_fields(data: Dict[str, Any]) -> Dict[str, str]:
    keys = ("free_text", "supplemental_text", "reason", "history", "site", "onset", "character",
            "associations", "course", "inspection", "palpation", "rom_mmt")
    return {k: str(data.get(k, "") or "") for k in keys}


def _has_feature(text: str, terms: List[str]) -> Tuple[bool, bool]:
    """Match evidence with short list-scoped negation.

    Commas do not automatically end Vietnamese negation scope: e.g.
    'không tràn dịch, khóa khớp, mất vững hoặc tê'. Sentence/contrast
    boundaries do. A positive and a negative mention are both retained.
    """
    t = norm(text)
    affirmed = False
    negated = False
    for term in terms:
        term_n = norm(term)
        if not term_n:
            continue
        for match in re.finditer(r"(?<!\w)" + re.escape(term_n) + r"(?!\w)", t):
            prefix = t[max(0, match.start() - 100):match.start()]
            prefix = re.split(r"[.!?;\n]|\b(?:nhung|tuy nhien|song|trai lai|hien tai|luc nay|sau do)\b", prefix)[-1]
            negators = list(re.finditer(r"\b(?:khong co|khong bi|khong thay|khong ghi nhan|khong|chua|phu nhan)\b", prefix))
            is_negated = False
            if negators:
                tail = prefix[negators[-1].end():]
                is_negated = len(tail) <= 75
            if is_negated:
                negated = True
            else:
                affirmed = True
    return affirmed, negated


def extract_features(data: Dict[str, Any], region: str = None) -> Dict[str, Any]:
    region = region or data.get("region", "")
    fields = _get_text_fields(data)
    full_text = " ".join(fields.values())
    # Do not append synonym expansions to source text: doing so destroys negation
    # scope (e.g. "không mất vững" must never become an affirmed synonym).
    full_text_expanded = norm(full_text)

    codes: Set[str] = set()
    negated: Set[str] = set()
    section_matches: Dict[str, List[str]] = {}

    for code, meta in FEATURES.items():
        applies = "*" in meta["regions"] or region in meta["regions"]
        if not applies:
            continue

        affirmed_any = False
        negated_any = False
        matched_sections: List[str] = []

        for section in meta.get("section_priority", []):
            section_text = fields.get(section, "")
            if not section_text:
                continue
            section_text_exp = norm(section_text)
            affirmed, neg = _has_feature(section_text_exp, meta["terms"])
            if affirmed:
                affirmed_any = True
                matched_sections.append(section)
            elif neg:
                negated_any = True

        if not affirmed_any and not negated_any:
            affirmed, neg = _has_feature(full_text_expanded, meta["terms"])
            affirmed_any = affirmed
            negated_any = neg
            if affirmed:
                matched_sections.append("full_text")

        if affirmed_any:
            codes.add(code)
            section_matches[code] = matched_sections
        elif negated_any:
            negated.add(code)

    # Structured neurological findings may be documented in free-form MMT/reflex notes.
    objective_text = norm(" ".join([fields.get("rom_mmt", ""), fields.get("associations", ""), fields.get("free_text", "")]))
    ehl_pattern = r"(?:ehl|duoi ngon cai dai|extensor hallucis longus)[^.;\n]{0,100}?(?:4\s*/\s*5|bac\s*4\s*/\s*5)"
    if re.search(ehl_pattern, objective_text):
        codes.add("ehl_weakness")
        codes.add("leg_weakness")
        section_matches["ehl_weakness"] = ["rom_mmt/free_text"]
    reflex_pattern = r"(?:phan xa gan got|phan xa achilles|gan got)[^.;\n]{0,90}?(?:trai|ben trai)[^.;\n]{0,25}?(?:1\s*\+|giam|yeu)"
    reflex_pattern_reverse = r"(?:trai|ben trai)[^.;\n]{0,50}?(?:phan xa gan got|phan xa achilles)[^.;\n]{0,25}?(?:1\s*\+|giam|yeu)"
    if re.search(reflex_pattern, objective_text) or re.search(reflex_pattern_reverse, objective_text):
        codes.add("reduced_ankle_reflex")
        section_matches["reduced_ankle_reflex"] = ["rom_mmt/free_text"]
    if re.search(r"(?:yeu|giam suc co|suc co giam)[^.;\n]{0,70}(?:chan|ban chan|ngon cai)", objective_text) or re.search(r"yeu[^.;\n]{0,70}(?:nhac mui|duoi ngon cai|di got)", objective_text):
        codes.add("leg_weakness")

    positive, negative, unperformed = [], [], []
    for name, value in (data.get("tests") or {}).items():
        v = norm(value)
        test_name = norm(name).replace("-", " ").replace("–", " ")
        test_name = re.sub(r"\s+", " ", test_name).strip()
        aliases = {
            "lasegue cheo": "crossed_lasegue_test", "crossed lasegue": "crossed_lasegue_test",
            "lasegue": "lasegue_test", "lasègue": "lasegue_test",
            "slr": "slr_test", "straight leg raise": "slr_test",
            "straight leg raise test": "slr_test", "bragard": "bragard_test",
        }
        canonical_test = next((code for alias, code in aliases.items() if alias in test_name), test_name.replace(" ", "_"))
        code = f"test_{canonical_test}"
        if "chua lam" in v or "chua thuc hien" in v:
            unperformed.append(name)
            codes.add(f"{code}_unperformed")
        elif "duong tinh" in v:
            positive.append(name)
            codes.add(f"{code}_pos")
        elif "am tinh" in v:
            negative.append(name)
            codes.add(f"{code}_neg")
        else:
            unperformed.append(name)
            codes.add(f"{code}_unknown")

    temporal_hits = {label: bool(re.search(pattern, full_text_expanded)) for label, pattern in TEMPORAL_PATTERNS.items()}
    # Explicit short recent flare on a documented chronic background.
    has_recent_days = bool(re.search(r"\b\d+\s*ngay\b", full_text_expanded))
    has_chronic_background = temporal_hits.get("chronic", False) or bool(re.search(r"man tinh|keo dai|dau[^.;\n]{0,45}\b\d+\s*nam\b|\d+\s*nam[^.;\n]{0,45}dau", full_text_expanded))
    if has_recent_days and has_chronic_background:
        temporal = "acute_on_chronic"
    elif temporal_hits.get("chronic"):
        temporal = "chronic"
    elif temporal_hits.get("subacute") or has_recent_days:
        temporal = "subacute"
    elif temporal_hits.get("acute"):
        temporal = "acute"
    elif temporal_hits.get("chronic"):
        temporal = "chronic"
    else:
        temporal = "unknown"

    return {
        "codes": codes,
        "positive_tests": positive,
        "negative_tests": negative,
        "unperformed_tests": unperformed,
        "temporal": temporal,
        "raw_text": full_text,
        "negated_features": negated,
        "section_matches": section_matches,
    }