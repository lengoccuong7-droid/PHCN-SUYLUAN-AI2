"""General, explainable clinical reasoning layer for PHCN AI.

This layer is deliberately syndrome-/mechanism-oriented. It does not require a
pre-authored disease rule and never turns missing data into a negative finding.
It is decision support only, not a diagnostic model or a substitute for review.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, List, Tuple

TEXT_FIELDS = (
    "free_text", "supplemental_text", "reason", "history", "site", "onset", "character", "radiation",
    "associations", "course", "inspection", "palpation", "rom_mmt",
)


def normalize(value: Any) -> str:
    text = str(value or "").lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text.replace("đ", "d"))


def _contains(text: str, terms: Iterable[str]) -> bool:
    return any(normalize(term) in text for term in terms)


def _is_negated(text: str, start: int) -> bool:
    """Recognize direct and short list-scoped Vietnamese negation.

    Examples: 'không tê', 'không té ngã/chấn thương',
    'không sưng, nóng, đỏ hoặc đau'. A contrast marker ends the scope.
    """
    prefix = text[max(0, start - 120):start]
    # Do not carry a negation across separate fields or completed sentences.
    prefix = re.split(r"[.!?;\n]", prefix)[-1]
    negators = list(re.finditer(r"\b(?:khong|phu nhan|chua ghi nhan|khong ro)\b", prefix))
    if not negators:
        return False
    last = negators[-1]
    tail = prefix[last.end():]
    if len(tail) > 75:
        return False
    if re.search(r"\b(nhung|tuy nhien|song|ma|nay|sau do)\b", tail):
        return False
    # A later explicit positive clause should not be swallowed by an earlier 'không'.
    return True


def _mentions(text: str, terms: Iterable[str]) -> bool:
    """Match whole clinical terms/phrases, avoiding accidental substrings."""
    for term in terms:
        needle = normalize(term)
        if not needle:
            continue
        pattern = re.compile(r"(?<!\w)" + re.escape(needle) + r"(?!\w)")
        for match in pattern.finditer(text):
            if not _is_negated(text, match.start()):
                return True
    return False


def _field_state(data: Dict[str, Any], key: str, terms: Iterable[str]) -> str:
    """Return present / absent / unknown; absent only when explicitly negated."""
    value = normalize(data.get(key, ""))
    if not value:
        return "unknown"
    if _mentions(value, terms):
        return "present"
    if _contains(value, ["khong", "không", "phu nhan", "phủ nhận"]):
        return "absent"
    return "unknown"


def extract_evidence(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract neutral evidence without assigning a disease label."""
    chunks = {key: normalize(data.get(key, "")) for key in TEXT_FIELDS}
    narrative = "\n".join(chunks.values())
    tests = data.get("tests") or {}
    positive, negative, unperformed = [], [], []
    for name, raw in tests.items():
        state = normalize(raw)
        if "duong tinh" in state:
            positive.append(str(name))
        elif "am tinh" in state:
            negative.append(str(name))
        else:
            unperformed.append(str(name))

    groups = {
        "mechanical_or_load_related": ["tang khi van dong", "dau khi chiu luc", "dau khi di lai", "dau khi len cau thang", "dau khi cui", "giam khi nghi", "tang khi xoay", "dau khi nang tay", "dau tang khi nang tay", "dau khi dang tay", "dau khi chay", "dau tang khi chay", "chay xuong doc", "dau khi xuong doc"],
        "neuropathic_features": ["te", "cham chich", "kien bo", "nong rat", "dien giat", "lan theo duong than kinh", "te theo khoanh da", "yeu co theo khoanh than kinh"],
        "inflammatory_or_systemic_features": ["cung buoi sang keo dai", "sot", "ret run", "met moi toan than", "sung nong do", "dau ve dem khong giam"],
        "traumatic_features": ["nga", "va dap", "chan thuong", "xoay van dot ngot", "nghe tieng rac", "sung nhanh sau chan thuong"],
        "functional_impact": ["kho di lai", "han che di lai", "kho len cau thang", "kho dung lau", "kho nam ngua", "can tro giup", "giam kha nang sinh hoat"],
    }
    detected = {name: _mentions(narrative, terms) for name, terms in groups.items()}

    # Safety cues are intentionally conservative; they trigger review, not diagnosis.
    red_cues = {
        "Rối loạn cơ tròn / bí tiểu mới xuất hiện": ["bi tieu moi xuat hien", "bi tieu", "tieu khong tu chu", "mat kiem soat dai tieu tien"],
        "Tê vùng yên ngựa": ["te vung yen ngua", "te vung hoi am"],
        "Yếu tiến triển hoặc yếu hai chân": ["yeu tien trien", "yeu tang dan", "yeu hai chan"],
        "Sốt / rét run kèm triệu chứng cơ xương khớp": ["sot", "ret run"],
        "Tiền sử ung thư / sụt cân không chủ ý": ["tien su ung thu", "ung thu", "sut can khong chu y"],
        "Chấn thương đáng kể / không chịu lực được": ["chan thuong manh", "nga cao", "khong chiu luc duoc", "khong the chiu luc"],
    }
    warnings = [label for label, terms in red_cues.items() if _mentions(narrative, terms)]

    # Detect explicit contradiction between parallel fields.
    contradictions = []
    radiation = chunks["radiation"]
    combined = " ".join(chunks[k] for k in ("reason", "history", "character", "associations", "course"))
    if _mentions(combined, ["lan xuong tay", "lan xuong chan", "te ngon tay", "te ban chan"]) and _contains(radiation, ["khong lan", "khong co huong lan"]):
        contradictions.append("Bệnh sử mô tả triệu chứng lan/dị cảm nhưng trường hướng lan ghi không lan; cần xác minh.")

    missing = [label for label, key in (
        ("Lý do khám", "reason"), ("Vị trí triệu chứng", "site"),
        ("Thời điểm/kiểu khởi phát", "onset"), ("Diễn tiến", "course"),
        ("Khám thực thể", "inspection"), ("Sờ nắn", "palpation"),
        ("ROM và sức cơ", "rom_mmt"),
    ) if not str(data.get(key, "") or "").strip()]
    if not tests:
        missing.append("Nghiệm pháp phù hợp với giả thuyết đang xem xét")

    return {
        "fields": chunks,
        "positive_tests": positive,
        "negative_tests": negative,
        "unperformed_tests": unperformed,
        "domains": detected,
        "warnings": warnings,
        "contradictions": contradictions,
        "missing": missing,
        "narrative_available": bool(narrative.strip()),
    }


