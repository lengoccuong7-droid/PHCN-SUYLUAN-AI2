"""Tab 6 – Theo dõi tiến triển và thống kê học."""
import streamlit as st
from database.storage import list_visits, list_patient_visits_by_id, get_visit_detail


def render():
    st.subheader("📈 Theo dõi tiến triển phục hồi chức năng")
    st.caption(
        "Dữ liệu lấy từ các lần khám đã lưu trong SQLite. "
        "Chỉ so sánh thông tin thực sự có trong hồ sơ; "
        "không tự suy diễn cải thiện nếu thiếu thang đo lặp lại."
    )
    try:
        visits = list_visits(500)
    except Exception as exc:
        st.error(f"Không đọc được dữ liệu theo dõi: {exc}")
        return
    if not visits:
        st.info(
            "Chưa có lần khám nào được lưu. Sau khi lưu lần khám ở Tab Khám Lâm sàng, "
            "dữ liệu sẽ xuất hiện tại đây."
        )
        return
    people = {}
    for v in visits:
        birth = f" · {v['birth_year']}" if v["birth_year"] else ""
        label = f"{v['name']}{birth} · Hồ sơ #{v['patient_id']}"
        people[label] = int(v["patient_id"])
    chosen = st.selectbox(
        "Chọn hồ sơ bệnh nhân", list(people.keys()), key="tab6_patient",
    )
    rows = list_patient_visits_by_id(people[chosen], 200)
    if not rows:
        st.info("Chưa có dữ liệu theo dõi cho hồ sơ này.")
        return
    st.markdown("### Dòng thời gian khám")
    st.dataframe(
        [
            {"Mã lần khám": r["id"], "Ngày giờ": r["created_at"], "Vùng khám": r["region"]}
            for r in rows
        ],
        use_container_width=True,
        hide_index=True,
    )
    opts = {
        f"#{r['id']} · {r['created_at']} · {r['region']}": r["id"]
        for r in rows
    }
    selected = st.selectbox(
        "Xem chi tiết lần khám", list(opts.keys()), key="tab6_visit_detail",
    )
    detail = get_visit_detail(opts[selected])
    if detail:
        with st.expander("Thông tin hành chính", expanded=False):
            st.write({
                "Họ tên": detail.get("name"),
                "Năm sinh": detail.get("birth_year"),
                "Số điện thoại": detail.get("phone") or "Không cung cấp",
                "Nghề nghiệp": detail.get("job"),
            })
        st.markdown("**Tóm tắt dữ liệu khám**")
        st.text_area(
            "Nội dung",
            value=detail.get("summary_text") or "",
            height=220,
            key=f"tab6_summary_{detail['id']}",
        )
        st.markdown("**Kết quả phân tích đã lưu**")
        report = detail.get("report_text") or "Chưa có báo cáo phân tích được lưu."
        st.text_area(
            "Báo cáo",
            value=report,
            height=260,
            key=f"tab6_report_{detail['id']}",
        )
        st.caption(
            "Đây là bản ghi lịch sử, không phải đánh giá hiện trạng hôm nay. "
            "Muốn đánh giá tiến triển cần lượng giá lại cùng thang đo, "
            "cùng điều kiện và cùng cách thực hiện."
        )
    st.markdown("---")
    st.markdown("### 🎓 Thống kê quá trình học")
    st.caption(
        "Bộ não học từ phản hồi của bác sĩ. "
        "Số liệu này cho biết mức độ đã học."
    )
    try:
        from core.learning_engine import get_learning_statistics
        from core.semantic_learner import get_learning_stats as get_semantic_stats
        stats = get_learning_statistics()
        semantic_stats = get_semantic_stats()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Trọng số đã học", stats["so_trong_so_da_hoc"])
        with col2:
            st.metric("Phản hồi đã nhận", stats["so_phan_hoi"])
        with col3:
            st.metric("Từ đồng nghĩa mới", semantic_stats["so_tu_dong_nghia"])
        with col4:
            st.metric("Cụm từ mới", semantic_stats["so_cum_tu"])
        if stats["phan_hoi_gan_nhat"]:
            with st.expander("Phản hồi gần nhất", expanded=False):
                st.dataframe(stats["phan_hoi_gan_nhat"], use_container_width=True)
        if semantic_stats["cum_tu_pho_bien"]:
            with st.expander("Cụm từ phổ biến", expanded=False):
                st.dataframe(semantic_stats["cum_tu_pho_bien"], use_container_width=True)
    except Exception as exc:
        st.warning(f"Không đọc được thống kê học: {exc}")