"""Tab 3 – Khám lâm sàng và Ghi nhận Phục hồi Chức năng độc lập."""
import streamlit as st
from core.knowledge_loader import load_knowledge
import json
import hashlib
import uuid
from core.clinical_engine import analyze_case, render_report
from database.storage import save_visit, save_analysis_rounds, save_clinical_review


def _render_phcn_record():
    st.subheader("📝 Ghi nhận tình trạng và buổi phục hồi chức năng")
    st.caption("Có thể lưu hồ sơ phục hồi chức năng mà không cần thực hiện phiếu khám lâm sàng.")
    active = st.session_state.get("current_patient", {}) or {}
    library = load_knowledge("rehabilitation/exercise_library.json")
    with st.form("phcn_only_record_form", clear_on_submit=False):
        st.markdown("#### 1. Thông tin người bệnh")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Họ tên", value=active.get("name", ""))
            birth_year = st.number_input(
                "Năm sinh", min_value=1900, max_value=2026,
                value=int(active.get("age") or 1990), step=1,
            )
        with c2:
            phone = st.text_input("Số điện thoại (nếu có)", value=active.get("phone", ""))
            job = st.text_input("Nghề nghiệp", value=active.get("job", ""))
        st.markdown("#### 2. Tình trạng hiện tại")
        current_status = st.text_area("Mô tả tình trạng hiện tại", height=110)
        c3, c4, c5 = st.columns(3)
        with c3:
            systolic = st.number_input("Huyết áp tâm thu (mmHg)", min_value=0, max_value=300, value=0, step=1)
        with c4:
            diastolic = st.number_input("Huyết áp tâm trương (mmHg)", min_value=0, max_value=200, value=0, step=1)
        with c5:
            pulse = st.number_input("Mạch (lần/phút, nếu đo)", min_value=0, max_value=250, value=0, step=1)
        bp_note = st.text_input("Thời điểm hoặc tư thế đo huyết áp")
        history = st.text_area("Tiền sử và lưu ý liên quan", height=100)
        st.markdown("#### 3. Bài tập trong buổi phục hồi chức năng")
        group = st.selectbox("Nhóm bài tập hoặc bệnh lý", list(library.keys()), index=0)
        exercise_options = library.get(group, [])
        selected_exercises = st.multiselect("Chọn các bài tập đã thực hiện", exercise_options)
        other_exercises = st.text_area("Bài tập khác hoặc bài tập tự thiết kế", height=70)
        exercise_note = st.text_area("Liều lượng và cách thực hiện thực tế", height=100)
        response = st.text_area("Đáp ứng sau tập", height=90)
        therapist_note = st.text_area("Ghi chú kỹ thuật viên hoặc kế hoạch buổi tiếp theo", height=90)
        submitted = st.form_submit_button(
            "💾 Lưu hồ sơ phục hồi chức năng", type="primary", use_container_width=True,
        )
    if submitted:
        if not name.strip():
            st.error("Vui lòng nhập họ tên người bệnh trước khi lưu.")
            return
        if (not current_status.strip() and not history.strip()
                and not selected_exercises and not other_exercises.strip()
                and not exercise_note.strip() and not systolic and not diastolic and not pulse):
            st.error("Vui lòng nhập ít nhất tình trạng hiện tại, tiền sử hoặc nội dung bài tập.")
            return
        bp = {
            "systolic_mmhg": int(systolic) if systolic else None,
            "diastolic_mmhg": int(diastolic) if diastolic else None,
            "pulse_bpm": int(pulse) if pulse else None,
            "measurement_note": bp_note.strip(),
        }
        payload = {
            "record_type": "phcn_only",
            "current_status": current_status.strip(),
            "blood_pressure": bp,
            "history": history.strip(),
            "exercise_group": group,
            "selected_exercises": selected_exercises,
            "other_exercises": other_exercises.strip(),
            "exercise_note": exercise_note.strip(),
            "response_after_session": response.strip(),
            "therapist_note": therapist_note.strip(),
        }
        summary = (
            "[GHI NHẬN BUỔI PHỤC HỒI CHỨC NĂNG]\n"
            f"Người bệnh: {name.strip()} | Năm sinh: {int(birth_year)}\n"
            f"Tình trạng hiện tại: {current_status.strip() or 'Chưa ghi'}\n"
            f"Huyết áp: "
            + (f"{int(systolic)}/{int(diastolic)} mmHg" if systolic and diastolic else "Chưa ghi đủ")
            + "\n"
            f"Mạch: {int(pulse) if pulse else 'Chưa ghi'}\n"
            f"Tiền sử: {history.strip() or 'Chưa ghi'}\n"
            f"Nhóm bài tập: {group}\n"
            f"Bài tập: {'; '.join(selected_exercises) if selected_exercises else 'Chưa chọn'}\n"
            f"Bài tập khác: {other_exercises.strip() or 'Không ghi'}\n"
            f"Liều lượng và cách thực hiện: {exercise_note.strip() or 'Chưa ghi'}\n"
            f"Đáp ứng: {response.strip() or 'Chưa ghi'}\n"
            f"Ghi chú kỹ thuật viên: {therapist_note.strip() or 'Chưa ghi'}"
        )
        try:
            patient_token = active.get("patient_token") or ("PHCN-" + uuid.uuid4().hex)
            visit_id = save_visit(
                {"name": name.strip(), "phone": phone.strip(),
                 "age": int(birth_year), "job": job.strip(), "patient_token": patient_token},
                "Phục hồi chức năng – Ghi nhận điều trị (không khám)",
                payload, summary, {}, "",
            )
            st.session_state.current_patient = {
                **active, "name": name.strip(), "phone": phone.strip(),
                "age": int(birth_year), "job": job.strip(), "patient_token": patient_token,
            }
            st.success(
                f"Đã lưu hồ sơ phục hồi chức năng số {visit_id}. "
                "Có thể xem lại trong Tab Hồ sơ và Lịch sử."
            )
            st.text_area(
                "Tóm tắt hồ sơ vừa lưu",
                value=summary, height=260,
                key=f"phcn_saved_summary_{visit_id}",
            )
        except Exception as exc:
            st.error(f"Không thể lưu hồ sơ phục hồi chức năng: {exc}")