def generate_hypotheses(evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate broad mechanism hypotheses; never invent a specific diagnosis."""
    domains = evidence["domains"]
    candidates: List[Tuple[str, str, List[str]]] = []
    if domains["mechanical_or_load_related"]:
        candidates.append(("Kiểu hình liên quan tải/cơ học", "Triệu chứng có liên hệ với vận động, tư thế hoặc chịu tải.", ["Cần xác định tải nào làm tăng/giảm triệu chứng", "Đối chiếu vị trí đau, ROM, sức cơ và chức năng"]))
    if domains["neuropathic_features"]:
        candidates.append(("Kiểu hình có thành phần thần kinh", "Có mô tả dị cảm, tê, nóng rát, lan hoặc yếu cơ.", ["Lập bản đồ cảm giác và phân bố triệu chứng", "Khám sức cơ, phản xạ và dấu hiệu thần kinh phù hợp"]))
    if domains["inflammatory_or_systemic_features"]:
        candidates.append(("Kiểu hình cần xem xét nguyên nhân viêm/toàn thân", "Có dấu hiệu có thể liên quan viêm hoặc bệnh lý toàn thân; chưa đủ để xác định nguyên nhân.", ["Làm rõ thời gian cứng khớp, triệu chứng toàn thân và diễn tiến", "Cân nhắc đánh giá y khoa khi có dấu hiệu toàn thân"]))
    if domains["traumatic_features"]:
        candidates.append(("Kiểu hình sau chấn thương", "Có cơ chế hoặc diễn tiến gợi ý liên quan chấn thương.", ["Làm rõ cơ chế, thời điểm sưng và khả năng chịu lực", "Kiểm tra tiêu chuẩn cần đánh giá/chẩn đoán hình ảnh"]))
    if domains["functional_impact"]:
        candidates.append(("Suy giảm chức năng cần lượng giá độc lập", "Có ảnh hưởng đến hoạt động hoặc sinh hoạt; cần lượng hóa riêng với nguyên nhân đau.", ["Đo khả năng đi lại, chuyển tư thế và hoạt động mục tiêu", "Ghi nhận mức trợ giúp và giới hạn tham gia"]))

    if not candidates:
        candidates.append(("Chưa xác định được kiểu hình từ dữ liệu hiện tại", "Thông tin hiện có chưa đủ đặc điểm để ưu tiên một nhóm cơ chế.", ["Bổ sung vị trí chính xác, khởi phát, diễn tiến và yếu tố tăng/giảm", "Ghi nhận khám thực thể và nghiệm pháp phù hợp với vùng giải phẫu"]))

    output = []
    for title, rationale, next_steps in candidates:
        output.append({"label": title, "rationale": rationale, "next_steps": next_steps})
    return output



def _all_text(data: Dict[str, Any]) -> str:
    return "\n".join(normalize(data.get(k, "")) for k in TEXT_FIELDS)


def _feature(data: Dict[str, Any], positive_terms: Iterable[str], negative_terms: Iterable[str] = ()) -> str:
    """Tri-state feature extraction: present / absent / unknown.

    A feature is absent only when a corresponding explicit negative is found.
    Missing or unrecognized wording remains unknown.
    """
    text = _all_text(data)
    if _mentions(text, positive_terms):
        return "present"
    if _mentions(text, negative_terms):
        return "absent"
    return "unknown"


def _test_matches(tests: Dict[str, Any], name_terms: Iterable[str], state: str) -> List[str]:
    found = []
    for name, value in (tests or {}).items():
        n_name, n_value = normalize(name), normalize(value)
        if any(normalize(term) in n_name for term in name_terms) and state in n_value:
            found.append(str(name))
    return found


def assess_clinical_patterns(data: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Cross-field pattern synthesis; produces mechanisms, not disease diagnoses.

    It deliberately combines location, loading, motion, time-course and test
    context. No single keyword or special test is sufficient to produce a
    high-confidence conclusion.
    """
    fields = evidence["fields"]
    all_text = "\n".join(fields.values())
    tests = data.get("tests") or {}
    patterns: List[Dict[str, Any]] = []
    gaps: List[str] = []

    gradual = _mentions(all_text, ["tu tu", "dan dan", "khoi phat tu tu", "khong ro chan thuong"])
    trauma = evidence["domains"]["traumatic_features"]
    load_related = evidence["domains"]["mechanical_or_load_related"]
    neuro = evidence["domains"]["neuropathic_features"]
    systemic = evidence["domains"]["inflammatory_or_systemic_features"]

    # Shoulder/other joint stiffness: require both active and passive restriction
    # in the supplied narrative, with no assumption that a named disorder is proven.
    active_passive = _mentions(all_text, ["han che ca chu dong va thu dong", "han che rom chu dong va thu dong", "rom chu dong va thu dong deu han che", "arom va prom deu han che"])
    global_restriction = _mentions(all_text, ["han che da huong", "han che toan bo", "han che nhieu huong", "han che gap dang xoay", "han che gap, dang va xoay"])
    external_rotation = _mentions(all_text, ["xoay ngoai han che", "han che xoay ngoai", "external rotation han che", "xoay ngoai giam ro"])
    shoulder_location = _mentions(all_text, ["vai", "khop vai", "deltoid", "co delta"])
    if shoulder_location and (active_passive or (global_restriction and external_rotation)):
        support = []
        if active_passive: support.append("Cả vận động chủ động và thụ động đều được mô tả hạn chế")
        if global_restriction: support.append("Hạn chế vận động có tính đa hướng")
        if external_rotation: support.append("Xoay ngoài bị hạn chế nổi bật")
        if gradual: support.append("Diễn tiến khởi phát từ từ")
        patterns.append({
            "label": "Kiểu hình cứng khớp vai / hạn chế vận động khớp đa hướng",
            "support": support,
            "counterpoints": ["Cần phân biệt hạn chế do đau với co rút bao khớp hoặc bệnh lý thoái hóa khớp", "Cần xác nhận ROM thụ động bằng đo lường chuẩn và so sánh hai bên"],
            "interpretation": "Mẫu hạn chế vận động khớp đa hướng được ưu tiên đánh giá hơn một giả thuyết chỉ dựa vào đau khi nâng tay.",
            "confidence": "moderate" if active_passive and (global_restriction or external_rotation) else "low",
        })
        gaps.extend(["Đo riêng AROM và PROM theo các mặt phẳng, ghi góc và cảm giác cuối tầm", "Xác định hạn chế có vượt quá mức giải thích bởi đau hay không", "Cân nhắc đánh giá hình ảnh khi cần loại trừ bệnh lý cấu trúc khớp theo chỉ định"])

    # Focal load-related soft-tissue pattern. The engine describes the location
    # and loading behavior rather than naming a specific syndrome from one test.
    lateral_knee = _mentions(all_text, ["mat ngoai goi", "ngoai goi", "loi cau ngoai xuong dui", "tren loi cau ngoai", "lateral femoral epicondyle"])
    angle_30 = _mentions(all_text, ["30 do", "30°", "khoang 30", "goc gap goi 30"])
    downhill = _mentions(all_text, ["xuong doc", "chay xuong doc", "doan doc xuong", "downhill"])
    focal = _mentions(all_text, ["dau khu tru", "an dau khu tru", "diem dau khu tru", "tenderness khu tru"])
    if lateral_knee and load_related and (angle_30 or downhill or focal):
        support = ["Đau vùng ngoài gối có liên hệ với hoạt động hoặc tải"]
        if angle_30: support.append("Triệu chứng được tái hiện quanh góc gấp gối khoảng 30°")
        if downhill: support.append("Đau tăng khi chạy hoặc di chuyển xuống dốc")
        if focal: support.append("Có mô tả đau khu trú khi sờ nắn")
        positive_lateral = _test_matches(tests, ["noble"], "duong tinh")
        if positive_lateral: support.append("Nghiệm pháp Noble được ghi dương tính; chỉ là dữ kiện hỗ trợ trong bối cảnh phù hợp")
        patterns.append({
            "label": "Kiểu hình đau mô mềm vùng ngoài gối liên quan tải và góc gấp",
            "support": support,
            "counterpoints": ["Cần phân biệt cấu trúc dải chậu-chày với sụn chêm ngoài, dây chằng bên ngoài, gân cơ nhị đầu đùi và cơ khoeo", "Nghiệm pháp đơn lẻ không đủ xác nhận cấu trúc gây đau"],
            "interpretation": "Vị trí giải phẫu và điều kiện tái hiện đau có giá trị hơn việc chỉ ghi nhận đau mặt ngoài gối.",
            "confidence": "moderate" if len(support) >= 3 else "low",
        })
        gaps.extend(["Khoanh chính xác điểm đau so với lồi cầu ngoài, khe khớp ngoài và đầu xương mác", "Xác định nghiệm pháp nào tái hiện đúng cơn đau quen thuộc", "Đánh giá đáp ứng với tải, chạy xuống dốc và kiểm soát chi dưới khi squat một chân"])

    # Neurological pattern requires sensory/radiating features; weakness alone
    # is not assumed to be neurogenic without distribution/reflex context.
    if neuro:
        patterns.append({
            "label": "Kiểu hình có thành phần thần kinh cần định khu",
            "support": ["Có mô tả tê, dị cảm, nóng rát, lan theo đường thần kinh hoặc yếu cơ"],
            "counterpoints": ["Đau lan đơn thuần không xác định được rễ thần kinh hay dây thần kinh ngoại biên", "Cần đối chiếu phân bố cảm giác, sức cơ theo nhóm cơ và phản xạ"],
            "interpretation": "Chỉ định hướng có thành phần thần kinh; chưa đủ để xác định vị trí tổn thương.",
            "confidence": "low",
        })
        # Ask only for neurological elements not already documented in the case.
        sensory_map = _mentions(all_text, ["ban do cam giac", "theo khoanh da", "dermatome", "phan bo cam giac l4", "phan bo cam giac l5", "phan bo cam giac s1"])
        mmt_recorded = _mentions(all_text, ["mmt", "suc co", "4/5", "5/5", "bac 4", "bac 5"])
        reflex_recorded = _mentions(all_text, ["phan xa gan goi", "phan xa gan got", "phan xa achilles"])
        nerve_test_recorded = bool(tests) or _mentions(all_text, ["lasegue", "slr", "bragard", "straight leg raise"])
        if not sensory_map:
            gaps.append("Lập bản đồ cảm giác theo khoanh da L4-L5-S1 và so sánh hai bên")
        if not mmt_recorded:
            gaps.append("Khám sức cơ theo nhóm cơ/myotome hai bên và ghi MMT")
        if not reflex_recorded:
            gaps.append("Ghi phản xạ gân gối và gân gót hai bên")
        if not nerve_test_recorded:
            gaps.append("Thực hiện nghiệm pháp căng thần kinh phù hợp khi có chỉ định")

    if systemic:
        patterns.append({
            "label": "Kiểu hình cần sàng lọc nguyên nhân viêm hoặc toàn thân",
            "support": ["Có ít nhất một dấu hiệu toàn thân/viêm được mô tả; cần xác minh bối cảnh"],
            "counterpoints": ["Các dấu hiệu như đau đêm hoặc cứng buổi sáng không tự xác định bệnh viêm"],
            "interpretation": "Ưu tiên làm rõ triệu chứng toàn thân và nguy cơ trước khi quy kết nguyên nhân cơ học.",
            "confidence": "low",
        })
        gaps.append("Làm rõ sốt, sụt cân, thời gian cứng khớp buổi sáng, bệnh nền và diễn tiến")

    if trauma:
        patterns.append({
            "label": "Kiểu hình liên quan chấn thương",
            "support": ["Có mô tả cơ chế chấn thương hoặc khởi phát sau chấn thương"],
            "counterpoints": ["Cần xác định mức năng lượng chấn thương, sưng, bầm, mất vững và khả năng chịu lực"],
            "interpretation": "Cần đánh giá tổn thương cấu trúc theo cơ chế và dấu hiệu khám; không suy ra loại tổn thương từ cơ chế đơn độc.",
            "confidence": "low",
        })
        gaps.append("Làm rõ cơ chế, thời điểm sưng/bầm và khả năng chịu lực ngay sau chấn thương")

    if not patterns:
        patterns.append({
            "label": "Chưa hình thành được kiểu hình lâm sàng đủ đặc trưng",
            "support": [],
            "counterpoints": ["Không có nghĩa là không có bệnh lý; dữ liệu hiện tại có thể chưa đủ hoặc cách diễn đạt chưa được nhận diện"],
            "interpretation": "Không ép hệ thống chọn bệnh. Cần bổ sung bệnh sử, vị trí giải phẫu và khám có mục tiêu.",
            "confidence": "insufficient",
        })
        gaps.extend(["Xác định vị trí giải phẫu chính xác và bên bị ảnh hưởng", "Làm rõ khởi phát, diễn tiến và yếu tố tăng/giảm triệu chứng", "Ghi nhận ROM, sức cơ, chức năng và nghiệm pháp phù hợp"])

    return {"patterns": patterns, "targeted_gaps": list(dict.fromkeys(gaps))}

def reason_case(data: Dict[str, Any], disease_result: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Combine generic reasoning with the legacy region-specific engine result."""
    evidence = extract_evidence(data)
    candidates = generate_hypotheses(evidence)
    pattern_assessment = assess_clinical_patterns(data, evidence)
    legacy_hypotheses = (disease_result or {}).get("hypotheses", [])
    # A specific rule can enrich the broad reasoning, but cannot erase uncertainty.
    known_specific = [x for x in legacy_hypotheses if x and "chưa đủ dữ liệu" not in normalize(x) and "chưa phân nhóm" not in normalize(x)]
    warnings = list(dict.fromkeys(evidence["warnings"] + (disease_result or {}).get("red_flags", [])))
    unresolved = list(evidence["missing"])
    unresolved.extend(evidence["contradictions"])
    unresolved.extend(pattern_assessment["targeted_gaps"])
    all_case_text = "\n".join(normalize(data.get(k, "")) for k in TEXT_FIELDS)
    has_rom = bool(normalize(data.get("rom_mmt", "")))
    has_exam = bool(normalize(data.get("inspection", "")) or normalize(data.get("palpation", "")))
    for item in candidates:
        for step in item["next_steps"]:
            step_n = normalize(step)
            if "doi chieu vi tri dau, rom, suc co" in step_n and has_rom:
                continue
            if "kham suc co, phan xa va dau hieu than kinh" in step_n and has_rom and bool(data.get("tests")):
                continue
            if "ghi nhan kham thuc the" in step_n and has_exam:
                continue
            unresolved.append(step)
    unresolved = list(dict.fromkeys(unresolved))
    # Prefer one precise neurological gap over the generic duplicate prompt.
    if any("Lập bản đồ cảm giác theo khoanh da" in x for x in unresolved):
        unresolved = [x for x in unresolved if x != "Lập bản đồ cảm giác và phân bố triệu chứng"]

    if warnings:
        certainty = "Tạm dừng định hướng PHCN thường quy; cần ưu tiên đánh giá an toàn/y khoa."
    elif not evidence["narrative_available"] or len(evidence["missing"]) >= 5:
        certainty = "Chưa đủ dữ liệu để hình thành giả thuyết có độ tin cậy."
    elif evidence["contradictions"]:
        certainty = "Độ chắc chắn thấp: có dữ liệu mâu thuẫn cần xác minh."
    elif len(candidates) >= 2 and known_specific:
        certainty = "Có nhiều nhóm cơ chế cần đối chiếu; giả thuyết bệnh lý cụ thể chỉ là hướng cần kiểm chứng."
    else:
        certainty = "Định hướng sơ bộ theo nhóm cơ chế; chưa phải chẩn đoán xác định."

    return {
        "engine": "general_reasoning_v1",
        "evidence": evidence,
        "mechanism_hypotheses": candidates,
        "clinical_patterns": pattern_assessment["patterns"],
        "known_rule_hypotheses": known_specific,
        "warnings": warnings,
        "contradictions": evidence["contradictions"],
        "information_gaps": unresolved,
        "certainty": certainty,
        "scope_note": "Bộ suy luận tổng quát hỗ trợ phân nhóm và đặt câu hỏi; không tự xác nhận bệnh lý, không thay thế khám trực tiếp.",
    }
