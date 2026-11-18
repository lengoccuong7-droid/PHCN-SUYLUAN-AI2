"""Tab 8 – Quản trị dữ liệu, sao lưu và duyệt đề xuất học."""
import sqlite3
import tempfile
import json
from pathlib import Path
import streamlit as st
from database.storage import DB_PATH, connect, init_db, save_visit
from core.learning_engine import list_learning_proposals, review_learning_proposal
from core.clinical_engine import analyze_case, render_report


def _backup_bytes():
    source = sqlite3.connect(str(DB_PATH))
    try:
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=True) as tmp:
            target = sqlite3.connect(tmp.name)
            try:
                source.backup(target)
                target.commit()
            finally:
                target.close()
            tmp.seek(0)
            return tmp.read()
    finally:
        source.close()


def render():
    st.subheader("⚙️ Hệ thống, sao lưu và kiểm soát tri thức")
    st.caption("Quản lý dữ liệu cục bộ, kiểm tra tài nguyên và duyệt đề xuất học từ phản hồi.")
    st.info("Bộ suy luận 4.5 là hệ thống hỗ trợ quyết định dựa trên quy tắc và NLP offline; không tự học từ ca bệnh để thay đổi kết luận, không đưa ra chẩn đoán xác định thay bác sĩ.")
    init_db()
    db_exists = DB_PATH.exists()
    db_size = DB_PATH.stat().st_size if db_exists else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Cơ sở dữ liệu", "Sẵn sàng" if db_exists else "Chưa tạo")
    col2.metric("Dung lượng SQLite", f"{db_size / 1024:.1f} KB")
    version_file = Path(__file__).resolve().parents[1] / "VERSION"
    app_version = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "Không rõ"
    col3.metric("Phiên bản", app_version)

    required = [
        "clinical_manual.json",
        "clinical_tests/region_tests.json",
        "rehabilitation/exercise_catalog.json",
        "rehabilitation/exercise_details.json",
        "rehabilitation/exercise_library.json",
    ]
    root = Path(__file__).resolve().parents[1] / "knowledge"
    checks = [{"Tài liệu": name, "Trạng thái": "OK" if (root / name).is_file() else "Thiếu"} for name in required]
    st.markdown("#### Kiểm tra kho tri thức")
    st.dataframe(checks, use_container_width=True, hide_index=True)

    st.markdown("#### Ghi nhận offline trên điện thoại")
    st.markdown(
        "[Mở phiếu ghi nhận offline / thêm vào Màn hình chính](/app/static/offline_capture.html)"
    )
    st.caption(
        "Phiếu offline được lưu trong IndexedDB của trình duyệt. Khi có mạng, xuất JSON từ trang offline "
        "rồi nhập tại đây để phân tích và lưu vào SQLite. Mỗi mã phiếu chỉ được nhập một lần."
    )
    offline_file = st.file_uploader("Nhập file phcn_ai_offline_records.json", type=["json"], key="offline_import_file")
    if offline_file is not None and st.button("Phân tích và nhập các phiếu offline", key="import_offline_records", type="primary"):
        try:
            bundle = json.loads(offline_file.getvalue().decode("utf-8"))
            records = bundle.get("records", []) if isinstance(bundle, dict) else []
            if not isinstance(records, list):
                raise ValueError("Cấu trúc records không hợp lệ.")
            imported_count = 0
            skipped_count = 0
            errors = []
            for idx, record in enumerate(records, 1):
                try:
                    record_id = str(record.get("id") or "").strip()
                    case_data = record.get("case_data") or {}
                    token = str(record.get("patient_token") or "").strip()
                    if not record_id or not token or not case_data.get("region"):
                        raise ValueError("Thiếu mã phiếu, mã hồ sơ hoặc vùng khám.")
                    analysis = analyze_case(case_data)
                    report = render_report(analysis)
                    summary = "Phiếu được nhập từ chế độ ghi nhận offline. Thời điểm ghi nhận: " + str(record.get("created_at", "không rõ"))
                    visit_id = save_visit(
                        {"name": str(record.get("patient_label") or token), "phone": "",
                         "age": None, "job": "", "patient_token": token},
                        case_data["region"], case_data, summary, analysis, report,
                        source_record_id=record_id,
                    )
                    if visit_id:
                        imported_count += 1
                except Exception as exc:
                    errors.append(f"Phiếu {idx}: {exc}")
            st.success(f"Đã xử lý {imported_count} phiếu. Mã phiếu đã nhập trước đó sẽ không tạo bản ghi trùng.")
            if errors:
                st.warning("Một số phiếu chưa nhập được:\n" + "\n".join(errors[:10]))
        except Exception as exc:
            st.error(f"Không đọc được file offline: {exc}")

    st.markdown("#### Sao lưu SQLite")
    st.warning("File sao lưu chứa dữ liệu hồ sơ sức khỏe. Chỉ tải về thiết bị cá nhân an toàn; không gửi qua kênh công khai.")
    try:
        backup = _backup_bytes()
        st.download_button(
            "Tải bản sao lưu cơ sở dữ liệu",
            data=backup,
            file_name=f"PHCN_AI_{app_version.replace('.', '_')}_backup.sqlite",
            mime="application/vnd.sqlite3",
            use_container_width=True,
        )
    except Exception as exc:
        st.error(f"Không tạo được bản sao lưu: {exc}")

    st.markdown("#### Đề xuất học đang chờ duyệt")
    proposals = list_learning_proposals("pending")
    if not proposals:
        st.info("Chưa có đề xuất điều chỉnh trọng số nào. Phản hồi không tự thay đổi bộ quy tắc.")
    for proposal in proposals:
        with st.container(border=True):
            st.write(f"**{proposal['hypothesis_key']}** · {proposal['feature_code']} · {proposal['rule_type']}")
            st.caption(f"Trọng số hiện tại: {proposal['old_weight']:.3f} → đề xuất: {proposal['proposed_weight']:.3f}")
            c1, c2 = st.columns(2)
            if c1.button("Duyệt đề xuất", key=f"approve_learning_{proposal['id']}", use_container_width=True):
                if review_learning_proposal(proposal["id"], True):
                    st.success("Đã duyệt. Trọng số sẽ được nạp ở lần phân tích tiếp theo.")
                    st.rerun()
            if c2.button("Từ chối", key=f"reject_learning_{proposal['id']}", use_container_width=True):
                if review_learning_proposal(proposal["id"], False):
                    st.info("Đã từ chối đề xuất.")
                    st.rerun()

    st.markdown("#### Nguyên tắc vận hành")
    st.markdown(
        "- Không có kết nối API AI bên ngoài.\n"
        "- SQLite lưu tại máy chủ/máy chạy ứng dụng.\n"
        "- Không đưa dữ liệu bệnh nhân thật vào bộ kiểm thử.\n"
        "- Nếu truy cập qua Internet công cộng, bắt buộc cấu hình mật khẩu và HTTPS ở reverse proxy.\n"
        "- Khi điện thoại mất kết nối tới máy chủ từ xa, giao diện Streamlit không thể tiếp tục chạy; cần mở lại khi có kết nối."
    )
