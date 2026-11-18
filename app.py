# PHCN AI 4.5 – Integrated offline-first clinical support
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st
from database.storage import init_db
from modules.tab1_hoso import render as render_tab1
from modules.tab2_trithuc import render as render_tab2
from modules.tab3_kham import render as render_tab3
from modules.tab4_phcn import render as render_tab4
from modules.tab5_doi_soat import render as render_tab5
from modules.tab6_theo_doi import render as render_tab6
from modules.tab7_kehoach import render as render_tab7
from modules.tab8_hethong import render as render_tab8
import os
import hmac

st.set_page_config(
    page_title="PHCN AI 4.5",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """<style>
    .grid-card-box{background:#fff;border-radius:16px;padding:14px 8px;text-align:center;box-shadow:0 3px 8px rgba(0,0,0,.06);border:1px solid #eaeaea;margin-bottom:12px}
    .icon-circle-btn{width:50px;height:50px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:24px;margin:0 auto 8px;color:white;box-shadow:0 2px 5px rgba(0,0,0,.1)}
    .scrollable-feed{max-height:850px;overflow-y:auto;padding-right:12px}
    @media (max-width: 768px) {
      .block-container {padding-left: 0.8rem !important; padding-right: 0.8rem !important; padding-top: 0.8rem !important;}
      [data-testid="stSidebar"] {min-width: 0 !important;}
      [data-testid="stHorizontalBlock"] {gap: 0.55rem !important;}
      [data-testid="stMetric"] {padding: 0.45rem !important;}
      .scrollable-feed {max-height: none; overflow: visible; padding-right: 0;}
      .grid-card-box {padding: 12px 6px; margin-bottom: 8px;}
      .stButton > button, .stDownloadButton > button {min-height: 44px; width: 100%;}
      input, textarea, [data-baseweb="select"] {font-size: 16px !important;}
      h1 {font-size: 1.55rem !important;}
      h2 {font-size: 1.3rem !important;}
      h3 {font-size: 1.12rem !important;}
    }
    </style>""",
    unsafe_allow_html=True,
)

init_db()


def main():
    app_password = os.environ.get("PHCN_APP_PASSWORD", "")
    if app_password:
        if not st.session_state.get("authenticated", False):
            st.title("🔐 PHCN AI 4.5 – Đăng nhập")
            with st.form("login_form"):
                entered = st.text_input("Mật khẩu ứng dụng", type="password")
                submitted = st.form_submit_button("Đăng nhập", type="primary")
            if submitted:
                if hmac.compare_digest(entered, app_password):
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Mật khẩu không đúng.")
            return
    else:
        st.warning("Chưa cấu hình PHCN_APP_PASSWORD. Chỉ dùng trong môi trường riêng tư; không công khai máy chủ khi chưa bật mật khẩu và HTTPS.")

    st.title("🩺 PHCN AI 4.5 – Trợ lý Phục hồi Chức năng và Lâm sàng")
    st.caption(
        "Tích hợp suy luận chuyên biệt + suy luận tổng quát + NLP bệnh sử offline + tổng hợp chẩn đoán sơ bộ + suy luận nhiều vòng · "
        "SQLite cục bộ · kho tri thức và 315 biến thể bài tập · không dùng API AI bên ngoài"
    )
    st.info(
        "Đây là hệ thống hỗ trợ suy luận lâm sàng, không phải công cụ chẩn đoán xác định và không thay thế bác sĩ. "
        "Mọi giả thuyết, điểm thuật toán, cảnh báo và hướng xử trí phải được người hành nghề có thẩm quyền xác minh trước khi áp dụng."
    )

    pages = {
        "👤 Hồ sơ và Lịch sử": render_tab1,
        "📚 Cẩm nang Tri thức": render_tab2,
        "🩺 Khám Lâm sàng": render_tab3,
        "🏋️ Kho Bài tập PHCN": render_tab4,
        "🔎 Đối soát chẩn đoán": render_tab5,
        "📈 Theo dõi tiến triển": render_tab6,
        "🎯 Kế hoạch PHCN": render_tab7,
        "⚙️ Hệ thống & Sao lưu": render_tab8,
    }

    with st.sidebar:
        st.title("PHCN AI 4.5")
        st.caption("Điều hướng nhanh")
        selected_page = st.radio(
            "Chọn chức năng",
            list(pages.keys()),
            key="main_navigation",
            label_visibility="collapsed",
        )
        st.divider()
        patient = st.session_state.get("current_patient", {})
        st.caption("BỆNH NHÂN ĐANG CHỌN")
        st.write(patient.get("name") or "Chưa chọn bệnh nhân")
        if patient.get("age"):
            st.caption(f"Năm sinh: {patient.get('age')}")
        if patient.get("job"):
            st.caption(f"Nghề nghiệp: {patient.get('job')}")

    pages[selected_page]()


if __name__ == "__main__":
    main()