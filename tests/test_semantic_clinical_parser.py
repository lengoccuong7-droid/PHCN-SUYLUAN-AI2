import unittest
from core.semantic_clinical_parser import parse_narrative
from core.clinical_engine import analyze_case, render_report


class SemanticClinicalParserTests(unittest.TestCase):
    def test_unseen_free_text_extracts_relations_timeline_and_side(self):
        result = parse_narrative({
            "free_text": "Người bệnh đau vùng thắt lưng bên phải sau khi nâng vật nặng 3 tuần trước. Ban đầu đau khu trú, vài ngày gần đây đau lan xuống mặt sau đùi, tăng khi ngồi lâu và giảm khi đi lại nhẹ. Không tê bàn chân, không bí tiểu."
        })
        self.assertEqual(result["anatomical_locations"], ["thắt lưng", "đùi", "bàn chân"])
        self.assertEqual(result["laterality"], "phải")
        self.assertIn("sau chấn thương/sự kiện", result["timeline_patterns"])
        self.assertTrue(result["reported_relations"])
        self.assertTrue(result["causal_chains"])
        self.assertIn("chưa chứng minh", result["causal_chains"][0]["interpretation"])
        self.assertTrue(any(x["symptom"] == "tê/dị cảm" and x["state"] == "phủ định" for x in result["symptoms"]))
        self.assertFalse(result["safety_cues"])

    def test_red_flag_not_triggered_when_explicitly_denied(self):
        result = parse_narrative({"free_text": "Không sốt, không rét run, không bí tiểu."})
        self.assertEqual(result["safety_cues"], [])

    def test_red_flag_positive_is_flagged(self):
        result = parse_narrative({"free_text": "Đau lưng kèm bí tiểu mới xuất hiện."})
        self.assertIn("Rối loạn cơ tròn/bí tiểu mới", result["safety_cues"])

    def test_conflicting_symptom_states_are_reported(self):
        result = parse_narrative({"free_text": "Lúc đầu không tê, hiện tại tê bàn chân."})
        self.assertTrue(any("tê/dị cảm" in x for x in result["contradictions"]))

    def test_integrated_engine_includes_narrative_report(self):
        data = {
            "region": "Cột sống thắt lưng",
            "reason": "Đau lưng",
            "history": "",
            "free_text": "Đau thắt lưng bên trái 2 tuần, tăng khi cúi, giảm khi nghỉ ngơi.",
            "site": "",
            "onset": "",
            "character": "",
            "radiation": "",
            "associations": "",
            "course": "",
            "inspection": "",
            "palpation": "",
            "rom_mmt": "",
            "tests": {},
        }
        result = analyze_case(data)
        self.assertIn("narrative_analysis", result)
        report = render_report(result)
        self.assertIn("PHCN AI 4.5", report)
        self.assertIn("PHÂN TÍCH BỆNH SỬ TỰ DO", report)

if __name__ == "__main__":
    unittest.main()
