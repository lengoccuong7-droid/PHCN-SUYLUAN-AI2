"""Tab 5 – Đối soát chẩn đoán hai chiều tự động."""
import streamlit as st
from core.diagnostic_audit import run_bidirectional_audit, render_audit_report


def render():
    st.subheader("🔎 Đối soát chẩn đoán hai chiều tự động")
    st.caption(
        "Tab này tự đọc dữ liệu từ Tab Khám Lâm sàng. "
        "Không cần nhập lại và không có nút kiểm chứng thủ công."
    )
    last_analysis = st.session_state.get("phcn_last_analysis")
    last_payload = st.session_state.get("phcn_last_payload")
    last_signature = st.session_state.get("phcn_last_signature")
    current_signature = st.session_state.get("phcn_current_signature")
    current_payload = st.session_state.get("phcn_current_payload")
    if not last_analysis or not last_payload:
        st.info(
            "Chưa có kết quả khám. Vào Tab Khám Lâm sàng, chọn vùng khám, "
            "nhập dữ liệu và chạy phân tích. Tab này sẽ tự động đối soát sau đó."
        )
    elif not current_payload or not current_signature:
        st.warning(
            "Chưa có ảnh chụp dữ liệu khám hiện hành để xác nhận kết quả. "
            "Quay lại Tab Khám Lâm sàng và mở phiếu khám đang thực hiện."
        )
    elif last_signature != current_signature:
        st.error(
            "Dữ liệu Tab Khám Lâm sàng đã thay đổi sau lần phân tích gần nhất. "
            "Kết quả cũ không được dùng để đối soát. Hãy chạy phân tích lại."
        )
        st.caption("Cơ chế này ngăn Tab Đối soát hiển thị kết luận dựa trên dữ liệu cũ.")
    else:
        audit = run_bidirectional_audit(current_payload, last_analysis)
        audit_report = render_audit_report(audit)
        st.session_state["phcn_last_audit"] = audit
        st.session_state["phcn_last_audit_report"] = audit_report
        if audit["red_flags"]:
            st.error("🚩 Có cảnh báo an toàn từ Tab Khám Lâm sàng: " + "; ".join(audit["red_flags"]))
        st.warning("**Kết quả kiểm soát:** " + audit["overall"])
        st.markdown("### 1. Chiều thuận – hình thành giả thuyết từ dữ liệu")
        st.markdown(
            "Các giả thuyết dưới đây chỉ được đưa lên khi có ít nhất một dữ kiện gợi ý "
            "trong ghi chép. Đây không phải bảng xếp hạng xác suất."
        )
        if audit["forward"]:
            for item in audit["forward"]:
                with st.container(border=True):
                    st.markdown(
                        f"**{item['label']}** – điểm định hướng "
                        f"{item['do_tin_cay']*100:.0f}/100 ({item['muc_tin_cay']})"
                    )
                    st.markdown(
                        "**Dữ kiện gợi ý:** "
                        + ("; ".join(item["dac_trung_ung_ho"]) or "Chưa ghi nhận")
                    )
                    st.markdown(
                        "**Điểm chưa tương hợp:** "
                        + ("; ".join(item["dac_trung_chong_lai"]) or "Chưa ghi nhận rõ")
                    )
        else:
            st.info(
                "Chưa có kiểu hình nào đủ dữ kiện gợi ý để hình thành giả thuyết cụ thể. "
                "Không tự suy đoán khi dữ liệu chưa đủ."
            )
        st.markdown("### 2. Chiều ngược – kiểm tra từng giả thuyết")
        st.caption(
            "Mỗi giả thuyết được kiểm tra lại bằng các dấu hiệu kỳ vọng. "
            "Dữ kiện không được ghi nhận được xem là 'chưa biết', không tự động xem là âm tính."
        )
        if audit["reverse"]:
            for item in audit["reverse"]:
                with st.expander(
                    f"{item['label']} · {item['do_tin_cay']*100:.0f}/100 ({item['muc_tin_cay']})",
                    expanded=bool(item["dac_trung_ung_ho"] or item["dac_trung_chong_lai"]),
                ):
                    st.markdown("**Ủng hộ:**")
                    for value in item["dac_trung_ung_ho"] or [
                        "Chưa tìm thấy dữ kiện ủng hộ trong phần ghi chép."
                    ]:
                        st.markdown(f"- {value}")
                    st.markdown("**Chống lại hoặc chưa tương hợp:**")
                    for value in item["dac_trung_chong_lai"] or [
                        "Chưa ghi nhận dữ kiện chống lại rõ ràng."
                    ]:
                        st.markdown(f"- {value}")
                    st.markdown(
                        "**Dấu hiệu kỳ vọng chưa có thông tin (không đồng nghĩa âm tính):**"
                    )
                    for value in item["dac_trung_con_thieu"] or [
                        "Không còn mục chưa xác minh trong nhóm dấu hiệu này."
                    ]:
                        st.markdown(f"- {value}")
                    st.info("Ghi chú chuyên môn: " + item["luu_y"])
        else:
            st.info(
                "Vùng khám này chưa có bộ giả thuyết chuyên biệt trong phiên bản hiện tại. "
                "Hệ thống không tự mở rộng kết luận ngoài phạm vi đã lập trình."
            )
        if audit.get("syndromes"):
            st.markdown("### 3. Hội chứng phát hiện")
            for syn in audit["syndromes"]:
                if syn["co_nguy_hiem"]:
                    st.error(f"🚨 {syn['ten']}: {syn['ket_luan']}")
                else:
                    st.info(f"ℹ️ {syn['ten']}: {syn['ket_luan']}")
        st.markdown("### 4. Mâu thuẫn và giới hạn dữ liệu")
        if audit["contradictions"]:
            for item in audit["contradictions"]:
                st.warning(item)
        else:
            st.success(
                "Chưa phát hiện mâu thuẫn tự động từ các trường dữ liệu được kiểm tra. "
                "Điều này không chứng minh chẩn đoán là đúng."
            )
        st.markdown("### 5. Báo cáo đối soát có thể sao chép")
        if st.session_state.get("phcn_audit_report_signature") != last_signature:
            st.session_state["phcn_audit_report_copy"] = audit_report
            st.session_state["phcn_audit_report_signature"] = last_signature
        st.text_area("Báo cáo Tab Đối soát", height=460, key="phcn_audit_report_copy")
        st.caption(
            "Báo cáo được tạo tự động từ dữ liệu Tab Khám Lâm sàng hiện hành. "
            "Nếu sửa dữ liệu, cần phân tích lại để tạo báo cáo mới."
        )
        with st.expander("Giới hạn và nguyên tắc an toàn", expanded=False):
            for item in audit["limitations"]:
                st.markdown(f"- {item}")