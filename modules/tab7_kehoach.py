"""Tab 7 – Lập và lưu bản dự thảo kế hoạch PHCN có người hành nghề duyệt."""
import streamlit as st
from database.storage import (
    list_visits, list_patient_visits_by_id, get_visit_detail, save_treatment_plan,
)
from core.knowledge_loader import load_knowledge


def render():
    st.subheader("🎯 Định hướng điều trị và kế hoạch PHCN")
    st.caption(
        "Tạo bản dự thảo theo mục tiêu chức năng và dữ liệu đã khám. "
        "Ứng dụng không tự kê phác đồ; người hành nghề phải kiểm tra và duyệt trước khi áp dụng."
    )
    visits = list_visits(500)
    if not visits:
        st.info("Cần có ít nhất một hồ sơ/lần khám đã lưu trước khi lập kế hoạch.")
        return
    people = {}
    for row in visits:
        label = f"{row['name']} · Hồ sơ #{row['patient_id']}"
        people[label] = int(row['patient_id'])
    chosen_person = st.selectbox("Chọn bệnh nhân", list(people), key="plan_patient")
    patient_id = people[chosen_person]
    rows = list_patient_visits_by_id(patient_id, 200)
    if not rows:
        st.info("Chưa có lần khám để liên kết kế hoạch.")
        return
    visit_labels = {f"#{r['id']} · {r['created_at']} · {r['region']}": int(r['id']) for r in rows}
    chosen_visit = st.selectbox("Lần khám làm căn cứ", list(visit_labels), key="plan_source_visit")
    detail = get_visit_detail(visit_labels[chosen_visit])
    if not detail:
        st.error("Không đọc được lần khám nguồn.")
        return
    st.markdown("#### Dữ liệu khám nguồn")
    st.caption(f"Vùng khám: {detail.get('region')} · Ngày: {detail.get('created_at')}")
    if detail.get("report_text"):
        with st.expander("Xem báo cáo suy luận đã lưu", expanded=False):
            st.text(detail["report_text"])
    st.warning("Chỉ sử dụng kế hoạch sau khi đối chiếu chẩn đoán, chống chỉ định, mức chịu lực và tình trạng hiện tại.")

    catalog = load_knowledge("rehabilitation/exercise_catalog.json")
    groups = catalog.get("groups", [])
    group_map = {g.get("title", g.get("key", "Nhóm bài tập")): g for g in groups}
    selected_group = st.selectbox("Nhóm bài tập tham khảo", list(group_map) or ["Chưa có dữ liệu"])
    exercise_names = [e.get("name", "") for e in group_map.get(selected_group, {}).get("exercises", [])]
    selected_exercise = st.selectbox("Bài tập tham khảo", exercise_names or ["Chưa có bài tập"])
    selected_ex = next((e for e in group_map.get(selected_group, {}).get("exercises", []) if e.get("name") == selected_exercise), {})
    if selected_ex:
        st.caption("Mục tiêu: " + str(selected_ex.get("purpose", "")))
        with st.expander("Xem kỹ thuật cơ bản", expanded=False):
            st.write(selected_ex.get("technique", ""))
            st.warning(selected_ex.get("common_errors", "Đối chiếu kỹ thuật chuẩn trước khi thực hiện."))

    with st.form("phcn_plan_form"):
        goals = st.text_area(
            "Mục tiêu chức năng (nên ghi cụ thể, đo lường được)",
            placeholder="Ví dụ: cải thiện khả năng đứng lên-ngồi xuống; tăng ROM gấp gối; đi bộ độc lập hơn...",
            height=100,
        )
        interventions = st.text_area(
            "Định hướng can thiệp dự kiến",
            placeholder="Ghi kỹ thuật dự kiến, vùng tác động và mục đích; cần người hành nghề duyệt.",
            height=110,
        )
        exercise_dose = st.text_area(
            "Liều lượng / mức hỗ trợ dự kiến",
            placeholder="Số lần, hiệp, thời gian, mức trợ giúp, tần suất và tiêu chí tiến triển – chỉ điền sau lượng giá.",
            height=100,
        )
        precautions = st.text_area(
            "Chống chỉ định, thận trọng và giới hạn cần tuân thủ",
            placeholder="Ví dụ: giới hạn chịu lực sau mổ, hạn chế ROM, đau tăng, nguy cơ té ngã, bệnh nền...",
            height=100,
        )
        stop_criteria = st.text_area(
            "Tiêu chí dừng / đánh giá lại",
            placeholder="Dừng và đánh giá lại khi xuất hiện triệu chứng bất thường, dấu hiệu cảnh báo hoặc đáp ứng vượt ngưỡng an toàn.",
            height=80,
        )
        review_date = st.date_input("Ngày dự kiến đánh giá lại")
        submitted = st.form_submit_button("Lưu bản dự thảo kế hoạch PHCN", type="primary", use_container_width=True)
    if submitted:
        if not goals.strip():
            st.error("Cần ghi ít nhất một mục tiêu chức năng.")
            return
        plan = {
            "region": detail.get("region"),
            "source_visit_id": int(detail["id"]),
            "goals": goals.strip(),
            "interventions": interventions.strip(),
            "selected_exercise_group": selected_group,
            "selected_exercise": selected_exercise,
            "exercise_purpose": selected_ex.get("purpose", ""),
            "exercise_technique": selected_ex.get("technique", ""),
            "exercise_dose": exercise_dose.strip(),
            "precautions": precautions.strip(),
            "stop_criteria": stop_criteria.strip(),
            "review_date": review_date.isoformat(),
            "review_status": "Chờ người hành nghề duyệt",
        }
        try:
            plan_id = save_treatment_plan(patient_id, detail["id"], plan)
            st.success(f"Đã lưu bản dự thảo kế hoạch PHCN #{plan_id}. Bản này chưa được duyệt để áp dụng.")
        except Exception as exc:
            st.error(f"Không thể lưu kế hoạch: {exc}")
