"""Regression checks using the two supplied hypothetical clinical cases."""
from core.clinical_engine import analyze_case


def _ca13():
    return {
        "region": "Khớp vai", "reason": "Đau và cứng vai trái",
        "history": "Nữ 52 tuổi, đái tháo đường type 2 đã 5 năm, dùng thuốc và tương đối ổn định. Không té ngã/chấn thương vai, không phẫu thuật ngực hoặc chi trên. Khởi phát tự nhiên từ từ 4 tháng trước, đau tăng dần. Khó cài áo ngực, chải tóc, mặc áo khoác và với tay ra sau. Đau về đêm ảnh hưởng giấc ngủ.",
        "site": "Đau sâu lan tỏa vùng vai và cơ delta trái", "onset": "Khởi phát từ từ trong 4 tháng",
        "character": "Đau âm ỉ liên tục, đau nhói cuối tầm hoặc khi vận động đột ngột; NRS 6",
        "radiation": "Lan mặt ngoài cánh tay, đôi khi đau nhẹ vùng cổ trái",
        "associations": "Đau tăng khi nâng tay, chải tóc, với tay ra sau; đau đêm",
        "course": "Tăng dần, hạn chế sinh hoạt hàng ngày",
        "inspection": "Vai hơi nâng và khép; teo nhẹ cơ delta và trên gai; không sưng đỏ biến dạng, nhiệt độ da bình thường",
        "palpation": "Đau lan tỏa bao khớp trước và sau, rãnh nhị đầu; căng cơ thang trên và ngực bé; mạch quay bình thường",
        "rom_mmt": "AROM và PROM đều hạn chế đa hướng: gấp 85 độ, dạng 70 độ, xoay ngoài 15 độ; xoay trong đến mông cùng bên. MMT 4/5 trong tầm không đau.",
        "tests": {"Apley Scratch": "Dương tính", "Shrug sign": "Dương tính"}, "red_flags": {},
    }


def _ca14():
    return {
        "region": "Khớp gối", "reason": "Đau mặt ngoài gối phải khi chạy",
        "history": "Nam 29 tuổi, kỹ sư công trình, đạp xe và chạy trail 40-50 km/tuần. Không chấn thương trực tiếp, không phẫu thuật. Đau xuất hiện 2 tuần sau giải trail nhiều đoạn xuống dốc. Ban đầu đau sau 5 km chạy, hiện đau sớm hơn, kể cả đi nhanh hoặc xuống dốc. Không tràn dịch, khóa khớp, mất vững hoặc tê bàn chân.",
        "site": "Đau khu trú mặt ngoài gối, khoảng 2 cm phía trên lồi cầu ngoài xương đùi; đôi khi lan lên mặt ngoài đùi",
        "onset": "Khởi phát sau tăng tải chạy và chạy trail xuống dốc",
        "character": "Đau rát hoặc nhói ở một góc gấp gối; cảm giác cọ hoặc bật nhẹ; NRS 5",
        "radiation": "Đôi khi lan lên mặt ngoài đùi, không lan xuống cẳng chân",
        "associations": "Đau tăng khi chạy, đặc biệt chạy xuống dốc, xuống cầu thang và squat; hết khi nghỉ hoặc duỗi thẳng",
        "course": "Tăng dần, xuất hiện sớm hơn khi chạy", "inspection": "Không tràn dịch; squat một chân có valgus động và sụt chậu đối bên",
        "palpation": "Đau khu trú vùng lồi cầu ngoài xương đùi, rõ hơn khoảng 30 độ gấp gối; khe khớp và dây chằng không đau",
        "rom_mmt": "ROM gối 0-135 độ; hơi đau ngoài gối ở 30 độ gấp có kháng lực. Cơ tứ đầu và gân kheo 5/5; cơ mông nhỡ phải 4/5. Hạn chế nhẹ khép háng.",
        "tests": {"Ober": "Dương tính", "Noble Compression": "Dương tính", "Lachman": "Âm tính", "McMurray": "Âm tính"}, "red_flags": {},
    }


def test_ca13_detects_global_shoulder_stiffness_without_false_red_flags_or_trauma():
    result = analyze_case(_ca13())
    generic = result["general_reasoning"]
    assert any("cứng khớp vai" in p["label"].lower() for p in generic["clinical_patterns"])
    assert not generic["warnings"]
    assert not any("chấn thương" in p["label"].lower() for p in generic["clinical_patterns"])


def test_ca14_detects_lateral_knee_load_pattern_without_false_neurological_or_contradiction_flags():
    result = analyze_case(_ca14())
    generic = result["general_reasoning"]
    assert any("ngoài gối" in p["label"].lower() for p in generic["clinical_patterns"])
    assert not any("thần kinh" in p["label"].lower() for p in generic["clinical_patterns"])
    assert not generic["contradictions"]
    assert not generic["warnings"]
