"""PHCN AI 1.9 - Engine suy luận lâm sàng có đối soát ngược.
Offline, giải thích được; không thay thế bác sĩ khám trực tiếp.
"""
from __future__ import annotations
import re, unicodedata
from typing import Dict, List, Any


def norm(s: Any) -> str:
    s = str(s or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    return re.sub(r"\s+", " ", s)


def has(text: str, *terms: str) -> bool:
    t = norm(text)
    return any(norm(x) in t for x in terms)


def affirmed(text: str, *terms: str) -> bool:
    """Match whole clinical terms and respect explicit negation/list scope."""
    t = norm(text)
    for term in terms:
        term_n = norm(term)
        if not term_n:
            continue
        pattern = re.compile(r"(?<!\w)" + re.escape(term_n) + r"(?!\w)")
        for match in pattern.finditer(t):
            prefix = t[max(0, match.start() - 120):match.start()]
            prefix = re.split(r"[.!?;\n]", prefix)[-1]
            neg = list(re.finditer(r"\b(?:khong|phu nhan|chua ghi nhan|khong ro)\b", prefix))
            if neg:
                tail = prefix[neg[-1].end():]
                if len(tail) <= 75 and not re.search(r"\b(nhung|tuy nhien|song|ma|nay|sau do)\b", tail):
                    continue
            return True
    return False


def _test_state(results: Dict[str, str]) -> Dict[str, List[str]]:
    """Keep positive, negative and not-performed test states separate."""
    positive, negative, unperformed = [], [], []
    for name, value in (results or {}).items():
        value_n = norm(value)
        if "chua lam" in value_n or "chua thuc hien" in value_n:
            unperformed.append(name)
        elif "duong tinh" in value_n:
            positive.append(name)
        elif "am tinh" in value_n:
            negative.append(name)
        else:
            # Empty, not performed, or any unrecognized state remains unknown.
            unperformed.append(name)
    return {"positive": positive, "negative": negative,
            "unperformed": unperformed, "unknown": unperformed}


def analyze_case(data: Dict[str, Any]) -> Dict[str, Any]:
    region = data.get("region", "Chưa xác định")
    tests = _test_state(data.get("tests", {}))
    pos = tests["positive"]
    unknown_tests = tests["unperformed"]
    negative_tests = tests["negative"]
    history = " ".join(str(data.get(k, "") or "") for k in ["reason", "history", "site", "onset", "character", "radiation", "associations", "course"])
    exam = " ".join(str(data.get(k, "") or "") for k in ["inspection", "palpation", "rom_mmt"])
    all_text = norm(history + " " + exam)
    red_checked = data.get("red_flags", {})
    red_positive = [label for label, checked in red_checked.items() if checked]

    # Symptom-derived warning terms: prompts review; not a diagnosis.
    warning_terms = {
        "Rối loạn cơ tròn / bí tiểu / mất kiểm soát đại tiểu tiện": ["bi tieu", "bi tieu", "tieu khong tu chu", "dai tien khong tu chu", "mat kiem soat dai tieu tien"],
        "Yếu cơ tiến triển / yếu hai chân / dáng đi xấu nhanh": ["yeu tang dan", "yeu tien trien", "yeu hai chan", "di lai xau nhanh"],
        "Tê vùng yên ngựa": ["te vung yen ngua", "te vung hoi am"],
        "Sốt / rét run / dấu nhiễm trùng": ["sot", "ret run", "nhiem trung"],
        "Tiền sử ung thư / sụt cân không chủ ý": ["ung thu", "sut can khong chu y"],
        "Chấn thương đáng kể / không chịu lực được": ["chan thuong manh", "nga cao", "khong chiu luc duoc", "khong the chiu luc"],
    }
    inferred_warnings=[]
    for label, terms in warning_terms.items():
        if affirmed(all_text, *terms): inferred_warnings.append(label)
    all_red = list(dict.fromkeys(red_positive + inferred_warnings))

    missing=[]
    required = [("Lý do khám", "reason"), ("Vị trí triệu chứng", "site"), ("Diễn tiến", "course"), ("Khám thực thể", "inspection"), ("ROM/MMT", "rom_mmt")]
    for label,key in required:
        if not str(data.get(key, "") or "").strip(): missing.append(label)
    if not str(data.get("radiation", "") or "").strip(): missing.append("Hướng lan / xác nhận không lan")
    if not data.get("tests"): missing.append("Kết quả nghiệm pháp")

    # Explicitly separate findings that support, oppose, or remain unknown.
    supporting=[]; opposing=[]; unresolved=[]; hypotheses=[]; clinical_cautions=[]
    radicular = affirmed(history, "lan xuong chan", "lan xuong ban chan", "lan xuong ngon chan", "lan xuong tay", "te bi", "kien bo")
    no_radiation = has(data.get("radiation", ""), "khong lan", "khong co huong lan", "khong lan xa")
    mechanical = affirmed(history, "khoa khop", "ket khop", "luc cuc", "sung sau van dong", "dau khi xoay")
    groin = affirmed(history, "dau ben", "dau vung ben", "dau mat truoc khop hang", "dau hang")
    weakness = affirmed(exam, "yeu co", "mat luc", "suc co giam")
    trauma = affirmed(history, "nga", "va dap", "chan thuong", "xoay van")

    # Region-specific pattern hypotheses. No single special test is treated as confirmatory.
    if region == "Cột sống thắt lưng":
        if radicular and any("Lasègue" in x or "SLR" in x or "Bragard" in x for x in pos):
            hypotheses.append("Kiểu hình đau thắt lưng kèm triệu chứng kiểu rễ thần kinh: cần khám thần kinh theo rễ và đối chiếu phân bố đau/tê.")
            supporting += ["Có mô tả triệu chứng lan hoặc dị cảm", "Có ít nhất một nghiệm pháp căng thần kinh được ghi dương tính"]
        elif radicular:
            hypotheses.append("Có triệu chứng lan/dị cảm; chưa đủ dữ liệu để quy kết bệnh lý rễ thần kinh.")
            supporting.append("Bệnh sử có mô tả lan hoặc dị cảm")
        else:
            hypotheses.append("Đau thắt lưng chưa phân nhóm được từ dữ liệu hiện có; cần phân biệt đau cơ học, đau quy chiếu, đau kiểu rễ và nguyên nhân ngoài cơ xương khớp.")
        if no_radiation and radicular: opposing.append("Bệnh sử có mô tả lan nhưng trường hướng lan lại ghi không lan: cần xác minh trực tiếp.")
        if has(all_text, "tang khi cui", "tang khi ngoi lau", "giam khi di lai"): supporting.append("Có mô tả liên quan tư thế/tải cơ học")
    elif region == "Cột sống cổ":
        arm_rad = has(history, "lan xuong tay", "lan xuong ngon tay", "te ngon tay", "te ban tay")
        if arm_rad and "Spurling Test" in pos:
            hypotheses.append("Có kiểu hình nghi kích thích rễ thần kinh cổ; cần đối chiếu cảm giác, sức cơ, phản xạ theo khoanh tủy và loại trừ bệnh lý tủy.")
            supporting += ["Triệu chứng lan/dị cảm chi trên", "Spurling được ghi dương tính"]
        elif arm_rad:
            hypotheses.append("Có triệu chứng chi trên; cần phân biệt nguồn gốc cổ, thần kinh ngoại biên và bệnh lý vai.")
            supporting.append("Có mô tả lan/tê chi trên")
        else:
            hypotheses.append("Chưa đủ dữ liệu phân loại đau cổ; cần đánh giá vận động cổ, thần kinh chi trên và dấu hiệu bệnh lý tủy.")
        if "Lhermitte Sign" in pos or "Babinski Sign" in pos: all_red.append("Dấu hiệu gợi ý tổn thương đường dẫn truyền trung ương/tủy: cần đánh giá y khoa sớm")
    elif region == "Khớp vai":
        cuff_tests=[x for x in pos if any(k in x for k in ["Jobe", "Neer", "Hawkins"])]
        if cuff_tests and has(history, "dau khi nang tay", "dau khi dang tay", "dau ve dem", "dau khi nam nghieng"):
            hypotheses.append("Kiểu hình đau vai liên quan chóp xoay/chạm dưới mỏm cùng có thể được cân nhắc; các test dương tính không tự xác nhận rách gân.")
            supporting += ["Có test vai liên quan chóp xoay/chạm vai dương tính", "Bệnh sử có đau khi nâng/dạng tay hoặc đau về đêm"]
        elif cuff_tests:
            hypotheses.append("Có test vai dương tính nhưng bệnh sử chưa đủ tương hợp; cần xác minh vị trí đau, cung đau, sức cơ và ROM thụ động.")
        else:
            hypotheses.append("Chưa đủ dữ liệu phân nhóm đau vai; cần phân biệt bệnh lý chóp xoay, đông cứng khớp vai, khớp cùng-đòn và đau quy chiếu từ cổ.")
        if has(exam, "rom thu dong han che", "han che rom thu dong", "xoay ngoai han che"): supporting.append("Ghi nhận hạn chế ROM thụ động; cần đối chiếu kiểu hạn chế đa hướng")
    elif region == "Khớp gối":
        # Knee reasoning uses the complete structured narrative, not only test names.
        knee_text = norm(" ".join(str(data.get(k, "") or "") for k in (
            "reason", "history", "site", "onset", "character", "radiation",
            "associations", "course", "inspection", "palpation", "rom_mmt"
        )))
        test_lookup = {norm(name): norm(value) for name, value in (data.get("tests") or {}).items()}
        def _matching_test_states(*names):
            return [value for key, value in test_lookup.items()
                    if any(norm(n) in key or key in norm(n) for n in names)]
        def test_is_positive(*names):
            return any("duong tinh" in value for value in _matching_test_states(*names))
        def test_is_negative(*names):
            return any("am tinh" in value and "chua" not in value
                       for value in _matching_test_states(*names))
        def contains(*terms):
            return affirmed(knee_text, *terms)

        pivot = contains("xoay van", "xoay tren chan tru", "chan tru co dinh", "doi huong dot ngot", "chuyen huong khi da bong")
        pop = contains("nghe tieng rac", "tieng pop", "tieng bat", "tieng tac")
        early_swelling = contains("sung sau 4 gio", "sung trong vai gio", "sung xuat hien sau", "sung nhanh sau chan thuong", "tran dich sau chan thuong")
        instability = contains("goi long", "long khop", "cam giac long khop", "mat vung goi", "giving way", "khuy goi")
        lachman_pos = test_is_positive("Lachman Test", "Lachman")
        drawer_pos = test_is_positive("Anterior Drawer Test", "Anterior Drawer")
        acl_support = []
        if pivot: acl_support.append("Cơ chế xoay vặn/chuyển hướng trên chân trụ")
        if pop: acl_support.append("Có tiếng kêu tại thời điểm chấn thương")
        if early_swelling: acl_support.append("Sưng xuất hiện trong vài giờ sau chấn thương")
        if instability: acl_support.append("Có cảm giác gối mất vững/lỏng khớp")
        if lachman_pos: acl_support.append("Lachman được ghi dương tính")
        if drawer_pos: acl_support.append("Anterior Drawer được ghi dương tính")
        acl_related = pivot or pop or early_swelling or instability or lachman_pos or drawer_pos
        if acl_related:
            hypotheses.append("Tổn thương dây chằng chéo trước (ACL) là giả thuyết cần ưu tiên kiểm chứng; tổ hợp cơ chế chấn thương, diễn tiến sưng, cảm giác mất vững và nghiệm pháp có thể làm tăng nghi ngờ nhưng không xác định mức độ rách.")
            supporting.extend(acl_support)
            if test_is_negative("Lachman Test", "Lachman"):
                opposing.append("Lachman được ghi âm tính; cần xem xét kỹ thuật, điểm cuối và so sánh hai bên, không dùng riêng test này để loại trừ ACL.")
            if test_is_negative("Anterior Drawer Test", "Anterior Drawer"):
                opposing.append("Anterior Drawer được ghi âm tính; diễn giải cùng các dấu hiệu khác và chất lượng thực hiện.")
            unresolved.extend(["So sánh độ dịch chuyển và điểm cuối Lachman hai bên", "Đánh giá tràn dịch và khả năng chịu lực", "Xác định mức độ mất vững qua khám trực tiếp"])

        medial_joint_pain = contains("dau khe khop trong", "dau mat trong khe khop", "dau khe khop phia trong")
        medial_mcl_tender = contains("diem bam mcl", "dau day chang ben trong", "an dau mcl", "dau day chang ben trong goi")
        twist_load = pivot or contains("xoay khi chiu luc", "xoay van chiu luc", "ngoi xo gom")
        deep_flexion = contains("dau khi gap sau", "dau gap goi sau", "dau khi ngoi chom ho", "dau khi ngoi xo chom")
        locking = contains("khoa khop", "ket khop", "mac khop")
        mcmurray_pos = test_is_positive("McMurray Test", "McMurray")
        meniscus_support=[]
        if medial_joint_pain: meniscus_support.append("Đau khu trú khe khớp trong")
        if twist_load: meniscus_support.append("Cơ chế xoay vặn khi chịu tải")
        if deep_flexion: meniscus_support.append("Đau tăng khi gấp gối sâu/ngồi xổm")
        if locking: meniscus_support.append("Có triệu chứng khóa/kẹt khớp được mô tả")
        if mcmurray_pos: meniscus_support.append("McMurray được ghi dương tính")
        if len(meniscus_support) >= 2 or mcmurray_pos:
            hypotheses.append("Tổn thương sụn chêm, đặc biệt sụn chêm trong, cần được đưa vào chẩn đoán phân biệt; đau khe khớp hoặc cơ chế xoay không tự chứng minh rách sụn chêm.")
            supporting.extend(meniscus_support)
        if test_is_negative("McMurray Test", "McMurray"):
            opposing.append("McMurray được ghi âm tính; kết quả này không tự loại trừ tổn thương sụn chêm.")
        if not mcmurray_pos and not test_is_negative("McMurray Test", "McMurray"):
            unresolved.append("McMurray chưa có kết quả được xác nhận; không diễn giải là âm tính.")
        unresolved.extend(["Xác minh có khóa khớp thật sự hay chỉ đau/hạn chế do sưng", "Đối chiếu vị trí đau khe khớp với khám trực tiếp"])

        if medial_mcl_tender:
            hypotheses.append("Tổn thương dây chằng bên trong (MCL) hoặc cấu trúc vùng trong gối cần được xem xét do có đau khu trú; cần đánh giá độ vững valgus ở 0° và 30° bởi người có chuyên môn.")
            supporting.append("Đau khi ấn vùng dây chằng/điểm bám MCL được mô tả")
            unresolved.append("Chưa có kết quả nghiệm pháp valgus stress ở 0° và 30°")

        if not acl_related and not meniscus_support and not medial_mcl_tender:
            hypotheses.append("Chưa đủ dữ liệu phân loại đau gối; cần đánh giá tràn dịch, khả năng chịu lực, ROM, vị trí đau, cơ chế khởi phát và nghiệm pháp phù hợp.")

        # Capture functional/objective findings so the report does not silently ignore them.
        if contains("sung", "tran dich", "bap benh xuong ban che"):
            supporting.append("Có mô tả sưng/tràn dịch hoặc dấu hiệu gợi ý dịch khớp")
        if contains("rom", "0-95", "0–95", "han che gap goi", "gap goi 95"):
            supporting.append("Có ghi nhận ROM gối hạn chế; cần đối chiếu bên lành và đo chuẩn hóa")
        if contains("mmt", "4/5", "suc co giam", "co tu dau", "hamstring"):
            supporting.append("Có dữ liệu sức cơ; cần ghi rõ nhóm cơ, bên và phương pháp lượng giá")
        if contains("khong te", "khong yeu ban chan", "mach mu chan ro", "mach chay sau ro"):
            supporting.append("Có ghi nhận một số dấu hiệu thần kinh-mạch máu ngoại vi; vẫn cần khám đầy đủ khi có chỉ định")

        if not str(data.get("rom_mmt", "") or "").strip():
            missing.extend(["ROM chủ động/thụ động hai bên", "Sức cơ các nhóm cơ quanh gối"])
        if not any(x in knee_text for x in ("chiu luc", "di lai", "di duoc", "di khong duoc", "di khap khieng")):
            missing.append("Khả năng chịu trọng lượng và đi lại")
        if not any(x in knee_text for x in ("valgus", "mcl stress", "day chang ben trong")):
            missing.append("Đánh giá độ vững MCL bằng valgus stress khi phù hợp")
        if not any(x in knee_text for x in ("khoa khop", "ket khop", "khong khoa khop")):
            missing.append("Có hay không triệu chứng khóa/kẹt khớp")
        if trauma and (early_swelling or instability or lachman_pos or drawer_pos):
            clinical_cautions.append("Chấn thương gối cấp kèm sưng hoặc dấu hiệu mất vững: cần được bác sĩ/chuyên gia chấn thương chỉnh hình đánh giá trực tiếp sớm; tạm tránh thể thao, xoay vặn và tải mạnh cho đến khi được đánh giá.")
    elif region == "Khớp háng":
        if groin and ("FADIR Test" in pos or "FABER / Patrick Test" in pos):
            hypotheses.append("Đau vùng bẹn kèm test khớp háng dương tính: cần đánh giá bệnh lý nội khớp háng; không thể kết luận FAI chỉ từ FADIR.")
            supporting += ["Đau vùng bẹn được mô tả", "Có test kích thích khớp háng dương tính"]
        else: hypotheses.append("Chưa đủ dữ liệu phân loại đau háng; cần phân biệt nội khớp, quanh khớp, cột sống thắt lưng và nguyên nhân vùng chậu.")
    elif region == "Cổ chân – bàn chân":
        achilles_site = has(history, "gan got", "gân gót", "achilles", "than gan got", "than gan got cach diem bam", "sau got")
        loading_pain = has(history, "nhon got", "chay", "leo cau thang", "buoc dai", "di bo", "chiu luc")
        morning_stiffness = has(history, "buoc dau buoi sang", "cung buoi sang", "sau khi ngoi lau", "sau nghi")
        achilles_thickening = has(exam, "day len", "day gan", "sung gan", "hinh thoi", "dau khi an doc gan")
        achilles_tests = [x for x in pos if any(k in norm(x) for k in ("royal london", "painful arc", "arc sign"))]
        thompson_negative = any("thompson" in norm(x) for x in negative_tests)
        if achilles_site and loading_pain and (morning_stiffness or achilles_thickening or achilles_tests):
            hypotheses.append("Kiểu hình đau gân Achilles liên quan tải (Achilles tendinopathy) cần được cân nhắc. Cần phân biệt thể đoạn giữa với thể điểm bám và loại trừ tổn thương cấu trúc khác; chưa đủ cơ sở xác định mức độ tổn thương.")
            supporting.extend(["Đau khu trú vùng gân Achilles", "Đau tăng khi hoạt động chịu tải/nhón gót" if loading_pain else "Có triệu chứng liên quan tải"])
            if morning_stiffness: supporting.append("Có cứng đau bước đầu buổi sáng hoặc sau thời gian nghỉ")
            if achilles_thickening: supporting.append("Khám ghi nhận dày/sưng vùng gân")
            if achilles_tests: supporting.append("Có nghiệm pháp gợi ý bệnh lý gân Achilles dương tính: " + ", ".join(achilles_tests))
            if thompson_negative:
                opposing.append("Thompson âm tính làm giảm nghi ngờ đứt hoàn toàn gân Achilles nhưng không loại trừ rách một phần hoặc bệnh lý gân.")
            unresolved.extend(["Xác định đau ở đoạn giữa gân hay ngay điểm bám xương gót", "Đánh giá khả năng và chất lượng nhón gót một chân", "Định lượng sức bền cơ gấp gan chân và đáp ứng với tải", "Khám sưng nóng, bầm tím, khuyết gân và khả năng chịu lực"])
        else:
            hypotheses.append("Chưa đủ dữ kiện nhận diện kiểu hình bệnh lý cổ chân – bàn chân. Cần xác định chính xác vị trí đau, cơ chế khởi phát, quan hệ với tải, ROM, sức cơ và nghiệm pháp theo cấu trúc nghi ngờ.")
        if affirmed(all_text, "tieng no", "nghe tieng rac", "dut phut", "lo khuyet gan", "co khuyet gan", "khong the nhon got", "khong di duoc"):
            clinical_cautions.append("Có dấu hiệu cần loại trừ tổn thương gân cấp hoặc mất chức năng chịu lực; cần đánh giá y khoa trực tiếp trước khi tập tải.")
    elif region == "Thần kinh & Khác":
        deep_gluteal_pain = has(history, "dau mong", "vung mong", "mong phai", "mong trai", "dau sau mong")
        sitting_aggravation = has(history, "ngoi lau", "ngoi 30 phut", "ghe cung", "lai xe", "ngoi")
        posterior_radiation = has(history, "mat sau dui", "xuong khoeo", "mat sau bap chan")
        sensory = has(history, "te", "cham chich", "kien bo", "nong rat")
        provocative = [x for x in pos if any(k in norm(x) for k in ("fair", "pace", "reiberg", "f Freiberg".lower()))]
        slr_negative = any("slr" in norm(x) or "lasegue" in norm(x) for x in negative_tests)
        if deep_gluteal_pain and sitting_aggravation and (posterior_radiation or sensory) and provocative:
            hypotheses.append("Kiểu hình đau mông sâu (deep gluteal pain syndrome) cần được cân nhắc; các nghiệm pháp kích thích vùng mông dương tính hỗ trợ định hướng nhưng không đủ xác nhận hội chứng cơ hình lê.")
            supporting.extend(["Đau khu trú vùng mông sâu", "Triệu chứng tăng khi ngồi lâu/đè ép vùng mông", "Có lan mặt sau đùi hoặc dị cảm", "Có nghiệm pháp kích thích vùng mông dương tính: " + ", ".join(provocative)])
            if slr_negative: opposing.append("SLR âm tính làm giảm sự hỗ trợ cho một số kiểu kích thích thần kinh tọa khi nâng chân thẳng, nhưng không loại trừ bệnh lý rễ hoặc đau mông sâu.")
            unresolved.extend(["Khám thần kinh theo rễ L5/S1: cảm giác, sức cơ và phản xạ", "Đánh giá gân kheo gần ụ ngồi và nghiệm pháp kháng trở", "Đánh giá khớp háng và khớp cùng-chậu bằng cụm nghiệm pháp phù hợp", "Xác định nghiệm pháp nào tái hiện đúng triệu chứng quen thuộc"])
        elif deep_gluteal_pain:
            hypotheses.append("Có đau vùng mông; cần phân biệt đau mông sâu, đau quy chiếu từ cột sống thắt lưng, bệnh lý khớp háng, gân kheo gần và khớp cùng-chậu.")
            supporting.append("Bệnh sử ghi nhận đau vùng mông")
        else:
            hypotheses.append("Chưa đủ dữ liệu phân loại thần kinh và các vùng khác; cần xác định kiểu phân bố triệu chứng, khám thần kinh, chức năng vận động và dấu hiệu trung ương/ngoại biên.")
        if affirmed(all_text, "yeu tien trien", "mat phan xa", "te tang dan", "roi loan co tron", "te vung yen ngua"):
            clinical_cautions.append("Có dấu hiệu thần kinh cần đánh giá y khoa trực tiếp; không tự động quy kết cho đau mông sâu hoặc cơ hình lê.")
    else:
        hypotheses.append(f"Vùng {region}: chưa có bộ quy tắc suy luận chuyên biệt đã được thẩm định trong phiên bản này. Chỉ tổng hợp dữ liệu và yêu cầu bác sĩ đánh giá.")

    # Contradiction / reverse-audit layer.
    if trauma and has(history, "khong chan thuong", "khong co chan thuong"): opposing.append("Có mâu thuẫn giữa mô tả chấn thương và phủ nhận chấn thương.")
    if no_radiation and radicular: opposing.append("Mô tả hướng lan không nhất quán với phần triệu chứng khác.")
    if weakness and not has(exam, "ben", "trai", "phai", "2 ben"): unresolved.append("Có ghi yếu cơ nhưng chưa rõ nhóm cơ, bên và mức MMT.")
    if not pos: unresolved.append("Không có nghiệm pháp nào được ghi dương tính; điều này không đồng nghĩa đã loại trừ bệnh lý.")
    if unknown_tests: unresolved.append("Các test chưa thực hiện, chưa có kết quả để diễn giải: " + ", ".join(unknown_tests))
    if not str(data.get("rom_mmt", "") or "").strip(): unresolved.append("Chưa có số đo ROM/MMT nên chưa thể lượng giá hạn chế vận động hoặc suy giảm sức cơ.")
    if not str(data.get("inspection", "") or "").strip(): unresolved.append("Chưa có mô tả nhìn: sưng, biến dạng, teo cơ, dáng đi hoặc tư thế.")

    # Confidence is deliberately capped; no validated score/likelihood ratio is claimed.
    evidence_domains = sum(bool(x) for x in [history.strip(), exam.strip(), pos])
    if all_red:
        confidence="Không đưa ra kết luận PHCN trước khi đánh giá nguy cơ/cờ đỏ."
    elif evidence_domains >= 3 and supporting and not opposing:
        confidence="Mức định hướng: trung bình; cần xác minh bằng khám trực tiếp và dữ liệu còn thiếu."
    else:
        confidence="Mức định hướng: thấp; dữ liệu hiện tại chưa đủ để kết luận."

    safety=[]
    if all_red:
        safety.append("Có dấu hiệu cảnh báo được chọn hoặc phát hiện trong bệnh sử. Ưu tiên đánh giá y khoa trực tiếp; không tự động bắt đầu bài tập/điều trị thường quy trước khi làm rõ nguy cơ.")
    else:
        safety.append("Chưa ghi nhận cờ đỏ trong các mục hiện có; điều này KHÔNG loại trừ bệnh lý nghiêm trọng vì danh mục sàng lọc hiện tại còn giới hạn.")
    safety.extend(clinical_cautions)
    safety.append("Không dùng kết quả test đơn lẻ để xác nhận hoặc loại trừ chẩn đoán.")

    from core.reasoning_engine import reason_case
    legacy_result = {"hypotheses": list(dict.fromkeys(hypotheses)), "red_flags": all_red}
    general_reasoning = reason_case(data, legacy_result)

    return {
        "region": region, "hypotheses": list(dict.fromkeys(hypotheses)),
        "supporting": list(dict.fromkeys(supporting)), "opposing": list(dict.fromkeys(opposing)),
        "unresolved": list(dict.fromkeys(unresolved)), "missing": missing,
        "red_flags": all_red, "confidence": confidence, "safety": safety,
        "positive_tests": pos, "negative_tests": negative_tests,
        "unperformed_tests": unknown_tests, "unknown_tests": unknown_tests,
        "summary": str(data.get("reason", "") or "Chưa ghi nhận lý do khám"),
        "general_reasoning": general_reasoning
    }


def render_report(result: Dict[str, Any]) -> str:
    def bullets(items): return "\n".join("- " + x for x in items) if items else "- Chưa có dữ liệu đủ để nhận định."
    sections = [
        "PHCN AI 3.0 – BÁO CÁO HỖ TRỢ SUY LUẬN LÂM SÀNG",
        f"Vùng khám: {result['region']}",
        "\n1. GIẢ THUYẾT / ĐỊNH HƯỚNG CẦN KIỂM CHỨNG\n" + bullets(result['hypotheses']),
        "\n2. DỮ KIỆN ỦNG HỘ\n" + bullets(result['supporting']),
        "\n3. DỮ KIỆN CHỐNG LẠI / MÂU THUẪN\n" + bullets(result['opposing']),
        "\n4. DỮ LIỆU CHƯA RÕ / CẦN BỔ SUNG\n" + bullets(result['unresolved']),
        "\n5. DỮ LIỆU CÒN THIẾU\n" + bullets(result['missing']),
        "\n6. CẢNH BÁO AN TOÀN\n" + bullets(result['red_flags'] + result['safety']),
        "\n7. MỨC ĐỘ TIN CẬY\n- " + result['confidence'],
        "\n8. SUY LUẬN TỔNG QUÁT THEO NHÓM CƠ CHẾ\n" + bullets([x["label"] + ": " + x["rationale"] for x in result.get("general_reasoning", {}).get("mechanism_hypotheses", [])]),
        "\n9. THÔNG TIN CẦN BỔ SUNG ĐỂ PHÂN BIỆT\n" + bullets(result.get("general_reasoning", {}).get("information_gaps", [])),
        "\n10. MẪU LÂM SÀNG TỔNG HỢP\n" + bullets([x["label"] + " (" + x["confidence"] + "): " + x["interpretation"] for x in result.get("general_reasoning", {}).get("clinical_patterns", [])]),
        "\n11. KẾT LUẬN SỬ DỤNG\n- Đây là hỗ trợ tổng hợp dữ liệu, không phải chẩn đoán xác định. Bác sĩ cần đối chiếu khám trực tiếp, bệnh sử đầy đủ, cận lâm sàng khi có chỉ định và hướng dẫn chuyên môn hiện hành.",
    ]
    return "\n".join(sections)
