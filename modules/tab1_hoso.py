"""Tab 1 – Hồ sơ bệnh nhân và lịch sử khám."""
import streamlit as st
import uuid
from database.storage import list_visits


def render():
    st.subheader("👤 Quản lý Hồ sơ Bệnh nhân và Lịch sử Khám")
    st.info(
        "Nhập thông tin hành chính ban đầu để hệ thống tự động liên kết "
        "sang phiếu khám lâm sàng."
    )
    if "current_patient" not in st.session_state:
        st.session_state.current_patient = {"name": "", "phone": "", "age": 1990, "job": "", "patient_token": "PHCN-" + uuid.uuid4().hex}
    elif not st.session_state.current_patient.get("patient_token"):
        st.session_state.current_patient["patient_token"] = "PHCN-" + uuid.uuid4().hex
    with st.form("patient_form"):
        p_name = st.text_input("Họ tên bệnh nhân", value=st.session_state.current_patient["name"])
        p_phone = st.text_input("Số điện thoại", value=st.session_state.current_patient["phone"])
        p_age = st.number_input(
            "Năm sinh", min_value=1900, max_value=2026,
            value=int(st.session_state.current_patient["age"]),
        )
        p_job = st.text_input("Nghề nghiệp", value=st.session_state.current_patient["job"])
        if st.form_submit_button("💾 Lưu thông tin bệnh nhân", use_container_width=True):
            st.session_state.current_patient = {
                "name": p_name, "phone": p_phone, "age": p_age, "job": p_job,
                "patient_token": st.session_state.current_patient.get("patient_token"),
            }
            st.success(
                f"✅ Đã lưu thông tin cho bệnh nhân: **{p_name}**! "
                "Mời bác sĩ chuyển sang Tab Khám Lâm sàng để tiến hành thăm khám thực thể."
            )
    with st.expander("🗂️ Lịch sử các lần khám đã lưu", expanded=False):
        try:
            saved_visits = list_visits(100)
            if saved_visits:
                st.dataframe([dict(x) for x in saved_visits], use_container_width=True, hide_index=True)
            else:
                st.caption("Chưa có lần khám nào được lưu.")
        except Exception as exc:
            st.error(f"Không đọc được lịch sử: {exc}")