def render():
    mode = st.radio(
        "Chọn hình thức ghi nhận",
        ["Khám lâm sàng", "Ghi nhận phục hồi chức năng (không cần khám)"],
        horizontal=True,
        key="tab3_record_mode",
    )
    if mode == "Ghi nhận phục hồi chức năng (không cần khám)":
        _render_phcn_record()
        return
    if "exam_active_region" not in st.session_state:
        st.session_state.exam_active_region = None
    regions = [
        ("Cột sống cổ", "🦴", "C1-C7 và hội chứng chèn ép", "linear-gradient(135deg, #ff6b6b, #ee5253)"),
        ("Cột sống thắt lưng", "🩻", "Thoát vị đĩa đệm, đau thần kinh tọa", "linear-gradient(135deg, #10ac84, #1dd1a1)"),
        ("Khớp vai", "🦾", "Chóp xoay và đông cứng khớp vai", "linear-gradient(135deg, #5f27cd, #341f97)"),
        ("Khuỷu tay", "💪", "Viêm lồi cầu, hội chứng ống khuỷu", "linear-gradient(135deg, #ff9f43, #ee5253)"),
        ("Cổ tay – bàn tay", "✋", "Hội chứng ống cổ tay, De Quervain", "linear-gradient(135deg, #48dbfb, #0abde3)"),
        ("Khớp háng", "🦿", "Thoái hóa và kẹp háng", "linear-gradient(135deg, #f39c12, #e67e22)"),
        ("Khớp gối", "🦵", "Dây chằng chéo trước, sụn chêm, thoái hóa", "linear-gradient(135deg, #2e86de, #222f3e)"),
        ("Cổ chân – bàn chân", "🦶", "Bong gân, viêm cân gan chân, gân Achilles", "linear-gradient(135deg, #ee5253, #ff6b6b)"),
        ("Thần kinh và Khác", "🧠", "Đột quỵ, phục hồi chức năng thần kinh", "linear-gradient(135deg, #0abde3, #2e86de)"),
    ]
    if st.session_state.exam_active_region is None:
        st.subheader("🎯 Chọn Vùng Thăm Khám Lâm Sàng")
        st.markdown("Chọn vùng cơ thể bên dưới để mở phiếu thăm khám chuyên sâu độc lập:")
        cols_r = st.columns(2)
        for idx, item in enumerate(regions):
            title, icon, desc, color = item
            with cols_r[idx % 2]:
                st.markdown(
                    f"""
                    <div class="grid-card-box">
                        <div class="icon-circle-btn" style="background: {color};">
                            {icon}
                        </div>
                        <div style="font-weight: 700; font-size: 12px; color: #1f2937; min-height: 35px; display: flex; align-items: center; justify-content: center;">{title}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("🩺 Bắt đầu khám", use_container_width=True, key=f"open_exam_{idx}"):
                    st.session_state.exam_active_region = title
                    st.rerun()
    else:
        current_reg = st.session_state.exam_active_region
        c_top1, c_top2 = st.columns([1, 4])
        with c_top1:
            if st.button("⬅️ Quay lại", type="secondary"):
                st.session_state.exam_active_region = None
                st.rerun()
        with c_top2:
            st.subheader(f"📋 PHIẾU KHÁM: {current_reg.upper()}")
        st.markdown("---")
        active_patient = st.session_state.get(
            "current_patient", {"name": "", "phone": "", "age": 1990, "job": ""}
        )
        if active_patient.get("name"):
            st.info(
                f"🔗 Hồ sơ đang liên kết: **{active_patient.get('name')}** · "
                f"Năm sinh: **{active_patient.get('age') or 'Chưa nhập'}**"
            )
        st.markdown('<div class="scrollable-feed">', unsafe_allow_html=True)
        p_name = st.text_input("Họ tên bệnh nhân", value=active_patient.get("name", ""), key="rt_p_name")
        birth_default = int(active_patient.get("age") or 1990)
        p_birth_year = st.number_input(
            "Năm sinh", min_value=1900, max_value=2026,
            value=birth_default, step=1, key="rt_p_birth_year",
        )
        p_job = st.text_input("Nghề nghiệp", value=active_patient.get("job", ""), key="rt_p_job")
        ly_do = st.text_input("🏥 Lý do vào viện hoặc than phiền chính", key="rt_ly_do")
        tien_su = st.text_area("📜 Tiền sử bệnh (bản thân, chấn thương)", key="rt_tien_su")
        free_narrative = st.text_area(
            "🧠 Bệnh sử tự do – nhập hoặc dán nguyên văn bất kỳ",
            placeholder="Ví dụ: Người bệnh đau vùng thắt lưng bên phải sau khi nâng vật nặng 3 tuần trước. Ban đầu đau khu trú, vài ngày gần đây đau lan xuống mặt sau đùi, tăng khi ngồi lâu và giảm khi đi lại nhẹ. Không tê bàn chân, không bí tiểu...",
            height=150, key="rt_free_narrative",
            help="Có thể nhập văn bản theo cách ghi bệnh án thông thường. Hệ thống sẽ trích xuất dấu hiệu, vị trí, bên, diễn tiến, yếu tố tăng/giảm và mối liên hệ được mô tả; dữ kiện chưa nhận diện vẫn được giữ là chưa rõ.",
        )
        with st.expander("🩺 Bệnh sử chi tiết (quy trình ghi nhận chuẩn)", expanded=True):
            st.caption("Khai thác triệu chứng theo từng mục (nhập tự do từng mục):")
            soc_s = st.text_input("• **Vị trí đau:**", key="rt_soc_s")
            soc_o = st.text_input("• **Hoàn cảnh khởi phát:**", key="rt_soc_o")
            soc_c = st.text_input("• **Tính chất đau:**", key="rt_soc_c")
            soc_r = st.text_input("• **Hướng lan:**", key="rt_soc_r")
            soc_a = st.text_input("• **Triệu chứng đi kèm:**", key="rt_soc_a")
            soc_t = st.text_input("• **Diễn tiến thời gian:**", key="rt_soc_t")
            col_nrs1, col_nrs2 = st.columns([1, 2])
            with col_nrs1:
                nrs = st.selectbox(
                    "• **Mức độ đau (thang 0 đến 10):**",
                    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                    key="rt_nrs",
                )
            with col_nrs2:
                nrs_note = st.text_input("• **Ghi chú mức độ đau:**", key="rt_nrs_note")
        with st.expander("🔍 Khám thực thể chuẩn (nhìn, sờ, đo tầm vận động)", expanded=True):
            inspect = st.text_area("👁️ NHÌN – biến dạng, sưng nề, teo cơ", key="rt_inspect")
            palp = st.text_area("✋ SỜ – điểm đau chói, nhiệt độ, trương lực", key="rt_palp")
            rom_meas = st.text_area("📏 ĐO VÀ GÕ – tầm vận động, lực cơ", key="rt_rom")
        with st.expander("🖼️ Hình ảnh lâm sàng và cận lâm sàng", expanded=False):
            uploaded_image = st.file_uploader(
                "📤 Tải ảnh X-quang hoặc MRI:",
                type=["png", "jpg", "jpeg"],
                key="rt_uploaded_img",
            )
            if uploaded_image is not None:
                st.image(uploaded_image, caption="Ảnh được tải lên để lưu/đối chiếu thủ công", use_container_width=True)
                st.info("Phiên bản hiện tại chỉ hiển thị ảnh; chưa có chức năng đọc MRI/X-quang hoặc phân tích ảnh tự động. Không dùng ảnh tải lên như một kết quả chẩn đoán của ứng dụng.")
        specific_tests_db = load_knowledge("clinical_tests/region_tests.json")
        active_tests = specific_tests_db.get(current_reg, [
            ("Nghiệm pháp đặc hiệu 1", "Đánh giá tổn thương cấu trúc", "Thực hiện kỹ thuật chuẩn."),
            ("Nghiệm pháp đặc hiệu 2", "Kiểm tra độ vững", "Thực hiện theo quy trình lâm sàng."),
            ("Nghiệm pháp đặc hiệu 3", "Đánh giá chức năng", "Thực hiện theo hướng dẫn."),
            ("Nghiệm pháp đặc hiệu 4", "Kiểm tra bổ trợ", "Thực hiện kỹ thuật lâm sàng."),
        ])
        # Keep the initial clinical screen concise: show at most three priority tests.
        priority_tests = active_tests[:3]
        with st.expander(f"🧬 Nghiệm pháp ưu tiên ({current_reg}) – tối đa 3 nghiệm pháp", expanded=True):
            test_results = {}
            st.caption("Chọn nghiệm pháp phù hợp với bệnh sử và khám thực thể; các nghiệm pháp khác có thể tra cứu trong Cẩm nang Tri thức.")
            for t_idx, (t_name, t_use, t_tech) in enumerate(priority_tests):
                st.markdown(f"**🔹 {t_idx+1}. {t_name}**")
                st.caption(f"• **Công dụng:** {t_use}  \n• **Kỹ thuật:** {t_tech}")
                res = st.radio(
                    f"Kết quả {t_name}:",
                    ["Chưa thực hiện", "Âm tính (-)", "Dương tính (+)"],
                    horizontal=True,
                    key=f"ex_t_res_{t_idx}",
                )
                test_results[t_name] = res
                st.markdown("---")
        with st.expander("🚩 Cờ đỏ an toàn lâm sàng", expanded=False):
            rf_1 = st.checkbox("Hội chứng đuôi ngựa hoặc rối loạn cơ tròn", key="rt_rf1")
            rf_2 = st.checkbox("Sụt cân nhanh hoặc tiền sử ung thư", key="rt_rf2")
            rf_3 = st.checkbox("Sốt cao, sưng nóng đỏ đau cấp tính", key="rt_rf3")
        st.markdown("---")
        st.markdown("### 📄 Tờ Giấy Trắng Tổng Hợp và Phân Tích (cập nhật trực tiếp)")
        pos_tests_list = [t for t, res in test_results.items() if res == "Dương tính (+)"]
        neg_tests_list = [t for t, res in test_results.items() if res == "Âm tính (-)"]
        unperformed_tests_list = [t for t, res in test_results.items() if res == "Chưa thực hiện"]
        summary_text = f"""[BỆNH ÁN PHỤC HỒI CHỨC NĂNG CHUYÊN SÂU]
    - Vùng khám: {current_reg}
    - Bệnh nhân: {p_name if p_name else '---'}
    - Năm sinh: {p_birth_year if p_birth_year else '---'}
    - Nghề nghiệp: {p_job if p_job else '---'}
    - Lý do vào viện: {ly_do if ly_do else '---'}
    - Tiền sử: {tien_su if tien_su else '---'}
    - Bệnh sử tự do: {free_narrative if free_narrative else '---'}
    [BỆNH SỬ]
    - Vị trí: {soc_s if soc_s else '---'}
    - Khởi phát: {soc_o if soc_o else '---'}
    - Tính chất: {soc_c if soc_c else '---'}
    - Hướng lan: {soc_r if soc_r else '---'}
    - Triệu chứng kèm: {soc_a if soc_a else '---'}
    - Diễn tiến: {soc_t if soc_t else '---'}
    - Mức độ đau: {nrs}/10
    ----------------------------------------
    [KHÁM THỰC THỂ]
    - Nhìn: {inspect if inspect else '---'}
    - Sờ: {palp if palp else '---'}
    - Tầm vận động và lực cơ: {rom_meas if rom_meas else '---'}
    - Nghiệm pháp dương tính: {', '.join(pos_tests_list) if pos_tests_list else 'Không có'}
    - Nghiệm pháp âm tính: {', '.join(neg_tests_list) if neg_tests_list else 'Không có'}
    - Nghiệm pháp chưa thực hiện: {', '.join(unperformed_tests_list) if unperformed_tests_list else 'Không có'}
    - Cờ đỏ: {'Có dấu hiệu nguy cơ được đánh dấu' if (rf_1 or rf_2 or rf_3) else 'Chưa ghi nhận dấu hiệu cảnh báo trong các mục đã nhập; không đồng nghĩa đã loại trừ bệnh lý nghiêm trọng'}"""
        st.text_area(
            "📄 Tờ giấy trắng – tự cập nhật theo dữ kiện vừa nhập:",
            value=summary_text, height=300,
            key=f"quick_copy_box_{hashlib.md5(summary_text.encode()).hexdigest()[:8]}",
        )
        case_payload = {
            "region": current_reg,
            "reason": ly_do,
            "history": tien_su,
            "free_text": free_narrative,
            "site": soc_s,
            "onset": soc_o,
            "character": soc_c,
            "radiation": soc_r,
            "associations": soc_a,
            "course": soc_t,
            "nrs": nrs,
            "inspection": inspect,
            "palpation": palp,
            "rom_mmt": rom_meas,
            "tests": test_results,
            "red_flags": {
                "Rối loạn cơ tròn hoặc nghi hội chứng đuôi ngựa": rf_1,
                "Tiền sử ung thư hoặc sụt cân nhanh": rf_2,
                "Sốt cao hoặc sưng nóng đỏ đau cấp tính": rf_3,
            },
        }
        case_signature = hashlib.sha256(
            json.dumps(case_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        st.session_state["phcn_current_payload"] = case_payload
        st.session_state["phcn_current_signature"] = case_signature
        if st.button(
            "🚀 Chạy Phân Tích Suy Luận Lâm Sàng",
            type="primary", use_container_width=True,
        ):
            st.session_state["phcn_last_payload"] = dict(case_payload)
            st.session_state["phcn_iteration_base_payload"] = dict(case_payload)
            st.session_state["phcn_supplement_entries"] = []
            st.session_state["phcn_analysis_rounds"] = []
            st.session_state["phcn_last_signature"] = case_signature
            initial_result = analyze_case(case_payload)
            initial_result["analysis_round"] = 1
            st.session_state["phcn_last_analysis"] = initial_result
            st.session_state["phcn_last_report"] = render_report(initial_result)
            st.session_state["phcn_analysis_rounds"].append({
                "round": 1,
                "payload": dict(case_payload),
                "analysis": initial_result,
                "report": st.session_state["phcn_last_report"],
            })
        analysis_is_current = (
            st.session_state.get("phcn_last_signature") == case_signature
        )
        if st.session_state.get("phcn_last_analysis") and analysis_is_current:
            st.markdown("---")
            st.markdown("### 🔄 BỔ SUNG THÔNG TIN VÀ PHÂN TÍCH LẠI")
            st.caption(
                "Nhập tự do dữ kiện mới sau khi hỏi bệnh hoặc khám bổ sung. "
                "Thông tin cũ được giữ nguyên; mỗi lần phân tích lại tạo một vòng mới. "
                "Nếu sửa dữ kiện đã ghi trước đó, hãy nêu rõ giá trị cũ và giá trị đã xác minh lại."
            )
            next_supplement_number = len(st.session_state.get("phcn_supplement_entries", [])) + 1
            supplement_text = st.text_area(
                "Thông tin bổ sung của bác sĩ",
                key=f"phcn_supplement_input_{next_supplement_number}",
                height=130,
                placeholder=(
                    "Ví dụ: Khám lại sức cơ: gấp mu bàn chân trái 4/5; "
                    "cảm giác giảm vùng ...; phản xạ ...; xác minh triệu chứng chỉ ở bên trái. "
                    "Hoặc: Đính chính kết quả trước đây ... thành ..."
                ),
            )
            if st.button(
                "🔁 PHÂN TÍCH LẠI VỚI THÔNG TIN BỔ SUNG",
                type="primary", use_container_width=True,
                key="phcn_reanalyze_with_supplement",
                disabled=not bool(supplement_text.strip()),
            ):
                entries = list(st.session_state.get("phcn_supplement_entries", []))
                entries.append(supplement_text.strip())
                st.session_state["phcn_supplement_entries"] = entries
                combined = dict(st.session_state.get("phcn_iteration_base_payload", case_payload))
                combined["supplemental_text"] = "\n".join(
                    f"Bổ sung vòng {idx + 1}: {entry}" for idx, entry in enumerate(entries)
                )
                next_round = len(entries) + 1
                new_result = analyze_case(combined)
                new_result["analysis_round"] = next_round
                new_result["supplemental_text"] = combined["supplemental_text"]
                previous_rounds = list(st.session_state.get("phcn_analysis_rounds", []))
                previous_primary = None
                if previous_rounds:
                    prev_syn = (previous_rounds[-1].get("analysis") or {}).get("diagnosis_synthesis", {})
                    prev_primary = (prev_syn.get("primary") or {}).get("label")
                current_syn = new_result.get("diagnosis_synthesis", {})
                current_primary = (current_syn.get("primary") or {}).get("label")
                new_result["iteration_comparison"] = {
                    "previous_primary": previous_primary,
                    "current_primary": current_primary,
                    "changed": previous_primary != current_primary,
                }
                new_report = render_report(new_result)
                st.session_state["phcn_last_payload"] = combined
                st.session_state["phcn_last_analysis"] = new_result
                st.session_state["phcn_last_report"] = new_report
                st.session_state["phcn_last_signature"] = case_signature
                previous_rounds.append({
                    "round": next_round, "payload": combined,
                    "analysis": new_result, "report": new_report,
                })
                st.session_state["phcn_analysis_rounds"] = previous_rounds
                st.success(f"Đã hoàn tất vòng phân tích số {next_round}. Dữ liệu các vòng trước vẫn được giữ.")
                st.rerun()
            rounds = st.session_state.get("phcn_analysis_rounds", [])
            if len(rounds) > 1:
                with st.expander("📚 Lịch sử các vòng phân tích và thay đổi giả thuyết", expanded=False):
                    for item in rounds:
                        syn = (item.get("analysis") or {}).get("diagnosis_synthesis", {})
                        primary = (syn.get("primary") or {}).get("label") or syn.get("summary", "Chưa có giả thuyết ưu tiên")
                        st.markdown(f"**Vòng {item['round']}** — {primary}")
                        if item["round"] > 1:
                            st.caption("Thông tin bổ sung: " + str((item.get("payload") or {}).get("supplemental_text", "")))
                    comparison = (st.session_state.get("phcn_last_analysis") or {}).get("iteration_comparison", {})
                    if comparison:
                        if comparison.get("changed"):
                            st.warning(f"Giả thuyết ưu tiên đã thay đổi: {comparison.get('previous_primary')} → {comparison.get('current_primary')}")
                        else:
                            st.info("Giả thuyết ưu tiên chưa thay đổi sau khi bổ sung. Các bằng chứng, mức hỗ trợ và dữ liệu còn thiếu vẫn cần được xem xét.")
        if st.session_state.get("phcn_last_analysis") and analysis_is_current:
            result = st.session_state["phcn_last_analysis"]
            st.markdown("---")
            st.markdown("#### 🤖 KẾT QUẢ SUY LUẬN LÂM SÀNG")
            if result["red_flags"]:
                st.error("🚩 Có dấu hiệu cảnh báo: " + "; ".join(result["red_flags"]))
            else:
                st.warning(
                    "Lưu ý: chưa ghi nhận cờ đỏ trong các mục đã nhập không đồng nghĩa "
                    "đã loại trừ bệnh lý nghiêm trọng."
                )
            if result.get("syndromes"):
                st.markdown("**Hội chứng được kích hoạt**")
                for syn in result["syndromes"]:
                    if syn["co_nguy_hiem"]:
                        st.error(f"🚨 {syn['ten']}: {syn['ket_luan']}")
                    else:
                        st.info(f"ℹ️ {syn['ten']}: {syn['ket_luan']}")
                    st.caption(f"Đặc trưng khớp: {', '.join(syn['dac_trung_khop'])}")
            narrative_result = result.get("narrative_analysis", {})
            if narrative_result:
                with st.expander("🧠 Phân tích bệnh sử tự do (NLP offline)", expanded=True):
                    st.markdown("**Vị trí giải phẫu:** " + (", ".join(narrative_result.get("anatomical_locations", [])) or "Chưa nhận diện rõ"))
                    st.markdown("**Bên:** " + str(narrative_result.get("laterality", "chưa xác định")))
                    st.markdown("**Diễn tiến:** " + (", ".join(narrative_result.get("timeline_patterns", [])) or "Chưa đủ dữ kiện"))
                    st.markdown("**Thời lượng:** " + (", ".join(narrative_result.get("explicit_durations", [])) or "Chưa ghi rõ"))
                    st.markdown("**Triệu chứng:**")
                    if narrative_result.get("symptoms"):
                        for item in narrative_result["symptoms"]:
                            st.markdown(f"- {item['symptom']}: {item['state']}")
                    else:
                        st.caption("Chưa nhận diện được triệu chứng từ bộ từ vựng hiện tại; không đồng nghĩa không có triệu chứng.")
                    st.markdown("**Yếu tố tăng:** " + (", ".join(narrative_result.get("aggravating_factors", [])) or "Chưa nhận diện"))
                    st.markdown("**Yếu tố giảm:** " + (", ".join(narrative_result.get("relieving_factors", [])) or "Chưa nhận diện"))
                    for chain in narrative_result.get("causal_chains", []):
                        st.info(f"Bối cảnh/yếu tố: {chain['reported_trigger_or_context']} → Kết quả được thuật lại: {chain['reported_outcome']}")
                        st.caption(chain["interpretation"])
                    for item in narrative_result.get("reported_relations", []):
                        st.caption(f"{item['type']}: {item['text']} — {item['interpretation']}")
                    for item in narrative_result.get("contradictions", []):
                        st.warning(item)
                    st.caption("NLP offline dựa trên quy tắc; chưa phải mô hình hiểu ngôn ngữ tự do hoàn hảo.")
            detailed = result.get("detailed_hypotheses", [])
            if detailed:
                st.markdown("**Giả thuyết và định hướng cần kiểm chứng**")
                for h in detailed:
                    if h["do_tin_cay"] < 0.30:
                        continue
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{h['label']}**")
                        with col2:
                            st.metric(
                                "Điểm định hướng (heuristic)",
                                f"{h['do_tin_cay']*100:.0f}/100",
                                h["muc_tin_cay"],
                            )
                        st.progress(min(h["do_tin_cay"], 1.0))
                        if h["dac_trung_ung_ho"]:
                            with st.expander(
                                f"Dữ kiện ủng hộ ({len(h['dac_trung_ung_ho'])})",
                                expanded=False,
                            ):
                                for s in h["dac_trung_ung_ho"]:
                                    st.markdown(f"- {s}")
                        if h["dac_trung_chong_lai"]:
                            with st.expander(
                                f"Dữ kiện chống lại ({len(h['dac_trung_chong_lai'])})",
                                expanded=False,
                            ):
                                for o in h["dac_trung_chong_lai"]:
                                    st.markdown(f"- {o}")
                        if h["dac_trung_con_thieu"]:
                            with st.expander(
                                f"Dấu hiệu kỳ vọng chưa có ({len(h['dac_trung_con_thieu'])})",
                                expanded=False,
                            ):
                                for m in h["dac_trung_con_thieu"]:
                                    st.markdown(f"- {m}")
                        if not h["co_dau_hieu_vang"] and h["dau_hieu_vang_can_co"]:
                            st.warning("⚠️ Thiếu dấu hiệu vàng — không thể kết luận chắc chắn.")
                        st.caption(f"Ghi chú chuyên môn: {h['luu_y']}")
                        with st.expander("🎓 Phản hồi chuyên môn của bác sĩ", expanded=False):
                            from core.learning_engine import learn_from_feedback, record_feedback
                            agreement = st.radio(
                                "Bạn có đồng ý với giả thuyết này không?",
                                ["Đồng ý", "Không đồng ý", "Không rõ"],
                                key=f"fb_{h['key']}",
                                horizontal=True,
                            )
                            note = st.text_input("Ghi chú (tùy chọn):", key=f"fb_note_{h['key']}")
                            if st.button(
                                "Gửi phản hồi",
                                key=f"fb_submit_{h['key']}",
                                use_container_width=True,
                            ):
                                agreement_code = {
                                    "Đồng ý": "dong_y",
                                    "Không đồng ý": "khong_dong_y",
                                    "Không rõ": "khong_ro",
                                }[agreement]
                                record_feedback(
                                    visit_id=st.session_state.get("phcn_last_visit_id"),
                                    hypothesis_key=h["key"],
                                    doctor_agreement=agreement_code,
                                    doctor_note=note,
                                )
                                fb_result = learn_from_feedback(
                                    hypothesis_key=h["key"],
                                    doctor_agreement=agreement_code,
                                    triggered_features=h.get("triggered_features", []),
                                )
                                if fb_result["changed"]:
                                    st.success(
                                        f"Đã cập nhật {len(fb_result['changes'])} trọng số cho "
                                        f"{h['label']}."
                                    )
                                    for c in fb_result["changes"]:
                                        st.caption(
                                            f"- {c['feature']}: "
                                            f"{c['old_weight']} → {c['new_weight']}"
                                        )
                                else:
                                    st.info(fb_result.get("reason", "Không có thay đổi."))
            if result.get("cross_inferences"):
                st.markdown("**Suy luận bắc cầu**")
                for inf in result["cross_inferences"]:
                    st.markdown(f"- {inf}")
            if result.get("conditionals"):
                with st.expander("Mệnh đề điều kiện đã nhận diện", expanded=False):
                    for cond in result["conditionals"]:
                        st.markdown(
                            f"- **Nếu** {cond['condition']} **thì** {cond['consequence']}"
                        )
            with st.expander(
                f"Đặc trưng đã trích xuất ({len(result.get('features_extracted', []))})",
                expanded=False,
            ):
                for f in result.get("features_extracted", []):
                    st.markdown(f"- `{f}`")
            if result.get("cross_region_findings"):
                st.markdown("**Suy luận liên vùng**")
                for c in result["cross_region_findings"]:
                    st.markdown(f"- {c}")
            st.markdown("**Mức độ tin cậy tổng**")
            st.info(result["confidence"])
            st.caption(
                "Bộ não suy luận offline dựa trên luật có trọng số; chưa phải mô hình "
                "trí tuệ nhân tạo đã được thẩm định lâm sàng. Không dùng một nghiệm pháp "
                "đơn lẻ để xác nhận hoặc loại trừ bệnh."
            )
            st.text_area(
                "Báo cáo phân tích – sao chép để hội chẩn",
                value=st.session_state["phcn_last_report"],
                height=360,
                key="phcn_report_copy",
            )
            st.markdown("#### ⚖️ QUYẾT ĐỊNH CHUYÊN MÔN CỦA BÁC SĨ")
            st.caption("Kết quả của ứng dụng là đề xuất hỗ trợ. Bác sĩ trực tiếp khám quyết định chấp nhận, điều chỉnh hoặc bác bỏ.")
            doctor_decision = st.radio(
                "Bác sĩ đánh giá định hướng hiện tại:",
                ["Chấp nhận", "Chấp nhận có điều chỉnh", "Bác bỏ", "Chưa đủ dữ liệu"],
                horizontal=False,
                key=f"phcn_doctor_decision_{len(st.session_state.get('phcn_analysis_rounds', []))}",
            )
            doctor_review_note = st.text_area(
                "Lý do / chẩn đoán bác sĩ sau thăm khám (nếu có)",
                key=f"phcn_doctor_review_note_{len(st.session_state.get('phcn_analysis_rounds', []))}",
                height=90,
            )
            if st.button("💾 Lưu quyết định chuyên môn", use_container_width=True, key="phcn_save_doctor_decision"):
                saved_visit_id = st.session_state.get("phcn_last_visit_id")
                if not saved_visit_id:
                    st.warning("Hãy lưu hồ sơ lần khám trước, sau đó lưu quyết định chuyên môn để liên kết đúng ca bệnh.")
                else:
                    syn = result.get("diagnosis_synthesis", {})
                    primary = (syn.get("primary") or {}).get("label", "")
                    round_no = int(result.get("analysis_round", 1))
                    review_id = save_clinical_review(
                        saved_visit_id, round_no, doctor_decision, primary, doctor_review_note
                    )
                    st.success(f"Đã lưu quyết định chuyên môn số {review_id} cho vòng phân tích {round_no}.")
        st.markdown("---")
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button("🤖 Hỏi trợ lý ChatGPT", use_container_width=True):
                st.info(
                    "💡 Mẹo: sao chép nội dung bệnh án ở trên và dán vào trợ lý "
                    "kèm câu lệnh: 'Đóng vai bác sĩ phục hồi chức năng, hãy biện luận "
                    "chẩn đoán ca bệnh này'."
                )
        with col_b2:
            if st.button("✨ Hỏi trợ lý Gemini", use_container_width=True):
                st.success(
                    "💡 Mẹo: dùng nội dung bệnh án này để trao đổi trực tiếp với "
                    "trợ lý Gemini và nhận phác đồ điều trị."
                )
        with col_b3:
            if st.button("💾 Lưu hồ sơ", type="primary", use_container_width=True):
                if not p_name.strip():
                    st.warning("⚠️ Vui lòng nhập họ tên bệnh nhân!")
                elif (not st.session_state.get("phcn_last_analysis")
                      or st.session_state.get("phcn_last_signature") != case_signature):
                    st.warning(
                        "Dữ liệu đã thay đổi sau lần phân tích gần nhất. "
                        "Vui lòng phân tích lại trước khi lưu để tránh lưu kết quả cũ."
                    )
                else:
                    try:
                        patient_token = active_patient.get("patient_token") or ("PHCN-" + uuid.uuid4().hex)
                        visit_id = save_visit(
                            {"name": p_name.strip(),
                             "phone": active_patient.get("phone", ""),
                             "age": int(p_birth_year),
                             "job": p_job.strip(),
                             "patient_token": patient_token},
                            current_reg,
                            st.session_state["phcn_last_payload"],
                            summary_text,
                            st.session_state["phcn_last_analysis"],
                            st.session_state["phcn_last_report"],
                        )
                        st.session_state["phcn_last_visit_id"] = visit_id
                        saved_round_count = save_analysis_rounds(
                            visit_id, st.session_state.get("phcn_analysis_rounds", [])
                        )
                        st.session_state.current_patient = {
                            **active_patient,
                            "name": p_name.strip(),
                            "age": int(p_birth_year),
                            "job": p_job.strip(),
                            "patient_token": patient_token,
                        }
                        st.success(
                            f"Đã lưu lần khám số {visit_id} cho {p_name} vào SQLite cục bộ, "
                            f"kèm {saved_round_count} vòng phân tích."
                        )
                    except Exception as exc:
                        st.error(f"Không thể lưu hồ sơ: {exc}")
        st.markdown("</div>", unsafe_allow_html=True)