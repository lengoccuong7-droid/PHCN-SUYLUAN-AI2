"""Tab 4 – Kho bài tập phục hồi chức năng."""
import streamlit as st
from core.knowledge_loader import load_knowledge


def render():
    catalog = load_knowledge("rehabilitation/exercise_catalog.json")
    legacy = load_knowledge("rehabilitation/exercise_library.json")
    legacy_details = load_knowledge("rehabilitation/exercise_details.json")
    st.subheader("🏋️ Kho bài tập Phục hồi chức năng")
    st.caption("9 nhóm chức năng · 63 bài tập · 315 phương pháp triển khai cụ thể")
    st.warning(
        "Thư viện là tài liệu tham khảo hỗ trợ kỹ thuật viên, không tự động tạo phác đồ. "
        "Cần lượng giá trực tiếp và cá thể hóa. Sau phẫu thuật hoặc gãy xương phải đối chiếu "
        "chỉ định, giới hạn tầm vận động và mức chịu lực. Bài tập nuốt, trẻ nhỏ, hô hấp "
        "và thần kinh cần chuyên viên phù hợp hướng dẫn."
    )
    pathology_options = ["Không lọc bệnh lý"] + list(
        catalog.get("pathology_mapping", {}).keys()
    )
    pathology = st.selectbox(
        "Lọc theo bệnh lý hoặc tình trạng",
        pathology_options,
        key="exercise_pathology_filter",
    )
    allowed = (
        catalog["pathology_mapping"].get(pathology, [])
        if pathology != "Không lọc bệnh lý"
        else [g["key"] for g in catalog["groups"]]
    )
    groups = [g for g in catalog["groups"] if g["key"] in allowed]
    group_titles = {g["title"]: g for g in groups}
    if not group_titles:
        st.info("Không có nhóm bài tập phù hợp với bộ lọc hiện tại.")
        return
    selected_group_title = st.selectbox(
        "Nhóm mục tiêu phục hồi", list(group_titles), key="exercise_group_filter",
    )
    group = group_titles[selected_group_title]
    ex_map = {e["name"]: e for e in group["exercises"]}
    selected_ex = st.selectbox("Chọn bài tập", list(ex_map), key="exercise_item_filter")
    ex = ex_map[selected_ex]
    st.markdown(f"### {ex['name']}")
    st.markdown("**Mục tiêu bài tập**")
    st.write(ex["purpose"])
    st.markdown("**Kỹ thuật cơ bản**")
    st.write(ex["technique"])
    st.markdown("**Lỗi thường gặp**")
    st.write(ex["common_errors"])
    st.markdown("### Các phương pháp triển khai")
    st.caption(
        "Mỗi phương pháp có cách hỗ trợ và kỹ thuật riêng; "
        "không phải chỉ thay dụng cụ hoặc tăng độ khó."
    )
    variants = ex.get("variants", [])
    if not variants:
        st.info("Bài tập này chưa có phương pháp triển khai chi tiết.")
    for i, v in enumerate(variants, 1):
        title = v.get("method", v.get("equipment", "Phương pháp"))
        with st.expander(f"Phương pháp {i}: {title}", expanded=(i == 1)):
            st.markdown("**Tên phương pháp**")
            st.write(v["name"])
            st.markdown("**Mục tiêu hoặc khi nào cân nhắc**")
            st.write(v["purpose"])
            st.markdown("**Tư thế và dụng cụ chuẩn bị**")
            st.write(v.get("setup", v.get("equipment", "Theo lượng giá")))
            st.markdown("**Kỹ thuật thực hiện từng bước**")
            st.write(v["technique"])
            st.markdown("**Liều lượng tham khảo**")
            st.info(v["dose"])
            st.markdown("**Cách tăng mức hoặc tiến triển**")
            st.write(v.get("progression", "Chỉ tiến triển sau lượng giá."))
            st.markdown("**Cách giảm mức hoặc thoái triển**")
            st.write(v.get("regression", "Giảm biên độ hoặc tăng trợ giúp."))
            st.markdown("**Lỗi thường gặp**")
            st.write(v.get("common_errors", ex["common_errors"]))
            st.markdown("**An toàn và điều kiện giám sát**")
            st.warning(v["safety"])
            st.markdown("**Dấu hiệu cần dừng**")
            st.write(
                v.get(
                    "stop_criteria",
                    "Dừng khi triệu chứng bất thường hoặc chất lượng vận động suy giảm.",
                )
            )
            st.caption(
                v.get(
                    "supervision",
                    "Mức giám sát do kỹ thuật viên quyết định sau lượng giá.",
                )
            )
    if pathology in legacy:
        with st.expander("Bài tập chuyên biệt theo bệnh lý (thư viện hiện có)", expanded=False):
            st.caption(
                "Một số can thiệp chuyên biệt không thể thay thế bằng biến thể dụng cụ "
                "của bài tập vận động thông thường."
            )
            items = legacy.get(pathology, [])
            guides = legacy_details.get(pathology, [])
            for idx, item in enumerate(items):
                guide = guides[idx] if idx < len(guides) else {}
                with st.expander(item, expanded=False):
                    st.write("**Công dụng:**", guide.get("purpose", "Cần lượng giá để xác định mục tiêu."))
                    st.write("**Kỹ thuật:**", guide.get("technique", item))
                    st.write("**Tư thế:**", guide.get("position", "Theo hướng dẫn chuyên môn."))
                    st.info(guide.get("dose", "Liều lượng cá thể hóa."))
                    st.warning(
                        guide.get(
                            "safety",
                            "Chỉ thực hiện khi được chuyên viên phù hợp hướng dẫn.",
                        )
                    )